# Changelog

Все заметные изменения проекта. Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии — [SemVer](https://semver.org/lang/ru/).

## [2.1.0] — 2026-10-25

Поддержка Firefox и сборка готовых пакетов.

### Добавлено

- Сборка `tools/build.py`: `dist/open-rumiwifi-<версия>-chromium.zip`,
  `...-firefox.zip`, `...-firefox.xpi` и `SHA256SUMS.txt`.
- Firefox-манифест с `browser_specific_settings.gecko` (id, минимальная версия 142,
  `data_collection_permissions: none`).
- `extension/api.js` — единая обёртка над `chrome.*` и `browser.*`.
- Тесты прогоняются в двух режимах: Chromium (`chrome.*`) и Firefox (`browser.*`),
  включая popup.
- CI собирает пакеты и публикует их как артефакты (GitHub Actions и GitLab CI).

### Изменено

- GitHub Actions обновлены до версий на Node.js 24:
  `checkout@v5`, `setup-python@v6`, `setup-node@v5`, `upload-artifact@v6`.
- CI использует Node.js 24; GitLab-образ `node:24-bookworm-slim`.
- README: отдельные инструкции для Chromium и Firefox.

## [2.0.0] — 2026-10-25

Первая публичная версия Open RUMIWIFI.

### Добавлено

- Собственный словарь на 1105 строк, собранный по интерфейсу прошивки Xiaomi 2.0.28.
- Покрытие 14 разделов панели и страницы входа: 1193 строки, 0 китайских остатков.
- Перевод `placeholder`, `title`, `alt` и кнопок `input[type=button]`.
- Конвертация дат `2025年10月25日` → `25.10.2025` и времени `14时05分` → `14:05`.
- `MutationObserver` для динамически добавляемых узлов.
- Popup: включение/выключение, выбор языка, переход в панель.
- CI для GitHub Actions и GitLab CI, `tools/verify.py`, jsdom-тесты на снимках панели.
- Иконки, нарисованные специально для проекта (`tools/make_icons.py`).

### Изменено

- Движок перевода переписан без jQuery: trie + поиск самого длинного совпадения.
- Словарь больше не зависит от старого `zh_ru.json` RUMIWIFI: машинные переводы
  не используются.
- Страница входа и служебные сообщения переведены заново.

### Удалено

- Рекламная карусель роутеров, ссылки Boosty/4PDA и paywall.
- Скрытый переход на `updiap.com` через 11 дней.
- Тёмная тема RUMIWIFI (требовала Pro-подписку).

### Безопасность

- Из снимков панели удалены session-токены и MAC-адреса.
- Скрипты сбора строк берут пароль только из `RUMIWIFI_PASSWORD`.
- Расширение не делает сетевых запросов и не вызывает API роутера.

### Лицензия

- Проект распространяется под **GNU GPL v3.0** (`GPL-3.0-only`).

## Предыстория

- **RUMIWIFI 1.11.8** — стороннее расширение, взятое за основу анализа.
  Его файлы в репозитории не распространяются; разбор — в `original/README.md`.
