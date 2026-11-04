#!/usr/bin/env python3
"""Build static language editions from the English pages and checked-in translations.
Run after editing English content; missing translations fail rather than silently showing English.
Requires lxml (build-time only). No translation API or runtime dependency.
"""
from pathlib import Path
from lxml import html, etree
from urllib.parse import urlsplit, urlunsplit, urljoin
import json,re,copy,posixpath
ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/'dist'
LANGS={'en':'English','es':'Spanish','fr':'French','de':'German','pt':'Portuguese','ru':'Russian','ar':'Arabic'}
CAT=json.loads((ROOT/'scripts/locale-source.json').read_text())
IDS={x['text']:x['id'] for x in CAT}
UI=['Open navigation','Close navigation','WeChat number copied: 15118019493','Add this number in WeChat: 15118019493','Copied:','Email us at','Sending…','Thank you! Your enquiry has been submitted to China Attest. We will reply to the email address you provided.','Too many submissions. Please wait a few minutes before trying again, or email chinaattest.team@gmail.com.','We could not confirm your submission. Your details are still here. Please try again, or email chinaattest.team@gmail.com.','article','articles','Page','of']
MISSING=set()
def review_page(p):return p.name.startswith(('review-','testimonials'))
def protected(e,p):
 # Language labels always stay in English; reviews follow the page language.
 return any('language-switcher' in a.get('class','').split() for a in [e,*e.iterancestors()])

def trans(s,d):
 v=s.strip()
 if not v or not any(c.isalpha() for c in v):return s
 if v not in IDS:MISSING.add(v);return s
 return s[:len(s)-len(s.lstrip())]+d[IDS[v]]+s[len(s.rstrip()):]
def localurl(s,p,lang):
 u=urlsplit(s)
 if not s or s.startswith('#') or u.scheme or u.netloc:return s
 base='/'+p.relative_to(DIST).as_posix()
 path=urlsplit(urljoin(base,s)).path
 if path.startswith(tuple('/'+x+'/' for x in LANGS if x!='en')):return s
 resolved=DIST/path.lstrip('/')
 if resolved.is_dir():resolved=resolved/'index.html'
 if path.endswith('.html') or resolved.suffix=='.html' and resolved.exists():path='/'+lang+path if lang!='en' else path
 return urlunsplit(('', '',path,u.query,u.fragment))
def switcher(p,lang):
 relative=p.relative_to(DIST).as_posix()
 if relative=='index.html':relative=''
 elif relative.endswith('/index.html'):relative=relative[:-10]
 el=html.Element('div',{'class':'dropdown language-switcher notranslate','translate':'no','dir':'ltr'})
 btn=etree.SubElement(el,'button',{'type':'button','aria-expanded':'false','aria-label':'Language — '+LANGS[lang]})
 svg=html.fragment_fromstring('<svg viewBox="0 0 24 24" aria-hidden="true" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z"></path></svg>')
 btn.append(svg);svg.tail=' Language '
 etree.SubElement(btn,'span',{'class':'chevron'})
 sub=etree.SubElement(el,'div',{'class':'submenu language-options'})
 for code,name in LANGS.items():
  dest=('/' if code=='en' else '/'+code+'/')+relative
  a=etree.SubElement(sub,'a',{'href':dest,'lang':'en','hreflang':code})
  a.text=name
  a.set('dir','ltr')
  if code==lang:a.set('aria-current','true')
 return el

def decorate(t,p,lang):
 head=t.find('head')
 for e in t.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," language-switcher ")] | //link[@data-languages] | //script[@data-languages]'):
  e.getparent().remove(e)
 for nav in t.xpath('//header/nav'):nav.append(switcher(p,lang))
 for e in t.xpath('//script[@src]'):
  if e.get('src').split('?')[0].split('/')[-1] in ['app.js','contact.js']:e.set('src',e.get('src').split('?')[0]+'?v=20261103-languages')
 etree.SubElement(head,'link',{'rel':'stylesheet','href':'/languages.css?v=20261103-restored-nav','data-languages':'true'})
 if lang=='ar':etree.SubElement(head,'link',{'rel':'stylesheet','href':'/arabic.css?v=20261104-ltr','data-languages':'true'})
 if lang!='en':etree.SubElement(head,'script',{'src':'/i18n/'+lang+'-ui.js?v=20261103','data-languages':'true'}).text=''
 etree.SubElement(head,'script',{'src':'/language.js?v=20261103','defer':'defer','data-languages':'true'}).text=''

