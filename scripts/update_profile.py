"""从置顶公开仓库生成可点击的更新列表。"""
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
section = '<h3>存档有动静</h3>\n\n<table>\n'
for _, name, message, date, url in entries:
    section += (
        '<tr>\n'
        f'<td width="72%"><a href="https://github.com/mxisc/{esc(name)}"><strong>{esc(name)}</strong></a>'
        f'<br><br><a href="{esc(url)}">{esc(message)}</a></td>\n'
        f'<td align="right" valign="middle" width="28%"><code>{date:%Y-%m-%d}</code>'
        f'<br><br><code>{date:%H:%M}</code></td>\n'
        '</tr>\n'
    )
if not entries:
    section += '<tr><td>暂无置顶项目</td></tr>\n'
section += '</table>\n'
p = Path('README.md')
s = p.read_text()
start, end = '<!-- PUBLIC-PROJECTS:START -->', '<!-- PUBLIC-PROJECTS:END -->'
a, b = s.index(start) + len(start), s.index(end)
p.write_text(s[:a] + '\n' + section + '\n' + s[b:])
