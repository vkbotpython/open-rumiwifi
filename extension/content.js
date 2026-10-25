/*
 * Open RUMIWIFI — русская локализация веб-панели Xiaomi / Redmi роутеров.
 *
 * Расширение полностью офлайн: словарь lang/zh_ru.json лежит внутри пакета,
 * никакие данные никуда не отправляются. Скрипт не вызывает API роутера и
 * не меняет его настройки — он только заменяет текст в уже отрисованной
 * странице.
 */
(() => {
  'use strict';

  const CJK = /[\u3400-\u9fff\uf900-\ufaff]/;
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'CODE', 'PRE']);
  const ATTRS = ['placeholder', 'title', 'alt'];
  const ROUTER_HOST = /^(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|(?:[\w-]+\.)*miwifi\.com|localhost)$/i;

  function isRouterHost() {
    return ROUTER_HOST.test(location.hostname);
  }

  let trie = null;
  let dictSize = 0;
  let enabled = true;
  let translatedNodes = 0;
  let observer = null;
  const pending = new Set();
  const writing = new WeakSet();
  let flushTimer = 0;
  let scheduled = false;

  // ---------- словарь ----------

  function buildTrie(dict) {
    const root = Object.create(null);
    for (const key of Object.keys(dict)) {
      if (!key) continue;
      let node = root;
      for (let i = 0; i < key.length; i++) {
        const ch = key[i];
        node = node[ch] || (node[ch] = Object.create(null));
      }
      node.$ = dict[key];
    }
    return root;
  }

  /**
   * Даты и время панель собирает в китайском формате («2025年10月25日 14:00»).
   * Переводим их в привычный вид до подстановки словаря.
   */
  function translateDateForms(value) {
    return value
      .replace(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/g, (_, y, m, d) =>
        `${d.padStart(2, '0')}.${m.padStart(2, '0')}.${y}`)
      .replace(/(\d{4})\s*年\s*(\d{1,2})\s*月/g, (_, y, m) => `${m.padStart(2, '0')}.${y}`)
      .replace(/(\d{1,2})\s*时\s*(\d{1,2})\s*分/g, (_, h, m) =>
        `${h.padStart(2, '0')}:${m.padStart(2, '0')}`);
  }

  /**
   * Заменяет самый длинный известный фрагмент, начиная с текущей позиции.
   * Так «Wi-Fi多频合一» не разваливается на «Wi-Fi» + «多频合一».
   */
  function translateString(value) {
    if (!trie || !CJK.test(value)) return value;
    value = translateDateForms(value);
    let out = '';
    let i = 0;
    const n = value.length;
    while (i < n) {
      let node = trie;
      let j = i;
      let best = null;
      while (j < n) {
        node = node[value[j]];
        if (!node) break;
        j++;
        if (node.$ !== undefined) best = { text: node.$, end: j };
      }
      if (best) {
        out += best.text;
        i = best.end;
      } else {
        out += value[i];
        i++;
      }
    }
    return out;
  }

  // ---------- DOM ----------

  function translateTextNode(node) {
    const value = node.nodeValue;
    if (!value || !CJK.test(value)) return;
    const next = translateString(value);
    if (next === value) return;
    writing.add(node);
    node.nodeValue = next;
    translatedNodes++;
  }

  function translateAttributes(root) {
    const elements = root.querySelectorAll('[placeholder], [title], [alt]');
    for (const el of elements) {
      for (const attr of ATTRS) {
        const value = el.getAttribute(attr);
        if (!value || !CJK.test(value)) continue;
        const next = translateString(value);
        if (next !== value) {
          writing.add(el);
          el.setAttribute(attr, next);
        }
      }
      if (el.tagName === 'INPUT' && (el.type === 'button' || el.type === 'submit')) {
        const value = el.value;
        if (value && CJK.test(value)) el.value = translateString(value);
      }
    }
  }

  function translateTree(root) {
    if (!trie || !root) return;
    if (root.nodeType === Node.TEXT_NODE) {
      translateTextNode(root);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;

    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent || SKIP_TAGS.has(parent.tagName)) return NodeFilter.FILTER_REJECT;
        return CJK.test(node.nodeValue || '') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) translateTextNode(node);

    const element = root.nodeType === Node.ELEMENT_NODE ? root : document.body;
    if (element) translateAttributes(element);
  }

  function flush() {
    scheduled = false;
    const nodes = Array.from(pending);
    pending.clear();
    for (const node of nodes) {
      if (!node.isConnected) continue;
      translateTree(node);
    }
    if (nodes.length) markActivity();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    clearTimeout(flushTimer);
    flushTimer = setTimeout(flush, 60);
  }

  function startObserver() {
    observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'characterData') {
          if (writing.has(mutation.target)) continue;
          pending.add(mutation.target);
        } else {
          for (const node of mutation.addedNodes) {
            if (node.nodeType === Node.TEXT_NODE || node.nodeType === Node.ELEMENT_NODE) {
              if (writing.has(node)) continue;
              pending.add(node);
            }
          }
        }
      }
      if (pending.size) schedule();
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  // ---------- связь с popup ----------

  function markActivity() {
    try {
      chrome.runtime.sendMessage({ type: 'rumi:activity', count: translatedNodes }, () => {
        // popup может быть закрыт — ошибку доставки игнорируем
        void chrome.runtime.lastError;
      });
    } catch (_) {
      /* контекст расширения недоступен */
    }
  }

  function status() {
    return {
      enabled,
      dictSize,
      translated: translatedNodes,
      host: location.host,
      supported: true
    };
  }

  // ---------- запуск ----------

  async function loadDictionary() {
    const url = chrome.runtime.getURL('lang/zh_ru.json');
    const response = await fetch(url);
    if (!response.ok) throw new Error(`dictionary ${response.status}`);
    const data = await response.json();
    dictSize = Object.keys(data).length;
    trie = buildTrie(data);
  }

  async function boot() {
    if (!isRouterHost()) return;
    const settings = await chrome.storage.local.get({ rumiEnabled: true, rumiLang: 'ru' });
    enabled = settings.rumiEnabled !== false && settings.rumiLang !== 'no';

    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message && message.type === 'rumi:status') {
        sendResponse(status());
        return true;
      }
      if (message && message.type === 'rumi:setEnabled') {
        enabled = !!message.value;
        if (enabled) {
          translateTree(document.body);
        }
        sendResponse(status());
        return true;
      }
      return false;
    });

    if (!enabled) return;
    try {
      await loadDictionary();
    } catch (error) {
      console.warn('[open-rumiwifi] словарь не загружен:', error);
      return;
    }

    translateTree(document.body);
    startObserver();
    markActivity();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
