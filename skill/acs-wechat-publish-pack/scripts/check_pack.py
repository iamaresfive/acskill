#!/usr/bin/env python3
"""Check a local WeChat publishing package; never publishes or archives it."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile


class Article(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.text = []
        self.images = []
        self.markers = 0
        self.nested = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        marked = attrs.get('data-approved') == '1'
        if marked:
            self.markers += 1
            self.nested |= any(x[1] for x in self.stack)
        if tag == 'img':
            self.images.append(attrs.get('src', ''))
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                       'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, marked))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if any(x[1] for x in self.stack):
            self.text.append(data)


def normalize(s):
    return re.sub(r'\s+', '', s)


class Layout(HTMLParser):
    """Read only #article: image anchors and adjacent, unmarked captions."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.images, self.captions = [], [], []
        self.previous = {}
        self.last_approved = ''
        self.article_count = 0
        self.serial = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        active = attrs.get('id') == 'article' or bool(parent and parent['active'])
        if attrs.get('id') == 'article':
            self.article_count += 1
        self.serial += 1
        pid = parent['id'] if parent else 0
        node = {'id': self.serial, 'tag': tag, 'attrs': attrs, 'active': active,
                'parent': pid, 'previous': self.previous.get(pid), 'text': [],
                'marked': attrs.get('data-approved') == '1' or
                          bool(parent and parent['marked'])}
        self.previous[pid] = node
        if active and tag == 'img':
            node['after'] = self.last_approved
            self.images.append(node)
        if active and 'data-caption-for' in attrs:
            self.captions.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_data(self, text):
        for node in self.stack:
            if node['active']:
                node['text'].append(text)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                node = self.stack[i]
                if node['active'] and node['attrs'].get('data-approved') == '1':
                    self.last_approved = ''.join(node['text'])
                del self.stack[i:]
                break


