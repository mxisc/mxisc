"""从公开仓库 生成主页状态面板。"""
import html
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request

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

query = 'query { user(login:"mxisc") { pinnedItems(first:6, types:REPOSITORY) { nodes { ... on Repository { name nameWithOwner isFork isPrivate } } } } }'
headers = {'User-Agent': 'mxisc-profile', 'Content-Type': 'application/json',
           'Authorization': 'Bearer ' + os.environ['GH_TOKEN']}
request = urllib.request.Request('https://api.github.com/graphql',
    data=json.dumps({'query': query}).encode(), headers=headers)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)
if result.get('errors'):
    raise RuntimeError('置顶仓库查询失败')
repos = [r for r in result['data']['user']['pinnedItems']['nodes']
         if not r['isFork'] and not r['isPrivate']
         and r['nameWithOwner'].startswith('mxisc/') and r['name'] != 'mxisc']
entries = []
for r in repos:
    commits = json.loads(fetch(f"https://api.github.com/repos/mxisc/{r['name']}/commits?per_page=1", True))
    commit = commits[0]
    date = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00')).astimezone(CN)
    entries.append(('代码', r['name'], commit['commit']['message'].splitlines()[0], date, commit['html_url']))
now = datetime.now(CN)
height = 117 + max(1, len(entries)) * 61
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img" aria-label="铭心最近更新">',
'<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#19152c"/><stop offset="1" stop-color="#0c1524"/></linearGradient></defs>',
f'<rect x="1" y="1" width="898" height="{height-2}" rx="20" fill="url(#bg)" stroke="#46405f"/>',
'<path d="M30 77H870" stroke="#38344d"/><circle cx="34" cy="37" r="5" fill="#b59aff"/><circle cx="53" cy="37" r="5" fill="#83c8ff"/><circle cx="72" cy="37" r="5" fill="#78e6c8"/>',
'<g font-family="PingFang SC,Microsoft YaHei,Noto Sans CJK SC,sans-serif">',
'<text x="97" y="45" fill="#f1ecff" font-size="21" font-weight="600">存档有动静</text>',
f'<text x="865" y="43" text-anchor="end" fill="#b3a8d3" font-size="13">同步于 {now:%m-%d %H:%M} · 北京时间</text>']
for i, (kind, title, detail, date, url) in enumerate(entries):
    y = 111 + i * 61
    color = '#83c8ff'
    svg.extend([f'<rect x="30" y="{y-17}" width="48" height="24" rx="7" fill="{color}" fill-opacity=".12"/>',
    f'<text x="54" y="{y}" text-anchor="middle" fill="{color}" font-size="13">{kind}</text>',
    f'<text x="94" y="{y}" fill="#ebe6fc" font-size="17">{esc(short(title, 32))}</text>',
    f'<text x="865" y="{y}" text-anchor="end" fill="#a39cb9" font-size="13">{date:%m-%d %H:%M}</text>'])
    if detail:
        svg.append(f'<text x="94" y="{y+21}" fill="#a7a4be" font-size="13">{esc(short(detail, 65))}</text>')
if not entries:
    svg.append('<text x="30" y="125" fill="#a7a4be" font-size="16">暂无置顶项目</text>')
svg.extend(['</g>', f'<path d="M30 {height-29}H870" stroke="#38344d"/>', '</svg>'])
Path('assets/status-panel.svg').write_text('\n'.join(svg) + '\n')
# 外层链接在 GitHub README 中可点击，图片内部 SVG 链接不可靠。
links = ' &nbsp; · &nbsp; '.join(f'[{esc(e[1])}]({e[4]})' for e in entries)
section = '<img src="https://raw.githubusercontent.com/mxisc/mxisc/main/assets/status-panel.svg" alt="公开项目最近更新" width="100%" />\n\n' + links
p = Path('README.md')
s = p.read_text()
start, end = '<!-- PUBLIC-PROJECTS:START -->', '<!-- PUBLIC-PROJECTS:END -->'
a, b = s.index(start) + len(start), s.index(end)
p.write_text(s[:a] + '\n' + section + '\n' + s[b:])
