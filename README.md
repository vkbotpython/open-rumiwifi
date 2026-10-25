<div align="center">
    <a href="https://www.youtube.com/@avencores/" target="_blank">
      <img src="https://github.com/user-attachments/assets/338bcd74-e3c3-4700-87ab-7985058bd17e" alt="YouTube" height="40">
    </a>
    <a href="https://t.me/avencoresyt" target="_blank">
      <img src="https://github.com/user-attachments/assets/939f8beb-a49a-48cf-89b9-d610ee5c4b26" alt="Telegram" height="40">
    </a>
    <a href="https://vk.ru/avencoresreuploads" target="_blank">
      <img src="https://github.com/user-attachments/assets/dc109dda-9045-4a06-95a5-3399f0e21dc4" alt="VK" height="40">
    </a>
    <a href="https://dzen.ru/avencores" target="_blank">
      <img src="https://github.com/user-attachments/assets/bd55f5cf-963c-4eb8-9029-7b80c8c11411" alt="Dzen" height="40">
    </a>
</div>

# 📶 Open RUMIWIFI

<img src="extension/img/icon.png" width="88" align="right" alt="Open RUMIWIFI">

Русская локализация веб-панели Xiaomi / Redmi роутеров (MiWiFi) для **Chromium**
и **Firefox**. Словарь собран заново по живому интерфейсу прошивки **2.0.28**,
а не унаследован от старого расширения RUMIWIFI.

