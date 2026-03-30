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
