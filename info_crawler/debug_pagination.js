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

  // Look for pagination-related text in the entire page
  const pageText = await listPage.evaluate(() => {
    const allText = document.body.innerText;
    // Find lines containing "页"
    const lines = allText.split('\n').filter(l => l.includes('页') || l.includes('GO') || l.includes('记录'));
    return lines.slice(-10);
  });

  console.log('Relevant lines:', JSON.stringify(pageText, null, 2));

  // Try a more flexible regex
  const flexibleMatch = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match1 = bodyText.match(/第\s*\d+\s*页/);
    const match2 = bodyText.match(/共\s*\d+\s*页/);
    const match3 = bodyText.match(/共\s*[\d,]+\s*条记录/);
    return { match1: match1?.[0], match2: match2?.[0], match3: match3?.[0] };
  });

  console.log('Flexible matches:', flexibleMatch);

  // Also look at the DOM structure around pagination
  const paginationDOM = await listPage.evaluate(() => {
    const links = Array.from(document.querySelectorAll('a')).filter(a => 
      a.textContent.includes('首页') || a.textContent.includes('下一页') || a.textContent.includes('末页')
    );
    return links.map(a => ({
      text: a.textContent.trim(),
      href: a.href,
      id: a.id
    }));
  });

  console.log('Pagination DOM:', paginationDOM);

  await browser.disconnect();
})();