![Manifest V3](https://img.shields.io/badge/manifest-v3-2f7cf6)
![Chromium](https://img.shields.io/badge/chromium-chrome%20%7C%20edge-4285F4)
![Firefox 142+](https://img.shields.io/badge/firefox-142%2B-orange)
![License GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)
![No dependencies](https://img.shields.io/badge/runtime%20deps-0-success)

## ✨ Возможности

- Перевод **14 разделов** панели и страницы входа: 1193 строки, 0 китайских остатков.
- Словарь на **1105** пар «китайский → русский», собран вручную по реальному UI.
- Поиск по самому длинному совпадению: короткие слова не разрезают длинные фразы.
- `MutationObserver`: переводятся динамически добавленные узлы, `placeholder`, `title`.
- Даты `2025年10月25日` автоматически превращаются в `25.10.2025`.
- Работает **офлайн**, без jQuery и без единого внешнего запроса.
- Не вызывает API роутера и не меняет его настройки — только текст на странице.
- Готовые пакеты: `open-rumiwifi-<версия>-chromium.zip` и `...-firefox.xpi`.

## 🚀 Установка

### Chromium: Chrome, Edge, Yandex, Opera

1. Скачайте `dist/open-rumiwifi-2.1.1-chromium.zip` из релиза или соберите его:
   `python tools/build.py`.
2. Распакуйте архив в любую папку.
3. Откройте `chrome://extensions` (в Edge — `edge://extensions`) и включите
   «Режим разработчика».
4. Нажмите «Загрузить распакованное расширение» и выберите распакованную папку.
5. Откройте панель роутера: <http://192.168.31.1/cgi-bin/luci/web> и обновите страницу.

### Firefox 142+

1. Скачайте `dist/open-rumiwifi-2.1.1-firefox.xpi` из релиза или соберите его:
   `python tools/build.py`.
2. Откройте `about:debugging#/runtime/this-firefox`.
3. Нажмите «Загрузить временное дополнение» и выберите `.xpi` (или `manifest.json`
   из распакованного архива).
4. Откройте панель роутера и обновите страницу.

Для постоянной установки в обычном Firefox расширение должно быть подписано на
[addons.mozilla.org](https://addons.mozilla.org/). В Developer Edition и Nightly
можно отключить проверку подписи (`xpinstall.signatures.required = false`)
и установить `.xpi` напрямую.

Проверено на **Xiaomi AX3000T (RD03v2), прошивка 2.0.28**. На других моделях
с китайской прошивкой расширение тоже работает, но часть строк может остаться
на китайском — их легко добавить в словарь.

## 🔒 Безопасность

- Расширение не делает сетевых запросов: словарь лежит внутри пакета.
- Не читает и не сохраняет пароль роутера, не обращается к его API.
- В коде нет рекламы, paywall, телеметрии и внешних редиректов — в отличие
  от оригинального RUMIWIFI (см. [`original/README.md`](original/README.md)).
- Подробнее — в [`SECURITY.md`](SECURITY.md).

## 🆚 Чем отличается от RUMIWIFI

| | RUMIWIFI 1.11.8 | Open RUMIWIFI 2.1.1 |
|---|---|---|
| Браузеры | Chromium | Chromium и Firefox |
| Словарь | 2021 год, машинный перевод | собран по прошивке 2.0.28 |
| Подстановка | `replace()` по порядку ключей | trie + самое длинное совпадение |
| Динамический DOM | `DOMNodeInserted` + таймер | `MutationObserver` |
| Зависимости | jQuery, owl.carousel | нет |
| Реклама и paywall | есть | нет |
| Внешние переходы | `updiap.com` | нет |

## ⚙️ Как это работает

`extension/api.js` выбирает `browser.*` в Firefox и `chrome.*` в Chromium, поэтому
остальной код работает с промисами одинаково в обоих браузерах.

`extension/content.js` загружает `lang/zh_ru.json`, строит префиксное дерево и обходит
текстовые узлы страницы. Для каждой позиции выбирается самый длинный ключ словаря,
поэтому `Wi-Fi多频合一` переводится целиком, а не по частям. Наблюдатель за DOM
повторяет проход для новых узлов. Служебные теги (`script`, `style`, `textarea`,
`code`, `pre`) пропускаются.

## 🗂️ Структура

```
extension/            готовое расширение (manifest v3)
  api.js              chrome.* / browser.*
  content.js          переводчик DOM
  lang/zh_ru.json     словарь на 1105 строк
  popup.html/css/js   вкл/выкл, язык, переход в панель
  img/                иконки (генерируются tools/make_icons.py)
data/                 исходники перевода по разделам + TSV
tools/                сборка словаря и пакетов, отчёты, проверки
  build.py            dist/ для Chromium и Firefox
router/pages/         обезличенные снимки панели для офлайн-тестов
test-env/             jsdom-тесты (npm ci && node run-all.js)
docs/                 покрытие и инструкция по публикации
original/             разбор оригинального CRX (без чужих файлов)
dist/                 собранные .zip / .xpi (в .gitignore)
```

## 🛠️ Разработка

```bash
python tools/build_lang.py     # data/ru/*.json → extension/lang/zh_ru.json + проверка покрытия
python tools/report.py         # обновить docs/coverage.md
python tools/make_icons.py     # перерисовать иконки
python tools/build.py          # dist/: chromium.zip, firefox.zip, firefox.xpi, SHA256SUMS
python tools/verify.py         # проверки перед коммитом (секреты, ссылки, словарь)

cd test-env
npm ci
node run-all.js                # 14 страниц × Chromium/Firefox + DOM + popup
```

Добавление строк: найдите китайский текст в `router/pages/`, добавьте пару
в подходящий `data/ru/*.json`, пересоберите словарь. Подробнее — в
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## 📦 Публикация

Репозиторий уже подготовлен: лицензия, CI для GitHub/GitLab, `.gitignore`,
шаблоны issue/PR и инструкция [`docs/PUBLISHING.md`](docs/PUBLISHING.md).
CI собирает пакеты и прикладывает их к артефактам; к релизу стоит приложить
`dist/*.zip` и `dist/*.xpi`.

## 🤝 Участие

- как добавить перевод — [`CONTRIBUTING.md`](CONTRIBUTING.md);
- правила общения — [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md);
- уязвимости — [`SECURITY.md`](SECURITY.md).

## 📜 Лицензия

Код и переводы — **GNU General Public License v3.0** ([текст](LICENSE)).

Вы можете использовать, изменять и распространять проект, в том числе в
коммерческих целях, но производные работы должны распространяться под GPL-3.0
с открытым исходным кодом. Гарантий нет.

Иконки нарисованы специально для проекта (`tools/make_icons.py`). Проект не связан
с Xiaomi и авторами RUMIWIFI; Xiaomi, Redmi и MiWiFi — товарные знаки
соответствующих правообладателей.

---
## 💰 Поддержать автора
+ **SBER**: `2202 2050 1464 4675`
