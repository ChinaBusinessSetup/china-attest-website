#!/usr/bin/env python3
"""Read-only validation of BreadcrumbList against rendered static HTML.
Also checks the exact original non-Breadcrumb JSON-LD text recorded in Task 04.
"""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from collections import Counter
from lxml import html
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
BASE=json.loads((ROOT/'scripts/hreflang-baseline.json').read_text())
SCHEMA_BASE=json.loads((ROOT/'scripts/breadcrumb-schema-baseline.json').read_text())
LANGS=('en','es','fr','de','pt','ru','ar');ORIGIN='https://chinaattest.com'
errors=[];counts=Counter();parsed=0;original_blocks=0;schema_types=Counter();docs={}
def check(condition,message):
 if not condition:errors.append(message)
def walk(value):
 if isinstance(value,dict):
  yield value
  for v in value.values():yield from walk(v)
 elif isinstance(value,list):
  for v in value:yield from walk(v)
def has_type(node,name):
 types=node.get('@type',[])
 return types==name or isinstance(types,list) and name in types
def label(node):return ' '.join(''.join(node.itertext()).split())
def abs_url(href,rel):
 u=urlsplit(urljoin(ORIGIN+'/'+rel,href))
 path=u.path[:-10] if u.path.endswith('/index.html') else u.path
 return urlunsplit((u.scheme,u.netloc,path,u.query,u.fragment))
for p in sorted(DIST.rglob('*.html')):
 rel=p.relative_to(DIST).as_posix();docs[rel]=html.parse(str(p))
for rel,t in docs.items():
 scripts=t.xpath('//script[@type="application/ld+json"]');nodes=[];others=[]
 for script in scripts:
  try:
   data=json.loads(script.text);parsed+=1;nodes+=list(walk(data))
   for node in walk(data):
    types=node.get('@type',[])
    if isinstance(types,str):schema_types[types]+=1
  except (ValueError,TypeError) as e:errors.append(rel+': JSON-LD parse error '+str(e))
  if script.get('data-breadcrumb-schema') is None and script.get('data-entity-schema') is None:others.append(script.text)
 check(others==SCHEMA_BASE.get(rel,[]),rel+': original Article/BlogPosting schema differs beyond approved Organization identities')
 original_blocks+=len(others)
 breads=[node for node in nodes if has_type(node,'BreadcrumbList')]
 code=t.getroot().get('lang');nav=t.xpath('//main//nav[contains(concat(" ",normalize-space(@class)," ")," breadcrumb-nav ")]')
 if rel in BASE['redirect_sha256']:
  check(not breads and not t.xpath('//script[@data-breadcrumb-schema]'),rel+': redirect must not have breadcrumb schema')
  check(hashlib.sha256((DIST/rel).read_bytes()).hexdigest()==BASE['redirect_sha256'][rel],rel+': frozen redirect modified')
  continue
 source=rel if code=='en' else rel.removeprefix(code+'/')
 if source=='index.html':
  check(not breads and not nav and not t.xpath('//script[@data-breadcrumb-schema]'),rel+': homepage has breadcrumb schema')
  continue
 before=len(errors)
 check(len(breads)==1,rel+': expected exactly one BreadcrumbList')
 check(len(nav)==1,rel+': missing/duplicate visible breadcrumb')
 marked=t.xpath('//head/script[@type="application/ld+json"][@data-breadcrumb-schema="v69"]')
 check(len(marked)==1,rel+': expected one managed head schema block')
 if len(breads)!=1 or len(nav)!=1:continue
 data=breads[0];items=data.get('itemListElement',[]);li=nav[0].xpath('./ol[@class="breadcrumbs"]/li')
 check(isinstance(items,list) and len(items)>=2 and len(items)==len(li),rel+': item count differs from HTML')
 if not isinstance(items,list) or len(items)!=len(li):continue
 check([x.get('position') for x in items if isinstance(x,dict)]==list(range(1,len(li)+1)),rel+': positions not consecutive')
 for index,(entry,visible) in enumerate(zip(items,li),1):
  if not isinstance(entry,dict):errors.append(rel+': ListItem is not an object');continue
  check(entry.get('@type')=='ListItem' and type(entry.get('position')) is int,rel+': invalid ListItem type/position')
  links=visible.xpath('./a[@href]');current=index==len(li)
  if current:
   current_label=visible.xpath('./span[@class="breadcrumb-label"]')
   check(visible.get('aria-current')=='page' and not links and len(current_label)==1,rel+': invalid HTML current item')
   name=label(current_label[0]) if current_label else ''
   check('item' not in entry,rel+': generated current item should omit self URL')
  else:
   check(len(links)==1,rel+': ancestor must have one link')
   name=label(links[0]) if links else ''
   expected=abs_url(links[0].get('href'),rel) if links else ''
   check(entry.get('item')==expected,rel+': item URL differs from HTML '+str(entry.get('item')))
   value=entry.get('item')
   if not isinstance(value,str):errors.append(rel+': ancestor URL missing');continue
   u=urlsplit(value)
   check(u.scheme=='https' and u.netloc=='chinaattest.com' and not u.query,rel+': wrong item origin/URL '+value)
   path=unquote(u.path).lstrip('/')
   if not path or path.endswith('/'):path+='index.html'
   target=docs.get(path)
   check(target is not None,rel+': item target does not exist '+value)
   if target is not None:
    check(target.getroot().get('lang')==code,rel+': item points to wrong language '+value)
    check(path not in BASE['redirect_sha256'],rel+': item target is a redirect')
    check(target.xpath('//head/link[@rel="canonical"]/@href')==[urlunsplit((u.scheme,u.netloc,u.path,'',''))],rel+': item target is not canonical '+value)
    if u.fragment:check(bool(target.xpath('//*[@id=$id or @name=$id]',id=unquote(u.fragment))),rel+': item anchor missing '+value)
  check(bool(name) and entry.get('name')==name,rel+': schema name differs from localized HTML')
 if marked:
  check(json.loads(marked[0].text).get('@context')=='https://schema.org',rel+': missing Schema.org context')
 if code=='ar':check(t.getroot().get('dir')=='ltr',rel+': Arabic LTR changed')
 if len(errors)==before:counts[code]+=1
check(set(SCHEMA_BASE)<=set(docs),'A page containing original schema was removed')
check(counts==Counter({code:85 for code in LANGS}),'Expected 85 valid BreadcrumbLists per language: '+str(dict(counts)))
check(parsed==631 and original_blocks==14,'Expected 595 BreadcrumbList + 14 original + 22 entity JSON-LD blocks')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} BreadcrumbList failures')
print('PASS: BreadcrumbList 595/595; '+', '.join(code+' '+str(counts[code])+'/85' for code in LANGS))
print(f'PASS: {parsed} JSON-LD blocks parsed; {original_blocks} original blocks preserved with unified Organization identities; Article {schema_types["Article"]}, BlogPosting {schema_types["BlogPosting"]}, Organization {schema_types["Organization"]}.')
print('PASS: HTML names, positions, item URLs and fragments match; no duplicates/missing lists, homepage or redirect lists, incorrect domains or wrong-language items.')
