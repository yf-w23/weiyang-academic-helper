import axios, { AxiosInstance, AxiosError } from 'axios';
import { 
  GapAnalysisResponse, 
  ApiError, 
  ChatRequest, 
  ChatResponse, 
  ChatMessage,
  UploadTranscriptResponse 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 120000,
      headers: {
        'Accept': 'application/json',
      },
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError: ApiError = {
          message: '请求失败，请稍后重试',
          status: error.response?.status,
        };

        if (error.code === 'ECONNABORTED') {
          apiError.message = '请求超时，请稍后重试';
        } else if (!error.response) {
          apiError.message = '无法连接到服务器，请检查网络连接';
        } else if (error.response.status === 400) {
          const detail = (error.response.data as { detail?: string })?.detail;
          apiError.message = detail || '请求参数错误';
        } else if (error.response.status >= 500) {
          apiError.message = '服务器内部错误，请稍后重试';
        }

        return Promise.reject(apiError);
      }
    );
  }

  // ============ 原有API ============
  
  async uploadTranscript(file: File): Promise<GapAnalysisResponse> {
    const formData = new FormData();
    formData.append('transcript', file);

    const response = await this.client.post<GapAnalysisResponse>(
      '/api/advise/gap-analysis',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.client.get('/health', { timeout: 5000 });
      return response.status === 200;
    } catch {
      return false;
    }
  }

  // ============ 聊天API ============

  /**
   * 非流式对话
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>(
      '/api/chat/message',
      request
    );
    return response.data;
  }

  /**
   * 流式对话（SSE）
   */
  async sendMessageStream(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: (fullResponse: ChatResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            const data = trimmedLine.slice(6);
            
            if (data === '[DONE]') {
              try {
                const parsedData = JSON.parse(fullContent);
                onComplete(parsedData);
              } catch {
                onComplete({
                  session_id: request.session_id || '',
                  response: fullContent,
                  intent: 'chat',
                });
              }
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullContent += parsed.content;
                onChunk(parsed.content);
              }
            } catch {
              fullContent += data;
              onChunk(data);
            }
          }
        }
      }

      if (buffer.trim()) {
        const trimmedLine = buffer.trim();
        if (trimmedLine.startsWith('data: ')) {
          const data = trimmedLine.slice(6);
          if (data !== '[DONE]') {
            fullContent += data;
          }
        }
      }

      onComplete({
        session_id: request.session_id || '',
        response: fullContent,
        intent: 'chat',
      });
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Stream error'));
    }
  }

  /**
   * 上传成绩单（聊天上下文）
   */
  async uploadTranscriptChat(
    file: File,
    sessionId?: string
  ): Promise<UploadTranscriptResponse> {
    const formData = new FormData();
    formData.append('transcript', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    console.log('[API] Uploading file:', file.name, 'size:', file.size, 'bytes');

    try {
      const response = await this.client.post<UploadTranscriptResponse>(
        '/api/chat/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes for OCR + LLM processing
        }
      );
      console.log('[API] Upload success:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('[API] Upload error:', error);
      if (error.response) {
        console.error('[API] Error response:', error.response.status, error.response.data);
        throw new Error(error.response.data?.detail || `上传失败 (${error.response.status})`);
      }
      throw error;
    }
  }

  /**
   * 获取对话历史
   */
  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await this.client.get<ChatMessage[]>(
      `/api/chat/history/${sessionId}`
    );
    return response.data;
  }

  /**
   * 获取所有会话列表
   */
  async getSessions(): Promise<{ id: string; title: string; updated_at: string }[]> {
    const response = await this.client.get('/api/chat/sessions');
    return response.data;
  }

  /**
   * 清除会话
   */
  async clearSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/chat/session/${sessionId}`);
  }
}

export const apiClient = new ApiClient();
