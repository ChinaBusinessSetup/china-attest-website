"""English static Guides archives, derived from one checked-in HTML card source."""
from pathlib import Path
from lxml import html,etree
import json,math,copy
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';S=ROOT/'scripts';ORIGIN='https://chinaattest.com/'
CATEGORIES={'All Articles':'blog','City Guides':'blog-city-guides','Police Clearance':'blog-police-clearance','Apostille':'blog-apostille','China Police Certificates':'blog-china-police-certificates'}
def config():
 c=json.loads((S/'guides-pagination.json').read_text());assert isinstance(c['page_size'],int) and c['page_size']>0;return c

def source():return html.fromstring((S/'guides-source.html').read_bytes())
def cards():return source().xpath('//article[@class="blog-entry"]')
def filename(category,page):return CATEGORIES[category]+('' if page==1 else '-page-'+str(page))+'.html'
def groups():
 entries=cards();size=config()['page_size']
 return [(category,page,[e for e in entries if category=='All Articles' or e.get('data-category')==category]) for category in CATEGORIES for page in range(1,max(1,math.ceil(sum(category=='All Articles' or e.get('data-category')==category for e in entries)/size))+1)]
def generated_paths():return [filename(c,p) for c,p,_ in groups() if filename(c,p)!='blog.html']
def prepare():
 # Remove only files previously emitted by this builder, allowing article count reductions.
 manifest=D/'guides-manifest.json'
 if manifest.exists():
  for rel in json.loads(manifest.read_text())['generated']:
   assert rel.startswith('blog-') and rel.endswith('.html') and '/' not in rel
   (D/rel).unlink(missing_ok=True)
 (D/'police-certificate-format.html').write_bytes((S/'certificate-samples-source.html').read_bytes())
 (D/'blog.html').write_bytes((S/'guides-source.html').read_bytes())
def page_numbers(page,total):
 if total<=5:return list(range(1,total+1))
 keep=sorted({1,total,*range(max(1,page-1),min(total,page+1)+1),*(range(1,4) if page==1 else [] )})
 result=[]
 for n in keep:
  if result and isinstance(result[-1],int) and n-result[-1]>1:result.append(None)
  result.append(n)
 return result

def navigation(category,page,total):
 nav=etree.Element('nav',{'class':'guides-pagination','aria-label':'Guides pagination'})
 if page>1:etree.SubElement(nav,'a',{'href':filename(category,page-1),'rel':'prev'}).text='← Previous'
 else:etree.SubElement(nav,'span',{'class':'disabled','aria-disabled':'true'}).text='← Previous'
 for n in page_numbers(page,total):
  if n is None:etree.SubElement(nav,'span',{'class':'pagination-gap','aria-hidden':'true'}).text='…'
  elif n==page:etree.SubElement(nav,'span',{'aria-current':'page','aria-label':f'Page {n}'}).text=str(n)
  else:etree.SubElement(nav,'a',{'href':filename(category,n),'aria-label':f'Page {n}'}).text=str(n)
 if page<total:etree.SubElement(nav,'a',{'href':filename(category,page+1),'rel':'next'}).text='Next →'
 else:etree.SubElement(nav,'span',{'class':'disabled','aria-disabled':'true'}).text='Next →'
 return nav

