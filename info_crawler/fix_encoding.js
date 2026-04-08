const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const iconv = require('iconv-lite');

(async () => {
  const browser = await puppeteer.connect({
    browserURL: 'http://127.0.0.1:9222',
    defaultViewport: null
  });

  const pages = await browser.pages();
  let targetPage = null;
  for (const page of pages) {
    const title = await page.title();
    if (title.includes('教师网上录入课堂信息')) {
      targetPage = page;
    }
  }

  if (!targetPage) {
    console.log('教师网上录入课堂信息 page not found!');
    await browser.disconnect();
    return;
  }

  await targetPage.bringToFront();

  // Fetch as binary and decode with gb2312
  const htmlBuffer = await targetPage.evaluate(() => {
    return fetch(location.href)
      .then(r => r.arrayBuffer())
      .then(ab => Array.from(new Uint8Array(ab)));
  });

  const buffer = Buffer.from(htmlBuffer);
  let html = iconv.decode(buffer, 'gb2312');

  // Replace charset to utf-8 so browser renders correctly
  html = html.replace(/charset=gb2312/gi, 'charset=utf-8');
  html = html.replace(/charset=gbk/gi, 'charset=utf-8');

  // Extract course name from page
  const courseName = await targetPage.evaluate(() => {
    const allTd = document.querySelectorAll('td');
    for (const td of allTd) {
      const text = td.textContent.trim().replace(/[:：]/g, '');
      if (text === '课程名') {
        const nextTd = td.nextElementSibling;
        return nextTd ? nextTd.textContent.trim() : 'unknown';
      }
    }
    return 'unknown';
  });

  const safeName = courseName.replace(/[\\/:*?"<>|]/g, '_');
  const outputDir = path.join(__dirname, 'info_Courses');
  const filePath = path.join(outputDir, `${safeName}.html`);
  fs.writeFileSync(filePath, html, 'utf-8');

  console.log(`Saved fixed HTML for "${courseName}" to ${filePath}`);
  console.log('File size:', fs.statSync(filePath).size, 'bytes');

  await browser.disconnect();
})();
