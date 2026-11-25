#!/usr/bin/env python3
"""Read-only review exclusion, prompt removal and customer-content regression checks."""
from pathlib import Path
from lxml import html
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from collections import Counter
import json,hashlib,xml.etree.ElementTree as ET
from review_policy import CONFIG,is_review_page,LANGS
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
errors=[];counts=Counter();normal=Counter();redirects=Counter();head_links=0
def check(test,message):
 if not test:errors.append(message)
def digest(text):return hashlib.sha256(' '.join(text.strip().casefold().rstrip('.').split()).encode()).hexdigest()
robot=RobotFileParser();robot.parse((DIST/'robots.txt').read_text().splitlines())
expected=set(CONFIG['body_sha256']);actual=set();all_urls=set()
for p in DIST.rglob('*.html'):
 rel=p.relative_to(DIST).as_posix();t=html.parse(str(p));code=t.getroot().get('lang');review=is_review_page(rel)
 head=t.xpath('//head/link[@rel="alternate"][@hreflang]');head_links+=len(head)
 for link in head:
  u=urlsplit(link.get('href',''));path=u.path.lstrip('/');path=path+'index.html' if not path or path.endswith('/') else path
  check(not is_review_page(path),rel+': head hreflang advertises a noindex review')
 # The two forbidden UI prompts are detected by digests, not stored as live text.
 banned=set(CONFIG['retired_prompt_sha256'][code])
 for node in t.getroot().iter():
  if isinstance(node.tag,str):
   for value in (node.text,node.tail):
    if value and value.strip():check(digest(value) not in banned,rel+': retired template prompt remains')
 if review:
  actual.add(rel);counts[code]+=1
  check(t.xpath('//head/meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="robots"]/@content')==['noindex,follow'],rel+': noindex,follow missing/duplicate')
  check(not head and not t.xpath('//head/link[@hreflang]'),rel+': review still participates in head hreflang')
  check(hashlib.sha256(html.tostring(t.find('body'))).hexdigest()==CONFIG['body_sha256'].get(rel),rel+': protected customer body/name/image/navigation changed')
  check(robot.can_fetch('Googlebot','https://chinaattest.com/'+rel),rel+': robots blocks reading noindex')
  if t.xpath('//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'):redirects[code]+=1
  else:normal[code]+=1
 else:
  check(not t.xpath('//head/meta[@name="robots"][contains(@content,"noindex")]'),rel+': unrelated page acquired noindex')
check(actual==expected,'Review URL inventory differs from the audited553 pages')
check(counts==Counter({l:79 for l in LANGS}) and normal==Counter({l:55 for l in LANGS}) and redirects==Counter({l:24 for l in LANGS}),'Expected79 review URLs per language (55normal +24redirect)')
from build_guides import generated_paths
check(head_links==217*8+2*len(generated_paths()),'Expected1736 head hreflang links across217 indexable pages')
for filename in [ROOT/'sitemap.xml',DIST/'sitemap.xml']:
 urls=[e.text for e in ET.parse(filename).getroot().iter() if e.tag.endswith('}loc')]
 check(len(urls)==217 and len(set(urls))==217,str(filename)+': expected217 unique business/guide URLs')
 for url in urls:
  path=urlsplit(url).path.lstrip('/');path=path+'index.html' if not path or path.endswith('/') else path
  check(not is_review_page(path),str(filename)+': review URL remains '+url)
check(hashlib.sha256((DIST/'review-samples.json').read_bytes()).hexdigest()==CONFIG['source_record_sha256'],'Original review source records changed')
cat=json.loads((ROOT/'scripts/locale-source.json').read_text());retired={e['id']:e for e in cat if e.get('retired')}
check(set(retired)=={'765','768'} and all(e['text']=='' for e in retired.values()),'Retired prompt IDs must retain numbers with empty text')
for l in LANGS[1:]:
 d=json.loads((DIST/'i18n'/f'{l}.json').read_text());check(d['765']==d['768']=='',l+': retired prompt translation remains')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} review-indexing failures')
print('PASS:553/553 review pages noindex,follow; '+', '.join(l+' '+str(counts[l]) for l in LANGS)+' (each55normal +24redirect).')
print('PASS: source/published sitemap217 URLs; normal hreflang217 pages/31 groups, no review alternates; Googlebot may crawl reviews.')
print('PASS: both prompts removed in all languages; all553 review bodies match approved prompt-only cleanup; customer source records unchanged.')
