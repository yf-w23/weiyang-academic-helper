#!/usr/bin/env python3
"""Parse course data from MD files and Excel ratings"""
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).parent.parent
MD_DIR = BASE_DIR / 'info_courses_md'
STARS_DIR = BASE_DIR / 'info_courses_stars'


def parse_course_md(content: str) -> List[Dict]:
    """Parse markdown content to extract courses"""
    courses = []
    sections = re.split(r'\n##\s+', content)
    
    for section in sections[1:]:  # Skip first non-course section
        course = parse_single_course(section)
        if course and course.get('course_name'):
            courses.append(course)
    return courses


def parse_single_course(section: str) -> Dict:
    """Parse a single course section"""
    course = {}
    lines = section.strip().split('\n')
    
    if not lines:
        return None
    
    course['course_name'] = lines[0].strip()
    
    # Parse table fields
    for line in lines[1:]:
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                field, value = parts[0], parts[1]
                if '课程编号' in field:
                    course['course_code'] = None if value == '未知' else value
                elif field == '课程名':
                    course['course_name'] = value
                elif '总学时' in field:
                    try:
                        course['hours'] = int(value) if value not in ['未知', ''] else None
                    except:
                        course['hours'] = None
                elif '总学分' in field:
                    try:
                        course['credits'] = float(value) if value not in ['未知', ''] else None
                    except:
                        course['credits'] = None
                elif '开课教师编号' in field:
                    course['teacher_id'] = None if value == '未知' else value
                elif field == '开课教师':
                    course['teacher_name'] = None if value == '未知' else value
    
    # Extract sections
    course['description'] = extract_section(section, '### 课程内容简介', '### 考核方式')
    course['assessment'] = extract_section(section, '### 考核方式', '### 成绩评定标准')
    course['grading'] = extract_section(section, '### 成绩评定标准', '### 选课指导')
    course['guidance'] = extract_section(section, '### 选课指导', '---')
    
    return course


