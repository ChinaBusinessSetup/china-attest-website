"""Build discovery files from the original sitemap allowlist and source robots.txt.
No page scanning expands the allowlist. Noindex/refresh entries are excluded and
reported; missing files, invalid origins and non-canonical URLs fail the build.
"""
from pathlib import Path
from urllib.parse import urlsplit,unquote
from lxml import html
import xml.etree.ElementTree as ET
import re
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com'
NS='http://www.sitemaps.org/schemas/sitemap/0.9'
REFRESH='//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'

def source_urls():
 root=ET.parse(ROOT/'sitemap.xml').getroot()
 if root.tag!='{'+NS+'}urlset':raise ValueError('Source sitemap must be a namespaced urlset')
 urls=[]
 for node in root:
  loc=node.findall('{'+NS+'}loc')
  if node.tag!='{'+NS+'}url' or len(loc)!=1 or not loc[0].text:
   raise ValueError('Each source sitemap entry must contain one non-empty loc')
  urls.append(loc[0].text.strip())
 if len(urls)!=len(set(urls)):raise ValueError('Duplicate URLs in source sitemap')
 return urls

def target_file(url):
 u=urlsplit(url)
 if u.scheme!='https' or u.netloc!='chinaattest.com' or u.query or u.fragment or not u.path.startswith('/'):
  raise ValueError('Not a production canonical URL: '+url)
 path=unquote(u.path).lstrip('/')
 if '..' in Path(path).parts or '\\' in path:raise ValueError('Invalid sitemap path: '+url)
 if not path or path.endswith('/'):path+='index.html'
 p=DIST/path
 if not p.is_file():raise ValueError('Missing sitemap target: '+url)
 return p

def noindex_reasons(t):
 reasons=[]
 for e in t.xpath('//meta[@name]'):
  name=e.get('name','').lower()
  if name=='robots' or 'bot' in name or name in ('slurp','baiduspider'):
   directives=re.split(r'[\s,;]+',e.get('content','').lower())
   if 'noindex' in directives or 'none' in directives:reasons.append(name+'='+e.get('content',''))
 return reasons

def eligible_urls():
 included=[];excluded=[]
 for url in source_urls():
  p=target_file(url);t=html.parse(str(p));reasons=[]
  if t.xpath(REFRESH):reasons.append('Meta Refresh redirect')
  reasons+=noindex_reasons(t)
  if reasons:excluded.append((url,reasons));continue
  if t.xpath('//head/link[@rel="canonical"]/@href')!=[url]:
   raise ValueError('Sitemap URL differs from page Canonical: '+url)
  included.append(url)
 return included,excluded

def robots_source():
 data=(ROOT/'robots.txt').read_text(encoding='utf-8')
 expected='User-agent: *\nAllow: /\n\nSitemap: '+ORIGIN+'/sitemap.xml\n'
 if data!=expected:
  raise ValueError('Source robots rules changed; review crawl impact before building')
 return data

def build_discovery_files():
 urls,excluded=eligible_urls()
 robots=robots_source()
 ET.register_namespace('',NS)
 root=ET.Element('{'+NS+'}urlset')
 for url in urls:
  node=ET.SubElement(root,'{'+NS+'}url')
  ET.SubElement(node,'{'+NS+'}loc').text=url
 ET.indent(root,space='  ')
 ET.ElementTree(root).write(DIST/'sitemap.xml',encoding='utf-8',xml_declaration=True)
 (DIST/'robots.txt').write_text(robots,encoding='utf-8')
 for url,reasons in excluded:print('SITEMAP EXCLUDED:',url,'; '.join(reasons))
 print(f'Discovery: {len(urls)} sitemap URLs; {len(excluded)} exclusions; dist/sitemap.xml and dist/robots.txt generated.')

if __name__=='__main__':build_discovery_files()
