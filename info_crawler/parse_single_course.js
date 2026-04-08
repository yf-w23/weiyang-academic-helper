const fs = require('fs');
const path = require('path');

// Load teacher mapping
const teacherMap = new Map();
const teacherCsv = fs.readFileSync(path.join(__dirname, '../teacher_mapping.csv'), 'utf-8');
const teacherLines = teacherCsv.split('\n');
for (let i = 1; i < teacherLines.length; i++) {
  const line = teacherLines[i].trim();
  if (!line) continue;
  const commaIndex = line.indexOf(',');
  if (commaIndex > 0) {
    const teacherId = line.substring(0, commaIndex);
    const teacherName = line.substring(commaIndex + 1);
    teacherMap.set(teacherId, teacherName);
  }
}

// Parse a single HTML file
function parseCourseHtml(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Extract info from filename
  const fileName = path.basename(filePath);
  const match = fileName.match(/^([^;]+);(.+)\.html$/);
  if (!match) return null;
  
  const teacherId = match[1];
  const courseInfo = match[2];
  const courseNameMatch = courseInfo.match(/^_?([^_]+)$/);
  const courseNameFromFile = courseNameMatch ? courseNameMatch[1] : courseInfo;
  
  // Get teacher name from mapping
  const teacherName = teacherMap.get(teacherId) || '未知';
  
  // Extract fields from HTML using regex
  const extractField = (label) => {
    const regex = new RegExp(`<!--${label}[：:]?\\s*-->\\s*${label}[：:]?\\s*</div>\\s*</td>\\s*<td[^>]*>\\s*([^<]+)`, 's');
    const m = content.match(regex);
    return m ? m[1].trim() : '';
  };
  
  // Extract fields using different patterns
  const courseNumber = extractContent(content, '课程编号');
  const courseName = extractContent(content, '课程名');
  const totalHours = extractContent(content, '总学时');
  const totalCredits = extractContent(content, '总学分');
  const courseDescription = extractContent(content, '课程内容简介');
  const examMethod = extractContent(content, '考核方式');
  const gradingStandard = extractContent(content, '成绩评定标准');
  const courseGuide = extractContent(content, '选课指导');
  
  return {
    courseNumber: courseNumber || '未知',
    courseName: courseName || courseNameFromFile,
    totalHours: totalHours || '未知',
    totalCredits: totalCredits || '未知',
    courseDescription: courseDescription || '未知',
    examMethod: examMethod || '未知',
    gradingStandard: gradingStandard || '未知',
    courseGuide: courseGuide || '未知',
    teacherId: teacherId,
    teacherName: teacherName
  };
}

function extractContent(html, label) {
  // Try different patterns
  const patterns = [
    new RegExp(`<!--${label}[：:]?\\s*-->\\s*${label}[：:]?\\s*</div>\\s*</td>\\s*<td[^>]*align="left"[^>]*>\\s*([^<]+)`, 's'),
    new RegExp(`${label}[：:]?\\s*</div>\\s*</td>\\s*<td[^>]*>\\s*([^<]+)`, 's'),
    new RegExp(`<!--${label}[：:]?\\s*-->[^<]*<td[^>]*>\\s*([^<]+)`, 's'),
  ];
  
  for (const pattern of patterns) {
    const m = html.match(pattern);
    if (m && m[1].trim()) {
      return m[1].trim();
    }
  }
  
  // Try multi-line content for longer fields
  const multiLinePattern = new RegExp(`${label}[：:]?\\s*</div>\\s*</td>\\s*<td[^>]*colspan="3"[^>]*>([\\s\\S]*?)</td>`, 's');
  const m = html.match(multiLinePattern);
  if (m) {
    return m[1].replace(/<[^>]+>/g, '').trim();
  }
  
  return '';
}

// Parse one file
const filePath = path.join(__dirname, '../info_Courses/1957990010;00050071_环境保护与可持续发展.html');
const course = parseCourseHtml(filePath);

if (course) {
  const md = `# ${course.courseName}

## 基本信息

| 字段 | 内容 |
|------|------|
| 课程编号 | ${course.courseNumber} |
| 课程名 | ${course.courseName} |
| 总学时 | ${course.totalHours} |
| 总学分 | ${course.totalCredits} |
| 开课教师编号 | ${course.teacherId} |
| 开课教师 | ${course.teacherName} |

## 课程内容简介

${course.courseDescription}

## 考核方式

${course.examMethod}

## 成绩评定标准

${course.gradingStandard}

## 选课指导

${course.courseGuide}
`;

  console.log(md);
  fs.writeFileSync(path.join(__dirname, '../sample_course.md'), md, 'utf-8');
  console.log('\n已保存到 sample_course.md');
}