def check_layout(spec, article_html, copy_html, source_text):
    """Validate the current user's explicit layout requirements in both pages."""
    errors = []
    if not isinstance(spec.get('account'), str) or not spec['account'].strip():
        errors.append('发布包缺少明确account字段')
    layout = spec.get('layout')
    if not isinstance(layout, dict):
        return errors + ['缺少图文交付清单layout'], None
    requirements = layout.get('requirements')
    if not isinstance(requirements, dict):
        return errors + ['缺少layout.requirements交付要求'], None
    if not isinstance(requirements.get('basis'), str) or not requirements['basis'].strip():
        errors.append('交付要求须说明依据basis')
    count = requirements.get('illustration_count')
    card_required = requirements.get('author_card_required')
    if type(count) is not int or count < 0 or type(card_required) is not bool:
        return errors + ['交付要求的数量或作者卡开关无效'], None
    override = layout.get('override')
    if override is not None:
        if not isinstance(override, dict) or not isinstance(override.get('user_instruction'), str) or not override['user_instruction'].strip():
            errors.append('增减交付项须记录本次用户明确指令，不能自行省略')
        else:
            count = override.get('illustration_count', count)
            card_required = override.get('author_card_required', card_required)
    if type(count) is not int or count < 0 or type(card_required) is not bool:
        return errors + ['交付例外的数量或作者卡开关无效'], None
    illustrations = layout.get('illustrations')
    if not isinstance(illustrations, list) or any(not isinstance(x, dict) for x in illustrations):
        return errors + ['layout.illustrations必须为正文插图对象数组'], None
    if len(illustrations) != count:
        errors.append('正文插图数量不符：要求%d张，实际清单%d张；封面和作者卡不计入' % (count, len(illustrations)))
    fields = ('image', 'after_paragraph', 'caption')
    if any(any(not isinstance(x.get(k), str) or not x[k].strip() for k in fields) for x in illustrations):
        return errors + ['每张插图必须列出image、after_paragraph和caption，不能空填'], None
    card = layout.get('author_card')
    if card_required and (not isinstance(card, str) or not card.strip()):
        errors.append('缺少固定文末作者卡')
        card = None
    if not card_required:
        card = None
    expected_images = [x['image'] for x in illustrations] + ([card] if card else [])
    if len(expected_images) != len(set(expected_images)):
        errors.append('插图与作者卡角色不能重复使用同一文件')
    if spec.get('body_images') != expected_images:
        errors.append('body_images与插图及文末作者卡的顺序不符')
    for name, markup in [('正文HTML', article_html), ('发布复制页', copy_html)]:
        parsed = Layout()
        parsed.feed(markup)
        if parsed.article_count != 1:
            errors.append(name + '须恰有一个id=article正文范围')
        refs = [unquote(n['attrs'].get('src', '')) for n in parsed.images]
        if refs != expected_images:
            errors.append(name + '正文范围内图片缺失、顺序错误或混入封面')
        if len(parsed.captions) != len(illustrations):
            errors.append(name + '图下小解说数量与插图不符')
        for item in illustrations:
            image = item['image']
            imgs = [n for n in parsed.images if unquote(n['attrs'].get('src', '')) == image]
            caps = [n for n in parsed.captions if n['attrs'].get('data-caption-for') == image]
            if normalize(item['after_paragraph']) not in normalize(source_text):
                errors.append(name + '插图锚点不属于定稿原文：' + image)
            if len(imgs) != 1 or normalize(imgs[0]['after']) != normalize(item['after_paragraph']):
                errors.append(name + '插图未放在约定段落之后：' + image)
            if len(caps) != 1:
                errors.append(name + '缺少唯一的图下小解说：' + image)
                continue
            cap = caps[0]
            if ''.join(cap['text']).strip() != item['caption'].strip() or cap['marked']:
                errors.append(name + '图下小解说内容不符或混入锁稿标记：' + image)
            if len(imgs) != 1 or cap['parent'] != imgs[0]['parent'] or cap['previous'] is not imgs[0]:
                errors.append(name + '小解说必须紧跟同一容器中的对应图片：' + image)
        if card and (not parsed.images or refs[-1] != card or normalize(parsed.images[-1]['after']) != normalize(source_text.strip().split('\n\n')[-1])):
            errors.append(name + '作者卡必须在定稿正文之后的末尾')
    return errors, {'account': spec.get('account'), 'expected_illustrations': count,
                    'captions_required': True, 'author_card_required': card_required,
                    'override_requires_human_verification': override is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--visual-reviewed', action='store_true')
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--approved-author-card', type=Path, help='Current user-approved source image; never bundled automatically')
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    errors = []

    def local(name):
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            raise ValueError('要求包内相对文件路径：' + str(name))
        parts = Path(name).parts
        if any(p in {'.', '..'} or p.startswith('.') for p in parts):
            raise ValueError('禁止隐藏文件或目录穿越：' + name)
        cur = root
        for part in parts:
            cur = cur / part
            if cur.is_symlink():
                raise ValueError('禁止符号链接：' + name)
        cur.resolve().relative_to(root)
        if not cur.is_file() or cur.stat().st_size == 0:
            raise ValueError('文件缺失或为空：' + name)
        return cur

    manifest = local('package.json')
    spec = json.loads(manifest.read_text(encoding='utf-8'))
    keys = ['source', 'article', 'copy_page', 'copy_text', 'cover',
            'mobile_preview', 'first_screen', 'instructions', 'rights']
    names = [spec[k] for k in keys]
    body_images = spec.get('body_images', [])
    extras = spec.get('extras', [])
    if not isinstance(body_images, list) or not isinstance(extras, list):
        raise ValueError('body_images和extras必须是数组')
    names += body_images + extras + ['package.json']
    paths = {name: local(name) for name in names}
    for name in [spec['cover'], spec['mobile_preview'], spec['first_screen']] + body_images:
        data = paths[name].read_bytes()
        if not (data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8\xff')
                or (data.startswith(b'RIFF') and data[8:12] == b'WEBP')):
            errors.append('图片签名不支持或无效：' + name)
    article = Article()
    article.feed(paths[spec['article']].read_text(encoding='utf-8'))
    source_text = paths[spec['source']].read_text(encoding='utf-8')
    expected = normalize(source_text)
    same = bool(expected) and expected == normalize(''.join(article.text))
    if not same or not article.markers or article.nested:
        errors.append('定稿正文不一致、缺少data-approved标记或标记嵌套')
    copy_article = Article()
    copy_article.feed(paths[spec['copy_page']].read_text(encoding='utf-8'))
    copy_same = bool(expected) and expected == normalize(''.join(copy_article.text))
    if not copy_same or not copy_article.markers or copy_article.nested:
        errors.append('发布复制页定稿正文不一致、缺少标记或标记嵌套')
    refs = []
    for ref in article.images:
        u = urlsplit(ref)
        if u.scheme or u.netloc or u.query or u.fragment:
            errors.append('正文图片必须为包内相对路径：' + ref)
            continue
        p = paths[spec['article']].parent / unquote(u.path)
        relative = p.relative_to(root).as_posix()
        local(relative)
        refs.append(relative)
    if refs != body_images:
        errors.append('正文图片数量/顺序与清单不符')
    if len(body_images) != len(set(body_images)):
        errors.append('正文配图清单重复')
    layout_errors, layout_report = check_layout(spec, paths[spec['article']].read_text(encoding='utf-8'), paths[spec['copy_page']].read_text(encoding='utf-8'), source_text)
    errors.extend(layout_errors)
    if layout_report and layout_report['author_card_required']:
        card_name = spec.get('layout', {}).get('author_card')
        if args.approved_author_card is None:
            errors.append('需要作者卡：请提供--approved-author-card准源，不能自行替代')
        elif isinstance(card_name, str) and card_name in paths:
            if args.approved_author_card.is_symlink():
                raise ValueError('作者卡准源不能是符号链接')
            expected_card = args.approved_author_card.resolve(strict=True)
            expected_bytes = expected_card.read_bytes()
            if paths[card_name].read_bytes() != expected_bytes:
                errors.append('作者卡与用户确认的固定成图不符；不得重画或使用候选版本')
            layout_report['author_card_reference_sha256'] = hashlib.sha256(expected_bytes).hexdigest()
    if spec.get('summary_status') not in {'建议', '用户确认', '用户提供'}:
        errors.append('需说明摘要状态：建议/用户确认/用户提供')
    if not isinstance(spec.get('platform_paste_verified'), bool):
        errors.append('platform_paste_verified需为布尔值')
    if args.zip and not args.visual_reviewed:
        errors.append('生成最终ZIP前需实际视觉检查，再传--visual-reviewed')
    if args.zip and args.zip.exists():
        errors.append('ZIP已存在，拒绝覆盖，请使用新版本名称')
    report = {
        'mechanical_pass': not errors,
        'approved_text_matches_ignoring_whitespace': same,
        'copy_text_matches_ignoring_whitespace': copy_same,
        'body_image_count': len(refs),
        'layout_check': layout_report,
        'visual_review_declared_by_operator': args.visual_reviewed,
        'platform_paste_verified': spec.get('platform_paste_verified'),
        'errors': errors,
        'sha256': {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()},
    }
    report_path = root / '检查结果.json'
    if report_path.is_symlink():
        raise ValueError('检查结果不能是符号链接')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if errors:
        print(json.dumps(report, ensure_ascii=False))
        return 1
    if args.zip:
        # Exclusive creation prevents races overwriting an earlier package.
        with zipfile.ZipFile(args.zip, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for name, p in paths.items():
                z.write(p, arcname=root.name + '/' + name)
            z.write(report_path, arcname=root.name + '/检查结果.json')
        with zipfile.ZipFile(args.zip) as z:
            if z.testzip() is not None:
                raise ValueError('ZIP完整性检查失败')
    print(json.dumps({'pass': True, 'files': len(paths), 'zip': str(args.zip) if args.zip else None}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
