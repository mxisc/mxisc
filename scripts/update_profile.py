import json, os, urllib.request
from pathlib import Path

def get(path):
    headers={'User-Agent':'mxisc-profile','Accept':'application/vnd.github+json'}
    if os.getenv('GH_TOKEN'): headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/'+path,headers=headers),timeout=20) as response:return json.load(response)
repos=[]
for page in range(1,20):
    batch=get(f'users/mxisc/repos?per_page=100&page={page}')
    repos.extend(batch)
    if len(batch)<100:break
repos=[r for r in repos if not r['fork'] and not r.get('private',False) and r['name']!='mxisc']
selected=['Dream2.0-MXIN','Hysteria2MX','Aria2MX','mtools']
lookup={r['name']:r for r in repos}
rows=[]
for name in selected:
    r=lookup.get(name)
    if r:rows.append(f"| [{name}]({r['html_url']}) | {r['language'] or '—'} | {r['pushed_at'][:10]} |")
section='| 项目 | 语言 | 最近推送（UTC） |\n|---|---|---|\n'+'\n'.join(rows)
p=Path('README.md');s=p.read_text();start='<!-- PUBLIC-PROJECTS:START -->';end='<!-- PUBLIC-PROJECTS:END -->';a=s.index(start)+len(start);b=s.index(end);p.write_text(s[:a]+'\n'+section+'\n'+s[b:])
