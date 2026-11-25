/* Static archives work without JavaScript. Search enhances these same archives using the generated card index. */
(()=>{'use strict';if(!document.documentElement.hasAttribute('data-static-guides'))return;
const root=document.documentElement,search=document.querySelector('#blog-search'),form=document.querySelector('.guides-search'),category=root.dataset.guidesCategory,params=new URLSearchParams(location.search);let dataPromise,currentQuery=params.get('q')||'',timer;
search.value=currentQuery;
function data(){return dataPromise||(dataPromise=fetch('guides-data.json').then(r=>{if(!r.ok)throw Error('Search index unavailable');return r.json()}))}
function path(d,page){return d.categories[category]+(page===1?'':'-page-'+page)+'.html'}
function href(d,page,q){const base=path(d,1),s=new URLSearchParams();if(q)s.set('q',q);if(page>1)s.set('page',page);return base+(s.size?'?'+s:'')}
function numbers(page,total){if(total<=5)return Array.from({length:total},(_,i)=>i+1);let keep=new Set([1,total,page-1,page,page+1]);if(page===1){keep.add(2);keep.add(3)}let out=[];for(const n of [...keep].filter(n=>n>=1&&n<=total).sort((a,b)=>a-b)){if(out.length&&n-out[out.length-1]>1)out.push(null);out.push(n)}return out}
async function render(query,page,changeURL){const d=await data();if(query!==currentQuery)return;query=query.trim();const matched=d.articles.filter(a=>(category==='All Articles'||a.category===category)&&a.search.toLowerCase().includes(query.toLowerCase()));const total=Math.max(1,Math.ceil(matched.length/d.pageSize));page=Math.max(1,Math.min(page,total));
if(changeURL)history.replaceState(null,'',href(d,page,query));
document.querySelector('link[rel=canonical]').href='https://chinaattest.com/'+path(d,1);document.title=query?'Search Guides | China Attest':d.meta[category].title;document.querySelector('meta[name=description]').content=d.meta[category].description;
const list=document.querySelector('.blog-list');list.innerHTML=matched.slice((page-1)*d.pageSize,page*d.pageSize).map(a=>a.html).join('');
document.querySelector('#blog-count').textContent=matched.length+' '+(matched.length===1?'article':'articles');document.querySelector('#blog-empty').hidden=matched.length>0;
const nav=document.querySelector('.guides-pagination');nav.replaceChildren();function item(text,n,attrs={}){const e=document.createElement(n?'a':'span');e.textContent=text;Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(n)e.href=href(d,n,query);nav.append(e)}
item('← Previous',page>1?page-1:0,page>1?{rel:'prev'}:{class:'disabled','aria-disabled':'true'});for(const n of numbers(page,total)){if(n===null)item('…',0,{'aria-hidden':'true',class:'pagination-gap'});else item(String(n),n===page?0:n,n===page?{'aria-current':'page','aria-label':'Page '+n}:{'aria-label':'Page '+n})}item('Next →',page<total?page+1:0,page<total?{rel:'next'}:{class:'disabled','aria-disabled':'true'});
for(const a of document.querySelectorAll('[data-filter]')){a.href=d.categories[a.dataset.filter]+'.html'+(query?'?'+new URLSearchParams({q:query}):'')}
}
function run(page=1,changeURL=true){currentQuery=search.value;render(currentQuery,page,changeURL).catch(()=>{document.querySelector('#blog-count').textContent='Search unavailable. Please reload or browse the article pages below.'})}
search.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>run(),180)});form.addEventListener('submit',e=>{e.preventDefault();clearTimeout(timer);run()});
if(currentQuery)run(Number(params.get('page'))||1,false);
})();
