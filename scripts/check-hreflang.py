#!/usr/bin/env python3
"""Read-only Task 02 regression checks; called by check-locales.py.
The baseline records Task 01 page paths and frozen redirect hashes. Update it
only when a later task explicitly authorizes changing that page inventory.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote, urljoin
from collections import Counter
from lxml import html
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com'
LANGS=('en','es','fr','de','pt','ru','ar')
BASE=json.loads((ROOT/'scripts/hreflang-baseline.json').read_text())
REFRESH='//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'
errors=[]
def check(condition,message):
 if not condition:errors.append(message)
def path_for(source,code):return source if code=='en' else code+'/'+source
def expected_url(source,code):
 path=path_for(source,code)
 if path=='index.html':path=''
 elif path.endswith('/index.html'):path=path[:-10]
 return ORIGIN+'/'+path
normal={path_for(source,code) for source in BASE['normal_english_pages'] for code in LANGS}
redirects=BASE['redirect_sha256']
actual={p.relative_to(DIST).as_posix() for p in DIST.rglob('*.html')}
check(actual==normal|set(redirects),'HTML inventory differs from Task 01: missing='+str(sorted((normal|set(redirects))-actual))+' extra='+str(sorted(actual-(normal|set(redirects)))))
docs={rel:html.parse(str(DIST/rel)) for rel in actual}
for rel,digest in redirects.items():
 p=DIST/rel
 if not p.is_file():continue
 check(hashlib.sha256(p.read_bytes()).hexdigest()==digest,rel+': redirect bytes changed')
 check(bool(docs[rel].xpath(REFRESH)),rel+': lost refresh')
 check(not docs[rel].xpath('//link[@hreflang]'),rel+': redirect has head hreflang')
counts=Counter();maps={};urls={};groups={}
for source in BASE['normal_english_pages']:
 group={code:expected_url(source,code) for code in LANGS}
 group['x-default']=group['en']
 for code in LANGS:
  rel=path_for(source,code)
  if rel not in docs:continue
  before=len(errors);doc=docs[rel];self_url=group[code]
  check(not doc.xpath(REFRESH),rel+': normal page became a redirect')
  check(doc.getroot().get('lang')==code,rel+': document language')
  if code=='ar':check(doc.getroot().get('dir')=='ltr',rel+': Arabic LTR changed')
  check(doc.xpath('//head/link[@rel="canonical"]/@href')==[self_url],rel+': canonical is not its original self URL')
  links=doc.xpath('//head/link[@rel="alternate"][@hreflang]')
  check(len(links)==8,rel+': expected 7 language alternates plus x-default')
  check(len(doc.xpath('//link[@hreflang]'))==8,rel+': duplicate/misplaced hreflang links')
  codes=[e.get('hreflang') for e in links]
  check(len(codes)==len(set(codes)),rel+': duplicate hreflang code')
  mapping={e.get('hreflang'):e.get('href') for e in links}
  check(mapping==group,rel+': alternate URLs do not match the same English-source topic')
  check(mapping.get(code)==self_url,rel+': missing self-reference')
  check(mapping.get('x-default')==group['en'],rel+': x-default does not point to its English counterpart')
  for target_code,href in mapping.items():
   if not href:errors.append(rel+': empty href');continue
   u=urlsplit(href)
   check(u.scheme=='https' and u.netloc=='chinaattest.com' and not u.query and not u.fragment,rel+': invalid origin or URL '+href)
   path=unquote(u.path.lstrip('/'))
   if not path or path.endswith('/'):path+='index.html'
   target=docs.get(path)
   check(target is not None,rel+': target missing '+href)
   if target is not None:
    check(not target.xpath(REFRESH),rel+': target redirects '+href)
    check(target.getroot().get('lang')==('en' if target_code=='x-default' else target_code),rel+': target language mismatch '+href)
  # Existing switcher destinations independently confirm the topic/path mapping.
  for anchor in doc.xpath('//header/nav//*[contains(concat(" ",normalize-space(@class)," ")," language-switcher ")]//a[@hreflang]'):
   destination=urljoin(self_url,anchor.get('href',''))
   u=urlsplit(destination);normalized=destination
   if u.path.endswith('/index.html'):normalized=destination[:-10]
   check(normalized==group.get(anchor.get('hreflang')),rel+': hreflang disagrees with existing language navigation')
  maps[self_url]=mapping;urls[self_url]=rel;groups[self_url]=group
  if len(errors)==before:counts[code]+=1
for self_url,mapping in maps.items():
 for code in LANGS:
  target=mapping.get(code)
  if target in maps:
   source_code=docs[urls[self_url]].getroot().get('lang')
   check(maps[target].get(source_code)==self_url,urls[self_url]+': one-way reference to '+target)
   check(maps[target]==groups[self_url],urls[self_url]+': inconsistent language cluster '+target)
  else:check(False,urls[self_url]+': counterpart is not an audited normal page '+str(target))
check(len(normal)==602 and len(redirects)==175,'Unexpected Task 01 baseline counts')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} hreflang failures')
print('PASS: hreflang 602/602 normal pages; '+', '.join(code+' '+str(counts[code])+'/86' for code in LANGS))
print('PASS: 86 complete topic groups; 4816 head alternate tags; self-references, reciprocal links, x-default, production URLs and Canonical.')
print('PASS: 175 redirect files unchanged, no redirect hreflang; HTML path inventory and Arabic LTR preserved.')
