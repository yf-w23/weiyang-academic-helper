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
    if (title.includes('选课开课信息查询')) {
      targetPage = page;
    }
  }

  if (!targetPage) {
    console.log('Page not found');
    await browser.disconnect();
    return;
  }

  const courses = await targetPage.evaluate(() => {
    const rows = document.querySelectorAll('table tr');
    const list = [];
    for (const row of rows) {
      const link = row.querySelector('a.mainHref');
      if (link) {
        list.push({
          name: link.textContent.trim(),
          href: link.href
        });
      }
    }
    return list;
  });

  console.log('Courses on current page:', courses.length);
  courses.forEach((c, i) => console.log(`${i + 1}. ${c.name}`));

  await browser.disconnect();
})();
