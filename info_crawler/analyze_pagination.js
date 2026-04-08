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

  // Analyze pagination
  const pagination = await targetPage.evaluate(() => {
    const result = {
      currentPage: null,
      totalPages: null,
      totalRecords: null,
      pageInput: null,
      goButton: null,
      nextButton: null,
      prevButton: null,
      firstButton: null,
      lastButton: null
    };

    // Look for text like "第 1 页 / 共 263 页 (共 5,252 条记录)"
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页\s*\(\s*共\s*([\d,]+)\s*条记录\s*\)/);
    if (match) {
      result.currentPage = parseInt(match[1]);
      result.totalPages = parseInt(match[2]);
      result.totalRecords = parseInt(match[3].replace(/,/g, ''));
    }

    // Find pagination buttons/links
    const allElements = document.querySelectorAll('a, input, button');
    allElements.forEach(el => {
      const text = el.textContent?.trim() || '';
      const value = el.value?.trim() || '';
      
      if (text === '下一页' || value === '下一页') {
        result.nextButton = { tag: el.tagName, text: text || value, outerHTML: el.outerHTML.substring(0, 200) };
      }
      if (text === '上一页' || value === '上一页') {
        result.prevButton = { tag: el.tagName, text: text || value, outerHTML: el.outerHTML.substring(0, 200) };
      }
      if (text === '首页' || value === '首页') {
        result.firstButton = { tag: el.tagName, text: text || value, outerHTML: el.outerHTML.substring(0, 200) };
      }
      if (text === '末页' || value === '末页') {
        result.lastButton = { tag: el.tagName, text: text || value, outerHTML: el.outerHTML.substring(0, 200) };
      }
      if (el.tagName === 'INPUT' && el.type === 'text' && el.name && el.name.toLowerCase().includes('page')) {
        result.pageInput = { name: el.name, id: el.id, value: el.value, outerHTML: el.outerHTML.substring(0, 200) };
      }
      if (el.tagName === 'INPUT' && (el.type === 'button' || el.type === 'submit') && (value === 'GO' || value === 'Go' || value === 'go')) {
        result.goButton = { name: el.name, id: el.id, value: value, outerHTML: el.outerHTML.substring(0, 200) };
      }
    });

    return result;
  });

  console.log('Pagination info:', JSON.stringify(pagination, null, 2));

  await browser.disconnect();
})();
