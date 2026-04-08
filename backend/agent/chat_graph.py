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
from backend.services.transcript_parser import extract_student_info
from backend.services.course_data_service import CourseDataService


class IntentType(str, Enum):
    """意图类型枚举"""
    UPLOAD_TRANSCRIPT = "upload_transcript"
    REQUEST_GAP_ANALYSIS = "request_gap_analysis"
    REQUEST_RECOMMENDATION = "request_recommendation"
    QUERY_COURSE = "query_course"
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
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        
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
        return Command(update={
            "current_intent": IntentType.GENERAL_CHAT,
            "error": f"Intent recognition failed: {str(e)}"
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
        transcript_data = []
        
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
        
        # 精简课程数据库信息用于 prompt
        course_db = []
        for c in candidate_courses[:30]:
            course_db.append({
                "course_name": c.get("course_name"),
                "course_code": c.get("course_code"),
                "teacher_name": c.get("teacher_name"),
                "credits": c.get("credits"),
                "semester": c.get("semester"),
                "rating": c.get("rating"),
                "description": (c.get("description") or "")[:100],
            })
        
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
        # 先查询全校课程数据库
        course_service = CourseDataService()
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
        
        # 精简数据库信息
        course_db = []
        for c in merged_results[:15]:
            course_db.append({
                "course_name": c.get("course_name"),
                "course_code": c.get("course_code"),
                "teacher_name": c.get("teacher_name"),
                "credits": c.get("credits"),
                "semester": c.get("semester"),
                "rating": c.get("rating"),
                "description": c.get("description"),
                "assessment": c.get("assessment"),
                "guidance": c.get("guidance"),
            })
        
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
            "chat_response": "chat_response",
            "error_handler": "error_handler",
            END: END
        }
    )
    
    builder.add_edge("handle_upload", END)
    builder.add_edge("gap_analysis", END)
    builder.add_edge("recommendation", END)
    builder.add_edge("course_query", END)
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
