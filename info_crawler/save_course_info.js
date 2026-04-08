const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

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

  // Get raw HTML by fetching the same URL within the page context
  const html = await targetPage.evaluate(() => {
    return fetch(location.href).then(r => r.text());
  });

  // Extract course name from page text
  const courseName = await targetPage.evaluate(() => {
    const allTd = document.querySelectorAll('td');
    for (const td of allTd) {
      const text = td.textContent.trim();
      if (text.includes('课程名') && !text.includes('建筑与城市美学')) {
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

  console.log(`Saved HTML for "${courseName}" to ${filePath}`);
  console.log('File size:', fs.statSync(filePath).size, 'bytes');

  await browser.disconnect();
})();
