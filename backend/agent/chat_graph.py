"""多轮对话状态图 - LangGraph based conversational agent."""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from backend.agent.chat_prompts import (
    get_intent_recognition_prompt,
    get_course_recommendation_prompt,
    get_course_query_prompt,
    get_chat_response_prompt,
    MISSING_TRANSCRIPT_MESSAGE,
    HELP_MESSAGE,
)
from backend.agent.tools import extract_transcript_from_pdf, load_graduation_schema
from backend.services.llm_service import LLMService
from backend.services.transcript_parser import extract_student_info, parse_transcript
from backend.services.course_data_service import CourseDataService
from backend.services.course_catalog_service import get_course_catalog_service
from backend.services.general_edu_recommendation import CourseRatingService
from backend.agent.general_edu_tools import (
    get_general_education_gaps,
    format_general_edu_summary,
    recommend_general_education_courses,
    query_general_edu_course_info,
)


class IntentType(str, Enum):
    """意图类型枚举"""
    UPLOAD_TRANSCRIPT = "upload_transcript"
    REQUEST_GAP_ANALYSIS = "request_gap_analysis"
    REQUEST_RECOMMENDATION = "request_recommendation"
    QUERY_COURSE = "query_course"
    QUERY_GENERAL_EDU = "query_general_edu"  # 通识课查询/推荐
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


class ChatState(TypedDict, total=False):
    """对话状态定义"""
    session_id: str
    messages: List[Dict[str, Any]]
    current_intent: Optional[str]
    uploaded_file: Optional[str]
    transcript_data: Optional[List[Dict]]
    transcript_md: Optional[str]
    gap_analysis_result: Optional[Dict]
    user_preferences: Dict[str, Any]
    enrollment_year: Optional[int]
    class_name: Optional[str]
    context: Dict[str, Any]
    response: Optional[str]
    error: Optional[str]


def format_chat_history(messages: List[Dict[str, Any]], max_turns: int = 5) -> str:
    """格式化对话历史"""
    if not messages:
        return "（无历史对话）"
    
    recent = messages[-max_turns * 2:]
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"用户：{content}")
        elif role == "assistant":
            lines.append(f"助手：{content}")
    return "\n".join(lines) if lines else "（无历史对话）"


def get_last_user_message(state: ChatState) -> str:
    """获取最后一条用户消息"""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def intent_recognition_node(state: ChatState) -> Command:
    """意图识别节点"""
    messages = state.get("messages", [])
    chat_history = format_chat_history(messages[:-1] if messages else [])
    current_message = get_last_user_message(state)
    
    if not current_message:
        return Command(update={
            "current_intent": IntentType.UNKNOWN,
            "response": "我没有收到您的消息，请重新发送。"
        })
    
    # 简单规则匹配（快速路径）
    msg_lower = current_message.lower()
    
    if any(kw in msg_lower for kw in ["帮助", "help", "能做什么", "怎么用"]):
        return Command(update={
            "current_intent": IntentType.GENERAL_CHAT,
            "response": HELP_MESSAGE
        })
    
    try:
        llm = LLMService()
        prompt = get_intent_recognition_prompt(chat_history, current_message)
        
        response = llm.chat_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # 解析JSON响应
        if not response or not response.strip():
            return Command(update={
                "current_intent": IntentType.GENERAL_CHAT,
            })

        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        # 尝试提取 JSON 对象（找第一个 { 到最后一个 }）
        if '{' in json_str and '}' in json_str:
            json_str = json_str[json_str.index('{'):json_str.rindex('}') + 1]

        result = json.loads(json_str)
        intent = result.get("intent", IntentType.UNKNOWN)
        entities = result.get("extracted_entities", {})
        
        valid_intents = [e.value for e in IntentType]
        if intent not in valid_intents:
            intent = IntentType.UNKNOWN
        
        context = state.get("context", {})
        context["extracted_entities"] = entities
        
        return Command(update={
            "current_intent": intent,
            "context": context
        })
            
    except Exception as e:
        # JSON 解析失败时不设 error，直接走 GENERAL_CHAT
        return Command(update={
            "current_intent": IntentType.GENERAL_CHAT,
        })


