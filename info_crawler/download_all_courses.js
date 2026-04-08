const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const iconv = require('iconv-lite');

const OUTPUT_DIR = path.join(__dirname, 'info_Courses');
const DELAY_MS = 800; // slightly higher delay for stability

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR);
  }

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
    console.error('选课开课信息查询 page not found!');
    await browser.disconnect();
    process.exit(1);
  }

  const detailPage = await browser.newPage();

  let totalSaved = 0;
  let totalSkipped = 0;
  const startTime = Date.now();

  await listPage.bringToFront();
  await sleep(2000);

  const paginationInfo = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页\s*（\s*共\s*([\d,]+)\s*条记录\s*）/);
    if (match) {
      return { totalPages: parseInt(match[2]), totalRecords: parseInt(match[3].replace(/,/g, '')) };
    }
    const lastLink = document.querySelector('a#endpage');
    if (lastLink) {
      const hrefMatch = lastLink.href.match(/turn\((\d+)\)/);
      if (hrefMatch) {
        return { totalPages: parseInt(hrefMatch[1]), totalRecords: null };
      }
    }
    return null;
  });

  if (!paginationInfo) {
    console.error('Could not determine total pages');
    await browser.disconnect();
    process.exit(1);
  }

  const { totalPages, totalRecords } = paginationInfo;
  console.log(`Total: ${totalRecords || '?'} records, ${totalPages} pages`);

  // Detect starting page from existing files if possible, else start from 1
  let startPage = 1;

  for (let pageNum = startPage; pageNum <= totalPages; pageNum++) {
    console.log(`\n=== Processing page ${pageNum}/${totalPages} ===`);

    await listPage.bringToFront();

    if (pageNum > 1) {
      // Try to turn page with retries
      let pageTurned = false;
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          await listPage.evaluate((n) => turn(n), pageNum);
          await listPage.waitForFunction(
            (n) => {
              const bodyText = document.body.innerText;
              const match = bodyText.match(/第\s*(\d+)\s*页/);
              return match && parseInt(match[1]) === n;
            },
            { timeout: 20000 },
            pageNum
          );
          pageTurned = true;
          break;
        } catch (err) {
          console.warn(`  Turn page ${pageNum} attempt ${attempt} failed: ${err.message}`);
          await sleep(3000);
        }
      }

      if (!pageTurned) {
        console.error(`  Failed to turn to page ${pageNum} after 3 attempts, skipping...`);
        continue;
      }

      await sleep(1500);
    }

    // Extract course links with retry
    let courses = [];
    for (let attempt = 1; attempt <= 3; attempt++) {
      courses = await listPage.evaluate(() => {
        const rows = document.querySelectorAll('table tr');
        const list = [];
        for (const row of rows) {
          const link = row.querySelector('a.mainHref');
          if (link) {
            list.push({
              name: link.textContent.trim(),
              url: link.href
            });
          }
        }
        return list;
      });

      if (courses.length > 0) break;
      console.warn(`  No courses found on page ${pageNum}, attempt ${attempt}, retrying...`);
      await sleep(2000);
    }

    console.log(`Found ${courses.length} courses on page ${pageNum}`);

    if (courses.length === 0) {
      console.error(`  Still no courses on page ${pageNum}, skipping...`);
      continue;
    }

    for (let i = 0; i < courses.length; i++) {
      const course = courses[i];
      const pIdMatch = course.url.match(/p_id=([^&]+)/);
      const pId = pIdMatch ? pIdMatch[1] : 'unknown';
      const safeName = course.name.replace(/[\\/:*?"<>|]/g, '_');
      const fileName = `${pId}_${safeName}.html`;
      const filePath = path.join(OUTPUT_DIR, fileName);

      if (fs.existsSync(filePath)) {
        console.log(`[SKIP] ${fileName} already exists`);
        totalSkipped++;
        continue;
      }

      let saved = false;
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          await detailPage.goto(course.url, { waitUntil: 'networkidle2', timeout: 20000 });

          const htmlBuffer = await detailPage.evaluate(() => {
            return fetch(location.href)
              .then(r => r.arrayBuffer())
              .then(ab => Array.from(new Uint8Array(ab)));
          });

          const buffer = Buffer.from(htmlBuffer);
          let html = iconv.decode(buffer, 'gb2312');
          html = html.replace(/charset=gb2312/gi, 'charset=utf-8');
          html = html.replace(/charset=gbk/gi, 'charset=utf-8');

          fs.writeFileSync(filePath, html, 'utf-8');
          totalSaved++;
          console.log(`[SAVED ${totalSaved}] ${fileName}`);
          saved = true;
          break;
        } catch (err) {
          console.error(`[ERROR attempt ${attempt}] ${fileName}: ${err.message}`);
          await sleep(2000);
        }
      }

      if (!saved) {
        console.error(`[FAILED] Could not save ${fileName} after 3 attempts`);
      }

      await sleep(DELAY_MS);
    }

    const elapsed = (Date.now() - startTime) / 1000;
    const processed = totalSaved + totalSkipped;
    const avgPerCourse = elapsed / (processed || 1);
    const remainingCourses = (totalRecords || (totalPages * courses.length)) - processed;
    const remaining = remainingCourses * avgPerCourse;
    console.log(`Progress: ${totalSaved} saved, ${totalSkipped} skipped | Elapsed: ${(elapsed/60).toFixed(1)}min | ETA: ${(remaining/60).toFixed(1)}min`);
  }

  await detailPage.close();
  await browser.disconnect();

  console.log(`\n=== DONE ===`);
  console.log(`Total saved: ${totalSaved}`);
  console.log(`Total skipped: ${totalSkipped}`);
  console.log(`Output directory: ${OUTPUT_DIR}`);
})();
