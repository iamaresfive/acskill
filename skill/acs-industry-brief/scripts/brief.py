#!/usr/bin/env python3
"""离线排版与结构检查；不联网，不证明输入的事实或审阅声明真实。"""
import argparse
from datetime import date
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
SECTIONS = [('policy', 'c-blue', '一、监管与政策'), ('market', 'c-amber', '二、市场与同业'), ('sentiment', 'c-red', '三、网络舆情')]
KINDS = {
    'policy': {'处罚', '行政强制措施', '执法检查限期整改', '行政约谈', '提醒告诫', '合规提示', '行政公示', '征求意见稿', '拟处罚', '专项整治'},
    'market': {'机构经营', '资本动作', '产品师资', '行业数据'},
    'sentiment': {'司法风险', '投诉维权', '媒体调查'},
}
FORBIDDEN = ('你', '您', '咱们', '贵司', '建议立即', '建议动作', '建议把', '应尽快', '务必')
RISK = re.compile(r'首次|第一次|前所未有|最严|首例|首个|首份|空前|说明.{0,12}(被动|必然)|几乎没有协商空间|意味着.{0,12}(已经|必然)')


def require(test, message):
    if not test:
        raise ValueError(message)


def text(obj, key):
    v = obj.get(key)
    require(isinstance(v, str) and bool(v.strip()), f'{key}须为非空文本')
    return v


def day(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), '日期须为YYYY-MM-DD')
    return date.fromisoformat(value)


def url(value):
    require(isinstance(value, str) and not re.search(r'\s', value), '来源URL须为无空白文本')
    p = urlsplit(value)
    require(p.scheme in ('http', 'https') and p.hostname and not p.username and not p.password, '来源URL须为http(s)直达页，不含凭据')
    return value


def validate(data):
    require(isinstance(data, dict), '输入须为JSON对象')
    brief_date = day(data.get('brief_date'))
    require(data.get('editor_reviewed') is True, '尚未记录人工审定；脚本不能代替审阅')
    text(data, 'focus'); text(data, 'previous_review')
    keys = data.get('keywords')
    require(isinstance(keys, list) and len(keys) == 3 and all(isinstance(k, str) and k.strip() for k in keys), 'keywords须有三个非空词')
    groups = data.get('search_log')
    require(isinstance(groups, list) and 4 <= len(groups) <= 6, 'search_log须记录4—6组发现检索')
    for g in groups:
        require(isinstance(g, dict), '检索组须为对象'); text(g, 'direction')
        require(isinstance(g.get('queries'), list) and g['queries'] and all(isinstance(q, str) and q.strip() for q in g['queries']), '每组须记录实际检索词')
    require(isinstance(data.get('corrections'), list) and all(isinstance(x, str) and x.strip() for x in data['corrections']), 'corrections须为文本数组，无则空数组')
    cards = data.get('cards')
    require(isinstance(cards, list), 'cards须为数组')
    require(len(cards) <= 9, '超过9条：先筛选，或按用户新要求另行适配')
    require(isinstance(data.get('coverage_note'), str), 'coverage_note须为文本')
    if len(cards) < 7:
        text(data, 'coverage_note')
    for c in cards:
        require(isinstance(c, dict), '每卡须为对象')
        sec = c.get('section')
        require(sec in KINDS and c.get('kind') in KINDS[sec], '类别不匹配；纯考务日程不进简报')
        for k in ('title', 'fact', 'scope', 'verdict', 'reasoning_boundary', 'event_date'):
            text(c, k)
        for k in ('note', 'data_period'):
            require(isinstance(c.get(k, ''), str), f'{k}须为文本')
        require(isinstance(c.get('ai_topic', False), bool) and isinstance(c.get('historical_comparison', False), bool), '主题与比较标识须为布尔值')
        require(not c.get('ai_topic') or sec == 'policy', '非政策卡不设AI专题')
        if c['kind'] in ('机构经营', '行业数据'):
            text(c, 'data_period')
        sources = c.get('sources')
        require(isinstance(sources, list) and sources, '每卡须有已读全文来源')
        for src in sources:
            require(isinstance(src, dict), 'source须为对象')
            for k in ('publisher', 'title', 'quote'):
                text(src, k)
            require(day(src.get('published')) <= brief_date, '来源发布日期晚于本期日期')
            url(src.get('url'))
            require(src.get('access') in ('full_original', 'full_media'), '仅摘要／未打开原文不能进入正式事实卡')
        if sec == 'policy':
            text(c, 'document_no')
            require(sources[0]['access'] == 'full_original', '政策卡须读官方原文，不用媒体摘要代替')
        if c.get('historical_comparison'):
            ev = c.get('comparison_evidence')
            require(isinstance(ev, list) and len(ev) >= 3, '历史比较须有至少三个同类周期原文')
            require(len({text(x, 'cycle') for x in ev}) >= 3, '比较周期不可重复凑数')
            for e in ev:
                text(e, 'quote'); url(e.get('url')); require(day(e.get('published')) <= brief_date, '比较证据日期越界')
                require(e.get('access') == 'full_original', '历史比较不能只靠转载')
    return data


