"""Owner-approved review noindex policy; never changes content or redirect targets."""
from pathlib import Path
from lxml import html,etree
import json
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
CONFIG=json.loads((ROOT/'scripts/review-indexing.json').read_text())
PAGES=set(CONFIG['normal_pages'])|set(CONFIG['redirect_pages'])
LANGS=('en','es','fr','de','pt','ru','ar')
def validate_review_inventory():
 actual={p.name for p in DIST.glob('*.html') if p.name.startswith(('review-','testimonials'))}
 if actual!=PAGES:raise ValueError('Review inventory changed; review the explicit noindex manifest before building')

def source_path(path):
 parts=Path(path).as_posix().split('/')
 return '/'.join(parts[1:]) if parts[0] in LANGS[1:] else '/'.join(parts)
def is_review_page(path):return source_path(path) in PAGES

def apply_review_policy(t,page):
 if not is_review_page(page.relative_to(DIST).as_posix()):return
 for e in list(t.xpath('//head/meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="robots"] | //head/link[@hreflang]')):e.getparent().remove(e)
 etree.SubElement(t.find('head'),'meta',{'name':'robots','content':'noindex,follow'})

def patch_review_redirects():
 # These localized legacy files are intentionally NOT regenerated from English.
 # Only add the owner-approved robots tag, leaving all existing bytes intact.
 tag='<meta name="robots" content="noindex,follow">'
 for page in CONFIG['redirect_pages']:
  for code in LANGS:
   p=DIST/('' if code=='en' else code)/page
   raw=p.read_text();t=html.fromstring(raw)
   if not t.xpath('//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'):raise ValueError('Expected existing review refresh stub: '+str(p))
   robots=t.xpath('//head/meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="robots"]')
   if robots:
    if len(robots)!=1 or robots[0].get('content')!='noindex,follow':raise ValueError('Unexpected review redirect robots rule: '+str(p))
   else:
    if raw.count('</head>')!=1:raise ValueError('Expected one head in review stub: '+str(p))
    p.write_text(raw.replace('</head>',tag+'</head>'))
