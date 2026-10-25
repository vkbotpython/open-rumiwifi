import json, re, glob, os, sys
sys.path.insert(0, 'tools')
from analyze import extract_html, extract_js, clean, CJK

ARTIFACT = re.compile(r'[<>{}]|function\s*\(|var\s+\w|document\.|window\.|/cgi-bin|stok=|\\u[0-9a-f]{4}|https?://|\.css|\.js|!--')

data = {}
for f in sorted(glob.glob('router/pages/*.html')):
    page = os.path.basename(f)[:-5]
    for s in extract_html(open(f, encoding='utf-8', errors='replace').read()):
        data.setdefault(s, set()).add(page)

clean_strings = {}
for s, pages in data.items():
    if ARTIFACT.search(s):
        continue
    if len(s) < 2:
        continue
    if len(CJK.findall(s)) == 0:
        continue
    clean_strings[s] = sorted(pages)

json.dump(clean_strings, open('data/panel_strings.json', 'w'), ensure_ascii=False, indent=1)
print('clean strings', len(clean_strings), 'of', len(data))

lens = sorted((len(s), s) for s in clean_strings)
print('shortest:')
for n, s in lens[:15]:
    print(' ', n, s)
print('longest:')
for n, s in lens[-10:]:
    print(' ', n, s[:120])
