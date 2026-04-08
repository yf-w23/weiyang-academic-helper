export interface GapAnalysisRequest {
  enrollment_year: number;
  class_name: string;
}

export interface GapAnalysisResponse {
  success: boolean;
  message: string;
  analysis_result: string;
}

export interface ApiError {
  message: string;
  status?: number;
}

// ============ 聊天相关类型 ============

export interface CourseRecommendation {
  course_id: string;
  course_name: string;
  credits: number;
  priority: 'high' | 'medium' | 'low';
  reason: string;
  blocking_factor: number;
  rating?: number;
  semester?: string;
}

export interface CourseGroupStatus {
  group_name: string;
  required_credits: number;
  completed_credits: number;
  remaining_credits: number;
  completion_rate: number;
  courses: {
    course_name: string;
    credits: number;
    status: 'completed' | 'in_progress' | 'not_taken';
  }[];
}

export interface GapAnalysisResult {
  total_credits_required: number;
  total_credits_completed: number;
  total_credits_remaining: number;
  overall_completion_rate: number;
  course_groups: CourseGroupStatus[];
  mandatory_courses_missing: string[];
  recommendations?: CourseRecommendation[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  type?: 'text' | 'file' | 'analysis' | 'recommendation';
  metadata?: {
    fileName?: string;
    analysisResult?: GapAnalysisResult;
    recommendations?: CourseRecommendation[];
  };
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatRequest {
  session_id?: string;
  message: string;
  enrollment_year?: number;
  class_name?: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  intent: string;
  analysis_result?: GapAnalysisResult;
  recommendations?: CourseRecommendation[];
}

export interface UploadTranscriptResponse {
  session_id: string;
  response: string;
  intent: string;
  analysis_result?: GapAnalysisResult;
  recommendations?: CourseRecommendation[];
}
