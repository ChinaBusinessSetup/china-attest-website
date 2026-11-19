#!/usr/bin/env python3
"""Read-only validation of source allowlist and deployed discovery files."""
from pathlib import Path
from urllib.parse import urlsplit,unquote,urljoin
from urllib.robotparser import RobotFileParser
from collections import Counter
from lxml import html
import xml.etree.ElementTree as ET
import re
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
ORIGIN='https://chinaattest.com';NS='http://www.sitemaps.org/schemas/sitemap/0.9'
errors=[]
def check(condition,message):
 if not condition:errors.append(message)
def parse_urls(path):
 tree=ET.parse(path).getroot()
 check(tree.tag=='{'+NS+'}urlset',str(path)+': expected sitemap urlset')
 check(all(n.tag in ('{'+NS+'}urlset','{'+NS+'}url','{'+NS+'}loc') for n in tree.iter()),str(path)+': unexpected XML extension (no XML hreflang required)')
 urls=[]
 for node in tree:
  loc=node.findall('{'+NS+'}loc')
  check(len(loc)==1 and bool(loc[0].text),str(path)+': entry requires one loc')
  if loc and loc[0].text:urls.append(loc[0].text.strip())
 check(len(urls)==len(set(urls)),str(path)+': duplicate URLs')
 return urls
try:
 source=parse_urls(ROOT/'sitemap.xml');published=parse_urls(DIST/'sitemap.xml')
except (OSError,ET.ParseError) as e:raise SystemExit('FAIL: missing or invalid sitemap XML: '+str(e))
counts=Counter();excluded=[];expected=[];resources=set()
for url in source:
 u=urlsplit(url)
 valid=u.scheme=='https' and u.netloc=='chinaattest.com' and u.path.startswith('/') and not u.query and not u.fragment
 check(valid,'Source has non-production URL: '+url)
 if not valid:continue
 path=unquote(u.path.lstrip('/'))
 if not path or path.endswith('/'):path+='index.html'
 if '..' in Path(path).parts or '\\' in path:errors.append('Invalid source path: '+url);continue
 p=DIST/path
 check(p.is_file(),'Missing target '+url)
 if not p.is_file():continue
 t=html.parse(str(p));reasons=[]
 if t.xpath('//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'):reasons.append('Meta Refresh')
 for meta in t.xpath('//meta[@name]'):
  name=meta.get('name','').lower();tokens=re.split(r'[\s,;]+',meta.get('content','').lower())
  if (name=='robots' or 'bot' in name or name in ('slurp','baiduspider')) and {'noindex','none'}.intersection(tokens):reasons.append(name+' noindex')
 if reasons:
  excluded.append((url,reasons));check(url not in published,'Excluded URL published '+url);continue
 check(t.xpath('//head/link[@rel="canonical"]/@href')==[url],'Canonical mismatch '+url)
 expected.append(url);counts[t.getroot().get('lang')]+=1
 for value in t.xpath('//link[@rel="stylesheet"]/@href | //script/@src | //img/@src'):
  target=urljoin(url,value)
  if urlsplit(target).netloc=='chinaattest.com':resources.add(target)
check(published==expected,'Published sitemap does not equal eligible source URLs in source order')
for url in published:
 u=urlsplit(url)
 check(u.scheme=='https' and u.netloc=='chinaattest.com' and not u.query and not u.fragment,'Published URL is not production HTTPS canonical '+url)
check(set(counts)=={'en','es','fr','de','pt','ru','ar'},'Eligible sitemap must cover all seven current languages')
expected_robots='User-agent: *\nAllow: /\n\nSitemap: '+ORIGIN+'/sitemap.xml\n'
try:
 source_robots=(ROOT/'robots.txt').read_text();published_robots=(DIST/'robots.txt').read_text()
 check(source_robots==expected_robots,'Unexpected source robots rules: review before changing')
 check(published_robots==source_robots,'Published robots differs from source')
 robot=RobotFileParser();robot.parse(published_robots.splitlines())
 check(robot.site_maps()==[ORIGIN+'/sitemap.xml'],'Robots sitemap discovery URL')
 for agent in ('Googlebot','Googlebot-Image','Bingbot','*'):
  for url in expected+sorted(resources):check(robot.can_fetch(agent,url),f'Robots blocks {agent}: {url}')
except OSError as e:errors.append('Missing robots: '+str(e))
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} discovery failures')
print(f'PASS: dist/sitemap.xml XML parsed; {len(published)} canonical URLs; 0 duplicates, invalid URLs, redirect or noindex entries.')
print('PASS: sitemap languages '+', '.join(code+' '+str(counts[code]) for code in ('en','es','fr','de','pt','ru','ar')))
print(f'PASS: robots source equals dist; normal pages and {len(resources)} referenced resource URLs crawlable; {len(excluded)} source exclusions.')
for url,reasons in excluded:print('EXCLUDED:',url,', '.join(reasons))
