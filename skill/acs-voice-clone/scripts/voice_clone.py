#!/usr/bin/env python3
"""Offline voice-clone jobs with fingerprinted segments and fail-fast GPU ownership."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import wave

VERSION = '1.0'
DEFAULT_ROOT = Path.home()/'.local/share/acs-voice-clone'
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(obj):
    return digest_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode())


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, obj):
    if path.is_symlink():
        raise ValueError('拒绝覆盖软链接: '+str(path))
    fd, name = tempfile.mkstemp(prefix='.voice-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def inside(path, root):
    return path == root or root in path.parents


def protected(path):
    roots = [PACKAGE_ROOT, *(Path(p).expanduser().resolve() for p in
        os.environ.get('ACS_VOICE_PROTECTED_ROOTS', '').split(os.pathsep) if p)]
    return any(inside(path.resolve(), root) for root in roots)


def segments_from(path):
    raw = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.json':
        obj = json.loads(raw)
        rows = obj.get('segments') if isinstance(obj, dict) else obj
        if not isinstance(rows, list):
            raise ValueError('JSON需要segments数组或字符串数组')
    else:
        rows = []
        for para in re.split(r'\n\s*\n', raw.strip()):
            para = para.strip()
            chunk = ''
            for sentence in re.split(r'(?<=[。！？!?；;])', para):
                while len(sentence) > 140:
                    if chunk:
                        rows.append(chunk)
                        chunk = ''
                    rows.append(sentence[:140])
                    sentence = sentence[140:]
                if len(chunk)+len(sentence) > 140:
                    rows.append(chunk)
                    chunk = ''
                chunk += sentence
            if chunk.strip():
                rows.append(chunk.strip())
    result = []
    seen = set()
    for i, row in enumerate(rows or []):
        if isinstance(row, str):
            row = {'id':f's{i+1:02}', 'text':row}
        if not isinstance(row, dict) or not isinstance(row.get('text'), str):
            raise ValueError('每段必须有text字符串')
        sid = row.get('id', f's{i+1:02}')
        text = row['text'].strip()
        spoken = row.get('spoken_text', text)
        if not isinstance(sid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', sid) or sid in seen:
            raise ValueError('片段ID重复或非法')
        if not isinstance(spoken, str) or not text or not spoken.strip() or max(len(text),len(spoken)) > 300:
            raise ValueError('每段必须非空且不超过300字符；长段请拆分')
        seen.add(sid)
        result.append({'id':sid, 'text':text, 'spoken_text':spoken.strip()})
    if not result:
        raise ValueError('文稿为空')
    return result


def runtime_check(root, voice, deep=False):
    if not re.fullmatch(r'[a-z0-9-]+', voice):
        raise ValueError('声音配置ID非法')
    runtime = read_json(root/'runtime.json')
    profile_path = root/'voices'/voice/'profile.json'
    profile = read_json(profile_path)
    ref = profile_path.parent/profile['reference_file']
    if not inside(ref.resolve(), profile_path.parent.resolve()):
        raise ValueError('参考路径越界')
    if sha(ref) != profile['reference_sha256']:
        raise ValueError('参考音频指纹变化；先核实，不自动覆盖配置')
    if not profile.get('consent_note') or not profile.get('reference_text'):
        raise ValueError('缺少声音授权记录或参考文字')
    if not (root/'env/bin/python').is_file():
        raise ValueError('固定Python环境缺失')
    for item in runtime['model_files']:
        file = root/'model'/item['path']
        if not inside(file.resolve(), (root/'model').resolve()):
            raise ValueError('模型路径越界')
        stat = file.stat()
        if stat.st_size != item['size'] or stat.st_mtime_ns != item['mtime_ns']:
            raise ValueError('模型文件已变化: '+item['path'])
        if deep and sha(file) != item['sha256']:
            raise ValueError('模型哈希异常: '+item['path'])
    return runtime, profile, ref


@contextmanager
def exclusive(path):
    if path.is_symlink():
        raise ValueError('执行保护文件不可为软链接')
    with open(path, 'a+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('另一个配音任务正在使用本机GPU；本次未生成，请稍后按需重试')
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def safe_job(path, root):
    out = path.expanduser().absolute()
    if out.is_symlink() or out != out.resolve():
        # /tmp and user paths may contain OS symlinks: use their canonical spelling.
        raise ValueError('输出目录请使用真实绝对路径，不通过软链接写入')
    if protected(out) or inside(out, root.resolve()) or out in [Path('/'),Path.home()]:
        raise ValueError('输出须为独立任务目录，不能写模型、环境、Skill包或受保护目录')
    if out.exists() and not (out/'manifest.json').exists() and any(out.iterdir()):
        raise ValueError('非空目录不是本Skill任务；请使用新目录')
    return out


def cached_take(out, item, key):
    if not item or item.get('key') != key:
        return False
    path = out/item['file']
    if not inside(path.resolve(), out.resolve()) or path.is_symlink():
        raise ValueError('片段路径越界')
    if not path.is_file() or sha(path) != item['sha256']:
        raise ValueError('已有片段缺失或被修改；保留现场，使用新任务目录')
    return True


def check_audio(audio, sample_rate, token_count, max_tokens):
    import numpy as np
    if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
        raise ValueError('音频为空或有非有限值')
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio.astype(np.float64)**2)))
    duration = len(audio)/sample_rate
    if peak < 1e-5 or rms < 1e-6 or duration < 0.15:
        raise ValueError('音频为空白或过短')
    if token_count is not None and token_count >= max_tokens:
        raise ValueError('达到生成token上限，疑似截断；拆短该段后新建任务')
    gain = min(1.0, .97/peak)
    return {'duration':duration, 'samples':len(audio), 'sample_rate':sample_rate,
            'raw_peak':peak, 'rms':rms, 'gain':gain, 'peak':peak*gain,
            'token_count':token_count, 'machine_waveform_pass':True}


def write_wav(path, audio, sample_rate):
    import numpy as np
    if path.exists():
        raise ValueError('目标片段已存在，禁止覆盖: '+str(path))
    partial = path.with_suffix('.partial')
    with wave.open(str(partial), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
    os.replace(partial, path)


def assemble(out, segments, manifest, pause):
    timeline = []
    cursor = 0
    sr = None
    frames = []
    for index, segment in enumerate(segments):
        item = manifest['takes'][segment['id']]
        if not cached_take(out, item, item['key']):
            raise ValueError('缺少片段')
        with wave.open(str(out/item['file'])) as w:
            if w.getnchannels()!=1 or w.getsampwidth()!=2:
                raise ValueError('片段格式异常')
            if sr is None:
                sr = w.getframerate()
            if sr != w.getframerate():
                raise ValueError('片段采样率不一致')
            count = w.getnframes()
            frames.append(w.readframes(count))
        timeline.append({'id':segment['id'], 'text':segment['text'], 'spoken_text':segment['spoken_text'],
                         'start':cursor/sr, 'end':(cursor+count)/sr, 'file':item['file']})
        cursor += count
        if index+1 < len(segments):
            gap = round(pause*sr)
            frames.append(b'\0\0'*gap)
            cursor += gap
    dest = out/'旁白.wav'
    if dest.is_symlink():
        raise ValueError('拒绝覆盖软链接')
    if dest.exists() and (not manifest.get('output_sha256') or sha(dest)!=manifest['output_sha256']):
        raise ValueError('已有合成旁白被外部修改或未登记，拒绝覆盖')
    tmp = out/'旁白.partial'
    with wave.open(str(tmp), 'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(b''.join(frames))
    os.replace(tmp, dest)
    save_json(out/'timeline.json', {'sample_rate':sr,'duration':cursor/sr,'segments':timeline,
                                 'notice':'段落时间轴，不是逐词字幕；本人授权AI合成'})
    return sha(dest), cursor/sr


def generate(a, runtime, profile, ref):
    if not a.authorized:
        raise ValueError('本次尚未确认配音授权；未生成')
    root = a.runtime_root.expanduser().resolve()
    out = safe_job(a.output_dir, root)
    segments = segments_from(a.input)
    ids = {s['id'] for s in segments}
    if not set(a.redo or []).issubset(ids):
        raise ValueError('redo包含不存在的片段ID')
    if not 0 <= a.pause <= 5 or not math.isfinite(a.pause):
        raise ValueError('停顿须在0至5秒')
    spec = {'version':VERSION, 'segments':segments,'voice':profile, 'model':fingerprint(runtime),
            'seed':a.seed,'pause':a.pause,'temperature':.7,'top_p':.9,'max_tokens':1200}
    job_key = fingerprint(spec)
    out.mkdir(parents=True, exist_ok=True)
    with exclusive(out/'.job.lock'):
        mpath = out/'manifest.json'
        manifest = read_json(mpath) if mpath.exists() else {'schema':1,'job_key':job_key,'takes':{},'created':time.time()}
        if manifest['job_key'] != job_key:
            raise ValueError('输入、声音或参数已变化；请新建输出目录')
        # Never reuse a segment merely because its file name exists.
        pending = []
        for i,s in enumerate(segments):
            key = fingerprint({'job':job_key,'segment':s})
            item = manifest['takes'].get(s['id'])
            if item and item.get('key') != key:
                raise ValueError('片段清单与任务指纹不一致')
            reuse = cached_take(out,item,key)
            if not reuse or s['id'] in (a.redo or []):
                pending.append((i,s,key,item))
        if not pending and manifest.get('state')=='generated' and (out/'旁白.wav').exists() and sha(out/'旁白.wav')==manifest.get('output_sha256'):
            print(json.dumps({'status':'reused','output':str(out/'旁白.wav'),'segments':len(segments)},ensure_ascii=False))
            return
        if not pending and (out/'旁白.wav').exists() and sha(out/'旁白.wav')!=manifest.get('output_sha256'):
            raise ValueError('已合成旁白被修改；拒绝覆盖')
        with exclusive(root/'.generation.lock'):
            manifest.update(state='generating', voice=profile['id'], spec=spec)
            save_json(mpath,manifest)
            save_json(out/'input.json', {'segments':segments,'source_sha256':sha(a.input)})
            (out/'takes').mkdir(exist_ok=True)
            if (out/'takes').is_symlink():
                raise ValueError('takes不可是软链接')
            try:
                if pending:
                    import numpy as np
                    import mlx.core as mx
                    from mlx_audio.tts.utils import load_model
                    model = load_model(str(root/'model'))
                    sr = model.sample_rate
                    if sr != 24000:
                        raise ValueError('模型采样率与已验证配置不一致')
                for i,s,key,old in pending:
                    attempt = (old.get('attempt',0)+1) if old else 0
                    seed = a.seed+i+attempt*1000
                    mx.random.seed(seed)
                    chunks = []; tokens = []
                    print('GENERATING',s['id'],flush=True)
                    for r in model.generate(text=s['spoken_text'], ref_audio=str(ref), ref_text=profile['reference_text'],
                                            lang_code='chinese',temperature=.7,top_p=.9,max_tokens=1200,verbose=False):
                        chunks.append(np.asarray(r.audio).reshape(-1))
                        if isinstance(getattr(r,'token_count',None),int):
                            tokens.append(r.token_count)
                    audio = np.concatenate(chunks) if chunks else np.array([])
                    quality = check_audio(audio,sr,sum(tokens) if tokens else None,1200)
                    filename = f"takes/{s['id']}-{key[:10]}-v{attempt+1}.wav"
                    # An interrupted orphan stays intact; choose a different file name.
                    if (out/filename).exists():
                        filename = f"takes/{s['id']}-{key[:10]}-v{attempt+1}-{time.time_ns()}.wav"
                    write_wav(out/filename,audio*quality['gain'],sr)
                    manifest['takes'][s['id']] = {'file':filename,'sha256':sha(out/filename),'key':key,
                        'seed':seed,'attempt':attempt,'quality':quality}
                    save_json(mpath,manifest)
                    print('READY',s['id'],round(quality['duration'],3),flush=True)
                    mx.clear_cache()
                digest,duration = assemble(out,segments,manifest,a.pause)
                save_json(out/'quality.json',{'segments':{k:v['quality'] for k,v in manifest['takes'].items()},
                    'duration':duration,'machine_waveform_pass':True,'listening_review':'not_performed',
                    'notice':'波形通过不代表内容、音色和自然度已验收'})
                manifest.update(state='generated',output_sha256=digest,duration=duration)
                manifest.pop('error',None)
                save_json(mpath,manifest)
                print(json.dumps({'status':'generated','output':str(out/'旁白.wav'),'duration':duration,'segments':len(segments)},ensure_ascii=False))
            except Exception as exc:
                manifest.update(state='incomplete',error=str(exc))
                save_json(mpath,manifest)
                raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root',type=Path,default=DEFAULT_ROOT)
    sub = p.add_subparsers(dest='action',required=True)
    d = sub.add_parser('doctor');d.add_argument('--deep',action='store_true');d.add_argument('--voice',default='self')
    g = sub.add_parser('generate');g.add_argument('--voice',default='self')
    g.add_argument('--input',type=Path,required=True);g.add_argument('--output-dir',type=Path,required=True)
    g.add_argument('--authorized',action='store_true');g.add_argument('--seed',type=int,default=42)
    g.add_argument('--pause',type=float,default=.3);g.add_argument('--redo',action='append')
    a = p.parse_args()
    for key in ['HF_HUB_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_IMPLICIT_TOKEN','TRANSFORMERS_OFFLINE']:
        os.environ[key]='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    root = a.runtime_root.expanduser().resolve()
    try:
        runtime,profile,ref = runtime_check(root,a.voice,getattr(a,'deep',False))
        if a.action=='doctor':
            check = subprocess.run([str(root/'env/bin/python'),'-B','-c',
                'import mlx.core,mlx_audio.tts.utils; print("MLX_IMPORT_OK")'],capture_output=True,text=True)
            if check.returncode:
                raise RuntimeError('运行环境无法加载MLX（可能为沙箱Metal限制）: '+check.stderr[-1000:])
            print(json.dumps({'status':'ready','root':str(root),'model':runtime['model_id'],'voice':profile['speaker'],
                              'reference_sha256':profile['reference_sha256'],'deep':a.deep},ensure_ascii=False))
        elif Path(sys.prefix).resolve() != (root/'env').resolve():
            os.execv(str(root/'env/bin/python'),[str(root/'env/bin/python'),'-B',str(Path(__file__).resolve()),*sys.argv[1:]])
        else:
            generate(a,runtime,profile,ref)
        return 0
    except (ValueError,RuntimeError,OSError,KeyError) as exc:
        print('ERROR:',str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
