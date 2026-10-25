import re, json, sys, os, glob, html as htmllib, time

CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
WS = re.compile(r'\s+')
SCRIPT_BLOCK = re.compile(r'<script\b([^>]*)>(.*?)</script\s*>', re.S | re.I)
ATTR = re.compile(r'\b(placeholder|title|alt|reqmsg|data-tip|data-title|value)="([^"]{0,400})"', re.I)


def clean(s):
    s = htmllib.unescape(s)
    s = s.replace('\u00a0', ' ')
    return WS.sub(' ', s).strip()


def extract_js(text):
    out = set()
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in '"\'':
            q, j, buf = c, i + 1, []
            while j < n:
                ch = text[j]
                if ch == '\\':
                    buf.append(text[j:j+2]); j += 2; continue
                if ch == q:
                    break
                buf.append(ch); j += 1
            if j - i < 800:
                v = ''.join(buf).replace('\\n', ' ').replace('\\/', '/')
                if CJK.search(v):
                    v = clean(v)
                    if CJK.search(v):
                        out.add(v)
            i = j + 1
        else:
            i += 1
    return out


def extract_fragment(text):
    out = set()
    for m in ATTR.finditer(text):
        v = clean(m.group(2))
        if CJK.search(v):
            out.add(v)
    for chunk in text.split('<'):
        idx = chunk.find('>')
        if idx != -1:
            chunk = chunk[idx+1:]
        v = clean(chunk)
        if CJK.search(v) and len(v) > 1:
            out.add(v)
    return out


def extract_html(text):
    out = set()
    pos = 0
    for m in SCRIPT_BLOCK.finditer(text):
        out |= extract_fragment(text[pos:m.start()])
        attrs = m.group(1).lower()
        content = m.group(2)
        if 'tmpl' in attrs or 'html' in attrs:
            out |= extract_html(content)
        else:
            out |= extract_js(content)
        pos = m.end()
    out |= extract_fragment(text[pos:])
    return out


def collect(paths):
    strings = set()
    for f in paths:
        raw = open(f, encoding='utf-8', errors='replace').read()
        strings |= extract_js(raw) if f.endswith('.js') else extract_html(raw)
    return strings


class Matcher:
    def __init__(self, keys):
        self.trie = {}
        self.first = set()
        for k in keys:
            self.first.add(k[0])
            node = self.trie
            for ch in k:
                node = node.setdefault(ch, {})
            node['$'] = k

    def longest(self, s):
        best = None
        n = len(s)
        trie = self.trie
        first = self.first
        for i in range(n):
            if s[i] not in first:
                continue
            node = trie
            j = i
            while j < n and s[j] in node:
                node = node[s[j]]
                j += 1
                if '$' in node and (best is None or len(node['$']) > len(best)):
                    best = node['$']
        return best


def main():
    t0 = time.time()
    pages = sorted(glob.glob('router/pages/*.html'))
    js = sorted(glob.glob('router/js/*.js'))
    lang = json.load(open('original/extracted/lang/zh_ru.json', encoding='utf-8'))

    page_strings = collect(pages)
    print('pages parsed', round(time.time() - t0, 2), len(page_strings))
    js_strings = collect(js)
    print('js parsed', round(time.time() - t0, 2), len(js_strings))
    all_strings = page_strings | js_strings

    m = Matcher(lang.keys())
    missing, partial, exact = [], [], []
    for s in sorted(all_strings):
        k = m.longest(s)
        if k is None:
            missing.append(s)
        elif k == s:
            exact.append(s)
        else:
            partial.append((s, k))
    print('matched', round(time.time() - t0, 2))

    report = {
        'pages': len(pages), 'js': len(js),
        'strings_total': len(all_strings), 'page_strings': len(page_strings),
        'js_strings': len(js_strings),
        'keys_total': len(lang),
        'exact': len(exact), 'partial': len(partial), 'missing': len(missing),
        'missing_strings': missing,
        'partial_pairs': partial,
        'all_strings': sorted(all_strings),
    }
    json.dump(report, open('router/coverage.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
    print('\n--- missing (first 50) ---')
    for s in missing[:50]:
        print(s[:160])
