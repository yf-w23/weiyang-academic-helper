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

  await targetPage.bringToFront();

  // Test 1: Get course URLs from current page
  const courseUrls = await targetPage.evaluate(() => {
    const rows = document.querySelectorAll('table tr');
    const list = [];
    for (const row of rows) {
      const link = row.querySelector('a.mainHref');
      if (link) {
        list.push(link.href);
      }
    }
    return list;
  });

  console.log('Course URLs:', courseUrls.slice(0, 3));

  // Test 2: Try to goto the first course URL directly in a new page
  const testPage = await browser.newPage();
  await testPage.goto(courseUrls[0], { waitUntil: 'networkidle2', timeout: 15000 });
  const title = await testPage.title();
  const hasContent = await testPage.evaluate(() => document.body.innerText.includes('课程编号'));
  console.log('Direct access title:', title);
  console.log('Has content:', hasContent);
  await testPage.close();

  // Test 3: Try pagination by turn(2)
  await targetPage.evaluate(() => turn(2));
  await targetPage.waitForTimeout(3000);
  const page2Info = await targetPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页/);
    const firstCourse = document.querySelector('a.mainHref')?.textContent?.trim();
    return { match: match ? match[0] : null, firstCourse };
  });
  console.log('Page 2 info:', page2Info);

  await browser.disconnect();
})();
