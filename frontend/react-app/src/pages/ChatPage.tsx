import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../store/chatStore';
import { 
  Send, 
  Plus, 
  Trash2, 
  FileUp, 
  MessageSquare, 
  Loader2,
  ChevronLeft,
  Menu,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

export function ChatPage() {
  const [input, setInput] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    sessions,
    currentSessionId,
    isLoading,
    streamingContent,
    isStreaming,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
    uploadFile,
  } = useChatStore();

  const currentSession = sessions.find(s => s.id === currentSessionId);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, streamingContent]);

  // 如果没有会话，创建一个
  useEffect(() => {
    if (sessions.length === 0) {
      createSession();
    }
  }, [sessions.length]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    await sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadFile(file);
    e.target.value = '';
  };

  const handleNewChat = () => {
    createSession();
    setIsSidebarOpen(false);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧边栏 */}
      <div 
        className={`${isSidebarOpen ? 'w-64' : 'w-0'} 
          transition-all duration-300 bg-white border-r border-gray-200 
          flex flex-col overflow-hidden`}
      >
        {/* 新建对话按钮 */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 
              bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            新建对话
          </button>
        </div>

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto p-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => selectSession(session.id)}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                ${session.id === currentSessionId 
                  ? 'bg-blue-50 text-blue-700' 
                  : 'hover:bg-gray-100 text-gray-700'}`}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 truncate text-sm">
                {session.title}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(session.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 
                  rounded transition-all"
              >
                <Trash2 className="w-3 h-3 text-red-500" />
              </button>
            </div>
          ))}
        </div>

        {/* 底部留白 */}
        <div className="p-4 border-t border-gray-200">
          <p className="text-xs text-gray-400 text-center">
            上传成绩单 · 通识课分析 · 选课推荐
          </p>
        </div>
      </div>

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部导航 */}
        <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isSidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="font-semibold text-gray-800">学业规划助手</h1>
          </div>
          <div className="text-sm text-gray-500">
            {currentSession?.title}
          </div>
        </div>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {currentSession?.messages.length === 0 && (
            <div className="text-center py-20">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                你好！我是你的学业规划助手
              </h2>
              <p className="text-gray-600 max-w-md mx-auto">
                我可以帮你分析成绩单、检查培养方案缺口、分析通识课完成情况、
                推荐高评分课程等。
                <br />
                请先上传成绩单，或向我提问。
              </p>
            </div>
          )}

          {currentSession?.messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {message.type === 'file' ? (
                  <div className="flex items-center gap-2">
                    <FileUp className="w-4 h-4" />
                    <span>{message.content}</span>
                  </div>
                ) : (
                  <div className="markdown-content max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{message.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* 流式输出内容 */}
          {isStreaming && streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200">
                <div className="markdown-content max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{streamingContent}</ReactMarkdown>
                </div>
                <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
              </div>
            </div>
          )}

          {/* 加载状态 */}
          {isLoading && !isStreaming && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto flex gap-2">
            {/* 文件上传按钮 */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="p-3 border border-gray-300 rounded-xl hover:bg-gray-50 
                transition-colors disabled:opacity-50"
              title="上传成绩单"
            >
              <FileUp className="w-5 h-5 text-gray-600" />
            </button>

            {/* 文本输入 */}
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              rows={1}
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl 
                focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none
                disabled:opacity-50"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />

            {/* 发送按钮 */}
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="px-4 py-3 bg-blue-600 text-white rounded-xl 
                hover:bg-blue-700 transition-colors disabled:opacity-50
                disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          {/* 快捷操作 */}
          <div className="max-w-4xl mx-auto mt-3 flex gap-2 flex-wrap justify-center">
            {[
            '分析我的培养方案',
            '推荐下学期课程',
            '我通识课修满了吗',
            '推荐一些给分好的通识课',
            '查看未修必修课',
          ].map((text) => (
              <button
                key={text}
                onClick={() => {
                  setInput(text);
                }}
                className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 
                  rounded-full hover:bg-gray-200 transition-colors"
              >
                {text}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