def extract_section(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    """Extract content between markers"""
    start = text.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        end = len(text)
    content = text[start:end].strip()
    return content if content and content != '未知' else None


def load_rating_data(excel_path: Path) -> Dict:
    """Load rating data from Excel (Tsinghua course recommendation format)"""
    try:
        import pandas as pd
        df = pd.read_excel(excel_path)
        ratings = {}
        
        # Expected columns: 开课院系, 教师名, 课程号, 课程名, 分数1-7, 总人数, 平均分, 标准差, 百分制, 等级
        for _, row in df.iterrows():
            name = str(row.get('课程名', '')).strip() if pd.notna(row.get('课程名')) else ''
            teacher = str(row.get('教师名', '')).strip() if pd.notna(row.get('教师名')) else ''
            # Use 平均分 (1-7 scale) and 百分制 as rating references
            avg_score = float(row.get('平均分')) if pd.notna(row.get('平均分')) else None
            pct_score = float(row.get('百分制')) if pd.notna(row.get('百分制')) else None
            count = int(row.get('总人数')) if pd.notna(row.get('总人数')) else None
            
            if name and name != 'nan':
                # Normalize to 0-100 scale for consistency; prefer 百分制 if available
                if pct_score is not None:
                    rating = pct_score
                elif avg_score is not None:
                    rating = (avg_score / 7.0) * 100
                else:
                    rating = None
                
                # Key by course_name + teacher_name for more precise matching
                key = f"{name}_{teacher}" if teacher else name
                ratings[key] = {
                    'rating': rating,
                    'count': count,
                    'teacher': teacher,
                    'avg_score': avg_score,
                    'pct_score': pct_score,
                }
                # Also store plain name lookup fallback
                if name not in ratings:
                    ratings[name] = {
                        'rating': rating,
                        'count': count,
                        'teacher': teacher,
                        'avg_score': avg_score,
                        'pct_score': pct_score,
                    }
        return ratings
    except Exception as e:
        print(f"Error loading {excel_path}: {e}")
        return {}


def main():
    print("Starting course data parsing...")
    
    # 1. Parse all MD files
    all_courses = []
    md_files = sorted(MD_DIR.glob('*.md'))
    print(f"Found {len(md_files)} MD files")
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            courses = parse_course_md(content)
            all_courses.extend(courses)
            print(f"  {md_file.name}: {len(courses)} courses")
        except Exception as e:
            print(f"  Error {md_file.name}: {e}")
    
    print(f"\nTotal parsed: {len(all_courses)} courses")
    
    # 2. Load rating data
    spring_ratings = {}
    autumn_ratings = {}
    
    try:
        spring_file = STARS_DIR / '2025-2026春季学期课程推荐度.xlsx'
        autumn_file = STARS_DIR / '2025-2026秋季学期课程推荐度.xlsx'
        
        if spring_file.exists():
            spring_ratings = load_rating_data(spring_file)
            print(f"Spring ratings: {len(spring_ratings)}")
        
        if autumn_file.exists():
            autumn_ratings = load_rating_data(autumn_file)
            print(f"Autumn ratings: {len(autumn_ratings)}")
    except Exception as e:
        print(f"Error loading ratings: {e}")
    
    # 3. Merge and build output
    course_list = []
    schedule_info = {}
    seen_codes = {}
    matched_count = 0
    
    for course in all_courses:
        name = course.get('course_name', '')
        code = course.get('course_code')
        
        # Generate unique ID
        unique_id = code if code else f"{name}_{course.get('teacher_name', 'unknown')}"
        if unique_id in seen_codes:
            continue
        seen_codes[unique_id] = True
        
        # Match ratings by course_name + teacher_name first, then by course_name alone
        rating = None
        count = None
        matched_source = None
        teacher = course.get('teacher_name', '')
        key = f"{name}_{teacher}" if teacher else name
        
        for ratings in [spring_ratings, autumn_ratings]:
            if key in ratings:
                rating = ratings[key].get('rating')
                count = ratings[key].get('count')
                matched_source = ratings
                break
            elif name in ratings:
                rating = ratings[name].get('rating')
                count = ratings[name].get('count')
                matched_source = ratings
                break
        
        if rating is not None:
            matched_count += 1
        
        # Determine semester
        name_in_spring = name in spring_ratings or key in spring_ratings
        name_in_autumn = name in autumn_ratings or key in autumn_ratings
        if name_in_spring and name_in_autumn:
            semester = "全年"
        elif name_in_spring:
            semester = "春季"
        elif name_in_autumn:
            semester = "秋季"
        else:
            semester = "未知"
        
        course_data = {
            'course_code': code or f"UNKNOWN_{len(course_list)}",
            'course_name': name,
            'credits': course.get('credits'),
            'hours': course.get('hours'),
            'teacher_id': course.get('teacher_id'),
            'teacher_name': course.get('teacher_name'),
            'description': course.get('description'),
            'assessment': course.get('assessment'),
            'grading': course.get('grading'),
            'guidance': course.get('guidance'),
            'semester': semester,
            'rating': rating,
            'recommendation_count': count,
        }
        
        course_list.append(course_data)
        
        if code:
            schedule_info[code] = {
                'course_name': name,
                'credits': course.get('credits'),
                'semester': semester,
                'departments': [],
                'teacher_name': course.get('teacher_name'),
            }
    
    # 4. Create output directory
    output_dir = BASE_DIR / 'backend/data/courses'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. Write courses.json
    courses_output = {
        'courses': course_list,
        'metadata': {
            'total_count': len(course_list),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'version': '1.0.0',
        }
    }
    
    with open(output_dir / 'courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses_output, f, ensure_ascii=False, indent=2)
    
    print(f"\nGenerated: backend/data/courses/courses.json ({len(course_list)} courses)")
    
    # 6. Write course_schedule.json
    with open(output_dir / 'course_schedule.json', 'w', encoding='utf-8') as f:
        json.dump(schedule_info, f, ensure_ascii=False, indent=2)
    
    print(f"Generated: backend/data/courses/course_schedule.json ({len(schedule_info)} entries)")
    
    # Print final stats
    print("\n" + "="*50)
    print("Parsing complete!")
    print("="*50)
    print(f"Total courses: {len(course_list)}")
    print(f"With ratings: {matched_count}")
    print(f"With course code: {sum(1 for c in course_list if not c['course_code'].startswith('UNKNOWN'))}")
    print(f"Unknown course code: {sum(1 for c in course_list if c['course_code'].startswith('UNKNOWN'))}")


if __name__ == '__main__':
    main()
