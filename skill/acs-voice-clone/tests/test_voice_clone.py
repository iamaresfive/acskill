import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import voice_clone as v
from verify_voice import compare
import numpy as np


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def input(self,text,name='input.txt'):
        p=self.root/name;p.write_text(text,encoding='utf-8');return p

    def test_empty(self):
        with self.assertRaises(ValueError):v.segments_from(self.input('  '))

    def test_plain_split_preserves_text(self):
        text='招生只是开始。'*40
        rows=v.segments_from(self.input(text))
        self.assertEqual(''.join(r['text'] for r in rows),text)
        self.assertTrue(all(len(r['text'])<=140 for r in rows))

    def test_original_and_pronunciation_distinct(self):
        rows=v.segments_from(self.input(json.dumps({'segments':[{'text':'AI','spoken_text':'A I'}]}),'input.json'))
        self.assertEqual(rows[0]['text'],'AI');self.assertEqual(rows[0]['spoken_text'],'A I')

    def test_duplicate_id(self):
        with self.assertRaises(ValueError):
            v.segments_from(self.input(json.dumps([{'id':'s','text':'甲'},{'id':'s','text':'乙'}]),'input.json'))

    def test_path_traversal_id(self):
        with self.assertRaises(ValueError):v.segments_from(self.input('[{"id":"../bad","text":"甲"}]','input.json'))

    def test_overlong_json(self):
        with self.assertRaises(ValueError):v.segments_from(self.input(json.dumps(['字'*301]),'input.json'))

    def test_empty_spoken(self):
        with self.assertRaises(ValueError):v.segments_from(self.input('[{"text":"甲","spoken_text":""}]','input.json'))

    def test_unauthorized_does_not_write(self):
        with self.assertRaises(ValueError):v.generate(argparse.Namespace(authorized=False),{}, {},None)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_non_job_rejected(self):
        self.input('existing')
        with self.assertRaises(ValueError):v.safe_job(self.root,self.root/'runtime')

    def test_skill_package_rejected(self):
        with self.assertRaises(ValueError):v.safe_job(v.PACKAGE_ROOT/'output-test',self.root/'runtime')

    def test_configured_protected_root_rejected(self):
        source = self.root/'private-sources'
        with patch.dict(os.environ, {'ACS_VOICE_PROTECTED_ROOTS':str(source)}):
            with self.assertRaises(ValueError):v.safe_job(source/'output',self.root/'runtime')
            self.assertEqual(v.safe_job(self.root/'job',self.root/'runtime'),self.root/'job')

    def test_multiple_protected_roots(self):
        roots = [self.root/'sources',self.root/'archive']
        with patch.dict(os.environ, {'ACS_VOICE_PROTECTED_ROOTS':os.pathsep.join(map(str,roots))}):
            self.assertTrue(all(v.protected(p/'child') for p in roots))
            self.assertFalse(v.protected(self.root/'sources-other'))

    def test_cache_mismatch_is_not_reused(self):
        file=self.input('first','take.wav')
        item={'key':'a','file':file.name,'sha256':v.sha(file)}
        self.assertTrue(v.cached_take(self.root,item,'a'))
        self.assertFalse(v.cached_take(self.root,item,'b'))
        file.write_text('changed')
        with self.assertRaises(ValueError):v.cached_take(self.root,item,'a')

    def test_lock_fails_fast_and_releases(self):
        path=self.root/'.lock'
        with v.exclusive(path):
            with self.assertRaises(RuntimeError):
                with v.exclusive(path):pass
        with v.exclusive(path):pass

    def test_audio_nan(self):
        with self.assertRaises(ValueError):v.check_audio(np.array([float('nan')]),24000,2,1200)

    def test_audio_silence(self):
        with self.assertRaises(ValueError):v.check_audio(np.zeros(24000),24000,2,1200)

    def test_audio_cap(self):
        with self.assertRaises(ValueError):v.check_audio(np.ones(24000)*.1,24000,1200,1200)

    def test_peak_limited(self):
        q=v.check_audio(np.ones(24000)*1.2,24000,100,1200)
        self.assertAlmostEqual(q['peak'],.97)

    def test_write_preserves_existing(self):
        p=self.root/'a.wav';v.write_wav(p,np.ones(24000)*.1,24000)
        h=v.sha(p)
        with self.assertRaises(ValueError):v.write_wav(p,np.zeros(24000),24000)
        self.assertEqual(h,v.sha(p))

    def test_real_duration_timeline(self):
        segments=[{'id':'a','text':'甲','spoken_text':'甲'},{'id':'b','text':'乙','spoken_text':'乙'}]
        m={'takes':{}}
        for s,n in zip(segments,[24000,12000]):
            file=self.root/(s['id']+'.wav');v.write_wav(file,np.ones(n)*.1,24000)
            m['takes'][s['id']]={'key':s['id'],'file':file.name,'sha256':v.sha(file)}
        digest,duration=v.assemble(self.root,segments,m,.3)
        self.assertEqual(duration,1.8)
        t=v.read_json(self.root/'timeline.json')['segments']
        self.assertEqual(t[1]['start'],1.3);self.assertEqual(t[1]['end'],1.8)
        with self.assertRaises(ValueError):v.assemble(self.root,segments,m,.3)
        m['output_sha256']=digest
        self.assertEqual(v.assemble(self.root,segments,m,.3)[0],digest)

    def test_input_fingerprint_changes(self):
        self.assertNotEqual(v.fingerprint({'text':'甲'}),v.fingerprint({'text':'乙'}))

    def test_changed_input_refuses_existing_job(self):
        out=self.root/'job';out.mkdir()
        v.save_json(out/'manifest.json',{'job_key':'old-input','takes':{}})
        h=v.sha(out/'manifest.json')
        args=argparse.Namespace(authorized=True,runtime_root=self.root/'runtime',output_dir=out,
            input=self.input('新文稿'),redo=None,pause=.3,seed=42)
        with self.assertRaises(ValueError):v.generate(args,{}, {},None)
        self.assertEqual(h,v.sha(out/'manifest.json'))

    def test_invalid_redo_does_not_create_job(self):
        out=self.root/'job'
        args=argparse.Namespace(authorized=True,runtime_root=self.root/'runtime',output_dir=out,
            input=self.input('文稿'),redo=['missing'],pause=.3,seed=42)
        with self.assertRaises(ValueError):v.generate(args,{}, {},None)
        self.assertFalse(out.exists())

    def test_symlink_take_is_rejected(self):
        original=self.input('audio','original.wav');link=self.root/'link.wav';link.symlink_to(original)
        with self.assertRaises(ValueError):v.cached_take(self.root,{'key':'k','file':'link.wav','sha256':v.sha(original)},'k')

    def test_asr_exact_and_missing(self):
        self.assertEqual(compare('今天聊 AI。','今天聊AI')['status'],'machine_text_match')
        self.assertEqual(compare('招生只是开始交付才是关键','招生只是开始')['status'],'needs_review')
        self.assertEqual(compare('','')['status'],'needs_review')


if __name__=='__main__':unittest.main()
