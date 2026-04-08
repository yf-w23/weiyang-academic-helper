import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  ChatSession, 
  ChatMessage, 
  ChatRequest,
} from '../types';
import { apiClient } from '../api/client';

interface ChatStore {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  streamingContent: string;
  isStreaming: boolean;
  
  // 会话管理
  createSession: () => string;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => void;
  updateSessionTitle: (id: string, title: string) => void;
  
  // 消息管理
  addMessage: (sessionId: string, message: ChatMessage) => void;
  updateMessage: (sessionId: string, messageId: string, content: string) => void;
  clearMessages: (sessionId: string) => void;
  
  // 发送消息
  sendMessage: (content: string) => Promise<void>;
  sendMessageStream: (content: string) => Promise<void>;
  
  // 文件上传
  uploadFile: (file: File) => Promise<void>;
  
  // 流式输出
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  clearStreamingContent: () => void;
}

const generateId = () => Math.random().toString(36).substring(2, 15);

const createNewSession = (): ChatSession => {
  const now = new Date().toISOString();
  return {
    id: generateId(),
    title: '新对话',
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
};

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      isLoading: false,
      streamingContent: '',
      isStreaming: false,

      // ============ 会话管理 ============
      
      createSession: () => {
        const newSession = createNewSession();
        set((state) => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
        }));
        return newSession.id;
      },

      selectSession: (id: string) => {
        set({ currentSessionId: id });
      },

      deleteSession: (id: string) => {
        set((state) => {
          const newSessions = state.sessions.filter((s) => s.id !== id);
          return {
            sessions: newSessions,
            currentSessionId: 
              state.currentSessionId === id 
                ? (newSessions[0]?.id || null) 
                : state.currentSessionId,
          };
        });
      },

      updateSessionTitle: (id: string, title: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, title, updatedAt: new Date().toISOString() } : s
          ),
        }));
      },

      // ============ 消息管理 ============
      
      addMessage: (sessionId: string, message: ChatMessage) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { 
                  ...s, 
                  messages: [...s.messages, message],
                  updatedAt: new Date().toISOString(),
                  title: s.messages.length === 0 && message.role === 'user' 
                    ? message.content.slice(0, 20) + (message.content.length > 20 ? '...' : '')
                    : s.title
                }
              : s
          ),
        }));
      },

      updateMessage: (sessionId: string, messageId: string, content: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: s.messages.map((m) =>
                    m.id === messageId ? { ...m, content } : m
                  ),
                  updatedAt: new Date().toISOString(),
                }
              : s
          ),
        }));
      },

      clearMessages: (sessionId: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [], updatedAt: new Date().toISOString() }
              : s
          ),
        }));
      },

      // ============ 流式输出 ============
      
      setStreamingContent: (content: string) => {
        set({ streamingContent: content });
      },

      appendStreamingContent: (chunk: string) => {
        set((state) => ({
          streamingContent: state.streamingContent + chunk,
        }));
      },

      clearStreamingContent: () => {
        set({ streamingContent: '', isStreaming: false });
      },

      // ============ 发送消息 ============
      
      sendMessage: async (content: string) => {
        const { currentSessionId, addMessage } = get();
        
        if (!currentSessionId) {
          get().createSession();
        }
        
        const sessionId = get().currentSessionId!;
        
        // 添加用户消息
        const userMessage: ChatMessage = {
          id: generateId(),
          role: 'user',
          content,
          timestamp: new Date().toISOString(),
          type: 'text',
        };
        addMessage(sessionId, userMessage);

        set({ isLoading: true });

        try {
          const request: ChatRequest = {
            session_id: sessionId,
            message: content,
          };

          const response = await apiClient.sendMessage(request);

          // 添加助手消息
          const assistantMessage: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: response.response,
            timestamp: new Date().toISOString(),
            type: response.analysis_result ? 'analysis' : 'text',
            metadata: {
              analysisResult: response.analysis_result,
              recommendations: response.recommendations,
            },
          };
          addMessage(sessionId, assistantMessage);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '发送消息失败';
          const errorMsg: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: `抱歉，发生了错误：${errorMessage}`,
            timestamp: new Date().toISOString(),
            type: 'text',
          };
          addMessage(sessionId, errorMsg);
        } finally {
          set({ isLoading: false });
        }
      },

      sendMessageStream: async (content: string) => {
        const { currentSessionId, addMessage, appendStreamingContent, clearStreamingContent } = get();
        
        if (!currentSessionId) {
          get().createSession();
        }
        
        const sessionId = get().currentSessionId!;
        
        // 添加用户消息
        const userMessage: ChatMessage = {
          id: generateId(),
          role: 'user',
          content,
          timestamp: new Date().toISOString(),
          type: 'text',
        };
        addMessage(sessionId, userMessage);

        set({ isLoading: true, isStreaming: true });
        clearStreamingContent();

        const streamingMessageId = generateId();

        try {
          const request: ChatRequest = {
            session_id: sessionId,
            message: content,
          };

          await apiClient.sendMessageStream(
            request,
            (chunk) => {
              appendStreamingContent(chunk);
            },
            (response) => {
              // 流式传输完成
              const assistantMessage: ChatMessage = {
                id: streamingMessageId,
                role: 'assistant',
                content: response.response || get().streamingContent,
                timestamp: new Date().toISOString(),
                type: response.analysis_result ? 'analysis' : 'text',
                metadata: {
                  analysisResult: response.analysis_result,
                  recommendations: response.recommendations,
                },
              };
              addMessage(sessionId, assistantMessage);
              clearStreamingContent();
              set({ isLoading: false, isStreaming: false });
            },
            (error) => {
              const errorMsg: ChatMessage = {
                id: streamingMessageId,
                role: 'assistant',
                content: `抱歉，发生了错误：${error.message}`,
                timestamp: new Date().toISOString(),
                type: 'text',
              };
              addMessage(sessionId, errorMsg);
              clearStreamingContent();
              set({ isLoading: false, isStreaming: false });
            }
          );
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '发送消息失败';
          const errorMsg: ChatMessage = {
            id: streamingMessageId,
            role: 'assistant',
            content: `抱歉，发生了错误：${errorMessage}`,
            timestamp: new Date().toISOString(),
            type: 'text',
          };
          addMessage(sessionId, errorMsg);
          clearStreamingContent();
          set({ isLoading: false, isStreaming: false });
        }
      },

      // ============ 文件上传 ============
      
      uploadFile: async (file: File) => {
        const { currentSessionId, addMessage, createSession } = get();
        
        let sessionId = currentSessionId;
        if (!sessionId) {
          sessionId = createSession();
        }

        // 添加文件消息
        const fileMessage: ChatMessage = {
          id: generateId(),
          role: 'user',
          content: `上传文件：${file.name}`,
          timestamp: new Date().toISOString(),
          type: 'file',
          metadata: {
            fileName: file.name,
          },
        };
        addMessage(sessionId, fileMessage);

        set({ isLoading: true });

        try {
          const response = await apiClient.uploadTranscriptChat(
            file,
            sessionId
          );

          // 添加助手消息
          const assistantMessage: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: response.response,
            timestamp: new Date().toISOString(),
            type: response.analysis_result ? 'analysis' : 'text',
            metadata: {
              analysisResult: response.analysis_result,
              recommendations: response.recommendations,
            },
          };
          addMessage(sessionId, assistantMessage);
        } catch (error: any) {
          console.error('[ChatStore] Upload error:', error);
          const errorMessage = error?.message || error?.response?.data?.detail || '上传失败';
          const errorMsg: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: `抱歉，文件上传失败：${errorMessage}`,
            timestamp: new Date().toISOString(),
            type: 'text',
          };
          addMessage(sessionId, errorMsg);
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'chat-store',
      partialize: (state) => ({ sessions: state.sessions }),
    }
  )
);
