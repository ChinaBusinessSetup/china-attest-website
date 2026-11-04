#!/usr/bin/env python3
"""Finish domain-dependent SEO after the owner confirms the production HTTPS origin.
Usage: python3 scripts/configure-apostille-production-seo.py --origin https://OWNER-CONFIRMED-DOMAIN
Does not modify robots.txt, access controls, other articles or redirect policy.
"""
import argparse,json,re
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

def apply(origin):
 parsed=urlsplit(origin)
 if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
     or parsed.port or parsed.path not in ('','/') or parsed.query or parsed.fragment
     or '.' not in parsed.hostname or parsed.hostname in ('localhost','127.0.0.1')
     or parsed.hostname.endswith(('.chatgpt.site','.local','.test','.example','.invalid','.localhost'))):
  raise ValueError('Use the owner-confirmed production HTTPS origin, not a preview, test or localhost URL.')
 origin='https://'+parsed.netloc.lower();root=Path(__file__).resolve().parents[1];p=root/'dist/apostille-in-china/index.html';s=p.read_text();url=origin+'/apostille-in-china/'
 match=re.search(r'<script type="application/ld\+json">(.*?)</script>',s,re.S);data=json.loads(match[1]);article=next(x for x in data.get('@graph',[data]) if x.get('@type')=='Article')
 article={k:v for k,v in article.items() if k!='@context'};article['@id']=url+'#article';article['url']=url;article['mainEntityOfPage']={'@type':'WebPage','@id':url}
 article['author']['url']=origin+'/about.html';article['publisher']['url']=origin+'/'
 crumbs={'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':origin+'/'},{'@type':'ListItem','position':2,'name':'Guides','item':origin+'/blog.html'},{'@type':'ListItem','position':3,'name':article['headline'],'item':url}]}
 graph={'@context':'https://schema.org','@graph':[article,crumbs]}
 s=s[:match.start()]+'<script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False)+'</script>'+s[match.end():]
 s=re.sub(r'<link rel="canonical"[^>]*>','',s);s=re.sub(r'<meta property="og:url"[^>]*>','',s)
 s=s.replace('</head>',f'<link rel="canonical" href="{url}"><meta property="og:url" content="{url}"></head>');p.write_text(s)
 # A dedicated valid sitemap covers only this requested article; it does not overwrite the site's sitemap.
 ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9');ns='{http://www.sitemaps.org/schemas/sitemap/0.9}';tree=ET.Element(ns+'urlset');node=ET.SubElement(tree,ns+'url');ET.SubElement(node,ns+'loc').text=url
 ET.ElementTree(tree).write(root/'dist/sitemap-apostille.xml',encoding='utf-8',xml_declaration=True)
 print('Configured canonical, og:url, Article, BreadcrumbList and sitemap-apostille.xml for '+url)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--origin',required=True);apply(parser.parse_args().origin)