def handle_upload_node(state: ChatState) -> Command:
    """处理文件上传节点"""
    uploaded_file = state.get("uploaded_file")
    
    if not uploaded_file:
        return Command(update={
            "response": "请先上传成绩单PDF文件。",
            "current_intent": IntentType.UPLOAD_TRANSCRIPT
        })
    
    try:
        transcript_md = extract_transcript_from_pdf(uploaded_file)
        transcript_data = parse_transcript(transcript_md)
        # 规则解析失败时，延迟到通识课查询时再用 LLM 回退（避免上传时额外等待）
        
        # 自动从成绩单中提取年级和班级
        info = extract_student_info(transcript_md)
        year = info.get("year")
        class_name = info.get("class_name")
        
        update_state: Dict[str, Any] = {
            "transcript_md": transcript_md,
            "transcript_data": transcript_data,
        }
        
        if year:
            update_state["enrollment_year"] = int(year)
        if class_name:
            update_state["class_name"] = class_name
        
        if year and class_name:
            update_state["response"] = (
                f"成绩单上传成功！我已自动识别您为{class_name}（{year}级）。"
                f"现在可以为您进行培养方案缺口分析了。"
            )
        else:
            missing = []
            if not year:
                missing.append("入学年份")
            if not class_name:
                missing.append("班级")
            update_state["response"] = (
                f"成绩单上传成功！但未能自动识别您的{'、'.join(missing)}信息，"
                f"请在对话中告诉我，以便进行准确分析。"
            )
        
        return Command(update=update_state)
        
    except Exception as e:
        return Command(update={
            "error": f"成绩单解析失败: {str(e)}",
            "response": f"抱歉，成绩单解析失败：{str(e)}。请确保上传的是有效的PDF成绩单文件。"
        })


def gap_analysis_node(state: ChatState) -> Command:
    """缺口分析节点"""
    transcript_md = state.get("transcript_md")
    year = state.get("enrollment_year")
    class_name = state.get("class_name")
    
    if not transcript_md:
        return Command(update={
            "response": MISSING_TRANSCRIPT_MESSAGE
        })
    
    if not year or not class_name:
        return Command(update={
            "response": "请告诉我您的入学年份和班级（如'2021级 未央-软件11'），我才能进行准确的分析。"
        })
    
    try:
        schema_md = load_graduation_schema(str(year), class_name)
        
        llm = LLMService()
        analysis_result = llm.analyze_gap(
            schema=schema_md,
            transcript=transcript_md,
            year=str(year),
            class_name=class_name
        )
        
        gap_result = {
            "analysis_text": analysis_result,
            "enrollment_year": year,
            "class_name": class_name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_credits_required": 0,
                "total_credits_earned": 0,
                "completion_rate": 0.0
            }
        }
        
        return Command(update={
            "gap_analysis_result": gap_result,
            "response": analysis_result
        })
        
    except Exception as e:
        return Command(update={
            "error": f"Gap analysis failed: {str(e)}",
            "response": f"分析过程出错：{str(e)}。请稍后重试或联系管理员。"
        })


