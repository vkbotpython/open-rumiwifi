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
  const result = { file, cjk: count(text, CJK), punct: count(text, PUNCT) };
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
  await sleep(250);

  const ok =
    box.textContent.startsWith('Идёт тест скорости, подождите.ОК') &&
    box.querySelector('button').getAttribute('title') === 'Добавить Mesh-узел' &&
    box.querySelector('span').textContent === '25.10.2025 14:05';
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
  const ok = text.includes('Перевод активен') && dict === '1105';
  window.close();
  return ok;
}

(async () => {
  const files = fs.readdirSync(PAGES).filter((name) => name.endsWith('.html')).sort();
  const status = {
    enabled: true,
    dictSize: 1105,
    translated: 42,
    host: '192.168.31.1',
    supported: true
  };

  let failed = 0;
  for (const mode of MODES) {
    console.log(`\nРежим ${mode === 'firefox' ? 'Firefox (browser.*)' : 'Chromium (chrome.*)'}:`);
    for (const file of files) {
      const result = await checkPage(file, mode, status);
      const ok = result.cjk === 0 && result.punct === 0;
      if (!ok) failed++;
      console.log(
        `  ${ok ? 'OK  ' : 'FAIL'} ${file.padEnd(38)} CJK=${result.cjk} punct=${result.punct}`
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
