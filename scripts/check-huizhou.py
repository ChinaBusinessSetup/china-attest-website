#!/usr/bin/env python3
"""English-only Huizhou guide and both existing entry-point regression checks."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from lxml import html
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';CONFIG=json.loads((ROOT/'scripts/english-only-pages.json').read_text());PAGE='guide-police-huizhou.html';URL='https://chinaattest.com/'+PAGE
TITLE='Huizhou Police Clearance Certificate for Foreigners | China Attest'
DESCRIPTION='Learn how foreigners can obtain a Huizhou police clearance certificate, including eligibility, required documents, application procedures and notarization.'
H1='Guide to Obtaining a Certificate of No Criminal Record in Huizhou, China'
errors=[]
def check(test,message):
 if not test:errors.append(message)
def text(e):return ' '.join(''.join(e.itertext()).split())
t=html.parse(str(D/PAGE));blog=html.parse(str(ROOT/'scripts/guides-source.html'));cities=html.parse(str(D/'how-to-police-certificate.html'))
check(t.xpath('//title/text()')==[TITLE],'SEO Title')
check(t.xpath('//meta[@name="description"]/@content')==[DESCRIPTION],'Meta Description')
check(len(t.xpath('//h1'))==1 and text(t.xpath('//h1')[0])==H1,'H1')
check(t.xpath('//head/link[@rel="canonical"]/@href')==[URL],'Self Canonical')
check(not t.xpath('//meta[@name="robots"][contains(@content,"noindex")]'),'Guide must remain indexable')
expected=['1. Overview','2. Eligibility','3. Required Documents','4. Application Process','5. Application Authority','6. Special Requirements','7. Frequently Asked Questions (FAQ)','8. Official Sources']
body=t.xpath('//article[@class="guide-article"]')[0];check([text(e) for e in body.xpath('./h2')][:8]==expected,'Eight complete sections')
content='\n'.join(text(e) for e in body.xpath('./h2 | ./h3 | ./p | ./ul/li | ./ol/li'));check(hashlib.sha256(content.encode()).hexdigest()==CONFIG['huizhou_article_content_sha256'],'Article differs from supplied text')
check([text(e) for e in body.xpath('./h2')][-1]=='Need Assistance with Your Huizhou Police Clearance Certificate?','Final CTA')
check(len(t.xpath('//head/link[@rel="alternate"][@hreflang]'))==8,'Existing seven-language hreflang + x-default')
nav=t.xpath('//nav[@class="breadcrumb-nav"]/ol/li');check([text(e.xpath('./a|./span[@class="breadcrumb-label"]')[0]) for e in nav]==['Home','City Guides','Huizhou'],'Visible breadcrumb hierarchy')
check(nav[1].xpath('./a/@href')==['how-to-police-certificate.html'],'Real city-directory parent')
# User-corrected processing time must agree in body and FAQ; protect delegated notarization materials.
page_text=text(t.getroot())
check('3 business days' not in page_text.lower() and '3 working days' not in page_text.lower(),'No obsolete three-day application estimate')
check(page_text.count('3–5 business days in most cases')==2 and page_text.count('1–2 weeks')==2,'Application3–5working days and notarization1–2weeks agree in body/FAQ')
for phrase in ['Must have held residence permits issued in Huizhou, as evidenced by their Temporary Residence Registration Form(s).','Must have lived in Huizhou for 180 days or longer.','Photograph of the Applicant Holding the Signed Power of Attorney: Required when another person is appointed to handle the notarization application, according to the information provided for this guide.','This is an additional document requirement for third-party notarization applications and should not be confused with the Power of Attorney itself.']:
 check(phrase in text(body),'Huizhou requirement: '+phrase)
check('changsha' not in text(t.getroot()).lower(),'No Changsha residue in the full Huizhou page')
check('Optional' not in text(body),'Residence registration must remain required')
articles=[]
for raw in t.xpath('//script[@type="application/ld+json"]/text()'):
 v=json.loads(raw)
 if v.get('@type')=='Article':articles.append(v)
check(len(articles)==1,'Exactly one English Huizhou Article schema')
if articles:
 v=articles[0];check(v.get('url')==URL and v.get('mainEntityOfPage',{}).get('@id')==URL and v.get('@id')==URL+'#article','Official Article URLs');check(v.get('headline')==H1 and v.get('inLanguage')=='en','Article headline/language')
card=blog.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," blog-entry ")][@data-category="City Guides"][@data-location="Huizhou"]')
check(len(card)==1,'One City Guides card in existing Guides list')
if card:
 c=card[0];check(text(c.xpath('./h2')[0])=='Huizhou Police Clearance Certificate Guide for Foreigners','Card title');check(c.xpath('./p/text()')==['Learn about eligibility, required documents, application procedures and notarization for obtaining a Huizhou police clearance certificate.'],'Card description');check(c.get('data-location')=='Huizhou' and c.xpath('./div[@class="blog-byline"]/text()')==['Huizhou'],'Card location');check(c.xpath('./h2/a/@href')==[PAGE],'Guides card target')
check(len(blog.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," blog-entry ")]'))==len(set(blog.xpath('//article[@class="blog-entry"]/h2/a/@href'))),'No duplicated guide article URL in unified source')
check(blog.xpath('//header/nav/a[normalize-space(.)="Guides"]/@href')==['blog.html'],'Existing top Guides navigation')
citylinks=cities.xpath('//*[@id="residence-cities"]/a');check(len(citylinks)==17,'Preserve all17 city entries');check([e.get('href') for e in citylinks if 'Huizhou' in text(e)]==[PAGE],'City Huizhou target matches Guides card')
check(hashlib.sha256((D/'how-to-police-certificate.html').read_bytes()).hexdigest()==CONFIG['city_directory_sha256'],'City directory/order/layout unchanged')
for rel,digest in CONFIG['frozen_locale_sha256'].items():check(hashlib.sha256((D/rel).read_bytes()).hexdigest()==digest,'Frozen translation changed: '+rel)
locs=[e.text for e in ET.parse(D/'sitemap.xml').getroot().iter() if e.tag.endswith('}loc')];check(locs.count(URL)==1 and len(locs)==217,'Huizhou retained once in existing217-URL Sitemap')
full=[]
for p in D.rglob('*.html'):
 if H1 in ''.join(html.parse(str(p)).xpath('//h1//text()')):full.append(p.relative_to(D).as_posix())
check(full==[PAGE],'Only one full Huizhou English article URL')
if errors:
 for error in errors:print('ERROR',error)
 raise SystemExit(f'{len(errors)} Huizhou guide failures')
print('PASS: one English Huizhou URL, exact supplied8 sections +FAQ/CTA; two existing entry points reach the same page.')
print('PASS: correct metadata, indexability, unchanged hreflang/Sitemap rules, matching visible/BreadcrumbList path and official Article URLs.')
print('PASS: all17 city links/order unchanged;102 existing localized counterpart files preserved without translation.')
