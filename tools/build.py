#!/usr/bin/env python3
"""Build the personal copies of Butterfly Notes (formerly Mill Notes) from the single source (index.html at the repo root).

  /mill-notes/          -> asks for the name on first open
  /mill-notes/sharoon/  -> opens as Sharoon, no picker
  /mill-notes/naveed/   -> opens as Naveed, no picker

Each copy is its own Home Screen app on iOS (own manifest, own service worker, own offline cache).
Run from the repo root after every change to index.html / sw.js:  python3 tools/build.py
"""
import json, pathlib, shutil
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / 'index.html').read_text()
assert '<meta name="mn-user" content="">' in src, 'mn-user meta tag missing from index.html'
for name in ['Sharoon', 'Naveed']:
    d = root / name.lower(); d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(src.replace('<meta name="mn-user" content="">', f'<meta name="mn-user" content="{name}">'))
    shutil.copy(root / 'sw.js', d / 'sw.js')
    for icon in ['icon-180.png', 'icon-512.png', 'icon-512-maskable.png']:
        shutil.copy(root / icon, d / icon)
    m = json.loads((root / 'manifest.webmanifest').read_text())
    m['name'] = f'Butterfly Notes · {name}'; m['id'] = f'./?u={name.lower()}'
    (d / 'manifest.webmanifest').write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
    print('built', d.relative_to(root))
