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
  await new Promise(r => setTimeout(r, 2000));

  const pagination = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页/);
    const courses = document.querySelectorAll('a.mainHref').length;
    return { currentPage: match ? match[1] : null, totalPages: match ? match[2] : null, coursesOnPage: courses };
  });

  console.log('Current page:', pagination.currentPage);
  console.log('Total pages:', pagination.totalPages);
  console.log('Courses on page:', pagination.coursesOnPage);

  await browser.disconnect();
})();
