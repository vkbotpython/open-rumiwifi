/* SPDX-License-Identifier: GPL-3.0-only */
const DEFAULT_PANEL = "http://192.168.31.1/cgi-bin/luci/web";
const $ = (id) => document.getElementById(id);

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function setStatus(text, ok) {
  const el = $("status");
  el.textContent = text;
  el.classList.toggle("off", ok === false);
}

async function refresh() {
  const settings = await chrome.storage.local.get({ rumiEnabled: true, rumiLang: "ru" });
  $("enabled").checked = settings.rumiEnabled !== false;
  $("lang").value = settings.rumiLang === "no" ? "no" : "ru";

  const tab = await activeTab();
  if (!tab || !tab.id) {
    setStatus("Нет активной вкладки", false);
    return;
  }

  chrome.tabs.sendMessage(tab.id, { type: "rumi:status" }, (response) => {
    if (chrome.runtime.lastError || !response) {
      setStatus("Откройте панель роутера, чтобы увидеть перевод", false);
      return;
    }
    if (!response.supported) {
      setStatus("Эта страница не похожа на панель роутера", false);
      return;
    }
    setStatus(
      response.enabled ? `Перевод активен · ${response.host}` : "Перевод выключен",
      response.enabled
    );
    $("dict").textContent = response.dictSize ? String(response.dictSize) : "—";
    $("stats").textContent = response.translated
      ? `Заменено фрагментов: ${response.translated}`
      : "";
  });
}

async function reloadActive() {
  const tab = await activeTab();
  if (tab && tab.id) await chrome.tabs.reload(tab.id);
}

$("enabled").addEventListener("change", async (event) => {
  const enabled = event.target.checked;
  await chrome.storage.local.set(enabled ? { rumiEnabled: true, rumiLang: "ru" } : { rumiEnabled: false });
  await reloadActive();
  window.close();
});

$("lang").addEventListener("change", async (event) => {
  await chrome.storage.local.set({ rumiLang: event.target.value });
  await reloadActive();
  window.close();
});

$("open").addEventListener("click", async () => {
  const { rumiAddress } = await chrome.storage.local.get({ rumiAddress: "" });
  const url = /^https?:\/\//.test(rumiAddress)
    ? rumiAddress
    : rumiAddress
      ? `http://${rumiAddress}/cgi-bin/luci/web`
      : DEFAULT_PANEL;
  chrome.tabs.create({ url });
  window.close();
});

chrome.runtime.onMessage.addListener((message) => {
  if (message && message.type === "rumi:activity") {
    $("stats").textContent = message.count
      ? `Заменено фрагментов: ${message.count}`
      : "";
  }
});

refresh();
