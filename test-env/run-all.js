/* Полный прогон тестов расширения на обезличенных снимках панели. */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.resolve(__dirname, '..');
const EXT = path.join(ROOT, 'extension');
const PAGES = path.join(ROOT, 'router', 'pages');
const CJK = /[\u3400-\u9fff\uf900-\ufaff]/g;
const PUNCT = /[\u3000-\u303f]/g;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function createDom(html, url) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only', pretendToBeVisual: true });
  const { window } = dom;

  window.chrome = {
    storage: {
      local: {
        get: async (defaults) => ({ ...defaults, rumiEnabled: true, rumiLang: 'ru' })
      }
    },
    runtime: {
      getURL: (resource) => 'file://' + path.join(EXT, resource).replace(/\\/g, '/'),
      sendMessage: (_message, callback) => callback && callback(),
      lastError: null,
      onMessage: { addListener: () => {} }
    }
  };

  window.fetch = async (url) => {
    const file = decodeURIComponent(url.replace('file://', ''));
    return { ok: true, json: async () => JSON.parse(fs.readFileSync(file, 'utf8')) };
  };

  window.eval(fs.readFileSync(path.join(EXT, 'content.js'), 'utf8'));
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

async function checkPage(file) {
  const html = fs.readFileSync(path.join(PAGES, file), 'utf8');
  const isLogin = file === 'web_login.html';
  const url = isLogin
    ? 'http://192.168.31.1/cgi-bin/luci/web'
    : 'http://192.168.31.1/cgi-bin/luci/;stok=0/web/home';

  const window = createDom(html, url);
  await sleep(400);

  const text = visibleText(window);
  const cjk = count(text, CJK);
  const punct = count(text, PUNCT);
  window.close();
  return { file, cjk, punct };
}

async function checkDynamic() {
  const html = fs.readFileSync(path.join(PAGES, 'web_home.html'), 'utf8');
  const window = createDom(html, 'http://192.168.31.1/cgi-bin/luci/;stok=0/web/home');
  await sleep(400);

  const box = window.document.createElement('div');
  box.innerHTML = '<p>正在测速，请等待。</p><button title="添加Mesh节点">确定</button><span>2025年10月25日 14:05</span>';
  window.document.body.appendChild(box);
  await sleep(250);

  const ok =
    box.textContent.startsWith('Идёт тест скорости, подождите.ОК') &&
    box.querySelector('button').getAttribute('title') === 'Добавить Mesh-узел' &&
    box.querySelector('span').textContent === '25.10.2025 14:05';
  window.close();
  return ok;
}

async function checkPlaceholder() {
  const html = fs.readFileSync(path.join(PAGES, 'web_login.html'), 'utf8');
  const window = createDom(html, 'http://192.168.31.1/cgi-bin/luci/web');
  await sleep(400);
  const input = window.document.querySelector('#password');
  const value = input ? input.getAttribute('placeholder') : null;
  window.close();
  return value === 'Пароль роутера';
}

(async () => {
  const files = fs.readdirSync(PAGES).filter((name) => name.endsWith('.html')).sort();
  let failed = 0;

  console.log('Страницы панели:');
  for (const file of files) {
    const result = await checkPage(file);
    const ok = result.cjk === 0 && result.punct === 0;
    if (!ok) failed++;
    console.log(
      `  ${ok ? 'OK  ' : 'FAIL'} ${file.padEnd(38)} CJK=${result.cjk} punct=${result.punct}`
    );
  }

  const dynamic = await checkDynamic();
  console.log(`Динамический DOM: ${dynamic ? 'OK' : 'FAIL'}`);
  if (!dynamic) failed++;

  const placeholder = await checkPlaceholder();
  console.log(`Placeholder входа: ${placeholder ? 'OK' : 'FAIL'}`);
  if (!placeholder) failed++;

  console.log(failed ? `\nПровалено проверок: ${failed}` : `\nВсе проверки пройдены (${files.length} страниц).`);
  process.exit(failed ? 1 : 0);
})();
