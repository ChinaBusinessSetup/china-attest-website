"""Generate only BreadcrumbList from final static, localized breadcrumb HTML.
Existing schema blocks are never edited here. Generated blocks are removed
before translation on the next build and re-derived from the translated DOM.
"""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit,unquote
from lxml import html,etree
import copy,json
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com'
REFRESH='//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'

def is_breadcrumb(value):
 if isinstance(value,list):return any(is_breadcrumb(x) for x in value)
 if not isinstance(value,dict):return False
 typ=value.get('@type',[])
 if typ=='BreadcrumbList' or isinstance(typ,list) and 'BreadcrumbList' in typ:return True
 return any(is_breadcrumb(x) for x in value.values())

def visible_name(node):
 node=copy.deepcopy(node)
 for hidden in node.xpath('.//*[@aria-hidden="true"]'):hidden.drop_tree()
 return ' '.join(''.join(node.itertext()).split())

def item_url(href,page,lang):
 absolute=urljoin(ORIGIN+'/'+page.relative_to(DIST).as_posix(),href)
 u=urlsplit(absolute)
 if u.scheme!='https' or u.netloc!='chinaattest.com' or u.query:
  raise ValueError('Breadcrumb ancestor must use the production origin: '+absolute)
 path=unquote(u.path).lstrip('/')
 if '..' in Path(path).parts or '\\' in path:raise ValueError('Invalid breadcrumb path: '+absolute)
 if not path or path.endswith('/'):path+='index.html'
 target=DIST/path
 if not target.is_file():raise ValueError('Missing breadcrumb ancestor: '+absolute)
 t=html.parse(str(target))
 if t.getroot().get('lang')!=lang or t.xpath(REFRESH):raise ValueError('Breadcrumb ancestor has wrong language or redirects: '+absolute)
 normalized=u.path[:-10] if u.path.endswith('/index.html') else u.path
 expected=urlunsplit(('https','chinaattest.com',normalized,'',''))
 if t.xpath('//head/link[@rel="canonical"]/@href')!=[expected]:raise ValueError('Breadcrumb ancestor disagrees with Canonical: '+absolute)
 if u.fragment and not t.xpath('//*[@id=$value or @name=$value]',value=unquote(u.fragment)):raise ValueError('Missing breadcrumb anchor: '+absolute)
 return urlunsplit(('https','chinaattest.com',normalized,'',u.fragment))

def add_breadcrumb_schema(t,page):
 if t.xpath(REFRESH):return
 for script in list(t.xpath('//script[@data-breadcrumb-schema]')):script.getparent().remove(script)
 for script in t.xpath('//script[@type="application/ld+json"]'):
  if is_breadcrumb(json.loads(script.text)):raise ValueError('Existing unowned BreadcrumbList requires review; refusing a duplicate: '+str(page))
 nav=t.xpath('//main//nav[contains(concat(" ",normalize-space(@class)," ")," breadcrumb-nav ")]')
 if not nav:return
 if len(nav)!=1:raise ValueError('Expected one visible breadcrumb: '+str(page))
 items=nav[0].xpath('./ol[@class="breadcrumbs"]/li')
 if len(items)<2:raise ValueError('BreadcrumbList needs at least two items: '+str(page))
 result=[]
 for position,item in enumerate(items,1):
  name=visible_name(item)
  if not name:raise ValueError('Empty breadcrumb name: '+str(page))
  entry={'@type':'ListItem','position':position,'name':name}
  if position==len(items):
   if item.get('aria-current')!='page' or item.xpath('.//a'):raise ValueError('Final breadcrumb must be the unlinked current page: '+str(page))
  else:
   links=item.xpath('./a[@href]')
   if len(links)!=1:raise ValueError('Ancestor needs one actual HTML link: '+str(page))
   entry['item']=item_url(links[0].get('href'),page,t.get('lang'))
  result.append(entry)
 data={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':result}
 text=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
 etree.SubElement(t.find('head'),'script',{'type':'application/ld+json','data-breadcrumb-schema':'v69'}).text=text
