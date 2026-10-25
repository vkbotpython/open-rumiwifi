import json, re, sys

CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]+')


class Trie:
    def __init__(self, mapping):
        self.root = {}
        self.first = set()
        for k, v in mapping.items():
            if not k:
                continue
            self.first.add(k[0])
            node = self.root
            for ch in k:
                node = node.setdefault(ch, {})
            node['$'] = (k, v)

    def longest(self, s, i):
        node = self.root
        n = len(s)
        j = i
        best = None
        while j < n:
            node = node.get(s[j])
            if node is None:
                break
            j += 1
            if '$' in node:
                best = (node['$'], j)
        return best


def apply(s, trie):
    out = []
    i, n = 0, len(s)
    while i < n:
        if s[i] in trie.first:
            hit = trie.longest(s, i)
        else:
            hit = None
        if hit:
            (k, v), j = hit
            out.append(v)
            i = j
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def main():
    lang = json.load(open('original/extracted/lang/zh_ru.json', encoding='utf-8'))
    cov = json.load(open('router/coverage.json', encoding='utf-8'))
    strings = cov['all_strings']
    trie = Trie(lang)
    residual = []
    fully = 0
    for s in strings:
        ru = apply(s, trie)
        left = CJK.findall(ru)
        if left:
            residual.append({'zh': s, 'ru': ru, 'left': left})
        else:
            fully += 1
    print(f'total={len(strings)} fully_covered={fully} residual={len(residual)}')
    # group residual fragments
    from collections import Counter
    c = Counter()
    for r in residual:
        for frag in r['left']:
            c[frag] += 1
    print('unique leftover fragments:', len(c))
    for frag, n in c.most_common(60):
        print(f'{n:>4}  {frag[:100]}')
    json.dump(residual, open('router/residual.json', 'w'), ensure_ascii=False, indent=1)
