# SPDX-License-Identifier: GPL-3.0-only
"""Проверки репозитория перед публикацией и в CI.

Запуск: python tools/verify.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Пароль, который использовался при съёмке панели. Собираем из частей,
# чтобы сам скрипт не содержал его целиком.
SECRET = 'OKA' + '12332145' + 'OKA'

errors = []
warnings = []


def fail(message):
    errors.append(message)


def warn(message):
    warnings.append(message)


def read_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


# --- manifest и ссылки на файлы -------------------------------------------

manifest = read_json('extension/manifest.json')
for version_key in ('manifest_version', 'name', 'version', 'description'):
    if version_key not in manifest:
        fail(f'manifest.json: нет поля {version_key}')

referenced = set()
referenced.update(manifest.get('icons', {}).values())
for script in manifest.get('content_scripts', []):
    referenced.update(script.get('js', []))
    referenced.update(script.get('css', []))
action = manifest.get('action', {})
for key in ('default_popup', 'default_icon'):
    if action.get(key):
        referenced.add(action[key])

for path in sorted(referenced):
    if not os.path.isfile(os.path.join('extension', path)):
        fail(f'manifest.json ссылается на отсутствующий файл: {path}')

if len(manifest.get('name', '')) > 75:
    fail('manifest.json: имя длиннее 75 символов')
if len(manifest.get('description', '')) > 132:
    warn('manifest.json: описание длиннее 132 символов — Chrome может обрезать')

# --- словарь --------------------------------------------------------------

lang_path = 'extension/lang/zh_ru.json'
lang = read_json(lang_path)
CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')

if len(lang) < 500:
    fail(f'словарь подозрительно маленький: {len(lang)} строк')

for key, value in lang.items():
    if not key or not value:
        fail(f'пустой ключ или значение: {key!r}')
    if CJK.search(value):
        fail(f'китайские символы в переводе: {key!r} -> {value!r}')

lengths = [len(key) for key in lang]
if lengths != sorted(lengths, reverse=True):
    fail('словарь не отсортирован по убыванию длины ключей — запустите tools/build_lang.py')

if os.path.isfile('build/lang/zh_ru.json'):
    built = read_json('build/lang/zh_ru.json')
    if built != lang:
        fail('extension/lang/zh_ru.json устарел: запустите python tools/build_lang.py и закоммитьте результат')

# --- исходники перевода ---------------------------------------------------

sources = 0
for name in sorted(os.listdir('data/ru')):
    if not name.endswith('.json') or name == 'tz_tokens.json':
        continue
    data = read_json(os.path.join('data/ru', name))
    sources += len(data)
    if not data:
        warn(f'пустой файл перевода: data/ru/{name}')
if sources < 500:
    fail(f'в data/ru слишком мало строк: {sources}')

# --- снимки панели --------------------------------------------------------

TOKEN = re.compile(r';stok=(?!0{32})[0-9a-f]{32}')
MAC = re.compile(r'(?<!A)\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b')

pages_dir = 'router/pages'
if not os.path.isdir(pages_dir):
    fail('нет папки router/pages с тестовыми страницами')
else:
    pages = [p for p in os.listdir(pages_dir) if p.endswith('.html')]
    if len(pages) < 10:
        fail(f'мало тестовых страниц: {len(pages)}')
    for name in pages:
        text = open(os.path.join(pages_dir, name), encoding='utf-8', errors='replace').read()
        if TOKEN.search(text):
            fail(f'{name}: остался живой session-токен')
        if SECRET in text:
            fail(f'{name}: найден пароль роутера')
        for match in MAC.finditer(text):
            if not match.group(0).upper().startswith('AA:BB:CC:DD:EE:FF'):
                fail(f'{name}: MAC-адрес устройства не обезличен: {match.group(0)}')

# --- поиск секретов в текстовых файлах ------------------------------------

SKIP_DIRS = {'.git', 'node_modules', '.npm-cache', '__pycache__', 'build', 'extracted'}
TEXT_EXT = {'.py', '.js', '.json', '.md', '.html', '.css', '.yml', '.yaml', '.txt', '.ps1'}
for base, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        if os.path.splitext(name)[1].lower() not in TEXT_EXT:
            continue
        path = os.path.join(base, name)
        if os.path.getsize(path) > 5 * 1024 * 1024:
            fail(f'слишком большой текстовый файл: {path}')
            continue
        try:
            text = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        if SECRET in text:
            fail(f'{path}: найден пароль роутера')

# --- README: относительные ссылки ----------------------------------------

if os.path.isfile('README.md'):
    readme = open('README.md', encoding='utf-8').read()
    for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', readme):
        target = target.split('#')[0].strip()
        if not target or target.startswith(('http://', 'https://', 'mailto:')):
            continue
        if not os.path.exists(target):
            fail(f'README.md: битая ссылка «{label}» -> {target}')
else:
    fail('нет README.md')

# --- обязательные файлы ---------------------------------------------------

for path in ('LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
             'NOTICE.md', 'docs/coverage.md', 'docs/PUBLISHING.md'):
    if not os.path.isfile(path):
        fail(f'нет обязательного файла: {path}')

if os.path.isfile('LICENSE'):
    license_text = open('LICENSE', encoding='utf-8').read()
    if 'GNU GENERAL PUBLIC LICENSE' not in license_text or 'Version 3' not in license_text:
        fail('LICENSE не содержит текст GNU GPL v3.0')

if os.path.isdir('original/extracted') or os.path.isfile('original/rumiwifi.crx'):
    warn('в папке original/ лежат файлы RUMIWIFI — они не должны попасть в git (см. .gitignore)')

# --- итог ----------------------------------------------------------------

print(f'Строк в словаре: {len(lang)}')
print(f'Строк в исходниках: {sources}')
print(f'Тестовых страниц: {len(pages) if os.path.isdir(pages_dir) else 0}')

for message in warnings:
    print(f'[warn] {message}')
for message in errors:
    print(f'[error] {message}')

if errors:
    sys.exit(f'\nПроверка не пройдена: {len(errors)} ошибок')
print('\nВсе проверки пройдены.')
