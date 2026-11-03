"""离线合成用例；example.invalid不是新闻来源，不计真实采编验证。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('brief.py')
spec = importlib.util.spec_from_file_location('brief', SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(n=8):
    cards = []
    for i in range(n):
        sec = ['policy', 'market', 'sentiment'][i % 3]
        cards.append({
            'section': sec, 'kind': {'policy': '合规提示', 'market': '机构经营', 'sentiment': '司法风险'}[sec],
            'title': f'合成测试事项{i}，仅用于排版验收', 'fact': '以下均为虚构测试材料，不是实际新闻。',
            'scope': '虚构测试对象', 'event_date': '2000-01-01', 'data_period': '合成测试期间，不是真实报表',
            'verdict': '该用例只检验字段及版式处理，不形成行业判断。', 'reasoning_boundary': '合成输入，不可作为业务证据。',
            'document_no': '测试字〔2000〕1号', 'note': '',
            'sources': [{'publisher': '虚构测试发布者', 'title': '合成原文', 'published': '2000-01-01',
                         'url': f'https://example.invalid/testing/{i}', 'access': 'full_original', 'quote': '仅供离线测试'}]})
    return {'brief_date': '2000-01-02', 'editor_reviewed': True, 'focus': '合成测试，不是正式简报。',
            'keywords': ['合成', '离线', '测试'], 'search_log': [{'direction': f'合成方向{i}', 'queries': ['模拟检索记录']} for i in range(4)],
            'previous_review': '没有真实历史材料，未核真实重复。', 'coverage_note': '合成测试，不计真实使用。', 'corrections': [], 'cards': cards}


class Tests(unittest.TestCase):
    def test_full_round_trip_and_real_links(self):
        d = fixture(); h = m.render(d); errors, _ = m.check(h, d)
        self.assertEqual(errors, [])
        self.assertIn('2000-01-02（周日）', h)
        self.assertEqual(h.count('<div class="card">'), 8)
        self.assertEqual(h.count('<a href='), 8)

    def test_shortage_and_zero_sections(self):
        for n in (0, 1):
            d = fixture(n); self.assertEqual(m.check(m.render(d), d)[0], [])
            d['coverage_note'] = ''
            with self.assertRaises(ValueError): m.render(d)

    def test_source_gate_and_policy_primary(self):
        for access in ('search_snippet', 'unread', 'full_media'):
            d = fixture(); d['cards'][0]['sources'][0]['access'] = access
            with self.assertRaises(ValueError): m.render(d)
        d = fixture(); d['cards'][1]['sources'][0]['access'] = 'full_media'
        self.assertIn('仅核媒体全文，未核原披露', m.render(d))

    def test_no_fake_review_or_future_source(self):
        d = fixture(); d['editor_reviewed'] = False
        with self.assertRaises(ValueError): m.render(d)
        d = fixture(); d['cards'][0]['sources'][0]['published'] = '2000-01-03'
        with self.assertRaises(ValueError): m.render(d)

    def test_no_schedule_filler_or_ai_market(self):
        d = fixture(); d['cards'][1]['kind'] = '报名日程'
        with self.assertRaises(ValueError): m.render(d)
        d = fixture(); d['cards'][1]['ai_topic'] = True
        with self.assertRaises(ValueError): m.render(d)

    def test_history_gate(self):
        d = fixture(); d['cards'][0]['historical_comparison'] = True
        with self.assertRaises(ValueError): m.render(d)
        d['cards'][0]['comparison_evidence'] = [{'cycle': str(i), 'published': f'199{i}-01-01', 'url': f'https://example.invalid/{i}', 'quote': '合成对照', 'access': 'full_original'} for i in range(3)]
        self.assertEqual(m.check(m.render(d), d)[0], [])

    def test_injection_escape_and_unsafe_url(self):
        d = fixture(); d['cards'][0]['fact'] = '<script>alert(1)</script> & "测试"'
        h = m.render(d); self.assertNotIn('<script>', h); self.assertIn('&lt;script&gt;', h)
        d['cards'][0]['sources'][0]['url'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError): m.render(d)

    def test_tamper_link_and_css(self):
        d = fixture(); h = m.render(d)
        self.assertTrue(m.check(h.replace('虚构测试对象', '擅改适用对象', 1), d)[0])
        self.assertTrue(m.check(h.replace('href="https://example.invalid/testing/0"', 'href="javascript:alert(1)"'), d)[0])
        self.assertTrue(m.check(h.replace('max-width: 880px', 'max-width: 900px'), d)[0])

    def test_forbidden_language_and_extra_tags(self):
        d = fixture(); h = m.render(d)
        self.assertTrue(m.check(h.replace('该用例', '建议立即', 1))[0])
        self.assertTrue(m.check(h.replace('虚构测试对象', '<span>新增正文标签</span>', 1))[0])
        self.assertTrue(m.check(h.replace('虚构测试对象', '<img src="x">', 1))[0])

    def test_cli_no_overwrite_and_invalid_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); ip = td/'input.json'; payload = json.dumps(fixture(), ensure_ascii=False).encode(); ip.write_bytes(payload)
            cmd = [sys.executable, '-B', str(SCRIPT), 'render', str(ip), '--output-dir', str(td/'out')]
            p = subprocess.run(cmd, capture_output=True); self.assertEqual(p.returncode, 0, p.stderr)
            files = {str(x.relative_to(td)): x.read_bytes() for x in (td/'out').iterdir()}
            p = subprocess.run(cmd, capture_output=True); self.assertNotEqual(p.returncode, 0)
            self.assertEqual(files, {str(x.relative_to(td)): x.read_bytes() for x in (td/'out').iterdir()})
            self.assertEqual((td/'out/2000-01-02-公考培训行业动态简报-证据.json').read_bytes(), payload)
            d = fixture(); d['cards'][0]['sources'][0]['access'] = 'snippet'; ip.write_text(json.dumps(d))
            bad = td/'invalid'; p = subprocess.run(cmd[:-1]+[str(bad)], capture_output=True)
            self.assertNotEqual(p.returncode, 0); self.assertFalse(bad.exists())

    def test_cli_check_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); d = fixture(); ip = td/'i.json'; ip.write_text(json.dumps(d)); hp = td/'2000-01-02-公考培训行业动态简报.html'
            hp.write_text(m.render(d)); args = [sys.executable, '-B', str(SCRIPT), 'check', str(hp), '--input', str(ip)]
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
            hp.write_text(hp.read_text().replace('虚构测试对象', '被改动', 1))
            self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)


    def test_portable_install_can_render_outside_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); package = td/'acs-industry-brief'
            shutil.copytree(SCRIPT.parent.parent, package, ignore=shutil.ignore_patterns('__pycache__'))
            ip = td/'input.json'; ip.write_text(json.dumps(fixture()))
            cmd = [sys.executable, '-B', str(package/'scripts/brief.py'), 'render', str(ip), '--output-dir']
            p = subprocess.run(cmd+[str(td/'output')], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue((td/'output/2000-01-02-公考培训行业动态简报.html').is_file())
            p = subprocess.run(cmd+[str(package/'output')], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse((package/'output').exists())

    def test_identified_knowledge_vault_remains_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp); kb = td/'示例知识库'
            (kb/'原始材料').mkdir(parents=True); (kb/'AGENTS.md').write_text('测试入口')
            package = kb/'规范与工具/工具/Skill/acs-industry-brief'
            shutil.copytree(SCRIPT.parent.parent, package, ignore=shutil.ignore_patterns('__pycache__'))
            ip = td/'input.json'; ip.write_text(json.dumps(fixture()))
            cmd = [sys.executable, '-B', str(package/'scripts/brief.py'), 'render', str(ip), '--output-dir']
            p = subprocess.run(cmd+[str(kb/'成品')], capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse((kb/'成品').exists())
            p = subprocess.run(cmd+[str(td/'output')], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)


if __name__ == '__main__':
    unittest.main()