def recommendation_node(state: ChatState) -> Command:
    """选课推荐节点"""
    gap_result = state.get("gap_analysis_result")
    user_prefs = state.get("user_preferences", {})
    year = state.get("enrollment_year")
    class_name = state.get("class_name")
    
    if not gap_result:
        return Command(goto="gap_analysis")
    
    if not year or not class_name:
        return Command(update={
            "response": "请告诉我您的入学年份和班级，我才能给出准确的选课推荐。"
        })
    
    try:
        # 从全校课程库中搜索相关课程作为推荐候选
        course_service = CourseDataService()
        rating_service = CourseRatingService()
        interests = user_prefs.get("interests", [])
        search_keywords = interests if interests else ["通识", "专业"]

        candidate_courses = []
        seen_names = set()
        for keyword in search_keywords[:3]:
            results = course_service.search_courses(keyword)
            for course in results:
                name = course.get("course_name")
                if name and name not in seen_names:
                    seen_names.add(name)
                    candidate_courses.append(course)

        # 如果没有兴趣关键词，补充一些高评分课程
        if not candidate_courses:
            candidate_courses = course_service.get_high_rated_courses(min_rating=80)[:20]

        # 精简课程数据库信息用于 prompt，并附加评分数据
        course_db = []
        for c in candidate_courses[:30]:
            entry = {
                "course_name": c.get("course_name"),
                "course_code": c.get("course_code"),
                "teacher_name": c.get("teacher_name"),
                "credits": c.get("credits"),
                "semester": c.get("semester"),
                "rating": c.get("rating"),
                "description": (c.get("description") or "")[:100],
            }
            # 附加评教数据
            code = c.get("course_code", "")
            if code:
                rating = rating_service.get_rating(code)
                if rating:
                    entry["rating_detail"] = {
                        "avg_score": round(rating.avg_score, 1),
                        "grade": rating.grade,
                        "teacher": rating.teacher_name,
                        "total_students": rating.total_students,
                    }
            course_db.append(entry)
        
        llm = LLMService()
        prompt = get_course_recommendation_prompt(
            gap_result=gap_result,
            user_preferences=user_prefs,
            class_name=class_name,
            year=year,
            course_database=course_db
        )
        
        recommendation = llm.chat_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000
        )
        
        return Command(update={
            "response": recommendation
        })
        
    except Exception as e:
        return Command(update={
            "error": f"Recommendation failed: {str(e)}",
            "response": f"生成推荐时出错：{str(e)}。请稍后重试。"
        })


def course_query_node(state: ChatState) -> Command:
    """课程查询节点"""
    context = state.get("context", {})
    entities = context.get("extracted_entities", {})
    course_name = entities.get("course_name", "")
    teacher_name = entities.get("teacher_name", "")

    if not course_name and not teacher_name:
        return Command(update={
            "response": "请告诉我您想查询哪门课程或哪位教师的信息（如'数据结构'、'邓俊辉'等）。"
        })

    year = state.get("enrollment_year")
    class_name = state.get("class_name")

    try:
        # 查询全校课程数据库 + 课程目录
        course_service = CourseDataService()
        catalog_service = get_course_catalog_service()
        rating_service = CourseRatingService()
        merged_results = []
        seen_codes = set()

        if course_name:
            db_results = course_service.get_course_by_name(course_name, fuzzy=True)
            search_results = course_service.search_courses(course_name)
            for course in db_results + search_results:
                code = course.get("course_code") or course.get("course_name")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    merged_results.append(course)

        if teacher_name:
            teacher_results = course_service.search_courses(teacher_name)
            for course in teacher_results:
                code = course.get("course_code") or course.get("course_name")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    merged_results.append(course)

        # 也从课程目录中搜索（补充描述、考核方式等详情）
        catalog_results = []
        if course_name:
            catalog_results = catalog_service.search_courses(course_name)
        elif teacher_name:
            catalog_results = catalog_service.search_courses(teacher_name)
        catalog_by_code = {}
        for cr in catalog_results:
            if cr.code:
                catalog_by_code[cr.code] = cr

        # 精简数据库信息，并附加评分数据和课程目录详情
        course_db = []
        for c in merged_results[:15]:
            code = c.get("course_code", "")
            entry = {
                "course_name": c.get("course_name"),
                "course_code": code,
                "teacher_name": c.get("teacher_name"),
                "credits": c.get("credits"),
                "semester": c.get("semester"),
                "rating": c.get("rating"),
                "description": c.get("description"),
                "assessment": c.get("assessment"),
                "guidance": c.get("guidance"),
            }
            # 从课程目录补充详情（如果有）
            if code in catalog_by_code:
                cat = catalog_by_code[code]
                if not entry.get("description") and cat.description:
                    entry["description"] = cat.description
                if not entry.get("assessment") and cat.assessment:
                    entry["assessment"] = cat.assessment
                if not entry.get("guidance") and cat.guidance:
                    entry["guidance"] = cat.guidance
                if not entry.get("teacher_name") and cat.teacher_name:
                    entry["teacher_name"] = cat.teacher_name
                if not entry.get("credits") and cat.credits:
                    entry["credits"] = cat.credits
            # 附加评教数据
            if code:
                rating = rating_service.get_rating(code)
                if not rating:
                    rating = rating_service.get_rating_by_name(c.get("course_name", ""))
                if rating:
                    entry["rating_detail"] = {
                        "avg_score": rating.avg_score,
                        "grade": rating.grade,
                        "teacher": rating.teacher_name,
                        "total_students": rating.total_students,
                        "department": rating.department,
                    }
            course_db.append(entry)

        # 如果课程数据库没找到结果，直接从目录返回
        if not course_db and catalog_results:
            for cr in catalog_results[:15]:
                entry = {
                    "course_name": cr.name,
                    "course_code": cr.code,
                    "teacher_name": cr.teacher_name,
                    "credits": cr.credits,
                    "description": cr.description,
                    "assessment": cr.assessment,
                    "guidance": cr.guidance,
                }
                rating = rating_service.get_rating(cr.code)
                if not rating:
                    rating = rating_service.get_rating_by_name(cr.name)
                if rating:
                    entry["rating_detail"] = {
                        "avg_score": rating.avg_score,
                        "grade": rating.grade,
                        "teacher": rating.teacher_name,
                        "total_students": rating.total_students,
                        "department": rating.department,
                    }
                course_db.append(entry)
        
        # 如果有年级班级，加载培养方案作为补充
        schema_md = ""
        if year and class_name:
            try:
                schema_md = load_graduation_schema(str(year), class_name)
            except Exception:
                pass
        
        llm = LLMService()
        chat_history = format_chat_history(state.get("messages", []))
        
        query_target = course_name or teacher_name
        prompt = get_course_query_prompt(
            course_name=query_target,
            schema_md=schema_md or "（未提供培养方案）",
            chat_history=chat_history,
            course_database=course_db or None
        )
        
        response = llm.chat_completion(
            prompt=prompt,
            temperature=0.5,
            max_tokens=1500
        )
        
        return Command(update={
            "response": response
        })
        
    except Exception as e:
        return Command(update={
            "response": f'关于"{course_name or teacher_name}"：\n\n抱歉，查询课程信息时出错：{str(e)}。'
        })


