# SPDX-License-Identifier: GPL-3.0-only
import json, re, sys, html as htmllib
sys.path.insert(0, 'tools')
from simulate import Trie, apply

CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
WS = re.compile(r'[ \t]+')

lang = json.load(open('build/lang/zh_ru.json', encoding='utf-8'))
trie = Trie(lang)


def text_of(path):
    h = open(path, encoding='utf-8', errors='replace').read()
    h = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', ' ', h, flags=re.S | re.I)
    out = []
    for chunk in h.split('<'):
        i = chunk.find('>')
        if i != -1:
            chunk = chunk[i + 1:]
        v = htmllib.unescape(chunk).replace('\u00a0', ' ')
        v = WS.sub(' ', v).strip()
        if v:
            out.append(apply(v, trie))
    return out


if __name__ == '__main__':
    for line in text_of(sys.argv[1]):
        if line.strip():
            print(line)
