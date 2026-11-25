from pathlib import Path
from lxml import html
from urllib.parse import urljoin,urlsplit,unquote
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';PAGE='police-certificate-format.html';URL='https://chinaattest.com/'+PAGE;t=html.parse(str(D/PAGE));source=html.parse(str(ROOT/'scripts/certificate-samples-source.html'))
TITLE='China Police Certificate Samples & Notarization Guide | China Attest';H1='China Police Certificate Samples: What the Certificate and Notarial Document Look Like';DESC='See real samples of China police clearance certificates, notarial certificates, and apostilles. Understand document formats for US, Canada, UK, Australia and more.'
assert t.xpath('//title/text()')==[TITLE] and t.xpath('//meta[@name="description"]/@content')==[DESC]
assert t.xpath('//h1/text()')==[H1] and t.xpath('//link[@rel="canonical"]/@href')==[URL]
assert t.xpath('//meta[@name="robots"]/@content')==['index,follow'] and len(t.xpath('//link[@hreflang]'))==8
body=t.xpath('//section[contains(concat(" ",@class," ")," certificate-samples ")]')[0]
assert html.tostring(body)==html.tostring(source.xpath('//section[contains(concat(" ",@class," ")," certificate-samples ")]')[0])
ids=['overview','police-vs-notarial','police-sample','notarial-samples','apostille','important-things','faq','official-sources'];assert [e.get('id') for e in body.xpath('./section[@id]')]==ids
assert body.xpath('./nav//ol/li/a/@href')==['#'+i for i in ids]
assert len(t.xpath('//*[@id="faq"]/h3'))==10 and not t.xpath('//*[@id="faq"]//*[@hidden]')
manifest=json.loads((ROOT/'scripts/samples-image-manifest.json').read_text());imgs=body.xpath('.//img');assert len(imgs)==len(manifest)==5
for e,m in zip(imgs,manifest):
 assert e.get('src')==m['file'] and e.get('alt')==m['alt'] and e.get('width')==str(m['width']) and e.get('height')==str(m['height']) and e.get('loading')=='lazy'
 assert hashlib.sha256((D/m['file']).read_bytes()).hexdigest()==m['sha256'];assert e.xpath('ancestor::figure/figcaption')
for a in body.xpath('.//a[@href]'):
 u=urlsplit(urljoin(URL,a.get('href')))
 if u.netloc!='chinaattest.com':continue
 p=D/unquote(u.path).lstrip('/');p=p/'index.html' if p.is_dir() else p;assert p.is_file(),a.get('href')
 if u.fragment:assert html.parse(str(p)).xpath('//*[@id=$id]',id=u.fragment)
articles=[json.loads(s) for s in t.xpath('//script[@type="application/ld+json"]/text()') if json.loads(s).get('@type')=='Article'];assert len(articles)==1
v=articles[0];assert v['url']==URL and v['mainEntityOfPage']['@id']==URL and v['author']['name']=='China Attest Editorial Team' and v['publisher']['@id']=='https://chinaattest.com/#organization' and v['dateModified']=='2026-11-25'
bread=[json.loads(s) for s in t.xpath('//script[@type="application/ld+json"]/text()') if json.loads(s).get('@type')=='BreadcrumbList'][0];assert [x['name'] for x in bread['itemListElement']]==['Home','Guides','China Police Certificate Samples']
g=html.parse(str(ROOT/'scripts/guides-source.html'));card=g.xpath('//article[@data-category="China Police Certificates"]');assert len(card)==1 and card[0].xpath('./h2/a/@href')==[PAGE]
assert not html.parse(str(D/'how-to-police-certificate.html')).xpath('//*[@id="residence-cities"]/a[@href=$p]',p=PAGE)
assert len(g.xpath('//article[@class="blog-entry"]'))==19
locs=[e.text for e in ET.parse(D/'sitemap.xml').getroot().iter() if e.tag.endswith('}loc')];assert locs.count(URL)==1
text=' '.join(body.itertext());assert 'May 28, 2026' in text and 'not a statement that IRCC requires every applicant' in text and 'last two pages' in text and 'three-month validity wording' in text
print('PASS: samples19th card, one existing URL,8 sections,10 visible FAQs,8 TOC anchors,5 sample images with complete user-supplied notarial and Apostille examples/alt/captions/dimensions/lazy loading; article SEO/author/modified/breadcrumb/Sitemap/indexability and real internal targets.')

assert len(t.xpath('//img[contains(@src,"australia-uk-nz-complete.png")]'))==1
assert not t.xpath('//img[contains(@src,"australia-uk-nz-page-")]')

assert len(t.xpath('//img[contains(@src,"canada-complete.png")]'))==1
assert not t.xpath('//img[contains(@src,"canada-page-")]')

assert len(t.xpath('//img[contains(@src,"us-complete.png")]'))==1
assert not t.xpath('//img[contains(@src,"us-page-")]')

assert len(t.xpath('//img[contains(@src,"apostille-france-complete.png")]'))==1
assert not t.xpath('//img[contains(@src,"apostille-france-page-")]')

assert len(t.xpath('//img[contains(@src,"police-certificate-complete.png")]'))==1
assert not t.xpath('//img[contains(@src,"police-page-1.png")]')
