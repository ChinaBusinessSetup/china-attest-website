# Website languages

English remains at the original URLs. Static editions are built under `/es/`, `/fr/`, `/de/`, `/pt/` `/ru/` and `/ar/`. Language links retain the current page. Navigation works with JavaScript disabled; there is no translation provider or API dependency.

`locale-source.json` is the stable numbered source catalogue; `dist/i18n/{language}.json` holds all translations. After English copy changes, add any new strings with new IDs to the catalogue and all six dictionaries. Do not renumber existing entries. The build fails on unmapped source strings.

Run `python3 scripts/build-locales.py` (build-time dependency: lxml), then `python3 scripts/check-locales.py`. Generated HTML is checked in for buildless hosting. Rebuild rather than editing translated HTML directly.

Customer reviews, list pages and detail pages follow the selected language. Names and photos are preserved. Fictional/example labels were removed following the owner’s confirmation that these are real cases; no independent verification claim is added.

Form action, field names, option values and mail configuration are preserved. Only visible labels/placeholders and status messages are translated. Shared scripts use the small generated `*-ui.js` dictionaries; full translation files are build inputs, not runtime dependencies.

No official public domain has been confirmed. The generator avoids English canonicals and unconfirmed URL assertions on translated pages. Configure canonical/hreflang/sitemap URLs against the confirmed production origin when preparing public multilingual SEO. Do not remove private hosting access restrictions to do so.

Arabic uses Modern Standard Arabic with `lang="ar" dir="ltr"`, matching the English page layout as requested. The edition-only `arabic.css` provides legible Arabic typography without mirroring columns, navigation, alignment or controls. Contact details and organization names use bidi isolation. Review pages use the same LTR page layout.

Generated page links and shared asset references use relative paths, including explicit index.html links for language homepages, so extracted pages also support direct file opening. Language icon SVG includes explicit fill/stroke attributes. For form submission use an HTTP preview or the hosted website.