def make(t,p,lang,d):
 t.set('lang',lang)
 t.set('dir','ltr')
 for e in t.iter():
  if not isinstance(e.tag,str):continue
  if not protected(e,p):
   if e.tag not in ['script','style'] and not any(a.tag in ['script','style'] for a in e.iterancestors()):
    if e.text:e.text=trans(e.text,d)
   for key in ['alt','title','placeholder','aria-label']:
    if e.get(key):e.set(key,trans(e.get(key),d))
   if e.tag=='meta' and (e.get('name') in ['description','twitter:title','twitter:description'] or e.get('property') in ['og:title','og:description']):e.set('content',trans(e.get('content',''),d))
  if e.tail and e.getparent() is not None and not protected(e.getparent(),p) and not any(a.tag in ['script','style'] for a in e.iterancestors()):e.tail=trans(e.tail,d)
  if e.tag=='meta' and e.get('http-equiv','').lower()=='refresh':
   e.set('content',re.sub(r'(?i)(url=)(.*)',lambda m:m[1]+localurl(m[2],p,lang),e.get('content','')))
  if e.tag=='meta' and e.get('property')=='og:locale':e.set('content',{'es':'es_ES','fr':'fr_FR','de':'de_DE','pt':'pt_BR','ru':'ru_RU','ar':'ar_SA'}[lang])
  # Asset paths stay shared; page links stay in the chosen language edition.
  for key in ['href','src','poster','action']:
   if e.get(key):e.set(key,localurl(e.get(key),p,lang))
  if e.get('srcset'):
   e.set('srcset',', '.join(' '.join([localurl(x.split()[0],p,lang),*x.split()[1:]]) for x in e.get('srcset').split(',')))
  # Preserve submission option VALUES and filter keys; only labels are localized.
  if e.tag=='option' and e.get('value') is None:e.set('value',e.text or '')
  if e.tag=='script' and e.get('type')=='application/ld+json' and e.text:
   data=json.loads(e.text)
   def schema(x):
    if isinstance(x,list):return [schema(a) for a in x]
    if not isinstance(x,dict):return x
    result={}
    for k,v in x.items():
     if k in ['headline','description','articleSection','name'] and isinstance(v,str) and v in IDS:v=d[IDS[v]]
     if k=='inLanguage':v=lang
     # Production domain is not confirmed: omit URL assertions from localized schemas.
     if k in ['@id','url','mainEntityOfPage','item'] and isinstance(v,(str,dict)):continue
     result[k]=schema(v)
    return result
   e.text=json.dumps(schema(data),ensure_ascii=False)
 # Translated punctuation-leading tails may now begin with a word.
 # Keep adjacent inline nodes separated without flattening semantic markup.
 for e in t.iter():
  if not isinstance(e.tag,str) or e.tag not in ['a','strong','em','b','i','span'] or protected(e,p):continue
  if e.tail and e.tail.lstrip().startswith((',', '.')):e.tail=e.tail.lstrip()
  if e.tail and e.tail[0].isalnum():
   before=''.join(e.itertext())
   if before and not before[-1].isspace() and before[-1] not in "’'/-":e.tail=' '+e.tail
 if lang=='ar':prepare_arabic(t,p)
 # Do not canonicalize a translation to its English page or an unconfirmed domain.
 for e in list(t.xpath('//link[@rel="canonical"] | //meta[@property="og:url"]')):e.getparent().remove(e)
 for e in t.xpath('//*[@class and contains(concat(" ",normalize-space(@class)," ")," blog-entry ")]'):
  e.set('data-search',(' '.join(e.itertext())+' '+e.get('data-search','')).lower())
 decorate(t,p,lang)
 return t

def prepare_arabic(t,p):
 # Keep mixed-direction contact details and organization names intact.
 pattern=re.compile(r"Shenzhen Huanqiu Xuelv Technology Co\., Ltd\.|China Attest|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+86(?:[ \u00a0]?\d){11}|15118019493|[↗↘↙↖←→↓↑]")
 def isolate(e,attr):
  value=getattr(e,attr)
  if not value or not pattern.search(value):return
  pieces=pattern.split(value);matches=pattern.findall(value)
  setattr(e,attr,pieces[0])
  parent=e if attr=='text' else e.getparent()
  if parent is None:return
  index=0 if attr=='text' else parent.index(e)+1
  for match,tail in zip(matches,pieces[1:]):
   bdi=html.Element('bdi',dir='ltr');bdi.text=match;bdi.tail=tail
   paths={'↗':'M5 19 19 5M5 5h14v14','↘':'M5 5 19 19M5 19h14V5','↙':'M19 5 5 19M5 5v14h14','↖':'M19 19 5 5M5 19V5h14','←':'M20 12H4m7-7-7 7 7 7','→':'M4 12h16m-7-7 7 7-7 7','↓':'M12 4v16m-7-7 7 7 7-7','↑':'M12 20V4m-7 7 7-7 7 7'}
   if match in paths:
    bdi.text=None;bdi.set('class','ui-direction-arrow');bdi.set('aria-hidden','true')
    svg=html.fragment_fromstring('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="'+paths[match]+'"></path></svg>');bdi.append(svg)
   parent.insert(index,bdi);index+=1
 for e in list(t.iter()):
  if not isinstance(e.tag,str) or e.tag in ['script','style','title'] or any(a.tag in ['script','style','head'] for a in e.iterancestors()):continue
  if not protected(e,p):
   isolate(e,'text')
  if e.getparent() is not None and not protected(e.getparent(),p):isolate(e,'tail')
 for e in t.xpath('//input[@type="email"] | //input[@name="email"] | //*[@id="contact-count"]'):
  e.set('dir','ltr')
 for e in t.xpath('//input[@name="name"] | //textarea'):e.set('dir','ltr')
 for e in t.xpath('//a[starts-with(@href,"tel:")] | //a[starts-with(@href,"mailto:")] | //*[contains(concat(" ",normalize-space(@class)," ")," contact-value ")]'):
  # Preserve contact details in the English-layout edition.
  if not re.search(r'[\u0600-\u06ff]', ''.join(e.itertext())) or 'contact-value' in e.get('class',''):e.set('dir','ltr')

