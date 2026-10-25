"""Распаковка CRX3 от RUMIWIFI: original/rumiwifi.crx -> original/extracted/.

Запуск: node original/download.js && python original/unpack.py
Файлы RUMIWIFI не публикуются в репозитории (см. .gitignore) — они нужны
только для локального анализа.
"""

import io
import os
import struct
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'rumiwifi.crx')
OUTDIR = os.path.join(HERE, 'extracted')

data = open(SRC, 'rb').read()
assert data[:4] == b'Cr24', data[:4]
version = struct.unpack('<I', data[4:8])[0]
print('crx version', version)

if version == 3:
    header_len = struct.unpack('<I', data[8:12])[0]
    print('header len', header_len)
    zip_offset = 12 + header_len
elif version == 2:
    pubkey_len, sig_len = struct.unpack('<II', data[8:16])
    zip_offset = 16 + pubkey_len + sig_len
else:
    raise SystemExit('unknown CRX version')

print('zip offset', zip_offset, 'zip magic', data[zip_offset:zip_offset + 4])
os.makedirs(OUTDIR, exist_ok=True)
archive = zipfile.ZipFile(io.BytesIO(data[zip_offset:]))
archive.extractall(OUTDIR)

names = archive.namelist()
print('files', len(names))
for name in names:
    print(' ', name)
print('\nГотово. Не коммитьте папку original/extracted — она в .gitignore.')
