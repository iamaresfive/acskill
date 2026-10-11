#!/usr/bin/env python3
"""Build a persistent, offline runtime from a previously working local installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import venv
import wave

from voice_clone import protected


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root', type=Path, default=Path.home()/'.local/share/acs-voice-clone')
    p.add_argument('--reuse-env', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--reference-text', required=True)
    p.add_argument('--voice-id', default='self')
    p.add_argument('--speaker', required=True, help='声音主体名称或仅本机使用的代称')
    p.add_argument('--consent-note', required=True)
    p.add_argument('--authorized', action='store_true')
    a = p.parse_args()
    if not a.authorized or not a.consent_note.strip():
        p.error('需本人明确授权，不能把命令参数当作授权来源')
    root = a.runtime_root.expanduser().absolute()
    if protected(root) or root.resolve() in [Path('/'),Path.home().resolve()]:
        p.error('模型与声音工作副本必须放在独立目录，不能写Skill包或受保护目录')
    if not re.fullmatch(r'[a-z0-9-]+', a.voice_id) or not a.speaker.strip():
        p.error('声音ID仅可用小写英文、数字和连字符，声音主体不可为空')
    if root.exists() or root.is_symlink():
        p.error('目标已经存在；保留现场，使用 doctor 检查，不覆盖安装')
    old_python = a.reuse_env/'bin/python'
    code = "import sys,sysconfig,json,importlib.metadata as m;print(json.dumps({'version':list(sys.version_info[:2]),'site':sysconfig.get_paths()['purelib'],'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))"
    old = json.loads(subprocess.check_output([str(old_python), '-B', '-c', code], text=True))
    if old['version'] != list(sys.version_info[:2]):
        p.error('必须用与原环境相同主次版本的Python初始化')
    config = json.loads((a.model/'config.json').read_text())
    if (config.get('model_type') != 'qwen3_tts' or config.get('tts_model_type') != 'base'
            or config.get('tts_model_size') != '1b7' or config.get('quantization',{}).get('bits') != 8
            or not (a.model/'model.safetensors').is_file()):
        p.error('需要已下载完整的Qwen3-TTS 1.7B Base 8bit模型，不自动更换型号')
    with wave.open(str(a.reference)) as w:
        duration = w.getnframes()/w.getframerate()
        if w.getnchannels() != 1 or w.getsampwidth() != 2 or w.getframerate() != 24000 or not 3 <= duration <= 30:
            p.error('参考音频必须为3至30秒、单声道24kHz PCM16 WAV')
    if not a.reference_text.strip():
        p.error('参考文字不能为空')
    os.umask(0o077)
    root.mkdir(parents=True)
    venv.EnvBuilder(with_pip=False, symlinks=True).create(root/'env')
    py = root/'env/bin/python'
    site = Path(subprocess.check_output([str(py), '-c', 'import sysconfig;print(sysconfig.get_paths()["purelib"])'], text=True).strip())
    shutil.copytree(old['site'], site, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print('ENV_COPIED', flush=True)
    shutil.copytree(a.model, root/'model', ignore=shutil.ignore_patterns('.cache', '.DS_Store'))
    entries = []
    for file in sorted((root/'model').rglob('*')):
        if file.is_file():
            rel = file.relative_to(root/'model')
            digest = sha(file)
            if digest != sha(a.model/rel):
                raise RuntimeError('模型复制校验失败: '+str(rel))
            stat = file.stat()
            entries.append({'path':str(rel), 'sha256':digest, 'size':stat.st_size, 'mtime_ns':stat.st_mtime_ns})
    voices = root/'voices'/a.voice_id
    voices.mkdir(parents=True)
    shutil.copy2(a.reference, voices/'reference.wav')
    digest = sha(a.reference)
    if digest != sha(voices/'reference.wav'):
        raise RuntimeError('声音参考复制校验失败')
    profile = {'id':a.voice_id, 'speaker':a.speaker.strip(), 'reference_file':'reference.wav',
               'reference_sha256':digest, 'reference_text':a.reference_text,
               'source':str(a.reference.absolute()), 'consent_note':a.consent_note,
               'scope':'本人授权文稿本地合成；不授权上传、发布或其他身份用途'}
    (voices/'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2)+'\n')
    runtime = {'schema':1, 'model_id':'mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit',
               'model_files':entries, 'python_version':old['version'], 'packages':old['packages']}
    (root/'runtime.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2)+'\n')
    print('READY', root, 'model_files', len(entries), 'reference_seconds', round(duration,3), flush=True)


if __name__ == '__main__':
    main()
