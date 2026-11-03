#!/usr/bin/env python3
"""Regression checks for missing illustrations/captions and fixed author cards."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).with_name('check_pack.py')
spec_module = importlib.util.spec_from_file_location('wechat_check_pack', SCRIPT)
checker = importlib.util.module_from_spec(spec_module)
spec_module.loader.exec_module(checker)


class PackRequirements(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        body = '第一段正文。\n\n第二段正文。\n\n最后一段正文。'
        png = bytes.fromhex('89504e470d0a1a0a') + b'fixture'
        for name in ['cover.png', 'one.png', 'two.png', 'preview.png']:
            (self.root / name).write_bytes(png)
        self.approved = self.root / 'approved-card.png'
        self.approved.write_bytes(png + b'approved-card')
        (self.root / 'card.png').write_bytes(self.approved.read_bytes())
        for name, text in {'source.txt': body, 'copy.txt': body,
                           'instructions.md': '测试包，不用于发布',
                           'rights.md': '仅测试文件，不是正式交付'}.items():
            (self.root / name).write_text(text, encoding='utf-8')
        self.markup = '''<section id="article">
<p data-approved="1">第一段正文。</p>
<section><img src="one.png" alt="不能把alt当图下注释"><p data-caption-for="one.png">第一张图的解说。</p></section>
<p data-approved="1">第二段正文。</p>
<section><img src="two.png"><p data-caption-for="two.png">第二张图的解说。</p></section>
<p data-approved="1">最后一段正文。</p>
<section><img src="card.png"></section></section>'''
        self.spec = {'account': '示例账号', 'source': 'source.txt',
                     'article': 'article.html', 'copy_page': 'copy.html',
                     'copy_text': 'copy.txt', 'cover': 'cover.png',
                     'body_images': ['one.png', 'two.png', 'card.png'],
                     'mobile_preview': 'preview.png', 'first_screen': 'preview.png',
                     'instructions': 'instructions.md', 'rights': 'rights.md',
                     'extras': [], 'summary_status': '建议',
                     'platform_paste_verified': False,
                     'layout': {'requirements': {'basis': '测试指定两张图和固定作者卡', 'illustration_count': 2, 'author_card_required': True}, 'illustrations': [
                         {'image': 'one.png', 'after_paragraph': '第一段正文。', 'caption': '第一张图的解说。'},
                         {'image': 'two.png', 'after_paragraph': '第二段正文。', 'caption': '第二张图的解说。'}],
                         'author_card': 'card.png'}}

    def run_pack(self, article=None, copy=None, with_card=True, extra_args=()):
        (self.root / 'article.html').write_text(self.markup if article is None else article, encoding='utf-8')
        (self.root / 'copy.html').write_text(self.markup if copy is None else copy, encoding='utf-8')
        (self.root / 'package.json').write_text(json.dumps(self.spec, ensure_ascii=False), encoding='utf-8')
        argv = [str(SCRIPT), str(self.root)] + (['--approved-author-card', str(self.approved)] if with_card else []) + list(extra_args)
        with contextlib.redirect_stdout(io.StringIO()), mock.patch('sys.argv', argv):
            result = checker.main()
        report = json.loads((self.root / '检查结果.json').read_text())
        return result, report

    def test_complete_passes(self):
        self.assertEqual(self.run_pack()[0], 0)

    def test_remove_image_and_shorten_manifest_still_fails(self):
        self.spec['layout']['illustrations'].pop()
        self.spec['body_images'].remove('two.png')
        broken = self.markup.replace('<section><img src="two.png"><p data-caption-for="two.png">第二张图的解说。</p></section>', '')
        result, report = self.run_pack(broken, broken)
        self.assertEqual(result, 1)
        self.assertTrue(any('要求2张' in e for e in report['errors']))

    def test_missing_caption_fails_even_with_alt(self):
        broken = self.markup.replace('<p data-caption-for="one.png">第一张图的解说。</p>', '')
        self.assertEqual(self.run_pack(broken)[0], 1)

    def test_copy_page_alone_missing_caption_fails(self):
        broken = self.markup.replace('<p data-caption-for="two.png">第二张图的解说。</p>', '')
        result, report = self.run_pack(copy=broken)
        self.assertEqual(result, 1)
        self.assertTrue(any('发布复制页' in e for e in report['errors']))

    def test_caption_elsewhere_fails(self):
        broken = self.markup.replace('<p data-caption-for="one.png">第一张图的解说。</p>', '')
        broken = broken.replace('<p data-approved="1">第二段正文。</p>', '<p data-caption-for="one.png">第一张图的解说。</p><p data-approved="1">第二段正文。</p>')
        self.assertEqual(self.run_pack(broken)[0], 1)

    def test_wrong_anchor_fails(self):
        self.spec['layout']['illustrations'][0]['after_paragraph'] = '第二段正文。'
        self.assertEqual(self.run_pack()[0], 1)

    def test_caption_cannot_become_approved_source(self):
        broken = self.markup.replace('data-caption-for="one.png"', 'data-caption-for="one.png" data-approved="1"')
        self.assertEqual(self.run_pack(broken)[0], 1)

    def test_replaced_card_fails(self):
        (self.root / 'card.png').write_bytes((self.root / 'one.png').read_bytes())
        result, report = self.run_pack()
        self.assertEqual(result, 1)
        self.assertTrue(any('固定成图不符' in e for e in report['errors']))

    def test_missing_author_card_fails(self):
        self.spec['body_images'].remove('card.png')
        broken = self.markup.replace('<section><img src="card.png"></section>', '')
        self.assertEqual(self.run_pack(broken, broken)[0], 1)

    def test_copy_page_alone_missing_image_fails(self):
        broken = self.markup.replace('<img src="two.png">', '')
        self.assertEqual(self.run_pack(copy=broken)[0], 1)

    def test_missing_profile_not_silently_skipped(self):
        del self.spec['account']
        broken = '<aside>示例账号 · 公众号发布包</aside>' + self.markup
        self.assertEqual(self.run_pack(copy=broken)[0], 1)

    def test_explicit_one_image_exception(self):
        self.spec['layout']['override'] = {'user_instruction': '本次只放一张正文图。', 'illustration_count': 1}
        self.spec['layout']['illustrations'].pop()
        self.spec['body_images'].remove('two.png')
        reduced = self.markup.replace('<section><img src="two.png"><p data-caption-for="two.png">第二张图的解说。</p></section>', '')
        self.assertEqual(self.run_pack(reduced, reduced)[0], 0)

    def test_exception_without_user_instruction_fails(self):
        self.spec['layout']['override'] = {'illustration_count': 1}
        self.assertEqual(self.run_pack()[0], 1)

    def test_other_account_also_requires_layout(self):
        self.spec['account'] = '其他账号'
        del self.spec['layout']
        self.assertEqual(self.run_pack()[0], 1)

    def test_copy_page_changed_text_fails(self):
        self.assertEqual(self.run_pack(copy=self.markup.replace('最后一段正文。', '篡改后的内容。'))[0], 1)

    def test_card_requires_explicit_reference(self):
        self.assertEqual(self.run_pack(with_card=False)[0], 1)

    def test_missing_requirements_fails(self):
        del self.spec['layout']['requirements']
        self.assertEqual(self.run_pack()[0], 1)

    def test_invalid_count_type_fails(self):
        self.spec['layout']['requirements']['illustration_count'] = True
        self.assertEqual(self.run_pack()[0], 1)

    def test_simple_mode_needs_no_private_asset(self):
        self.spec['body_images'] = []
        self.spec['layout'] = {'requirements': {'basis': '用户要求简洁版', 'illustration_count': 0, 'author_card_required': False}, 'illustrations': []}
        simple = '<section id="article"><p data-approved="1">第一段正文。</p><p data-approved="1">第二段正文。</p><p data-approved="1">最后一段正文。</p></section>'
        self.assertEqual(self.run_pack(simple, simple, with_card=False)[0], 0)

    def test_traversal_rejected(self):
        self.spec['extras'] = ['../outside.txt']
        with self.assertRaises(ValueError):
            self.run_pack()

    def test_symlink_rejected(self):
        (self.root / 'alias.txt').symlink_to(self.root / 'source.txt')
        self.spec['extras'] = ['alias.txt']
        with self.assertRaises(ValueError):
            self.run_pack()

    def test_zip_needs_visual_review(self):
        target = self.root / 'deliverable.zip'
        self.assertEqual(self.run_pack(extra_args=['--zip', str(target)])[0], 1)
        self.assertFalse(target.exists())

    def test_zip_does_not_include_reference_or_stray_file(self):
        import zipfile
        target = self.root / 'deliverable.zip'
        (self.root / 'private.txt').write_text('not a deliverable')
        self.assertEqual(self.run_pack(extra_args=['--visual-reviewed', '--zip', str(target)])[0], 0)
        with zipfile.ZipFile(target) as archive:
            paths = archive.namelist()
            self.assertFalse(any(x.endswith('/approved-card.png') or x.endswith('/private.txt') for x in paths))
        self.assertEqual(self.run_pack(extra_args=['--visual-reviewed', '--zip', str(target)])[0], 1)


if __name__ == '__main__':
    unittest.main()
