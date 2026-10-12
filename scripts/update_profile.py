"""从公开仓库与博客 RSS 生成主页状态面板。"""
import html
import json
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

CN = timezone(timedelta(hours=8))

def fetch(url, github=False):
    headers = {'User-Agent': 'mxisc-profile'}
    if github:
        headers['Accept'] = 'application/vnd.github+json'
        if os.getenv('GH_TOKEN'):
            headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return response.read()

def esc(value):
    return html.escape(str(value), quote=True)

def short(value, length):
    return value if len(value) <= length else value[:length - 1] + '…'

repos = []
for page in range(1, 20):
    batch = json.loads(fetch(f'https://api.github.com/users/mxisc/repos?per_page=100&page={page}', True))
    repos.extend(batch)
    if len(batch) < 100:
        break
repos = [r for r in repos if not r['fork'] and not r.get('private') and r['name'] != 'mxisc']
repos.sort(key=lambda r: r['pushed_at'], reverse=True)
feed = ET.fromstring(fetch('https://www.mxin.me/feed/'))
items = feed.findall('./channel/item')[:2]
entries = []
for r in repos[:3]:
    commits = json.loads(fetch(f"https://api.github.com/repos/mxisc/{r['name']}/commits?per_page=1", True))
    commit = commits[0]
    date = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00')).astimezone(CN)
    entries.append(('代码', r['name'], commit['commit']['message'].splitlines()[0], date, commit['html_url']))
for item in items:
    date = parsedate_to_datetime(item.findtext('pubDate')).astimezone(CN)
    entries.append(('博客', item.findtext('title'), '', date, item.findtext('link')))
now = datetime.now(CN)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="440" viewBox="0 0 900 440" role="img" aria-label="铭心最近更新">',
'<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#19152c"/><stop offset="1" stop-color="#0c1524"/></linearGradient></defs>',
'<rect x="1" y="1" width="898" height="438" rx="20" fill="url(#bg)" stroke="#46405f"/>',
'<path d="M30 77H870" stroke="#38344d"/><circle cx="34" cy="37" r="5" fill="#b59aff"/><circle cx="53" cy="37" r="5" fill="#83c8ff"/><circle cx="72" cy="37" r="5" fill="#78e6c8"/>',
'<g font-family="PingFang SC,Microsoft YaHei,Noto Sans CJK SC,sans-serif">',
'<text x="97" y="45" fill="#f1ecff" font-size="21" font-weight="600">存档有动静</text>',
f'<text x="865" y="43" text-anchor="end" fill="#b3a8d3" font-size="13">同步于 {now:%m-%d %H:%M} · 北京时间</text>']
for i, (kind, title, detail, date, url) in enumerate(entries):
    y = 111 + i * 61
    color = '#83c8ff' if kind == '代码' else '#c4a5ff'
    svg.extend([f'<rect x="30" y="{y-17}" width="48" height="24" rx="7" fill="{color}" fill-opacity=".12"/>',
    f'<text x="54" y="{y}" text-anchor="middle" fill="{color}" font-size="13">{kind}</text>',
    f'<text x="94" y="{y}" fill="#ebe6fc" font-size="17">{esc(short(title, 32))}</text>',
    f'<text x="865" y="{y}" text-anchor="end" fill="#a39cb9" font-size="13">{date:%m-%d %H:%M}</text>'])
    if detail:
        svg.append(f'<text x="94" y="{y+21}" fill="#a7a4be" font-size="13">{esc(short(detail, 65))}</text>')
svg.extend(['</g>', '<path d="M30 411H870" stroke="#38344d"/>', '</svg>'])
Path('assets/status-panel.svg').write_text('\n'.join(svg) + '\n')
# 外层链接在 GitHub README 中可点击，图片内部 SVG 链接不可靠。
links = ' &nbsp; · &nbsp; '.join(f'[{esc(e[1])}]({e[4]})' for e in entries)
section = '<img src="https://raw.githubusercontent.com/mxisc/mxisc/main/assets/status-panel.svg" alt="博客与公开项目最近更新" width="100%" />\n\n' + links
p = Path('README.md')
s = p.read_text()
start, end = '<!-- PUBLIC-PROJECTS:START -->', '<!-- PUBLIC-PROJECTS:END -->'
a, b = s.index(start) + len(start), s.index(end)
p.write_text(s[:a] + '\n' + section + '\n' + s[b:])
