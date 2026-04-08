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

  // Try to restore the search results by going to the original URL
  const originalUrl = 'https://zhjwxk.cic.tsinghua.edu.cn/xkBks.vxkBksJxjhBs.do?m=kkxxSearch&p_xnxq=2025-2026-2&pathContent=%D2%BB%BC%B6%BF%CE%BF%AA%BF%CE%D0%C5%CF%A2';
  await listPage.goto(originalUrl, { waitUntil: 'networkidle2', timeout: 20000 });
  await new Promise(r => setTimeout(r, 3000));

  const pagination = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页\s*\(\s*共\s*([\d,]+)\s*条记录\s*\)/);
    return match ? { current: match[1], total: match[2], records: match[3] } : null;
  });

  const hasTable = await listPage.evaluate(() => !!document.querySelector('table a.mainHref'));
  console.log('Pagination:', pagination);
  console.log('Has course table:', hasTable);

  await browser.disconnect();
})();
