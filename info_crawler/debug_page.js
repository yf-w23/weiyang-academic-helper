const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.connect({
    browserURL: 'http://127.0.0.1:9222',
    defaultViewport: null
  });

  const pages = await browser.pages();
  let targetPage = null;
  for (const page of pages) {
    const title = await page.title();
    console.log('Page title:', title, 'URL:', page.url());
    if (title.includes('教师网上录入课堂信息')) {
      targetPage = page;
    }
  }

  if (!targetPage) {
    console.log('Page not found!');
    await browser.disconnect();
    return;
  }

  await targetPage.bringToFront();

  const bodyText = await targetPage.evaluate(() => document.body ? document.body.innerText.substring(0, 200) : 'no body');
  console.log('Body text:', bodyText);

  const htmlLen = await targetPage.evaluate(() => document.documentElement ? document.documentElement.outerHTML.length : 'no html');
  console.log('HTML length:', htmlLen);

  const iframes = await targetPage.evaluate(() => document.querySelectorAll('iframe').length);
  console.log('Iframes:', iframes);

  const courseName = await targetPage.evaluate(() => {
    const allTd = document.querySelectorAll('td');
    for (const td of allTd) {
      if (td.textContent.trim() === '课程名') {
        const nextTd = td.nextElementSibling;
        return nextTd ? nextTd.textContent.trim() : 'not found';
      }
    }
    return 'not found';
  });
  console.log('Course name:', courseName);

  await browser.disconnect();
})();
