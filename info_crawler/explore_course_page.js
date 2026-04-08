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
    console.log('Page title:', title);
    if (title.includes('选课开课信息查询')) {
      targetPage = page;
    }
  }

  if (!targetPage) {
    console.log('Target page not found!');
    await browser.disconnect();
    return;
  }

  await targetPage.bringToFront();
  console.log('Target page URL:', targetPage.url());

  // Take screenshot
  await targetPage.screenshot({ path: 'course_list_screenshot.png', fullPage: true });
  console.log('Screenshot saved to course_list_screenshot.png');

  // Try to find the course link
  const courseLinks = await targetPage.evaluate(() => {
    const links = [];
    document.querySelectorAll('a').forEach(a => {
      if (a.textContent.includes('建筑与城市美学')) {
        links.push({
          text: a.textContent.trim(),
          href: a.href,
          outerHTML: a.outerHTML
        });
      }
    });
    return links;
  });

  console.log('Course links found:', JSON.stringify(courseLinks, null, 2));

  // Get table structure to understand the page
  const tableInfo = await targetPage.evaluate(() => {
    const tables = document.querySelectorAll('table');
    return Array.from(tables).map((t, i) => ({
      index: i,
      rows: t.rows.length,
      firstRowText: t.rows[0] ? t.rows[0].innerText.substring(0, 200) : ''
    }));
  });

  console.log('Tables found:', JSON.stringify(tableInfo, null, 2));

  await browser.disconnect();
})();
