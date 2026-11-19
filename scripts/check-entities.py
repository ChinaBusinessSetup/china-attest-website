#!/usr/bin/env python3
"""Validate the shared company/site entities and actual multilingual services."""
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlsplit
from lxml import html
import json
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com';ORG=ORIGIN+'/#organization';SITE=ORIGIN+'/#website'
LANGS=('en','es','fr','de','pt','ru','ar');PAGES={'police-clearance.html','authentication.html','degree-verification.html'}
config=json.loads((ROOT/'scripts/service-schema.json').read_text());catalog={x['id']:x['text'] for x in json.loads((ROOT/'scripts/locale-source.json').read_text())}
errors=[];orgs=[];sites=[];services=[];blocks=0;descriptions=defaultdict(set);languages=Counter()
def check(test,message):
 if not test:errors.append(message)
def walk(value):
 if isinstance(value,dict):
  yield value
  for v in value.values():yield from walk(v)
 elif isinstance(value,list):
  for v in value:yield from walk(v)
check(set(config)==PAGES,'Only the three existing service pages may have Service schema')
for p in DIST.rglob('*.html'):
 rel=p.relative_to(DIST).as_posix();t=html.parse(str(p));code=t.getroot().get('lang');source=rel if code=='en' else rel.removeprefix(code+'/')
 managed=t.xpath('//head/script[@type="application/ld+json"][@data-entity-schema="v69"]')
 expected=rel=='index.html' or source in PAGES
 check(len(managed)==int(expected),rel+': missing/duplicated/unexpected entity graph')
 for script in t.xpath('//script[@type="application/ld+json"]'):
  try:data=json.loads(script.text);blocks+=1
  except (ValueError,TypeError):errors.append(rel+': invalid JSON-LD');continue
  if script.get('data-entity-schema'):
   check(isinstance(data,dict) and data.get('@context')=='https://schema.org',rel+': entity graph context')
  for node in walk(data):
   typ=node.get('@type')
   if typ=='Organization':orgs.append((rel,node));check(node.get('@id')==ORG,rel+': Organization not using the global ID')
   elif typ=='WebSite':sites.append((rel,node))
   elif typ=='Service':
    services.append((rel,node));languages[code]+=1
    check(source in PAGES,rel+': Service on a non-service page')
    if source not in PAGES:continue
    canonical=t.xpath('//head/link[@rel="canonical"]/@href')
    check(canonical==[node.get('url')],rel+': Service URL differs from Canonical')
    check(node.get('@id')==node.get('url','')+'#service',rel+': Service ID')
    check(node.get('provider')=={'@id':ORG},rel+': Service provider must reference shared Organization')
    label=t.xpath('//nav[@class="breadcrumb-nav"]//li[@aria-current="page"]/span[@class="breadcrumb-label"]')
    name=' '.join(''.join(label[0].itertext()).split()) if label else ''
    check(node.get('name')==name and node.get('serviceType')==name,rel+': localized service name/type differs from actual page')
    key=config[source]['description_id'];desc=catalog[key] if code=='en' else json.loads((DIST/'i18n'/f'{code}.json').read_text())[key]
    check(node.get('description')==desc and bool(desc.strip()),rel+': missing/wrong-language service description')
    descriptions[code].add(node.get('description'))
    check(set(node)=={'@type','@id','name','serviceType','url','description','provider'},rel+': unsupported/unreviewed service fields (prices, ratings, promises or claims)')
    u=urlsplit(node.get('url',''));check(u.scheme=='https' and u.netloc=='chinaattest.com' and not u.query and not u.fragment,rel+': invalid service origin')
full=[(rel,node) for rel,node in orgs if 'logo' in node or 'telephone' in node or 'email' in node]
check(len(full)==1 and full[0][0]=='index.html','Define the full Organization only on the English homepage')
if full:
 node=full[0][1]
 check(node=={'@type':'Organization','@id':ORG,'name':'China Attest','url':ORIGIN+'/','logo':ORIGIN+'/assets/brand-optimized.webp','telephone':'+8615118019493','email':'chinaattest.team@gmail.com'},'Organization fields differ from verified brand/contact information')
 home=html.parse(str(DIST/'index.html'));contact=html.parse(str(DIST/'contact.html'))
 check(home.xpath('//header/a[contains(@class,"brand")]/img/@src')==['assets/brand-optimized.webp'] and (DIST/'assets/brand-optimized.webp').is_file(),'Logo must be the real existing header image')
 check('tel:'+node['telephone'] in home.xpath('//a/@href') and 'mailto:'+node['email'] in contact.xpath('//a/@href'),'Contact information must be present in actual HTML')
check(len(orgs)==29 and {n.get('@id') for _,n in orgs}=={ORG},'All 28 existing Organization occurrences must resolve to one shared company identity')
check(len(sites)==1 and sites[0][0]=='index.html','Exactly one WebSite on the English homepage')
if sites:
 check(sites[0][1]=={'@type':'WebSite','@id':SITE,'name':'China Attest','url':ORIGIN+'/','publisher':{'@id':ORG},'inLanguage':list(LANGS)},'WebSite must use the shared publisher, verified languages and no invented SearchAction')
check(len(services)==21 and languages==Counter({code:3 for code in LANGS}),'Expected 3 Service pages per language / 21 total')
for code in LANGS:check(len(descriptions[code])==3,code+': each actual service must have its own distinct description')
check(blocks==631,'Expected 631 JSON-LD blocks (existing 609 + 22 entity graphs)')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} entity schema failures')
print('PASS: one global Organization identity, 1 English-home Organization definition + 28 existing linked occurrences; verified logo/contact only.')
print('PASS: 1 WebSite, shared Organization publisher, 7 verified languages, no SearchAction.')
print('PASS: 21 Service entities; '+', '.join(code+' '+str(languages[code])+'/3' for code in LANGS)+'; localized names and distinct descriptions.')
print('PASS: all 631 JSON-LD blocks parsed; service URLs match actual Canonicals; no invented prices, ratings, address, dates or credentials.')
