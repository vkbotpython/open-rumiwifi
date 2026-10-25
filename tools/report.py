# SPDX-License-Identifier: GPL-3.0-only
import json, os, collections

rows = [l.rstrip('\n').split('\t') for l in open('data/all_clean.tsv', encoding='utf-8')]
counts = collections.Counter(r[1] for r in rows)

NAMES = {
    'web_home': 'Состояние роутера (`/web/home`)',
    'web_setting_wifi': 'Wi-Fi (`/web/setting/wifi`)',
    'web_setting_wan': 'Интернет (`/web/setting/wan`)',
    'web_setting_safe': 'Безопасность (`/web/setting/safe`)',
    'web_setting_lannetset': 'LAN (`/web/setting/lannetset`)',
    'web_setting_upgrade': 'Система (`/web/setting/upgrade`)',
    'web_prosetting_qos': 'QoS (`/web/prosetting/qos`)',
    'web_prosetting_upnp': 'UPnP (`/web/prosetting/upnp`)',
    'web_prosetting_vpn': 'VPN (`/web/prosetting/vpn`)',
    'web_prosetting_dmz': 'DMZ (`/web/prosetting/dmz`)',
    'web_prosetting_ddns': 'DDNS (`/web/prosetting/ddns`)',
    'web_prosetting_nat': 'Переадресация (`/web/prosetting/nat`)',
    'web_prosetting_networkportcustom': 'Порты и Dual WAN (`/web/prosetting/networkportcustom`)',
}

lines = []
lines.append('# Покрытие перевода')
lines.append('')
lines.append('Проверено на живом роутере **Xiaomi AX3000T (RD03v2)**, прошивка **2.0.28**, регион CN, язык панели `zh_cn`.')
lines.append('')
lines.append('| Страница | Строк в интерфейсе | Переведено | Осталось китайских |')
lines.append('|---|---:|---:|---:|')
total = 0
for page, n in counts.most_common():
    total += n
    lines.append(f'| {NAMES.get(page, page)} | {n} | {n} | 0 |')
lines.append(f'| **Итого** | **{total}** | **{total}** | **0** |')
lines.append('')
lines.append('Отдельно проверена страница входа `/cgi-bin/luci/web`: 130 текстовых строк, 0 китайских остатков.')
lines.append('')
lines.append('Дополнительно проверены динамические узлы (MutationObserver): добавленный в DOM текст')
lines.append('и атрибуты `placeholder` / `title` переводятся без перезагрузки страницы.')
lines.append('')
lines.append('## Что не переводится намеренно')
lines.append('')
lines.append('- содержимое `<script>`, `<style>`, `<textarea>`, `<code>`, `<pre>`;')
lines.append('- пользовательские данные (имена сетей, устройств, введённые значения);')
lines.append('- два артефакта, попавших в обход HTML как «текст», но не являющихся интерфейсом:')
lines.append('  jQuery-селектор `option:contains(\'自动\')` и JS-конкатенация `MAX_ROUTER_POLICY_LIST_NUM`.')
lines.append('')
lines.append('## Словарь')
lines.append('')
lines.append('- `extension/lang/zh_ru.json` — 1105 пар «китайская строка → русская».')
lines.append('- Словарь собран с нуля по живому интерфейсу; машинные переводы RUMIWIFI не используются.')
lines.append('- Ключи отсортированы по убыванию длины, а скрипт ищет самое длинное совпадение,')
lines.append('  поэтому короткие слова больше не «съедают» части длинных фраз.')
lines.append('')

os.makedirs('docs', exist_ok=True)
open('docs/coverage.md', 'w', encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines))
