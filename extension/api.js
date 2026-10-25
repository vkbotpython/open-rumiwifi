/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Единая точка доступа к API расширения.
 *
 * Chromium предоставляет chrome.* с промисами (MV3), Firefox — browser.*
 * с промисами. Скрипты используют RumiApi.api, поэтому один и тот же код
 * работает в обоих браузерах.
 */
(() => {
  const isFirefox =
    typeof browser !== 'undefined' && !!browser.runtime && !!browser.runtime.id;
  const api = isFirefox ? browser : chrome;
  globalThis.RumiApi = { api, isFirefox };
})();