def render(data):
    validate(data)
    e = lambda s: escape(str(s), quote=True)
    d = day(data['brief_date']); ds = d.isoformat(); weekday = '一二三四五六日'[d.weekday()]
    css = (ASSETS/'style.css').read_text()
    a = ['<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">', '<meta name="viewport" content="width=device-width, initial-scale=1.0">', f'<title>公考培训行业动态简报 {ds}</title>', f'<style>\n{css}</style>\n</head>\n<body>\n<div class="wrap">', '<div class="header"><h1>公考培训行业动态简报</h1><div class="meta">', f'<span>日期：<b>{ds}（周{weekday}）</b></span>', '<span>覆盖：<b>监管政策 / 市场与同业 / 网络舆情</b></span>', f'<span>条数：<b>{len(data["cards"])} 条</b></span></div><div class="chips">']
    a += [f'<span class="chip">{e(k)}</span>' for k in data['keywords']]
    a += ['</div>', f'<div class="focus"><b>今日焦点：</b>{e(data["focus"])}</div></div>']
    for sec, color, heading in SECTIONS:
        cards = [c for c in data['cards'] if c['section'] == sec]
        a += [f'<div class="section {color}"><div class="sec-head"><div class="sec-bar"></div><h2>{heading}</h2><span class="pill">{len(cards)} 条</span></div>']
        if not cards:
            a += ['<div class="note">本期未取得符合范围及证据要求的新事项。</div>']
        for c in cards:
            src = c['sources'][0]
            refs = '；'.join(f'<a href="{e(s["url"])}">{e(s["publisher"])}：{e(s["title"])}</a>（{e(s["published"])}，{"已读原始披露" if s["access"] == "full_original" else "仅核媒体全文，未核原披露"}）' for s in c['sources'])
            quote = f'<b>“{e(src["quote"])}”</b>'
            note = f'事件日期：{c["event_date"]}；性质：{c["kind"]}。'
            if c['section'] == 'policy':
                note += '文号：' + c['document_no'] + '。'
            if c.get('data_period'):
                note += '数据期间／口径：' + c['data_period'] + '。'
            note += c.get('note', '') + '研判边界：' + c['reasoning_boundary']
            compare = ''
            if c.get('historical_comparison'):
                compare = '；历史比较依据：' + '；'.join(f'<a href="{e(x["url"])}">{e(x["cycle"])}（{e(x["published"])}）</a>' for x in c['comparison_evidence'])
            a += ['<div class="card">', f'<h3>{e(c["title"])}</h3>', f'<div class="tags"><span class="date">{e(src["published"])}</span> ｜ 来源：{e(src["publisher"])}</div>', f'<div class="fact">{e(c["fact"])} 原文关键句：{quote}。适用对象：{e(c["scope"])}</div>', f'<div class="verdict"><b>研判：</b>{e(c["verdict"])}</div>', f'<div class="note">{e(note)}<br>原文：{refs}{compare}</div>', '</div>']
        a += ['</div>']
    corrections = '；'.join(data['corrections']) or '本期无修正'
    a += ['<div class="footer">', f'口径提醒／修正说明：{e(corrections)}<br>', f'前期衔接：{e(data["previous_review"])}<br>']
    if data['coverage_note']:
        a += [f'覆盖与缺口：{e(data["coverage_note"])}<br>']
    a += [f'本简报基于公开信息整理，不构成投资或经营建议。 · {ds}', '</div></div></body></html>\n']
    return '\n'.join(a)


