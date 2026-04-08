"""
对话API路由 - 多轮对话接口
"""
import os
import tempfile
import traceback
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agent.chat_runner import get_chat_runner, ChatRunner
from backend.agent.chat_graph import IntentType
from backend.agent.tools import extract_transcript_from_pdf
from backend.config import settings
from backend.services.transcript_parser import extract_student_info


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """对话请求模型"""
    session_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    message: str = Field(..., min_length=1, description="用户消息")
    enrollment_year: Optional[int] = Field(None, ge=2021, le=2025, description="入学年份")
    class_name: Optional[str] = Field(None, description="班级名称，如'未央-电11'")


class ChatResponse(BaseModel):
    """对话响应模型"""
    session_id: str = Field(..., description="会话ID")
    response: str = Field(..., description="助手回复")
    intent: str = Field(..., description="识别的意图")
    is_new_session: bool = Field(False, description="是否为新会话")
    has_transcript: bool = Field(False, description="是否已上传成绩单")
    has_analysis: bool = Field(False, description="是否已完成缺口分析")


class ChatHistoryResponse(BaseModel):
    """对话历史响应模型"""
    session_id: str = Field(..., description="会话ID")
    messages: list = Field(default_factory=list, description="消息列表")


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    对话消息接口（非流式）
    
    - 发送消息给助手
    - 如需创建新会话，不传递session_id
    - 首次对话会返回欢迎消息
    """
    try:
        runner = get_chat_runner()
        result = runner.run_chat(
            session_id=request.session_id,
            message=request.message,
            enrollment_year=request.enrollment_year,
            class_name=request.class_name
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        print(f"[ERROR] chat_message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话处理失败: {str(e)}"
        )


@router.post("/message/stream")
async def chat_message_stream(request: ChatRequest):
    """
    对话消息接口（SSE流式）
    
    返回 Server-Sent Events 流，格式：
    - event: start - 开始处理
    - event: chunk - 内容片段 {"chunk": "..."}
    - event: done - 完成 {"session_id": "...", "intent": "..."}
    - event: error - 错误 {"error": "..."}
    """
    try:
        runner = get_chat_runner()
        
        async def event_generator():
            async for chunk in runner.run_chat_stream(
                session_id=request.session_id,
                message=request.message,
                enrollment_year=request.enrollment_year,
                class_name=request.class_name
            ):
                yield chunk
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        print(f"[ERROR] chat_message_stream: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式对话处理失败: {str(e)}"
        )


@router.post("/upload")
async def upload_transcript(
    session_id: Optional[str] = Form(None),
    transcript: UploadFile = File(...)
):
    """
    上传成绩单PDF
    
    - 上传成绩单后会自动解析
    - 自动从成绩单中识别入学年份和班级
    - 可以在对话中请求缺口分析
    """
    print(f"[UPLOAD] 收到上传请求: session_id={session_id}")
    print(f"[UPLOAD] 文件名: {transcript.filename}, content_type: {transcript.content_type}")
    
    # 验证文件类型
    if transcript.content_type != "application/pdf":
        if not transcript.filename or not transcript.filename.endswith(".pdf"):
            print(f"[UPLOAD] 错误: 文件类型不正确")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持PDF格式文件"
            )
    
    temp_file_path = None
    try:
        # 保存临时文件
        content = await transcript.read()
        print(f"[UPLOAD] 读取文件内容: {len(content)} bytes")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp:
            tmp.write(content)
            temp_file_path = tmp.name
            print(f"[UPLOAD] 临时文件保存: {temp_file_path}")
        
        # 从成绩单中提取年级和班级信息
        transcript_md = extract_transcript_from_pdf(temp_file_path)
        info = extract_student_info(transcript_md)
        enrollment_year_str = info.get("year")
        class_name = info.get("class_name")
        
        if not enrollment_year_str or not class_name:
            missing = []
            if not enrollment_year_str:
                missing.append("入学年份")
            if not class_name:
                missing.append("班级")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法从成绩单中识别{'、'.join(missing)}信息，请确认上传的是有效的清华大学成绩单"
            )
        
        enrollment_year = int(enrollment_year_str)
        print(f"[UPLOAD] 自动识别: year={enrollment_year}, class={class_name}")
        
        # 获取或创建会话
        runner = get_chat_runner()
        session = runner.get_or_create_session(session_id, enrollment_year, class_name)
        print(f"[UPLOAD] 会话创建/获取成功: {session.session_id}")
        
        session.set_uploaded_file(temp_file_path)
        session.state["transcript_md"] = transcript_md
        print(f"[UPLOAD] 设置上传文件成功")
        
        # 触发文件处理
        print(f"[UPLOAD] 开始处理文件...")
        result = session.run("我上传了成绩单")
        print(f"[UPLOAD] 文件处理完成")
        
        return {
            "success": True,
            "session_id": session.session_id,
            "message": f"成绩单上传并解析成功，已识别为{class_name}（{enrollment_year}级）",
            "response": result["response"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD] 错误: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    获取对话历史
    
    返回指定会话的所有消息记录
    """
    runner = get_chat_runner()
    history = runner.get_history(session_id)
    
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=history
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    清除会话
    
    清除会话的对话历史，但保留用户偏好设置
    """
    runner = get_chat_runner()
    
    if runner.clear_session(session_id):
        return {
            "success": True,
            "message": "会话已清除"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="会话不存在"
    )


@router.delete("/session/{session_id}/delete")
async def delete_session(session_id: str):
    """
    删除会话
    
    完全删除会话及其所有数据
    """
    runner = get_chat_runner()
    
    if runner.delete_session(session_id):
        return {
            "success": True,
            "message": "会话已删除"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="会话不存在"
    )