def _extract_courses_with_llm(transcript_md: str) -> List[Dict[str, Any]]:
    """使用 LLM 从成绩单 markdown 中提取结构化课程数据（正则解析失败时的回退方案）"""
    prompt = f"""请从以下成绩单内容中提取所有已修课程信息，以 JSON 数组格式返回。
每门课程包含以下字段：
- code: 课程号（如无法识别则为空字符串）
- name: 课程名称
- credits: 学分（数字）
- grade: 成绩（如 A、B+、90 等）
- is_passed: 是否通过（boolean）

只返回 JSON 数组，不要包含其他内容。如果课程不及格，is_passed 设为 false。

成绩单内容：
{transcript_md}
"""
    try:
        llm = LLMService()
        response = llm.chat_completion(
            prompt=prompt,
            temperature=0.1,
            max_tokens=4000,
        )
        # 提取 JSON
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        if "[" in text and "]" in text:
            text = text[text.index("["):text.rindex("]") + 1]
        courses = json.loads(text)
        # 验证并规范化
        result = []
        for c in courses:
            if not isinstance(c, dict) or not c.get("name"):
                continue
            result.append({
                "code": str(c.get("code", "")).strip(),
                "name": str(c["name"]).strip(),
                "credits": float(c.get("credits", 0)),
                "grade": str(c.get("grade", "")).strip(),
                "is_passed": bool(c.get("is_passed", True)),
            })
        return result
    except Exception:
        return []


