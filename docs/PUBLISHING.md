# Публикация на GitHub / GitLab

Проект уже подготовлен: есть `LICENSE`, `README`, `CHANGELOG`, CI, `.gitignore`
и проверки. Осталось создать удалённый репозиторий и запушить.

## 1. Проверка перед публикацией

```bash
python tools/build_lang.py
python tools/verify.py
cd test-env && npm ci && node run-all.js
cd ..
git status --short
```

Убедитесь, что в выводе нет:

- `original/rumiwifi.crx` и `original/extracted/` (они в `.gitignore`);
- `node_modules`, `__pycache__`, `build/`;
- файлов с паролями, токенами и MAC-адресами.

## 2. GitHub

### Вариант A — через `gh` CLI

```bash
git init -b main
git add .
git commit -m "feat: initial release 2.0.0"
gh repo create open-rumiwifi --public --source=. --remote=origin --push
```

### Вариант B — вручную

1. Создайте пустой репозиторий `open-rumiwifi` на github.com (без README и лицензии).
2. Выполните:

```bash
git init -b main
git add .
git commit -m "feat: initial release 2.0.0"
git remote add origin https://github.com/<user>/open-rumiwifi.git
git push -u origin main
```

После пуша GitHub сам определит лицензию GPL-3.0.

## 3. GitLab

```bash
git init -b main
git add .
git commit -m "feat: initial release 2.0.0"
git remote add origin https://gitlab.com/<user>/open-rumiwifi.git
git push -u origin main
```

CI подхватится из `.gitlab-ci.yml` автоматически.

## 4. Метаданные репозитория

**Описание:**

> Русская локализация веб-панели Xiaomi/Redmi роутеров (MiWiFi). Manifest V3, офлайн, без изменения настроек роутера.

**Темы (topics):**

```
xiaomi  redmi  miwifi  router  localization  russian  chrome-extension  manifest-v3  javascript
```

**Сайт:** можно указать `https://192.168.31.1/cgi-bin/luci/web` (необязательно).

## 5. Релиз

```bash
python tools/build.py
git tag -a v2.1.0 -m "Open RUMIWIFI 2.1.0"
git push origin v2.1.0
```

`tools/build.py` создаёт в `dist/`:

- `open-rumiwifi-2.1.0-chromium.zip` — для Chrome, Edge, Yandex, Opera;
- `open-rumiwifi-2.1.0-firefox.xpi` — для Firefox;
- `open-rumiwifi-2.1.0-firefox.zip` — тот же пакет для проверки;
- `SHA256SUMS.txt` — контрольные суммы.

Приложите эти файлы к релизу на GitHub/GitLab, чтобы расширение можно было
скачать без клонирования и сборки.

На GitLab: **Deploy → Releases → New release**, тег `v2.1.0`,
описание из `CHANGELOG.md`, файлы из `dist/`.

## 6. После публикации

- Проверьте, что вкладка **Actions** (GitHub) или **CI/CD → Pipelines** (GitLab)
  показывает зелёный статус и артефакты `open-rumiwifi-packages`.
- Добавьте бейдж CI в `README.md` (замените `<user>` и `<repo>`):

  ```markdown
  ![CI](https://github.com/<user>/open-rumiwifi/actions/workflows/ci.yml/badge.svg)
  ```

- Включите **Private vulnerability reporting** (GitHub) или **Security Dashboard** (GitLab).
- Проверьте, что GitHub не показывает предупреждений о больших файлах:
  снимки панели занимают около 1,6 МБ, это нормально.

## 7. Чек-лист

- [ ] `python tools/verify.py` проходит;
- [ ] `python tools/build.py` собирает chromium.zip и firefox.xpi;
- [ ] `cd test-env && node run-all.js` зелёный (Chromium и Firefox);
- [ ] в репозитории нет `original/extracted/`, `*.crx`, `node_modules`, `dist/`;
- [ ] лицензия GPL-3.0 видна на странице репозитория;
- [ ] CI зелёный;
- [ ] создан релиз `v2.1.0` с пакетами из `dist/`;
- [ ] в описании репозитория есть фраза «не связан с Xiaomi».
