const puppeteer = require('puppeteer-core');

(async () => {
  const browser = await puppeteer.connect({
    browserURL: 'http://127.0.0.1:9222',
    defaultViewport: null
  });

  const pages = await browser.pages();
  let listPage = null;
  for (const page of pages) {
    const title = await page.title();
    if (title.includes('选课开课信息查询')) {
      listPage = page;
    }
  }

  if (!listPage) {
    console.log('Page not found');
    await browser.disconnect();
    return;
  }

  await listPage.bringToFront();
  await new Promise(r => setTimeout(r, 3000));

  const bodyText = await listPage.evaluate(() => document.body.innerText.substring(0, 500));
  const hasTable = await listPage.evaluate(() => !!document.querySelector('table a.mainHref'));
  const pagination = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页\s*\(\s*共\s*([\d,]+)\s*条记录\s*\)/);
    return match ? { current: match[1], total: match[2], records: match[3] } : null;
  });

  console.log('Body text (first 500 chars):', bodyText);
  console.log('Has course table:', hasTable);
  console.log('Pagination:', pagination);

  await browser.disconnect();
})();
