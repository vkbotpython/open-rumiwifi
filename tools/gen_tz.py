import json, re

rows = [l.rstrip('\n').split('\t') for l in open('data/all_clean.tsv', encoding='utf-8')]
tz = [r[2] for r in rows if r[1] == 'web_setting_upgrade' and r[2].startswith('(')]
tok = json.load(open('data/ru/tz_tokens.json', encoding='utf-8'))

out, missing = {}, set()
for s in tz:
    m = re.match(r'^\((UTC[^)]*)\)(.*)$', s)
    if not m:
        print('NO MATCH', s)
        continue
    prefix, rest = m.group(1), m.group(2)
    parts = [p.strip() for p in re.split(r'[，,]', rest) if p.strip()]
    vals = []
    for p in parts:
        if p not in tok:
            missing.add(p)
            vals.append(p)
        else:
            vals.append(tok[p])
    out[s] = f'({prefix}) ' + ', '.join(vals)

print('strings', len(out), 'missing tokens', len(missing))
for t in sorted(missing):
    print('MISSING', t)
json.dump(out, open('data/ru/timezones.json', 'w'), ensure_ascii=False, indent=1)
