# SPDX-License-Identifier: GPL-3.0-only
import urllib.request, urllib.parse, http.cookiejar, hashlib, os, re, sys, json, time

BASE = 'http://192.168.31.1'
PWD = os.environ.get('RUMIWIFI_PASSWORD', '')
PAGES = 'router/pages'
JSDIR = 'router/js'
os.makedirs(PAGES, exist_ok=True)
os.makedirs(JSDIR, exist_ok=True)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36')]

BLOCK = re.compile(r'/(logout|login|syslock|reboot|shutdown|restore|reset|set_|del_|add_|remove|upload|download)', re.I)


def get(path):
    url = path if path.startswith('http') else BASE + path
    try:
        r = opener.open(url, timeout=25)
        return r.status, r.geturl(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, url, e.read()
    except Exception as e:
        return 0, url, str(e).encode()


def login():
    if not PWD:
        raise SystemExit('Задайте пароль роутера в переменной окружения RUMIWIFI_PASSWORD')
    _, _, raw = get('/cgi-bin/luci/web')
    page = raw.decode('utf-8', 'replace')
    key = re.search(r"key:\s*'([0-9a-f]{32})'", page).group(1)
    dev = re.search(r"deviceId\s*=\s*'([0-9a-f:]{17})'", page).group(1)
    nonce = '_'.join(['0', dev, str(int(time.time())), str(int.from_bytes(os.urandom(2), 'big') % 10000)])
    pwd = hashlib.sha256((nonce + hashlib.sha256((PWD + key).encode()).hexdigest()).encode()).hexdigest()
    data = urllib.parse.urlencode({'username': 'admin', 'password': pwd, 'logtype': '2', 'nonce': nonce}).encode()
    req = urllib.request.Request(BASE + '/cgi-bin/luci/api/xqsystem/login', data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                          'Referer': BASE + '/cgi-bin/luci/web'})
    j = json.loads(opener.open(req, timeout=25).read().decode())
    if j.get('code') != 0:
        raise SystemExit('login failed: %s' % j)
    return j['token']


def norm(route):
    route = route.split('#')[0].split('?')[0]
    route = re.sub(r'/cgi-bin/luci/;stok=[0-9a-f]+', '', route)
    if not route.startswith('/web/'):
        return None
    if BLOCK.search(route):
        return None
    return route


def discover(html):
    out = set()
    for m in re.finditer(r'(?:href|action)="([^"]+)"', html):
        r = norm(m.group(1))
        if r:
            out.add(r)
    for m in re.finditer(r'["\'](?:/cgi-bin/luci/;stok=[0-9a-f]+)?(/web/[a-z0-9_/]+)["\']', html):
        r = norm(m.group(1))
        if r:
            out.add(r)
    return out


SEEDS = '''/web/home /web/setting/wan /web/setting/wifi /web/setting/lannetset /web/setting/upgrade
/web/setting/safe /web/prosetting/qos /web/prosetting/upnp /web/prosetting/vpn /web/prosetting/dmz
/web/prosetting/ddns /web/prosetting/nat /web/prosetting/networkportcustom'''.split()

if __name__ == '__main__':
    token = login()
    print('token', token)
    seen, queue, js = set(), list(SEEDS), set()
    results = []
    while queue and len(seen) < 80:
        route = queue.pop(0)
        if route in seen:
            continue
        seen.add(route)
        st, final, raw = get(f'/cgi-bin/luci/;stok={token}{route}')
        html = raw.decode('utf-8', 'replace')
        cjk = sum(1 for c in html if '\u4e00' <= c <= '\u9fff')
        results.append({'route': route, 'status': st, 'bytes': len(raw), 'cjk': cjk})
        print(f'{st} {len(raw):>7} cjk={cjk:>6} {route}')
        if st == 200 and ';stok=' in final:
            open(os.path.join(PAGES, route.strip('/').replace('/', '_') + '.html'), 'w', encoding='utf-8').write(html)
            for r in discover(html):
                if r not in seen:
                    queue.append(r)
            for m in re.finditer(r'<script[^>]*src="([^"]+\.js[^"]*)"', html):
                src = m.group(1).split('?')[0]
                if src.startswith('/'):
                    js.add(src)
    for src in sorted(js):
        st, final, raw = get(src)
        name = src.strip('/').replace('/', '_')
        if st == 200:
            open(os.path.join(JSDIR, name), 'wb').write(raw)
        print('JS', st, len(raw), src)
    json.dump(results, open('router/crawl.json', 'w'), ensure_ascii=False, indent=1)
