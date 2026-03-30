"""
未央书院培养方案缺口分析助手 - Streamlit 前端（清新风格）
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PAGE_CONFIG, SUPPORTED_YEARS, BACKEND_URL
from api_client import upload_transcript, check_backend_health


# 页面配置
st.set_page_config(**PAGE_CONFIG)

# 自定义 CSS
st.markdown("""
<style>
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:disabled {
        background: #cbd5e1;
        color: #64748b;
    }
    .step-box {
        background: #f1f5f9;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        color: #475569;
        display: inline-block;
        margin-right: 0.5rem;
    }
    .step-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .info-text {
        color: #f59e0b;
        text-align: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_page():
    """初始化页面"""
    col1, col2 = st.columns([0.08, 0.92])
    with col1:
        st.markdown("🎓")
    with col2:
        st.markdown('<h1 class="main-title">未央书院培养方案缺口分析助手</h1>', unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">智能分析您的学业进度，发现课程缺口，规划选课方向</p>', unsafe_allow_html=True)
    st.divider()


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### ⚙️ 系统配置")
        
        backend_url = st.text_input(
            "后端 API 地址",
            value=st.session_state.get("backend_url", BACKEND_URL),
        )
        st.session_state["backend_url"] = backend_url
        
        if st.button("检查后端连接", use_container_width=True):
            with st.spinner("检查中..."):
                if check_backend_health(backend_url):
                    st.success("✅ 后端连接正常")
                else:
                    st.error("❌ 无法连接到后端")
        
        st.divider()
        
        st.markdown("### 📖 使用步骤")
        steps = [
            "选择入学年份",
            "输入班级名称（如：未央-机械31）",
            "上传成绩单 PDF",
            "点击开始分析",
        ]
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}.** {step}")
        
        st.divider()
        st.caption("支持 PDF 格式，建议文件大小 < 10MB")


def render_main_form():
    """渲染主表单"""
    # 步骤指示器
    cols = st.columns(3)
    with cols[0]:
        st.markdown('<span class="step-box step-active">1 基本信息</span>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<span class="step-box">2 上传成绩单</span>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<span class="step-box">3 智能分析</span>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 表单区域
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("📅 **入学年份**")
            year = st.selectbox(
                "选择入学年份",
                options=SUPPORTED_YEARS,
                index=2,
                label_visibility="collapsed",
            )
        
        with col2:
            st.markdown("🏫 **班级名称**")
            class_name = st.text_input(
                "输入班级",
                placeholder="例如：未央-机械31",
                label_visibility="collapsed",
            )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 文件上传
    with st.container():
        st.markdown("📄 **成绩单 PDF**")
        uploaded_file = st.file_uploader(
            "上传成绩单",
            type=["pdf"],
            label_visibility="collapsed",
        )
        
        if uploaded_file is not None:
            st.success(f"✅ 已选择：{uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        else:
            st.info("📎 拖拽文件到此处，或点击上传（支持 PDF 格式）")
    
    return year, class_name, uploaded_file


def perform_analysis(year: int, class_name: str, uploaded_file):
    """执行分析"""
    backend_url = st.session_state.get("backend_url", BACKEND_URL)
    
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0, text="正在初始化...")
    
    import time
    
    try:
        progress_bar.progress(30, text="正在解析成绩单...")
        time.sleep(0.3)
        
        result = upload_transcript(
            year=year,
            class_name=class_name,
            pdf_file=uploaded_file,
            backend_url=backend_url,
        )
        
        progress_bar.progress(70, text="正在进行智能分析...")
        time.sleep(0.3)
        
        progress_bar.progress(100, text="分析完成！")
        time.sleep(0.2)
        
        progress_placeholder.empty()
        return result
        
    except Exception as e:
        progress_placeholder.empty()
        st.error(f"❌ 分析失败：{str(e)}")
        return None


def render_result(result: dict):
    """渲染分析结果"""
    st.divider()
    
    st.markdown("### 📊 培养方案缺口分析报告")
    
    with st.container():
        analysis_result = result.get("analysis_result", "")
        if analysis_result:
            st.markdown(analysis_result)
        else:
            st.info("暂无分析结果")
    
    st.success("✅ 分析已完成！请查看上方报告")


def main():
    """主函数"""
    init_page()
    render_sidebar()
    
    year, class_name, uploaded_file = render_main_form()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 分析按钮
    is_ready = uploaded_file is not None and class_name.strip()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button(
            "🚀 开始智能分析",
            type="primary",
            disabled=not is_ready,
            use_container_width=True,
        )
    
    # 提示信息
    if not uploaded_file:
        st.markdown('<p class="info-text">⚠️ 请先上传成绩单 PDF 文件</p>', unsafe_allow_html=True)
    elif not class_name.strip():
        st.markdown('<p class="info-text">⚠️ 请输入班级名称</p>', unsafe_allow_html=True)
    
    # 执行分析
    if analyze_button:
        result = perform_analysis(year, class_name, uploaded_file)
        if result:
            render_result(result)


if __name__ == "__main__":
    main()