def _extract_target_group(message: str) -> Optional[str]:
    """从用户消息中提取指定的课组"""
    msg_lower = message.lower()
    
    # 艺术课组
    if any(kw in msg_lower for kw in ["艺术课组", "艺术课", "艺术类的"]):
        return "art"
    # 科学课组
    elif any(kw in msg_lower for kw in ["科学课组", "科学课", "科学类的"]):
        return "science"
    # 人文课组
    elif any(kw in msg_lower for kw in ["人文课组", "人文课", "人文类的"]):
        return "humanities"
    # 社科课组
    elif any(kw in msg_lower for kw in ["社科课组", "社科课", "社科类的", "社会科学"]):
        return "social"
    
    return None


def general_edu_node(state: ChatState) -> Command:
    """通识选修课分析/推荐节点"""
    current_message = get_last_user_message(state)
    transcript_md = state.get("transcript_md")
    transcript_data = state.get("transcript_data", [])
    context = state.get("context", {})
    entities = context.get("extracted_entities", {})
    
    # 检查是否有成绩单数据
    if not transcript_md:
        return Command(update={
            "response": "请先上传成绩单，我才能分析您的通识选修课完成情况。"
        })
    
    # 如果 transcript_data 为空，从 markdown 解析并持久化到 state
    extra_update = {}
    if not transcript_data:
        transcript_data = parse_transcript(transcript_md)
        # 规则解析失败时，回退到 LLM 提取
        if not transcript_data:
            transcript_data = _extract_courses_with_llm(transcript_md)
        if transcript_data:
            extra_update["transcript_data"] = transcript_data
    
    try:
        # 判断用户意图是查询缺口还是请求推荐
        msg_lower = current_message.lower()
        
        is_recommendation = any(kw in msg_lower for kw in [
            "推荐", "选课", "选什么", "建议", "推荐课程"
        ])
        
        is_gap_query = any(kw in msg_lower for kw in [
            "差几学分", "缺几学分", "没修满", "完成情况", "进度如何",
            "修了多少", "还差多少"
        ])
        
        # 获取用户兴趣偏好和指定课组
        interests = entities.get("interests", [])
        target_group = _extract_target_group(current_message)
        
        if is_recommendation:
            # 通识课推荐
            result = recommend_general_education_courses(
                transcript_data,
                interests=interests,
                target_group=target_group
            )
            
            # 如果指定了课组但没有找到该课组的课程，给出提示
            if target_group and not result["recommendations"]:
                group_names = {
                    "art": "艺术课组",
                    "science": "科学课组", 
                    "humanities": "人文课组",
                    "social": "社科课组"
                }
                group_name = group_names.get(target_group, target_group)
                response = f"抱歉，没有找到{group_name}的推荐课程。\n\n"
                response += "该课组可能已完成，或者课程数据需要更新。\n"
                response += "您可以查看您的通识课完成情况，或询问其他课组的推荐。"
                return Command(update={**extra_update, "response": response})

            return Command(update={
                **extra_update,
                "response": result["report"]
            })

        else:
            # 默认：提供完成情况摘要和缺口分析
            summary = format_general_edu_summary(transcript_data)
            gaps = get_general_education_gaps(transcript_data)

            response = f"{summary}\n\n{gaps}"

            # 如果有未完成的课组，提供推荐
            from backend.services.general_edu_service import get_general_edu_service
            service = get_general_edu_service()
            analysis = service.analyze_completion(transcript_data)
            incomplete = service.get_incomplete_groups(analysis)

            if incomplete and not is_gap_query:
                # 自动推荐一些课程
                result = recommend_general_education_courses(
                    transcript_data,
                    interests=interests,
                    max_recommendations=5
                )
                if result["recommendations"]:
                    response += "\n\n**为您推荐以下通识课**:\n"
                    for rec in result["recommendations"][:3]:
                        response += f"- {rec['course_name']} ({rec['group_name']}, {rec['credits']}学分) - {rec['reason']}\n"

            return Command(update={
                **extra_update,
                "response": response
            })

    except Exception as e:
        return Command(update={
            **extra_update,
            "error": f"General edu analysis failed: {str(e)}",
            "response": f"分析通识选修课时出错：{str(e)}。请稍后重试。"
        })


