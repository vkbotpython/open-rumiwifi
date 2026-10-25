# SPDX-License-Identifier: GPL-3.0-only
import urllib.request, urllib.parse, http.cookiejar, hashlib, os, sys, json, time

BASE = 'http://192.168.31.1'
PWD = os.environ.get('RUMIWIFI_PASSWORD', '')
OUT = 'router/pages'
os.makedirs(OUT, exist_ok=True)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36')]


def get(path, allow_redirect=True):
    url = path if path.startswith('http') else BASE + path
    try:
        r = opener.open(url, timeout=25)
        return r.status, r.geturl(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, url, e.read()


def login():
    if not PWD:
        raise SystemExit('Задайте пароль роутера в переменной окружения RUMIWIFI_PASSWORD')
    st, _, raw = get('/cgi-bin/luci/web')
    page = raw.decode('utf-8', 'replace')
    import re
    key = re.search(r"key:\s*'([0-9a-f]{32})'", page).group(1)
    dev = re.search(r"deviceId\s*=\s*'([0-9a-f:]{17})'", page).group(1)
    nonce = '_'.join(['0', dev, str(int(time.time())), str(int.from_bytes(os.urandom(2), 'big') % 10000)])
    pwd = hashlib.sha256((nonce + hashlib.sha256((PWD + key).encode()).hexdigest()).encode()).hexdigest()
    data = urllib.parse.urlencode({'username': 'admin', 'password': pwd, 'logtype': '2', 'nonce': nonce}).encode()
    req = urllib.request.Request(BASE + '/cgi-bin/luci/api/xqsystem/login', data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                          'Referer': BASE + '/cgi-bin/luci/web'})
    r = opener.open(req, timeout=25)
    j = json.loads(r.read().decode())
    print('login code', j.get('code'), 'url', j.get('url'))
    return j['token']


ROUTES = '''
/web/home
/web/setting/wan
/web/setting/wifi
/web/setting/lannetset
/web/setting/upgrade
/web/setting/security
/web/setting/firewall
/web/setting/qos
/web/setting/upnp
/web/setting/dhcp
/web/setting/staticdhcp
/web/setting/portforward
/web/setting/dmz
/web/setting/ddns
/web/setting/vpn
/web/setting/ipv6
/web/setting/led
/web/setting/nfc
/web/setting/mesh
/web/setting/wifi_guest
/web/setting/guest
/web/setting/ports
/web/setting/lan
/web/setting/wifiadvanced
/web/setting/wifi_adv
/web/setting/timeset
/web/setting/ntp
/web/setting/diagnose
/web/setting/tools
/web/setting/log
/web/setting/status
/web/setting/sysstatus
/web/setting/device
/web/setting/devices
/web/setting/blacklist
/web/setting/whitelist
/web/setting/access
/web/setting/parental
/web/setting/macfilter
/web/setting/ipfilter
/web/setting/urlfilter
/web/setting/network
/web/setting/netmode
/web/setting/wifiset
/web/setting/wifilist
/web/prosetting/qos
/web/prosetting/upnp
/web/prosetting/vpn
/web/prosetting/dhcp
/web/prosetting/portforward
/web/prosetting/dmz
/web/prosetting/ddns
/web/prosetting/staticdhcp
/web/prosetting/firewall
/web/prosetting/security
/web/prosetting/ipv6
/web/prosetting/mesh
/web/setting/wan6
/web/setting/ipv6_set
/web/setting/reboot
/web/setting/shutdown
'''.split()

if __name__ == '__main__':
    token = login()
    rows = []
    for route in ROUTES:
        if route.endswith(('reboot', 'shutdown')):
            continue
        path = f'/cgi-bin/luci/;stok={token}' + route
        st, final, raw = get(path)
        txt = raw.decode('utf-8', 'replace')
        cjk = sum(1 for c in txt if '\u4e00' <= c <= '\u9fff')
        name = route.strip('/').replace('/', '_')
        if st == 200 and 'stok=' in final:
            open(os.path.join(OUT, name + '.html'), 'w', encoding='utf-8').write(txt)
        rows.append((route, st, len(raw), cjk, final.replace(BASE, '')))
        print(f'{st} {len(raw):>7} cjk={cjk:>6}  {route}')
    json.dump(rows, open('router/route_status.json', 'w'), ensure_ascii=False, indent=1)
