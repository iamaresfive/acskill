#!/usr/bin/env python3
"""Offline ASR content screening; never substitutes for listening or identity checks."""
import argparse
import difflib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

from voice_clone import read_json, save_json, sha, fingerprint, cached_take, protected


def normalized(text):
    text = unicodedata.normalize('NFKC',text).lower()
    return ''.join(c for c in text if c.isalnum())


def compare(expected,actual):
    left,right = normalized(expected),normalized(actual)
    ratio = difflib.SequenceMatcher(None,left,right).ratio()
    differences = [{'operation':tag,'expected':left[i:j],'recognized':right[k:l]}
                   for tag,i,j,k,l in difflib.SequenceMatcher(None,left,right).get_opcodes() if tag!='equal']
    # Exact normalized text is the only automatic content-match label.
    return {'similarity':round(ratio,4),'differences':differences,
            'status':'machine_text_match' if left==right and left else 'needs_review'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job',type=Path,required=True)
    p.add_argument('--model',choices=['medium','large-v3'],default='medium')
    p.add_argument('--python',type=Path,default=Path(sys.executable))
    p.add_argument('--threads',type=int,default=4)
    a = p.parse_args()
    for key in ['HF_HUB_OFFLINE','HF_HUB_DISABLE_TELEMETRY','HF_HUB_DISABLE_IMPLICIT_TOKEN','TRANSFORMERS_OFFLINE']:
        os.environ[key]='1'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    try:
        out = a.job.expanduser().resolve()
        # Reports only belong in a generated external job, never in source archives.
        if protected(out):
            raise ValueError('不向Skill包或受保护目录写入转写报告')
        manifest = read_json(out/'manifest.json')
        if manifest.get('state')!='generated' or sha(out/'旁白.wav')!=manifest.get('output_sha256'):
            raise ValueError('配音未完成或音频已变化')
        segments = manifest['spec']['segments']
        for s in segments:
            item=manifest['takes'][s['id']]
            if not cached_take(out,item,item['key']):
                raise ValueError('片段不完整')
        key=fingerprint({'audio':manifest['output_sha256'],'takes':manifest['takes'],
                         'segments':segments,'model':a.model,'checker_version':1})
        path=out/f'asr-review-{a.model}.json'
        if path.exists():
            old=read_json(path)
            if old.get('key')==key:
                save_json(out/'asr-review.json',old)
                print(json.dumps({'status':old['status'],'reused':True,'report':str(path)},ensure_ascii=False))
                return 0 if old['status']=='machine_text_match' else 3
        if importlib.util.find_spec('faster_whisper') is None:
            if (not a.python.is_file() or a.python.absolute() == Path(sys.executable).absolute()
                    or os.environ.get('ACS_VOICE_ASR_REEXEC')=='1'):
                raise ValueError('离线Whisper环境缺失；用--python指定已安装faster-whisper的环境，未自动安装或联网')
            os.environ['ACS_VOICE_ASR_REEXEC']='1'
            os.execv(str(a.python),[str(a.python),'-B',str(Path(__file__).resolve()),*sys.argv[1:]])
        from faster_whisper import WhisperModel
        model=WhisperModel(a.model,device='cpu',compute_type='int8',local_files_only=True,cpu_threads=a.threads)
        rows=[]
        for s in segments:
            file=out/manifest['takes'][s['id']]['file']
            recognized,info=model.transcribe(str(file),language='zh',beam_size=5,word_timestamps=True,vad_filter=False)
            transcript=[{'start':x.start,'end':x.end,'text':x.text} for x in recognized]
            text=''.join(x['text'] for x in transcript)
            row={'id':s['id'],'expected':s['spoken_text'],'recognized':text,'transcript':transcript,
                 **compare(s['spoken_text'],text)}
            rows.append(row)
            print(json.dumps(row,ensure_ascii=False),flush=True)
        status='machine_text_match' if all(r['status']=='machine_text_match' for r in rows) else 'needs_review'
        report={'key':key,'model':a.model,'status':status,'segments':rows,'listening_review':'not_performed',
                'notice':'机器差异筛查，不是音色相似度、自然度或人工听验结论；同音字/数字/缩写须结合音频复核'}
        save_json(path,report);save_json(out/'asr-review.json',report)
        print(json.dumps({'status':status,'report':str(path)},ensure_ascii=False))
        return 0 if status=='machine_text_match' else 3
    except (ValueError,OSError,RuntimeError,KeyError) as exc:
        print('ERROR:',str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