def chat_response_node(state: ChatState) -> Command:
    """对话响应节点"""
    current_message = get_last_user_message(state)
    chat_history = format_chat_history(state.get("messages", [])[:-1])
    
    current_state = {
        "has_transcript": state.get("transcript_md") is not None,
        "has_analysis": state.get("gap_analysis_result") is not None,
        "enrollment_year": state.get("enrollment_year"),
        "class_name": state.get("class_name"),
        "user_preferences": state.get("user_preferences", {})
    }
    
    try:
        llm = LLMService()
        prompt = get_chat_response_prompt(
            message=current_message,
            chat_history=chat_history,
            current_state=current_state
        )
        
        response = llm.chat_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        return Command(update={
            "response": response
        })
        
    except Exception as e:
        generic_responses = {
            "你好": "你好！我是你的学业规划助手。有什么可以帮助你的吗？",
            "谢谢": "不客气！有问题随时问我。",
            "再见": "再见！祝你学业顺利！",
        }
        
        for key, resp in generic_responses.items():
            if key in current_message:
                return Command(update={"response": resp})
        
        return Command(update={
            "response": '抱歉，我没有完全理解您的问题。您可以：\n1. 上传成绩单进行分析\n2. 询问课程信息\n3. 请求选课推荐\n\n或者输入"帮助"查看我能做什么。'
        })


def error_handler_node(state: ChatState) -> Command:
    """错误处理节点"""
    error = state.get("error", "")
    error_response = f"抱歉，处理过程中出现了问题：{error}\n\n请稍后重试，或联系管理员。"
    
    return Command(update={
        "response": error_response,
        "error": None
    })


def route_by_intent(state: ChatState) -> str:
    """根据意图路由到不同节点"""
    intent = state.get("current_intent", IntentType.UNKNOWN)
    error = state.get("error")
    
    if error:
        return "error_handler"
    
    if state.get("response") and intent == IntentType.GENERAL_CHAT:
        return END
    
    routing_map = {
        IntentType.UPLOAD_TRANSCRIPT: "handle_upload",
        IntentType.REQUEST_GAP_ANALYSIS: "gap_analysis",
        IntentType.REQUEST_RECOMMENDATION: "recommendation",
        IntentType.QUERY_COURSE: "course_query",
        IntentType.QUERY_GENERAL_EDU: "general_edu",
        IntentType.GENERAL_CHAT: "chat_response",
        IntentType.UNKNOWN: "chat_response",
    }
    
    return routing_map.get(intent, "chat_response")


def build_chat_graph() -> StateGraph:
    """构建多轮对话状态图"""
    builder = StateGraph(ChatState)
    
    # 添加节点
    builder.add_node("intent_recognition", intent_recognition_node)
    builder.add_node("handle_upload", handle_upload_node)
    builder.add_node("gap_analysis", gap_analysis_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("course_query", course_query_node)
    builder.add_node("general_edu", general_edu_node)
    builder.add_node("chat_response", chat_response_node)
    builder.add_node("error_handler", error_handler_node)
    
    # 添加边
    builder.add_edge(START, "intent_recognition")
    
    builder.add_conditional_edges(
        "intent_recognition",
        route_by_intent,
        {
            "handle_upload": "handle_upload",
            "gap_analysis": "gap_analysis",
            "recommendation": "recommendation",
            "course_query": "course_query",
            "general_edu": "general_edu",
            "chat_response": "chat_response",
            "error_handler": "error_handler",
            END: END
        }
    )
    
    builder.add_edge("handle_upload", END)
    builder.add_edge("gap_analysis", END)
    builder.add_edge("recommendation", END)
    builder.add_edge("course_query", END)
    builder.add_edge("general_edu", END)
    builder.add_edge("chat_response", END)
    builder.add_edge("error_handler", END)
    
    return builder.compile()


# 全局图实例
_chat_graph = None


def get_chat_graph() -> StateGraph:
    """获取或创建编译后的对话图"""
    global _chat_graph
    if _chat_graph is None:
        _chat_graph = build_chat_graph()
    return _chat_graph
