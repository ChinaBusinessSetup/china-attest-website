#!/usr/bin/env python3
"""Static archive, source coverage, SEO, ordinary links and paging-window checks."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from lxml import html
import json
from build_guides import ROOT,D,cards,config,groups,filename,generated_paths,page_numbers
entries=cards();size=config()['page_size'];manifest=json.loads((D/'guides-manifest.json').read_text());assert manifest['generated']==generated_paths()
source_urls=[e.xpath('./h2/a/@href')[0] for e in entries];assert len(source_urls)==len(set(source_urls))
titles=set();descs=set();main=[]
for category,page,matched in groups():
 name=filename(category,page);t=html.parse(str(D/name));url='https://chinaattest.com/'+name
 got=t.xpath('//article[@class="blog-entry"]');expected=matched[(page-1)*size:page*size]
 assert len(got)==len(expected)<=size,name
 for a,b in zip(got,expected):
  a.xpath('./a[@class="blog-category"]')[0].set('href',b.xpath('./a[@class="blog-category"]')[0].get('href'))
  assert html.tostring(a)==html.tostring(b),name
 assert not t.xpath('//article[@hidden]'),name
 if category=='All Articles':main += [e.xpath('./h2/a/@href')[0] for e in got]
 assert t.xpath('//link[@rel="canonical"]/@href')==[url]
 assert not t.xpath('//meta[@name="robots"][contains(@content,"noindex")]')
 title=t.xpath('//title/text()')[0];desc=t.xpath('//meta[@name="description"]/@content')[0];assert title not in titles and desc not in descs; titles.add(title);descs.add(desc)
 nav=t.xpath('//nav[@class="guides-pagination"]')[0];assert nav.xpath('./span[@aria-current="page"]/text()')==[str(page)]
 total=(len(matched)+size-1)//size
 assert bool(nav.xpath('./a[@rel="prev"]'))==(page>1)
 assert bool(nav.xpath('./a[@rel="next"]'))==(page<total)
 for a in nav.xpath('./a'):
  target=D/a.get('href');assert target.is_file(),str(target)
 assert not nav.xpath('./a[@aria-current] | ./a[contains(@class,"pagination-gap")]')
 if name!='blog.html':assert t.xpath('//link[@hreflang]/@href')==[url,url]
assert main==source_urls,'Missing/duplicated/reordered cards across main pages'
assert not (D/filename('All Articles',len(main)//size+2)).exists(),'Unnecessary archive page'
for total in [1,2,4,10,25]:
 for page in range(1,total+1):
  numbers=page_numbers(page,total);ns=[n for n in numbers if n];assert page in ns and 1 in ns and total in ns;assert ns==sorted(set(ns))
  assert all(1<=n<=total for n in ns)
assert json.loads((D/'guides-data.json').read_text())['pageSize']==size
print(f'PASS: {len(entries)} source articles retained exactly once in main archive, {size}/page, {len(manifest["pages"])} static main/category pages; self Canonicals, unique meta, plain HTML links, boundary/current states, no noindex.')
print('PASS: generated archives have only real English hreflang targets; old seven-language groups remain under existing checks. Window/ellipsis logic verified through25 pages.')
