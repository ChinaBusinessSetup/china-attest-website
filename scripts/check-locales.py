#!/usr/bin/env python3
"""Check static editions, links, review exclusions and inquiry configuration."""
from pathlib import Path
from lxml import html
from urllib.parse import urlsplit,unquote
import json,re
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist';LANGS=['es','fr','de','pt','ru','ar']
source=json.loads((ROOT/'scripts/locale-source.json').read_text()); keys={x['id'] for x in source}
pages=[p for p in DIST.rglob('*.html') if p.relative_to(DIST).parts[0] not in LANGS]
errors=[]; checked=0
for lang in LANGS:
 d=json.loads((DIST/'i18n'/f'{lang}.json').read_text())
 if set(d)!=keys:errors.append((lang,'translation keys differ'))
 for p in pages:
  local=DIST/lang/p.relative_to(DIST)
  if not local.exists():errors.append((str(local),'missing page'));continue
  t=html.parse(str(local));en=html.parse(str(p));checked+=1
  if t.getroot().get('lang')!=lang:errors.append((str(local),'wrong document language'))
  if lang=='ar' and t.getroot().get('dir')!='ltr':errors.append((str(local),'Arabic does not use the English LTR layout'))
  if len(t.xpath('//h1'))!=len(en.xpath('//h1')):errors.append((str(local),'headings changed'))
  for e in t.xpath('//*[@href or @src or @action]'):
   for attr in ['href','src','action']:
    s=e.get(attr)
    if not s:continue
    u=urlsplit(s)
    if u.scheme or u.netloc or s.startswith('#'):continue
    dest=DIST/unquote(u.path).lstrip('/') if u.path.startswith('/') else local.parent/unquote(u.path)
    if dest.is_dir():dest=dest/'index.html'
    if not dest.exists():errors.append((str(local),'broken '+attr,s));continue
    if attr=='href' and dest.suffix=='.html':
     if not dest.is_relative_to(DIST/lang) and not any('language-switcher' in a.get('class','') for a in e.iterancestors()):errors.append((str(local),'left language edition',s))
     if u.fragment:
      target=html.parse(str(dest))
      if not target.xpath('//*[@id=$v or @name=$v]',v=unquote(u.fragment)):errors.append((str(local),'missing anchor',s))
  switch=t.xpath('//header/nav//div[contains(@class,"language-switcher")]')
  if en.xpath('//header/nav'):
   if len(switch)!=1 or len(switch[0].xpath('.//a'))!=7:errors.append((str(local),'wrong language switcher'))
  # Customer reviews follow the selected language.
  if t.xpath('//*[@id="testimonials"]') and lang!='en':
   section=t.xpath('//*[@id="testimonials"]')[0]
   if section.get('translate')=='no' or section.get('lang')=='en':errors.append((str(local),'review localization still disabled'))
   title=section.xpath('./h2')
   if not title or ''.join(title[0].itertext()).strip()!=d['751']:errors.append((str(local),'original review heading missing'))
  if p.name.startswith('review-sample-'):
   title=''.join(t.xpath('//title')[0].itertext()).strip()
   if title==''.join(en.xpath('//title')[0].itertext()).strip():errors.append((str(local),'review title untranslated'))
  if p.name=='contact.html':
   a=en.xpath('//form[@id="contact-inquiry"]')[0];b=t.xpath('//form[@id="contact-inquiry"]')[0]
   if a.get('action')!=b.get('action') or b.get('action')!='https://formspree.io/f/mbggpvyz':errors.append((lang,'form destination changed'))
   def fields(f):return [(e.tag,e.get('name'),e.get('type'),e.get('required'),e.get('maxlength')) for e in f.xpath('.//input|.//select|.//textarea')]
   if fields(a)!=fields(b):errors.append((lang,'form fields changed'))
   if a.xpath('.//option/@value')!=b.xpath('.//option/@value'):errors.append((lang,'service values changed'))
   if 'chinaattest.team@gmail.com' not in ''.join(t.getroot().itertext()):errors.append((lang,'contact email missing'))
  for e in t.xpath('//script[@type="application/ld+json"]'):json.loads(e.text)
print(f'Checked {checked} translated pages; {len(source)} strings × {len(LANGS)} languages.')
if errors:
 for x in errors[:80]:print('ERROR',x)
 raise SystemExit(f'{len(errors)} failures')
print('PASS: language routes, local links/anchors, localized reviews, form endpoint/fields/options, headings and JSON-LD.')
