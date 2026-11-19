"""Generate only Organization, WebSite and the three actual Service types.
Use one global identity; preserve article fields and BreadcrumbList unchanged.
"""
from pathlib import Path
from urllib.parse import urlsplit
from lxml import html,etree
import json
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com';ORG=ORIGIN+'/#organization';SITE=ORIGIN+'/#website'
LANGS=('en','es','fr','de','pt','ru','ar')
SERVICES=json.loads((ROOT/'scripts/service-schema.json').read_text())
CAT={x['id']:x['text'] for x in json.loads((ROOT/'scripts/locale-source.json').read_text())}

def company():
 home=html.parse(str(DIST/'index.html'));contact=html.parse(str(DIST/'contact.html'))
 logos=home.xpath('//header/a[contains(concat(" ",normalize-space(@class)," ")," brand ")]/img/@src')
 if logos!=['assets/brand-optimized.webp'] or not (DIST/logos[0]).is_file():raise ValueError('Verify the actual homepage brand logo before building')
 phone='+8615118019493';email='chinaattest.team@gmail.com'
 if 'tel:'+phone not in home.xpath('//a/@href') or 'mailto:'+email not in contact.xpath('//a/@href'):raise ValueError('Verify existing contact details before building')
 return {'@type':'Organization','@id':ORG,'name':'China Attest','url':ORIGIN+'/','logo':ORIGIN+'/'+logos[0],'telephone':phone,'email':email}

def add_entity_schema(t,page):
 rel=page.relative_to(DIST).as_posix();parts=rel.split('/');lang=parts[0] if parts[0] in LANGS[1:] else 'en';source=rel if lang=='en' else '/'.join(parts[1:])
 for s in list(t.xpath('//script[@data-entity-schema]')):s.getparent().remove(s)
 # Only enrich existing company Organization nodes. Do not change other schema fields.
 for script in t.xpath('//script[@type="application/ld+json"]'):
  data=json.loads(script.text);changed=False
  def identify(x):
   nonlocal changed
   if isinstance(x,list):
    for v in x:identify(v)
   elif isinstance(x,dict):
    if x.get('@type')=='Organization' and x.get('name')=='China Attest' and x.get('@id')!=ORG:x['@id']=ORG;changed=True
    for v in x.values():identify(v)
  identify(data)
  if changed:script.text=json.dumps(data,ensure_ascii=False)
 graph=[]
 if rel=='index.html':
  graph=[company(),{'@type':'WebSite','@id':SITE,'name':'China Attest','url':ORIGIN+'/','publisher':{'@id':ORG},'inLanguage':list(LANGS)}]
 elif source in SERVICES:
  labels=t.xpath('//nav[@class="breadcrumb-nav"]//li[@aria-current="page"]/span[@class="breadcrumb-label"]')
  if len(labels)!=1:raise ValueError('Service must have its existing visible service name: '+rel)
  name=' '.join(''.join(labels[0].itertext()).split());key=SERVICES[source]['description_id']
  description=CAT[key] if lang=='en' else json.loads((DIST/'i18n'/f'{lang}.json').read_text())[key]
  canonical=t.xpath('//head/link[@rel="canonical"]/@href')
  if len(canonical)!=1 or not canonical[0].startswith(ORIGIN+'/'):raise ValueError('Service needs its own production Canonical: '+rel)
  graph=[{'@type':'Service','@id':canonical[0]+'#service','name':name,'serviceType':name,'url':canonical[0],'description':description,'provider':{'@id':ORG}}]
 if graph:
  etree.SubElement(t.find('head'),'script',{'type':'application/ld+json','data-entity-schema':'v69'}).text=json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<','\\u003c')
