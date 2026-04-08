"""对话运行器 - 管理多轮对话会话。"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator

from backend.agent.chat_graph import get_chat_graph, ChatState, IntentType
from backend.agent.chat_prompts import WELCOME_MESSAGE, format_chat_history


class ChatSession:
    """单个对话会话管理"""
    
    def __init__(
        self,
        session_id: str,
        enrollment_year: Optional[int] = None,
        class_name: Optional[str] = None
    ):
        self.session_id = session_id
        self.state: ChatState = {
            "session_id": session_id,
            "messages": [],
            "current_intent": None,
            "uploaded_file": None,
            "transcript_data": None,
            "transcript_md": None,
            "gap_analysis_result": None,
            "user_preferences": {},
            "enrollment_year": enrollment_year,
            "class_name": class_name,
            "context": {},
            "response": None,
            "error": None
        }
        self.graph = get_chat_graph()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.state["messages"].append(message)
        self.last_activity = datetime.now()
        
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """更新用户偏好"""
        self.state["user_preferences"].update(preferences)
        
    def set_enrollment_info(self, year: int, class_name: str) -> None:
        """设置入学信息"""
        self.state["enrollment_year"] = year
        self.state["class_name"] = class_name
        
    def set_uploaded_file(self, file_path: str) -> None:
        """设置上传文件路径"""
        self.state["uploaded_file"] = file_path
        
    def run(self, message: str) -> Dict[str, Any]:
        """运行一轮对话（非流式）"""
        # 添加用户消息
        self.add_message("user", message)
        
        # 运行图
        final_state = self.graph.invoke(self.state)
        
        # 更新状态
        self.state = final_state
        
        # 获取响应
        response = final_state.get("response", "抱歉，我暂时无法处理您的请求。")
        
        # 添加助手回复
        self.add_message("assistant", response)
        
        return {
            "session_id": self.session_id,
            "response": response,
            "intent": final_state.get("current_intent", IntentType.UNKNOWN),
            "has_transcript": final_state.get("transcript_md") is not None,
            "has_analysis": final_state.get("gap_analysis_result") is not None
        }
        
    async def run_stream(self, message: str) -> AsyncGenerator[str, None]:
        """流式运行对话（SSE格式）"""
        # 添加用户消息
        self.add_message("user", message)
        
        # 发送开始事件
        yield 'event: start\ndata: {"status": "processing"}\n\n'
        
        try:
            # 运行图（非流式，但模拟流式输出）
            final_state = self.graph.invoke(self.state)
            self.state = final_state
            
            response = final_state.get("response", "")
            
            # 模拟流式输出（按句子分割）
            import re
            sentences = re.split(r'([。！？\n]+)', response)
            
            for sentence in sentences:
                if sentence.strip():
                    data = {"chunk": sentence}
                    yield f'event: chunk\ndata: {__import__("json").dumps(data)}\n\n'
                    await asyncio.sleep(0.05)  # 模拟延迟
            
            # 添加助手回复
            self.add_message("assistant", response)
            
            # 发送完成事件
            result = {
                "session_id": self.session_id,
                "intent": final_state.get("current_intent", IntentType.UNKNOWN),
                "has_transcript": final_state.get("transcript_md") is not None,
                "has_analysis": final_state.get("gap_analysis_result") is not None
            }
            yield f'event: done\ndata: {__import__("json").dumps(result)}\n\n'
            
        except Exception as e:
            error_data = {"error": str(e)}
            yield f'event: error\ndata: {__import__("json").dumps(error_data)}\n\n'
            
    def get_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.state.get("messages", [])
        
    def clear(self) -> None:
        """清除会话状态（保留基本信息）"""
        year = self.state.get("enrollment_year")
        class_name = self.state.get("class_name")
        prefs = self.state.get("user_preferences", {})
        
        self.state = {
            "session_id": self.session_id,
            "messages": [],
            "current_intent": None,
            "uploaded_file": None,
            "transcript_data": None,
            "transcript_md": None,
            "gap_analysis_result": None,
            "user_preferences": prefs,
            "enrollment_year": year,
            "class_name": class_name,
            "context": {},
            "response": None,
            "error": None
        }


class ChatRunner:
    """对话运行器（管理所有会话）"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        enrollment_year: Optional[int] = None,
        class_name: Optional[str] = None
    ) -> ChatSession:
        """获取或创建会话"""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            # 更新入学信息（如果提供）
            if enrollment_year:
                session.set_enrollment_info(enrollment_year, class_name or session.state.get("class_name", ""))
            return session
        
        # 创建新会话
        new_session_id = session_id or str(uuid.uuid4())
        new_session = ChatSession(
            session_id=new_session_id,
            enrollment_year=enrollment_year,
            class_name=class_name
        )
        self.sessions[new_session_id] = new_session
        return new_session
        
    def run_chat(
        self,
        session_id: Optional[str] = None,
        message: str = "",
        enrollment_year: Optional[int] = None,
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行对话（非流式）"""
        session = self.get_or_create_session(session_id, enrollment_year, class_name)
        
        # 首次对话发送欢迎消息
        if not session.state.get("messages"):
            return {
                "session_id": session.session_id,
                "response": WELCOME_MESSAGE,
                "intent": IntentType.GENERAL_CHAT,
                "is_new_session": True
            }
        
        result = session.run(message)
        result["is_new_session"] = False
        return result
        
    async def run_chat_stream(
        self,
        session_id: Optional[str] = None,
        message: str = "",
        enrollment_year: Optional[int] = None,
        class_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """运行对话（流式）"""
        session = self.get_or_create_session(session_id, enrollment_year, class_name)
        
        # 首次对话
        if not session.state.get("messages"):
            yield 'event: start\ndata: {"status": "welcome"}\n\n'
            data = {"chunk": WELCOME_MESSAGE}
            yield f'event: chunk\ndata: {__import__("json").dumps(data)}\n\n'
            yield f'event: done\ndata: {{"session_id": "{session.session_id}", "is_new_session": true}}\n\n'
            return
        
        async for chunk in session.run_stream(message):
            yield chunk
            
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取指定会话"""
        return self.sessions.get(session_id)
        
    def get_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取会话历史"""
        session = self.sessions.get(session_id)
        if session:
            return session.get_history()
        return None
        
    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            return True
        return False
        
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
        
    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 60) -> int:
        """清理不活跃会话"""
        now = datetime.now()
        to_delete = []
        
        for session_id, session in self.sessions.items():
            inactive_time = (now - session.last_activity).total_seconds() / 60
            if inactive_time > max_inactive_minutes:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self.sessions[session_id]
            
        return len(to_delete)


# 全局运行器实例
_chat_runner = None


def get_chat_runner() -> ChatRunner:
    """获取全局对话运行器"""
    global _chat_runner
    if _chat_runner is None:
        _chat_runner = ChatRunner()
    return _chat_runner
