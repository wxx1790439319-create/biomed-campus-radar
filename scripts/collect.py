#!/usr/bin/env python3
"""Public GitHub recruitment aggregation: no ATS bypass, no fabricated emails."""
import csv, io, json, os, re, sys, time
from datetime import date
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'biomed-campus-radar/0.1', 'Accept':'application/vnd.github+json'})
if os.getenv('GITHUB_TOKEN'): S.headers['Authorization']='Bearer '+os.getenv('GITHUB_TOKEN')
TODAY=date.today().isoformat()
FIELDS=['企业','毕业届别','公告发布年份','首次观察日期','岗位领域','岗位/岗位族','城市','招聘批次','公告学历','硕士可投判断','截止时间','在招状态','聚合来源','公告/申请链接','核实说明','GitHub原始文件','最后采集日期']

def get(url, tries=3):
 for i in range(tries):
  try:
   r=S.get(url,timeout=35)
   if r.status_code in (403,429):
    print('Rate limit or forbidden:',url,'status=',r.status_code,file=sys.stderr);return None
   r.raise_for_status();return r
  except requests.RequestException as e:
   if i==tries-1: print('Fetch failed:',url,str(e),file=sys.stderr)
   else: time.sleep(2*(i+1))
 return None

def status(deadline):
 if re.fullmatch(r'20\d\d-\d\d-\d\d',deadline or ''):
  return '已过公告截止日（未核验官网）' if deadline<TODAY else '截止日未到（需核验是否仍招）'
 return '截止日未公开／无法确认在招'

def normname(name):return re.sub(r'[\s（()）·•_\-—]','',name or '').lower()

def add(rows,r):
 if not r['企业']:return
 if r['毕业届别'] not in ('2026届','2027届'):return
 if r['公告学历'] and '硕士' not in r['公告学历'] and r['公告学历']!='未注明':return
 r['最后采集日期']=TODAY
 rows.append({k:r.get(k,'') for k in FIELDS})

def best(rows, max_companies=1200):
 index='https://raw.githubusercontent.com/oneetx-art/campus-announcements/master/by-industry/医疗/医药/生物.md'
 response=get(index)
 if not response:return
 names=list(dict.fromkeys(re.findall(r'^- \[([^\]]+)\]\(',response.text,re.M)))
 print('Best校招 index company count',len(names))
 for name in names[:max_companies]:
  raw=f'https://raw.githubusercontent.com/oneetx-art/campus-announcements/master/companies/{quote(name,safe="")}/README.md'
  res=get(raw,2)
  if not res:continue
  sections=re.split(r'(?=^### )',res.text,flags=re.M)
  for sec in sections:
   if not sec.startswith('### '):continue
   title=sec.splitlines()[0][4:].strip()
   cohort=re.search(r'202[67]\s*届|202[67]\s*校园招聘|202[67]\s*校招',title)
   if cohort: co=re.search(r'202[67]',cohort.group()).group()+'届'
   else: continue # No guessing from update year.
   def f(n):
    m=re.search(r'^- \*\*'+n+r'\*\*:\s*(.*)$',sec,re.M)
    return m.group(1).strip() if m else ''
   edu=f('学历');
   if not '硕士' in edu:continue
   dl=f('截止'); match=re.search(r'20\d{2}-\d\d-\d\d',dl)
   deadline=match.group() if match else '未公开'
   link=re.search(r'https?://[^)\s]+',sec)
   source=link.group() if link else raw
   add(rows,{'企业':name,'毕业届别':co,'公告发布年份':'未核实','首次观察日期':'未提供','岗位领域':'医疗/医药/生物','岗位/岗位族':f('岗位'),'城市':f('城市'),'招聘批次':f('批次'),'公告学历':edu,'硕士可投判断':'公告级包含硕士；需逐岗位核验','截止时间':deadline,'在招状态':status(deadline),'聚合来源':'oneetx-art/campus-announcements','公告/申请链接':source,'核实说明':'招聘聚合快照；发布年份未证实；不等于当前在招','GitHub原始文件':raw})

def xixicc(rows):
 url='https://raw.githubusercontent.com/xixicc186/xixicc2027/main/jobs.json';res=get(url)
 if not res:return
 try: records=res.json()
 except ValueError:return
 kw=re.compile(r'医药|生物|制药|药业|医疗|医械|医美|药企|医院|健康|药物|药学|药剂|临床|抗体|疫苗|医工|生命科学|国药|迈瑞|英科|新和成|恒瑞|齐鲁|扬子江|药明|康龙|先声|药石|石药|复星|人福|科伦')
 for x in records:
  cohort=x.get('cohort','');
  if cohort not in ('2026届','2027届'):continue
  title=' '.join([x.get('company',''),x.get('industry','')]+x.get('positions',[]))
  if not kw.search(title):continue
  dl=x.get('deadline') or '未公开'
  seen=x.get('first_seen') or ''
  link=x.get('apply_url') or url
  add(rows,{'企业':x.get('company',''),'毕业届别':cohort,'公告发布年份':'未核实','首次观察日期':seen,'岗位领域':x.get('industry',''),'岗位/岗位族':'；'.join(x.get('positions',[])) or '原文件未注明','城市':'；'.join(x.get('locations',[])),'招聘批次':x.get('batch',''),'公告学历':'未注明','硕士可投判断':'未验证硕士可投（线索池）','截止时间':dl,'在招状态':status(dl),'聚合来源':'xixicc186/xixicc2027','公告/申请链接':link,'核实说明':'首次观察日期不是公告发布日期；职位及学历须核验','GitHub原始文件':url})

def merge(rows):
 # Only identical announcements, not all campaigns from same company, collapse.
 keep={}
 for r in rows:
  url=r['公告/申请链接'].rstrip('/').lower()
  key=(normname(r['企业']),r['毕业届别'],url if 'besthotsearch.com/announcements1/' in url else (r['招聘批次'],r['岗位/岗位族'][:60],url))
  if key not in keep or (keep[key]['公告学历']=='未注明' and '硕士' in r['公告学历']):keep[key]=r
 return list(keep.values())

def write_csv(file,items,fields):
 with open(file,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)

def main():
 rows=[]
 best(rows,int(os.getenv('MAX_COMPANIES','1200')))
 xixicc(rows)
 rows=merge(rows)
 write_csv(OUT/'biomed_announcements.csv',rows,FIELDS)
 channels={}
 for r in rows:
  key=normname(r['企业']);rec=channels.setdefault(key,{'企业':r['企业'],'校招入口':'','投递邮箱':'','邮箱用途':'未公开/未经证实','信息来源':r['GitHub原始文件'],'最近核实日期':TODAY,'说明':'仅保留公开岗位渠道；不猜测邮箱'})
  link=r['公告/申请链接']
  if any(a in link for a in ('mokahr.com','zhiye.com','hotjob.cn','jobs.feishu.cn')):rec['校招入口']=link
 write_csv(OUT/'company_channels.csv',list(channels.values()),['企业','校招入口','投递邮箱','邮箱用途','信息来源','最近核实日期','说明'])
 print(f'Exported {len(rows)} announcements from {len(channels)} companies')

if __name__=='__main__':main()
