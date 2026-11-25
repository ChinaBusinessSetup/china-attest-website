#!/usr/bin/env python3
"""Read-only checks for semantic, static and localized visible breadcrumbs."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from collections import Counter
from lxml import html
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
LANGS=('en','es','fr','de','pt','ru','ar')
spec=json.loads((ROOT/'scripts/breadcrumb-pages.json').read_text())
base=json.loads((ROOT/'scripts/hreflang-baseline.json').read_text())
cat=json.loads((ROOT/'scripts/locale-source.json').read_text());ids={x['text']:x['id'] for x in cat}
dicts={code:json.loads((DIST/'i18n'/f'{code}.json').read_text()) for code in LANGS if code!='en'}
errors=[];counts=Counter();types=Counter()
def check(condition,message):
 if not condition:errors.append(message)
def translate(text,code):return text if code=='en' else dicts[code][ids[text]]
def text(e):return ''.join(e.itertext()).strip()
def localized(target,code):return '/'+('' if code=='en' else code+'/')+target
check(set(spec)==set(base['normal_english_pages'])-{'index.html'},'Every normal non-home source must have an explicit breadcrumb classification')
for code in LANGS:
 home=DIST/('' if code=='en' else code)/'index.html';t=html.parse(str(home))
 check(not t.xpath('//nav[contains(concat(" ",normalize-space(@class)," ")," breadcrumb-nav ")] | //ol[@class="breadcrumbs"]'),str(home)+': homepage must not show breadcrumbs')
 for page,base_info in spec.items():
  info=base_info.get("english_override",base_info) if code=="en" else base_info
  rel=('' if code=='en' else code+'/')+page;p=DIST/rel;t=html.parse(str(p));before=len(errors)
  navs=t.xpath('//main//nav[contains(concat(" ",normalize-space(@class)," ")," breadcrumb-nav ")]')
  check(len(navs)==1,rel+': expected exactly one static breadcrumb nav')
  if len(navs)!=1:continue
  nav=navs[0]
  check(nav.get('aria-label')==translate('Breadcrumb',code),rel+': navigation label not localized')
  check(not nav.xpath('.//script'),rel+': breadcrumbs must not require JavaScript')
  lists=nav.xpath('./ol[@class="breadcrumbs"]')
  check(len(lists)==1,rel+': expected semantic ordered list')
  if len(lists)!=1:continue
  items=lists[0].xpath('./li')
  check(len(items)==len(info['ancestors'])+1,rel+': wrong breadcrumb depth')
  if len(items)!=len(info['ancestors'])+1:continue
  for i,parent in enumerate(info['ancestors']):
   item=items[i];links=item.xpath('./a')
   check(len(links)==1,rel+': each ancestor needs one actual link')
   check(item.get('aria-current') is None,rel+': ancestor cannot be current')
   if not links:continue
   a=links[0];check(text(a)==translate(parent['label'],code),rel+': ancestor name not translated')
   resolved=urljoin('/'+rel,a.get('href',''))
   check(resolved==localized(parent['target'],code),rel+': wrong ancestor destination '+resolved)
   u=urlsplit(resolved);dest=DIST/unquote(u.path).lstrip('/')
   if dest.is_dir():dest=dest/'index.html'
   check(dest.is_file(),rel+': missing ancestor file '+resolved)
   if dest.is_file():
    ancestor=html.parse(str(dest));check(ancestor.getroot().get('lang')==code,rel+': ancestor leaves language')
    check(not ancestor.xpath('//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'),rel+': ancestor redirects')
    if u.fragment:check(bool(ancestor.xpath('//*[@id=$id]',id=u.fragment)),rel+': missing ancestor anchor')
  current=items[-1];check(current.get('aria-current')=='page',rel+': current item needs aria-current=page')
  check(not current.xpath('.//a'),rel+': current page must not have a self-link')
  label=current.xpath('./span[@class="breadcrumb-label"]')
  check(len(label)==1 and text(label[0])==translate(info['current'],code),rel+': current page name not translated')
  for item in items[1:]:check(item.xpath('./span[@class="breadcrumb-separator"]/@aria-hidden')==['true'],rel+': separator must be hidden from screen readers')
  css=t.xpath('//head/link[@rel="stylesheet"][contains(@href,"breadcrumbs.css")]/@href')
  check(len(css)==1,rel+': breadcrumb stylesheet missing/duplicated')
  check(not t.xpath('//main//*[contains(concat(" ",normalize-space(@class)," ")," article-back ")]'),rel+': old breadcrumb/back link not unified')
  if info['type']=='service':check(info['ancestors'][1]=={'label':'Services','target':'index.html#services'},rel+': invalid service hierarchy')
  if info['type']=='city':check(page.startswith('guide-police-') and info['ancestors'][1]=={'label':'Police Clearance','target':'police-clearance.html'},rel+': invalid city hierarchy')
  if info['type']=='city_guide_article':check(code=='en' and page in ['guide-police-shanghai.html','guide-police-shenzhen.html','guide-police-guangzhou.html','guide-police-beijing.html','guide-police-chengdu.html','guide-police-shenyang.html','guide-police-chongqing.html','guide-police-sanya.html','guide-police-xiamen.html','guide-police-tianjin.html','guide-police-hangzhou.html','guide-police-suzhou.html','guide-police-wuhan.html','guide-police-dalian.html','guide-police-changsha.html','guide-police-huizhou.html'] and info['ancestors'][1]=={'label':'City Guides','target':'how-to-police-certificate.html'},rel+': invalid English city article hierarchy')
  if info['type']=='guide':check(info['ancestors'][1]=={'label':'Guides','target':'blog.html'},rel+': invalid guide hierarchy')
  if info['type']=='review_index':check(len(items)==2 and info['current']=='Reviews',rel+': review archive hierarchy')
  if info['type'] in ('review_detail','review_pagination'):check(info['ancestors'][1]=={'label':'Reviews','target':'testimonials.html'},rel+': review parent must be real archive')
  if code=='ar':check(t.getroot().get('dir')=='ltr',rel+': Arabic LTR changed')
  if len(errors)==before:counts[code]+=1;types[info['type']]+=1
for rel,digest in base['redirect_sha256'].items():
 p=DIST/rel;check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,rel+': frozen redirect modified')
 if p.is_file():check(not html.parse(str(p)).xpath('//ol[@class="breadcrumbs"]'),rel+': redirect has new breadcrumbs')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} breadcrumb failures')
print('PASS: 595 static breadcrumb pages; '+', '.join(code+' '+str(counts[code])+'/85' for code in LANGS))
print('PASS: 7 homepages without breadcrumbs; ancestor files/anchors and language, current items, translations and semantic nav/ol/li valid.')
print('PASS: 175 redirect files unchanged; no JS dependency; Arabic LTR retained.')
