import axios, { AxiosInstance, AxiosError } from 'axios';
import { GapAnalysisResponse, ApiError } from '../types';

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

  async uploadTranscript(
    year: number,
    className: string,
    file: File
  ): Promise<GapAnalysisResponse> {
    const formData = new FormData();
    formData.append('enrollment_year', year.toString());
    formData.append('class_name', className);
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
}

export const apiClient = new ApiClient();