def portable_urls(t,p):
 # Relative URLs work both on the hosted Site and when opening extracted HTML files.
 base=p.relative_to(DIST).parent.as_posix()
 def relative(value):
  u=urlsplit(value)
  if u.scheme or u.netloc or not u.path:return value
  if not u.path.startswith('/'):
   if (DIST/base/u.path).is_dir():return urlunsplit(('', '',u.path.rstrip('/')+'/index.html',u.query,u.fragment))
   return value
  target=u.path.lstrip('/')
  if (DIST/target).is_dir():target=target.rstrip('/')+'/index.html' if target else 'index.html'
  return urlunsplit(('', '',posixpath.relpath(target,base),u.query,u.fragment))
 for e in t.iter():
  if not isinstance(e.tag,str):continue
  for key in ['href','src','poster','action']:
   if e.get(key):e.set(key,relative(e.get(key)))
  if e.get('srcset'):e.set('srcset',', '.join(' '.join([relative(x.split()[0]),*x.split()[1:]]) for x in e.get('srcset').split(',')))
  if e.tag=='meta' and e.get('http-equiv','').lower()=='refresh':e.set('content',re.sub(r'(?i)(url=)(.*)',lambda m:m[1]+relative(m[2]),e.get('content','')))

def main():
 pages=[p for p in sorted(DIST.rglob('*.html')) if p.relative_to(DIST).parts[0] not in LANGS or p.relative_to(DIST).parts[0]=='en']
 data={}
 for lang in LANGS:
  if lang=='en':continue
  d=json.loads((DIST/'i18n'/f'{lang}.json').read_text())
  assert set(d)==set(IDS.values()),(lang,'missing or unknown IDs')
  assert all(isinstance(x,str) and x.strip() for x in d.values()),lang
  data[lang]=d
  ui={s:d[IDS[s]] for s in UI}
  (DIST/'i18n'/f'{lang}-ui.js').write_text('window.siteTranslations='+json.dumps(ui,ensure_ascii=False)+';\n')
 for p in pages:
  original=html.fromstring(p.read_bytes())
  # Remove old generated additions before source translation on a rebuild.
  for e in original.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," language-switcher ")] | //link[@data-languages] | //script[@data-languages]'):e.getparent().remove(e)
  # Previously the review sections were excluded from translation.
  review_roots=original.xpath('//*[@id="testimonials"] | //*[contains(concat(" ",normalize-space(@class)," ")," service-feedback ")]')
  if review_page(p):review_roots+=original.xpath('//main')
  for e in review_roots:
   e.attrib.pop('translate',None);e.attrib.pop('lang',None);e.attrib.pop('dir',None)
  # Explicit option values must be captured BEFORE translating labels.
  for opt in original.xpath('//option[not(@value)]'):opt.set('value',opt.text or '')
  for lang,d in data.items():
   t=make(copy.deepcopy(original),p,lang,d)
   dest=DIST/lang/p.relative_to(DIST);dest.parent.mkdir(parents=True,exist_ok=True)
   portable_urls(t,dest)
   dest.write_bytes(html.tostring(t,encoding='utf-8',doctype='<!DOCTYPE html>'))
  decorate(original,p,'en')
  portable_urls(original,p)
  p.write_bytes(html.tostring(original,encoding='utf-8',doctype='<!DOCTYPE html>'))
 if MISSING:raise ValueError('Add new source strings and translations: '+repr(sorted(MISSING)))
 print(f'Built {len(pages)} English pages and {len(pages)*len(data)} translated pages; {len(IDS)} translation strings per language.')
if __name__=='__main__':main()