class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []; self.errors = []; self.sections = []; self.cards = 0; self.links = []; self.bodytext = []; self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs); cls = attrs.get('class', '')
        if tag in ('img', 'u', 'script', 'iframe', 'object', 'embed', 'link'):
            self.errors.append('禁用标签：'+tag)
        if any(k.startswith('on') or k == 'style' for k in attrs):
            self.errors.append('不接受内联样式或事件属性')
        if tag == 'span':
            parent = self.stack[-1] if self.stack else ('', '')
            allowed = ((cls == 'date' and parent == ('div', 'tags')) or (cls == 'chip' and parent == ('div', 'chips')) or (cls == 'pill' and parent == ('div', 'sec-head')) or (not cls and parent == ('div', 'meta')))
            if not allowed:
                self.errors.append('span角色不符合模板')
        if tag == 'div' and 'section' in cls.split():
            self.sections.append(cls)
        if tag == 'div' and cls == 'card':
            self.cards += 1
        if tag == 'a':
            try: self.links.append(url(attrs.get('href')))
            except ValueError as ex: self.errors.append(str(ex))
        if tag == 'style': self.hidden += 1
        if tag not in ('meta', 'br', 'hr', 'img', 'link', 'input'):
            self.stack.append((tag, cls))

    def handle_endtag(self, tag):
        if tag == 'style': self.hidden -= 1
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append('标签闭合不匹配：'+tag)
        else: self.stack.pop()

    def handle_data(self, value):
        if not self.hidden:
            self.bodytext.append(value)


def check(html, data=None):
    a = Audit(); a.feed(html); a.close()
    errors = a.errors
    if a.stack: errors.append('存在未闭合标签')
    if a.sections != ['section '+s[1] for s in SECTIONS]: errors.append('三节名称／顺序／class不符')
    if not (0 <= a.cards <= 9): errors.append('卡片数量越界')
    if html.count('font-size: 14px') != 1 or html.count('max-width: 880px') != 1: errors.append('14px／880px次数不符')
    styles = re.findall(r'<style>\s*([\s\S]*?)</style>', html)
    if len(styles) != 1 or styles[0].strip() != (ASSETS/'style.css').read_text().strip(): errors.append('CSS与v3固定样式不同')
    content = '\n'.join(a.bodytext)
    for word in FORBIDDEN:
        if word in content: errors.append('禁用表达：'+word)
    if re.search(r'\*\*|^\s*#{1,6}\s|^\s*-\s|\]\(https?://', content, re.M): errors.append('残留Markdown')
    if len(a.links) < a.cards: errors.append('来源链接不足，每卡至少一个')
    if data is not None and html != render(data): errors.append('成品与本期输入不一致')
    return errors, sorted(set(m.group() for m in RISK.finditer(content)))



def check_output_dir(out, skill):
    """安装位置可迁移；只保护Skill本身及按结构识别出的知识库。"""
    out = out.expanduser().resolve()
    skill = skill.resolve()
    require(not out.is_relative_to(skill), '运行输出不能写入Skill包')
    for parent in skill.parents:
        if ((parent/'原始材料').is_dir() and
                (parent/'规范与工具').is_dir() and
                (parent/'AGENTS.md').is_file()):
            require(not out.is_relative_to(parent), '运行输出须在库外；正式入库另按知识库规则')
            break
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='mode', required=True)
    r = sub.add_parser('render'); r.add_argument('input', type=Path); r.add_argument('--output-dir', type=Path, required=True)
    c = sub.add_parser('check'); c.add_argument('html', type=Path); c.add_argument('--input', type=Path)
    args = p.parse_args()
    try:
        input_bytes = args.input.read_bytes() if args.input else None
        data = json.loads(input_bytes) if input_bytes is not None else None
        if args.mode == 'render':
            html = render(data); errors, warnings = check(html, data)
            require(not errors, '；'.join(errors))
            # 不把运行产物写回Skill或可识别的知识库；不依赖固定安装层级。
            skill = Path(__file__).resolve().parents[1]
            out = check_output_dir(args.output_dir, skill)
            name = data['brief_date']+'-公考培训行业动态简报'
            hp = out/(name+'.html'); ep = out/(name+'-证据.json')
            require(not hp.exists() and not ep.exists(), '同名成品或证据已存在，拒绝覆盖')
            out.mkdir(parents=True, exist_ok=True)
            # x模式避免覆盖竞争中出现的目标；仅回滚本进程创建的文件。
            made = []
            try:
                with ep.open('xb') as f: made.append(ep); f.write(input_bytes)
                with hp.open('x', encoding='utf-8') as f: made.append(hp); f.write(html)
            except Exception:
                for fp in made: fp.unlink()
                raise
            print('HTML：'+str(hp)); print('证据：'+str(ep))
        else:
            html = args.html.read_text(); errors, warnings = check(html, data)
            if data is not None:
                require(args.html.name == data['brief_date']+'-公考培训行业动态简报.html', '成品文件名与本期日期不一致')
            require(not errors, '；'.join(errors))
        for w in warnings:
            print('人工复核提示｜'+w)
        print('PASS｜字段与结构通过；不代表来源已联网核实或研判成立')
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as ex:
        print('FAIL｜'+str(ex), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
