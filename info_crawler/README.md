# 清华大学选课系统爬虫工具集

## 依赖安装

```bash
npm install puppeteer-core iconv-lite
```

## 使用前准备

1. 启动 Chrome 调试模式（在 Chrome 快捷方式目标后添加）：
   ```
   --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
   ```

2. 登录清华大学选课系统

3. 进入"选课开课信息查询"页面

## 主要脚本

### 1. download_all_courses.js
**核心下载脚本**

下载所有课程的"教师网上录入课堂信息"页面。

```bash
node download_all_courses.js
```

- 输出：`../info_Courses/` 文件夹
- 格式：`{teacherId};{courseNumber}_{courseName}.html`
- 特点：支持断点续传，已下载的文件会自动跳过

### 2. extract_teacher_mapping.js
**提取教师映射表**

从选课列表页面提取教师ID与姓名的对应关系。

```bash
node extract_teacher_mapping.js
```

- 输出：`../teacher_mapping.csv`
- 格式：`teacher_id,teacher_name`

### 3. verify_page.js
**验证当前页面**

检查当前是否在正确的页面，显示当前页码和总页数。

```bash
node verify_page.js
```

## 辅助调试脚本

| 脚本名 | 用途 |
|--------|------|
| `explore_course_page.js` | 探索课程列表页面结构，截图保存 |
| `click_first_course.js` | 点击第一个课程，测试跳转 |
| `save_course_info.js` | 保存单个课程详情页（测试用） |
| `fix_encoding.js` | 修复 HTML 文件编码（GB2312→UTF-8） |
| `analyze_pagination.js` | 分析分页结构 |
| `debug_pagination.js` | 调试分页问题 |
| `count_courses.js` | 统计当前页课程数量 |
| `check_list_page.js` | 检查列表页面状态 |
| `restore_list_page.js` | 恢复列表页面到原始状态 |
| `test_direct_access.js` | 测试直接访问课程链接 |

## 文件名说明

下载的课程文件名格式：
```
{教师ID};{课程号}_{课程名}.html
```

例如：`1997990452;00000051_建筑与城市美学.html`

- 分号前：`1997990452` = 教师ID
- 分号后：`00000051` = 课程号

## 注意事项

1. **不要关闭 Chrome 调试窗口**，否则爬虫会中断
2. 如果断网或会话过期，需要重新登录后再继续
3. 脚本支持断点续传，已下载的文件不会重复下载

## 数据输出

爬虫完成后会生成：

1. `info_Courses/` - 包含所有课程的 HTML 文件（约 4,500+ 个）
2. `teacher_mapping.csv` - 教师ID与姓名的映射表
