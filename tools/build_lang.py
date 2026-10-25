# SPDX-License-Identifier: GPL-3.0-only
"""Собирает extension/lang/zh_ru.json из исходников в data/ru/.

Словарь полностью собственный: старый словарь RUMIWIFI не используется,
поэтому проект не тащит за собой чужие файлы и машинные переводы.
"""

import json
import glob
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from tools.simulate import Trie, apply

PANEL = json.load(open('data/panel_strings.json', encoding='utf-8'))
LOGIN_PAGE = 'router/pages/web_login.html'

IGNORE = {
    "错误：策略数量最大值为'+ MAX_ROUTER_POLICY_LIST_NUM +'",
    "option:contains('自动')",
    "不支持手机端网页管理路由器4",
}

translations = {}
for path in sorted(glob.glob('data/ru/*.json')):
    if os.path.basename(path) == 'tz_tokens.json':
        continue
    translations.update(json.load(open(path, encoding='utf-8')))

# Универсальные ключи для динамических строк, которые панель собирает в JS.
translations.update({
    '系统版本:': 'Версия системы:',
    '稳定版 MAC地址:': 'стабильная сборка, MAC-адрес:',
    '(家)': '(Дом)',
    '台': ' ',
})

for key in IGNORE:
    translations.pop(key, None)

# Никаких данных конкретного роутера в словаре.
for key in list(translations):
    if re.search(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}', key) or key == 'No name (家)':
        translations.pop(key)

items = sorted(translations.items(), key=lambda kv: (-len(kv[0]), kv[0]))
for target in ('build/lang/zh_ru.json', 'extension/lang/zh_ru.json'):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w', encoding='utf-8') as f:
        json.dump(dict(items), f, ensure_ascii=False, indent=1)
print('dictionary:', len(translations), 'strings')

CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]+')
trie = Trie(translations)


def check(strings, label):
    bad = []
    for s in strings:
        if s in IGNORE:
            continue
        ru = apply(s, trie)
        if CJK.search(ru):
            bad.append((s, ru))
    print(f'{label}: {len(strings)} strings, leftover CJK: {len(bad)}')
    for s, ru in bad[:20]:
        print('  BAD', s[:80], '=>', ru[:100])
    return bad


bad_panel = check(list(PANEL), 'panel')
sys.path.insert(0, 'tools')
from analyze import extract_html  # noqa: E402

login_html = open(LOGIN_PAGE, encoding='utf-8', errors='replace').read()
login_strings = [s for s in extract_html(login_html) if not re.search(r'[<>]', s)]
bad_login = check(login_strings, 'login')

if bad_panel or bad_login:
    raise SystemExit(1)
