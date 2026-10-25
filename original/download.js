/* Скачивает RUMIWIFI из Chrome Web Store в original/rumiwifi.crx.
 * Запуск: node original/download.js
 * Файл не публикуется в репозитории (см. .gitignore).
 */
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'rumiwifi.crx');
const URL =
  'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=131.0' +
  '&acceptformat=crx2,crx3&x=id%3Dmbiehbednoakmhlmjcpgpciocekdjabp%26uc';

(async () => {
  const response = await fetch(URL, {
    headers: {
      'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
  });
  console.log('status', response.status, response.headers.get('content-type'));
  const buffer = Buffer.from(await response.arrayBuffer());
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, buffer);
  console.log('bytes', buffer.length, 'magic', buffer.subarray(0, 4).toString());
})().catch((error) => {
  console.error('ERR', error.message, error.cause && error.cause.message);
  process.exit(1);
});
