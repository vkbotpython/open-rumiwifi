# SPDX-License-Identifier: GPL-3.0-only
"""Собирает готовые пакеты для Chromium и Firefox в dist/.

Запуск: python tools/build.py

Результат:
  dist/open-rumiwifi-<version>-chromium.zip
  dist/open-rumiwifi-<version>-firefox.zip
  dist/open-rumiwifi-<version>-firefox.xpi
  dist/SHA256SUMS.txt
"""

import hashlib
import json
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, 'extension')
DIST = os.path.join(ROOT, 'dist')
MANIFEST = os.path.join(EXT, 'manifest.json')

ZIP_DATE = (2026, 1, 1, 0, 0, 0)
GECKO_ID = 'open-rumiwifi@avencores'
GECKO_MIN_VERSION = '142.0'


def load_manifest():
    with open(MANIFEST, encoding='utf-8') as handle:
        return json.load(handle)


def collect_files():
    files = []
    for base, dirs, names in os.walk(EXT):
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, EXT).replace(os.sep, '/')
            files.append((rel, path))
    return files


def write_entry(archive, rel, data, executable=False):
    info = zipfile.ZipInfo(rel, date_time=ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o755 if executable else 0o644) << 16
    archive.writestr(info, data)


def build_zip(name, manifest, files):
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, name)
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel, path in files:
            if rel == 'manifest.json':
                write_entry(archive, rel, manifest_bytes)
            else:
                with open(path, 'rb') as handle:
                    write_entry(archive, rel, handle.read())

    with zipfile.ZipFile(out) as archive:
        packed = json.loads(archive.read('manifest.json').decode('utf-8'))
        names = set(archive.namelist())
    for required in ('manifest.json', 'api.js', 'content.js', 'popup.html', 'lang/zh_ru.json'):
        if required not in names:
            raise SystemExit(f'{name}: в пакете нет {required}')

    print(f'{name}: {os.path.getsize(out) / 1024:.1f} КиБ, файлов: {len(names)}')
    return out, packed


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    base = load_manifest()
    version = base['version']
    files = collect_files()

    chromium_manifest = json.loads(json.dumps(base))
    chromium_zip, _ = build_zip(
        f'open-rumiwifi-{version}-chromium.zip', chromium_manifest, files
    )

    firefox_manifest = json.loads(json.dumps(base))
    firefox_manifest['browser_specific_settings'] = {
        'gecko': {
            'id': GECKO_ID,
            'strict_min_version': GECKO_MIN_VERSION,
            'data_collection_permissions': {'required': ['none']},
        }
    }
    # В Firefox MV3 доступ к страницам выдаётся через host_permissions.
    firefox_manifest['host_permissions'] = ['<all_urls>']

    firefox_zip, packed = build_zip(
        f'open-rumiwifi-{version}-firefox.zip', firefox_manifest, files
    )
    firefox_xpi = os.path.join(DIST, f'open-rumiwifi-{version}-firefox.xpi')
    shutil.copyfile(firefox_zip, firefox_xpi)
    print(f'{os.path.basename(firefox_xpi)}: копия firefox.zip для установки')

    if packed.get('browser_specific_settings', {}).get('gecko', {}).get('id') != GECKO_ID:
        raise SystemExit('в firefox-пакете потерялся gecko id')

    sums = []
    for path in (chromium_zip, firefox_zip, firefox_xpi):
        digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        sums.append(f'{digest}  {os.path.basename(path)}')
    sums_path = os.path.join(DIST, 'SHA256SUMS.txt')
    with open(sums_path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write('\n'.join(sums) + '\n')

    print('\nГотово:')
    for line in sums:
        print(' ', line)


if __name__ == '__main__':
    main()
