const fs = require('fs');
const path = require('path');
const iconv = require('iconv-lite');

const INPUT_DIR = path.join(__dirname, 'info_Courses');
const OUTPUT_FILE = path.join(__dirname, 'teacher_mapping.csv');

// Extract teacher info from HTML files
const teacherMap = new Map();

const files = fs.readdirSync(INPUT_DIR).filter(f => f.endsWith('.html'));
console.log(`Processing ${files.length} files...`);

let processed = 0;
for (const file of files) {
  const filePath = path.join(INPUT_DIR, file);
  
  // Parse filename: teacherId;courseNumber_courseName.html
  const match = file.match(/^([^;]+);(.+)\.html$/);
  if (!match) continue;
  
  const teacherId = match[1];
  
  // Read file and extract teacher name
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Try to find teacher name in the HTML
  // Look for patterns like "主讲教师：XXX" or "教师姓名：XXX"
  const teacherMatches = content.match(/主讲教师[：:]\s*([^<\n]+)/);
  const teacherName = teacherMatches ? teacherMatches[1].trim() : '';
  
  if (teacherName && teacherName.length <= 10) {
    if (!teacherMap.has(teacherId)) {
      teacherMap.set(teacherId, new Set());
    }
    teacherMap.get(teacherId).add(teacherName);
  }
  
  processed++;
  if (processed % 500 === 0) {
    console.log(`Processed ${processed}/${files.length} files...`);
  }
}

// Write to CSV
const lines = ['teacher_id,teacher_name'];
for (const [teacherId, names] of teacherMap) {
  const nameStr = Array.from(names).join('|');
  lines.push(`${teacherId},"${nameStr}"`);
}
fs.writeFileSync(OUTPUT_FILE, lines.join('\n'), 'utf-8');

console.log(`\n=== DONE ===`);
console.log(`Total unique teacher IDs: ${teacherMap.size}`);
console.log(`Output file: ${OUTPUT_FILE}`);
