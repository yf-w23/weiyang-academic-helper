const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, 'teacher_mapping.csv');

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
    console.error('选课开课信息查询 page not found!');
    await browser.disconnect();
    process.exit(1);
  }

  // Get total pages
  await listPage.bringToFront();
  await new Promise(r => setTimeout(r, 2000));

  const paginationInfo = await listPage.evaluate(() => {
    const bodyText = document.body.innerText;
    const match = bodyText.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页/);
    return match ? { currentPage: parseInt(match[1]), totalPages: parseInt(match[2]) } : null;
  });

  if (!paginationInfo) {
    console.error('Could not determine pagination');
    await browser.disconnect();
    process.exit(1);
  }

  const { totalPages } = paginationInfo;
  console.log(`Total pages: ${totalPages}`);

  const teacherMap = new Map(); // teacherId (before semicolon) -> Set of teacher names

  // Process all pages
  for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
    console.log(`\n=== Processing page ${pageNum}/${totalPages} ===`);

    await listPage.bringToFront();

    if (pageNum > 1) {
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
          console.warn(`  Turn page ${pageNum} attempt ${attempt} failed`);
          await new Promise(r => setTimeout(r, 3000));
        }
      }
      if (!pageTurned) {
        console.error(`  Failed to turn to page ${pageNum}, skipping...`);
        continue;
      }
      await new Promise(r => setTimeout(r, 1000));
    }

    // Extract course info with teacher names from the table
    const courses = await listPage.evaluate(() => {
      const rows = document.querySelectorAll('table tr');
      const list = [];
      for (const row of rows) {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 6) {
          const link = row.querySelector('a.mainHref');
          if (link) {
            const teacherCell = cells[5];
            const teacherName = teacherCell ? teacherCell.textContent.trim() : '';
            
            list.push({
              url: link.href,
              teacherName: teacherName
            });
          }
        }
      }
      return list;
    });

    console.log(`Found ${courses.length} courses on page ${pageNum}`);

    for (const course of courses) {
      const pIdMatch = course.url.match(/p_id=([^&]+)/);
      if (pIdMatch && course.teacherName) {
        // Extract only the part before semicolon as teacherId
        const fullId = pIdMatch[1];
        const teacherId = fullId.split(';')[0]; // Only keep part before semicolon
        const teacherName = course.teacherName;
        
        if (!teacherMap.has(teacherId)) {
          teacherMap.set(teacherId, new Set());
        }
        teacherMap.get(teacherId).add(teacherName);
      }
    }

    console.log(`Unique teacher mappings so far: ${teacherMap.size}`);
  }

  await browser.disconnect();

  // Write to CSV with UTF-8 BOM for Excel
  const lines = ['teacher_id,teacher_name'];
  for (const [teacherId, names] of teacherMap) {
    const nameStr = Array.from(names).join('|');
    lines.push(`${teacherId},${nameStr}`);
  }
  
  const bom = Buffer.from([0xEF, 0xBB, 0xBF]);
  const content = Buffer.from(lines.join('\n'), 'utf-8');
  fs.writeFileSync(OUTPUT_FILE, Buffer.concat([bom, content]));

  console.log(`\n=== DONE ===`);
  console.log(`Total unique teacher IDs: ${teacherMap.size}`);
  console.log(`Output file: ${OUTPUT_FILE}`);
})();
