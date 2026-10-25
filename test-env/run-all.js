/* Полный прогон тестов расширения на обезличенных снимках панели.
 * Проверяются оба режима: Chromium (chrome.*) и Firefox (browser.*).
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.resolve(__dirname, '..');
const EXT = path.join(ROOT, 'extension');
const PAGES = path.join(ROOT, 'router', 'pages');
const CJK = /[\u3400-\u9fff\uf900-\ufaff]/g;
const PUNCT = /[\u3000-\u303f]/g;
const MODES = ['chromium', 'firefox'];
const DICT_SIZE = Object.keys(
  JSON.parse(fs.readFileSync(path.join(EXT, 'lang', 'zh_ru.json'), 'utf8'))
).length;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function fileUrl(resource) {
  return 'file://' + path.join(EXT, resource).replace(/\\/g, '/');
}

function runtimeMock(status) {
  const listeners = [];
  return {
    id: 'open-rumiwifi-test',
    getURL: fileUrl,
    sendMessage: async () => undefined,
    onMessage: { addListener: (fn) => listeners.push(fn) },
    lastError: null,
    _listeners: listeners,
    _status: status
  };
}

function createDom(html, url, mode, status) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only', pretendToBeVisual: true });
  const { window } = dom;
  const runtime = runtimeMock(status);

  const mock = {
    runtime,
    storage: {
      local: {
        get: async (defaults) => ({ ...defaults, rumiEnabled: true, rumiLang: 'ru' }),
        set: async () => undefined
      }
    },
    tabs: {
      query: async () => [{ id: 1, url }],
      sendMessage: async () => status,
      reload: async () => undefined,
      create: async () => ({ id: 2 })
    }
  };

  if (mode === 'firefox') {
    window.browser = mock;
  } else {
    window.chrome = mock;
  }

  window.fetch = async (request) => {
    const file = decodeURIComponent(String(request).replace('file://', ''));
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(file, 'utf8')) };
  };

  for (const script of ['api.js', 'content.js']) {
    window.eval(fs.readFileSync(path.join(EXT, script), 'utf8'));
  }
  return window;
}

function visibleText(window) {
  const clone = window.document.body.cloneNode(true);
  clone.querySelectorAll('script, style, noscript').forEach((node) => node.remove());
  return clone.textContent.replace(/\s+/g, ' ').trim();
}

function count(text, regex) {
  return (text.match(regex) || []).length;
}

async function checkPage(file, mode, status) {
  const html = fs.readFileSync(path.join(PAGES, file), 'utf8');
  const isLogin = file === 'web_login.html';
  const url = isLogin
    ? 'http://192.168.31.1/cgi-bin/luci/web'
    : 'http://192.168.31.1/cgi-bin/luci/;stok=0/web/home';

  const window = createDom(html, url, mode, status);
  await sleep(400);

  const text = visibleText(window);
  const title = window.document.title;
  const result = {
    file,
    cjk: count(text, CJK),
    punct: count(text, PUNCT),
    titleCjk: count(title, CJK),
    title,
    layout: window.document.documentElement.classList.contains('rumi-i18n')
  };
  window.close();
  return result;
}

async function checkDynamic(mode, status) {
  const html = fs.readFileSync(path.join(PAGES, 'web_home.html'), 'utf8');
  const window = createDom(html, 'http://192.168.31.1/cgi-bin/luci/;stok=0/web/home', mode, status);
  await sleep(400);

  const box = window.document.createElement('div');
  box.innerHTML =
    '<p>正在测速，请等待。</p><button title="添加Mesh节点">确定</button><span>2025年10月25日 14:05</span>';
  window.document.body.appendChild(box);

  // Строки, которые панель собирает в JS: раньше они переводились частично
  // («Порт “1” как WAN», «Текущая версия2.0.28», «还没有设备Добавить进来»).
  const dynamic = window.document.createElement('div');
  dynamic.innerHTML =
    '<p class="form-message">智能识别网口“1”作为WAN口</p>' +
    '<p id="version">当前版本<em>2.0.28</em>，你的版本是最新的，无需升级。</p>' +
    '<a id="add-rule"><span>添加规则</span></a>' +
    '<table><tbody><tr><td>还没有设备添加进来</td></tr></tbody></table>';
  window.document.body.appendChild(dynamic);

  window.document.title = '小米路由器';
  await sleep(250);
  const titleOk = window.document.title === 'Xiaomi роутер';
  window.document.title = 'Redmi路由器';
  await sleep(250);
  const redmiTitleOk = window.document.title === 'Redmi роутер';
  await sleep(250);

  const text = (selector) => dynamic.querySelector(selector).textContent;
  const ok =
    box.textContent.startsWith('Идёт тест скорости, подождите.ОК') &&
    box.querySelector('button').getAttribute('title') === 'Добавить Mesh-узел' &&
    box.querySelector('span').textContent === '25.10.2025 14:05' &&
    text('.form-message') === 'Порт «1» автоматически определён как WAN' &&
    text('#version') ===
      'Текущая версия 2.0.28, У вас последняя версия, обновление не требуется.' &&
    text('#add-rule') === 'Добавить правило' &&
    text('td') === 'Устройства ещё не добавлены' &&
    titleOk &&
    redmiTitleOk;
  window.close();
  return ok;
}

async function checkPlaceholder(mode, status) {
  const html = fs.readFileSync(path.join(PAGES, 'web_login.html'), 'utf8');
  const window = createDom(html, 'http://192.168.31.1/cgi-bin/luci/web', mode, status);
  await sleep(400);
  const input = window.document.querySelector('#password');
  const value = input ? input.getAttribute('placeholder') : null;
  window.close();
  return value === 'Пароль роутера';
}

async function checkPopup(mode, status) {
  const html = fs.readFileSync(path.join(EXT, 'popup.html'), 'utf8');
  const dom = new JSDOM(html, {
    url: 'https://example.invalid/popup.html',
    runScripts: 'outside-only',
    pretendToBeVisual: true
  });
  const { window } = dom;
  const runtime = runtimeMock(status);

  const mock = {
    runtime,
    storage: {
      local: {
        get: async (defaults) => ({ ...defaults }),
        set: async () => undefined
      }
    },
    tabs: {
      query: async () => [{ id: 1 }],
      sendMessage: async () => status,
      reload: async () => undefined,
      create: async () => ({ id: 2 })
    }
  };
  if (mode === 'firefox') window.browser = mock;
  else window.chrome = mock;

  window.eval(fs.readFileSync(path.join(EXT, 'api.js'), 'utf8'));
  window.eval(fs.readFileSync(path.join(EXT, 'popup.js'), 'utf8'));
  await sleep(200);

  const text = window.document.getElementById('status').textContent;
  const dict = window.document.getElementById('dict').textContent;
  const ok = text.includes('Перевод активен') && dict === String(DICT_SIZE);
  window.close();
  return ok;
}

(async () => {
  const files = fs.readdirSync(PAGES).filter((name) => name.endsWith('.html')).sort();
  const status = {
    enabled: true,
    dictSize: DICT_SIZE,
    translated: 42,
    host: '192.168.31.1',
    supported: true
  };

  let failed = 0;
  for (const mode of MODES) {
    console.log(`\nРежим ${mode === 'firefox' ? 'Firefox (browser.*)' : 'Chromium (chrome.*)'}:`);
    for (const file of files) {
      const result = await checkPage(file, mode, status);
      const ok =
        result.cjk === 0 &&
        result.punct === 0 &&
        result.titleCjk === 0 &&
        result.layout;
      if (!ok) failed++;
      console.log(
        `  ${ok ? 'OK  ' : 'FAIL'} ${file.padEnd(38)} CJK=${result.cjk} punct=${result.punct} title="${result.title}" layout=${result.layout}`
      );
    }
    const dynamic = await checkDynamic(mode, status);
    const placeholder = await checkPlaceholder(mode, status);
    const popup = await checkPopup(mode, status);
    console.log(`  ${dynamic ? 'OK  ' : 'FAIL'} динамический DOM`);
    console.log(`  ${placeholder ? 'OK  ' : 'FAIL'} placeholder входа`);
    console.log(`  ${popup ? 'OK  ' : 'FAIL'} popup`);
    if (!dynamic) failed++;
    if (!placeholder) failed++;
    if (!popup) failed++;
  }

  console.log(
    failed
      ? `\nПровалено проверок: ${failed}`
      : `\nВсе проверки пройдены (${files.length} страниц × 2 режима).`
  );
  process.exit(failed ? 1 : 0);
})();
