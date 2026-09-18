# Engine tests

Pure-Node harnesses that extract the shipped JavaScript out of the **built**
`index.html` and exercise it — no browser, no network, no dependencies.

```bash
python scraper.py          # build index.html first
node tests/engine.test.mjs     # 35 unit tests: parsing, camelCase, unicode, caps
node tests/jsonp.test.mjs      # JSONP transport: failover, timeout, leak checks
node tests/edgecases.test.mjs  # hostile keywords: CJK, emoji, all-stopword, 120 chars
```

`engine.test.mjs` exits non-zero on failure, so it can gate CI.
