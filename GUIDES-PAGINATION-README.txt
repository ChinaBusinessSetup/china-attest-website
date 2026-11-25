Guides static pagination — V69

Build: python3 scripts/build-locales.py
Verify: python3 scripts/check-locales.py
Python build dependency: lxml (same as the existing build).

Edit article cards only in scripts/guides-source.html, preserving their existing HTML order.
This is the single source of the 19 cards. Do not hand-edit emitted blog*.html or guides-data.json.
Every article retains its existing individual URL and body.
Page size has one source: scripts/guides-pagination.json (page_size=9).
The original build invokes build_guides.prepare(), existing language build, then build_guides.build().
The builder restores the complete source for the language build, preserves frozen translations, then emits English static archives and a derived search index.
Only previously managed generated archive files are removed before each build, so reducing article counts removes stale pagination files.

Primary archives:
/blog.html
/blog-page-2.html
/blog-page-3.html

Categories:
/blog-city-guides.html
/blog-city-guides-page-2.html
/blog-police-clearance.html
/blog-apostille.html
/blog-china-police-certificates.html

Main and category lists, article cards and pagination links are present in returned HTML and work without JavaScript.
Arbitrary keyword search retains the existing JavaScript requirement. It uses the build-derived index, not just the cards on the current page.
Search uses q and page query parameters (for example blog-city-guides.html?q=police&page=2), preserves category and supports direct access/refresh.
Normal static pages use self Canonicals. Search variants consolidate to their category's first archive URL.
Original blog.html hreflang remains untouched. Additional English-only archives use en and x-default self references, and the language menu opens the existing translated Guides centres.
No translated archive pages or article translations were created.
Sitemap and Robots files/rules remain unchanged. New archives are crawlable via ordinary HTML links from blog.html and category links.
There is no SPA fallback or catch-all route; nonexistent pagination files use the hosting platform's ordinary404 handling.

Assets: guides-pagination.css and guides-pagination.js are new source assets in the project's existing dist asset directory.
app.js has only a guard to leave the new static English archives to the new pagination script; all other original behaviour stays unchanged.
No publication/deployment was performed.
