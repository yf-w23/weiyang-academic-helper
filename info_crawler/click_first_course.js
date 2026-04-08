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
    console.log('Target page not found!');
    await browser.disconnect();
    return;
  }

  await targetPage.bringToFront();

  // Wait for new page after clicking
  const newPagePromise = new Promise(resolve =>
    browser.once('targetcreated', async target => {
      const newPage = await target.page();
      resolve(newPage);
    })
  );

  // Click the first course "建筑与城市美学"
  await targetPage.evaluate(() => {
    const links = document.querySelectorAll('a');
    for (const a of links) {
      if (a.textContent.trim() === '建筑与城市美学') {
        a.click();
        return true;
      }
    }
    return false;
  });

  const newPage = await newPagePromise;
  await newPage.waitForNetworkIdle({ idleTime: 1000, timeout: 10000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2000));

  console.log('New page title:', await newPage.title());
  console.log('New page URL:', newPage.url());

  await newPage.screenshot({ path: 'course_detail_screenshot.png', fullPage: true });
  console.log('Screenshot saved to course_detail_screenshot.png');

  // Search for "教师网上录入课堂信息"
  const infoLinks = await newPage.evaluate(() => {
    const results = [];
    document.querySelectorAll('a, button, td, span, div').forEach(el => {
      if (el.textContent.includes('教师网上录入课堂信息')) {
        results.push({
          tag: el.tagName,
          text: el.textContent.trim(),
          clickable: el.tagName === 'A' || el.tagName === 'BUTTON' || el.onclick !== null,
          outerHTML: el.outerHTML.substring(0, 500)
        });
      }
    });
    return results;
  });

  console.log('Info links found:', JSON.stringify(infoLinks, null, 2));

  await browser.disconnect();
})();