def build():
 size=config()['page_size'];entries=cards();template=source();generated=[];stats=[];meta={}
 assert len({e.xpath('./h2/a/@href')[0] for e in entries})==len(entries),'Duplicate article URLs in source'
 for category,page,matched in groups():
  t=copy.deepcopy(template);name=filename(category,page);total=max(1,math.ceil(len(matched)/size));t.set('data-static-guides','true');t.set('data-guides-category',category);t.set('data-guides-page',str(page))
  listing=t.xpath('//div[@class="blog-list"]')[0]
  for child in list(listing):listing.remove(child)
  listing.text=None
  for card in matched[(page-1)*size:page*size]:listing.append(copy.deepcopy(card))
  # Retain the original result count and empty-state nodes outside the card list.
  t.xpath('//*[@id="blog-count"]')[0].text=str(len(matched))+' articles'
  old=t.xpath('//*[@class="blog-pagination"]')[0];old.getparent().replace(old,navigation(category,page,total))
  for a in t.xpath('//*[@data-filter]'):
   cat=a.get('data-filter');dest=filename(cat,1)
   if a.tag=='button':
    a.tag='a';a.attrib.pop('type',None);a.attrib.pop('aria-pressed',None);a.set('class','guide-filter');a.set('href',dest)
    if cat==category:a.set('aria-current','true')
   else:a.set('href',dest)
  search=t.xpath('//*[@id="blog-search"]')[0];search.set('name','q')
  form=etree.Element('form',{'method':'get','action':filename(category,1),'class':'guides-search'});parent=search.getparent();parent.replace(search,form);form.append(search)
  for script in t.xpath('//script[contains(@src,"app.js")]'):script.set('src','app.js?v=v69-guides-pagination')
  head=t.find('head');etree.SubElement(head,'link',{'rel':'stylesheet','href':'guides-pagination.css?v=v69-pagination-3'});etree.SubElement(t.find('body'),'script',{'src':'guides-pagination.js?v=v69-pagination-3','defer':'defer'})
  if name!='blog.html':
   label=('Guides' if category=='All Articles' else category if category.endswith('Guides') else category+' Guides')+f' — Page {page}'
   t.xpath('//title')[0].text=label+' | China Attest'
   t.xpath('//meta[@name="description"]')[0].set('content',f'Browse page {page} of '+('China Attest guides' if category=='All Articles' else category.lower()+' guides')+' for foreign nationals, including police clearance, notarization and overseas document preparation.')
   t.xpath('//link[@rel="canonical"]')[0].set('href',ORIGIN+name)
   for e in t.xpath('//link[@hreflang]'):e.getparent().remove(e)
   for lang in ['en','x-default']:etree.SubElement(head,'link',{'rel':'alternate','hreflang':lang,'href':ORIGIN+name})
   # Language menu intentionally links to existing translated Guides centres, not nonexistent page translations.
   ol=t.xpath('//nav[@class="breadcrumb-nav"]/ol')[0]
   for child in list(ol):ol.remove(child)
   ol.append(html.fragment_fromstring('<li><a href="index.html">Home</a></li>'))
   ol.append(html.fragment_fromstring('<li><span class="breadcrumb-separator" aria-hidden="true">/</span><a href="blog.html">Guides</a></li>'))
   li=etree.SubElement(ol,'li',{'aria-current':'page'});etree.SubElement(li,'span',{'class':'breadcrumb-separator','aria-hidden':'true'}).text='/';etree.SubElement(li,'span',{'class':'breadcrumb-label'}).text=label
   for e in t.xpath('//script[@data-breadcrumb-schema]'):e.getparent().remove(e)
   from breadcrumb_schema import add_breadcrumb_schema
   add_breadcrumb_schema(t,D/name)
   generated.append(name)
  if page==1:meta[category]={'title':t.xpath('//title')[0].text,'description':t.xpath('//meta[@name="description"]')[0].get('content')}
  (D/name).write_bytes(html.tostring(t,encoding='utf-8',doctype='<!DOCTYPE html>'))
  stats.append({'category':category,'page':page,'file':name,'count':len(matched[(page-1)*size:page*size]),'total':len(matched)})
 data={'pageSize':size,'meta':meta,'categories':CATEGORIES,'articles':[{'html':html.tostring(e,encoding='unicode'),'category':e.get('data-category'),'search':e.get('data-search'),'url':e.xpath('./h2/a/@href')[0]} for e in entries]}
 (D/'guides-data.json').write_text(json.dumps(data,ensure_ascii=False)+'\n')
 (D/'guides-manifest.json').write_text(json.dumps({'generated':generated,'pages':stats},indent=2)+'\n')
 print(f'Guides: {len(entries)} original articles; {size}/page; {math.ceil(len(entries)/size)} main archive pages; {len(stats)} archive pages including categories.')
if __name__=='__main__':prepare();build()
