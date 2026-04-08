import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  FileText,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { apiClient } from '../api/client';
import { GapAnalysisResponse } from '../types';

interface UploadFormProps {
  onAnalysisComplete: (result: GapAnalysisResponse) => void;
}

export function UploadForm({ onAnalysisComplete }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      if (selectedFile.type !== 'application/pdf' && !selectedFile.name.endsWith('.pdf')) {
        setError('请上传 PDF 格式的文件');
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('文件大小不能超过 10MB');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  });

  const handleAnalyze = async () => {
    if (!file) {
      setError('请上传成绩单');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setProgress(10);

    try {
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 12;
        });
      }, 600);

      const result = await apiClient.uploadTranscript(file);

      clearInterval(progressInterval);
      setProgress(100);
      onAnalysisComplete(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '分析失败，请稍后重试';
      setError(errorMessage);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClearFile = () => {
    setFile(null);
    setError(null);
  };

  const isReady = !!file;

  return (
    <section id="analysis-form" className="py-24 relative">
      {/* Section background accent */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-50/30 to-transparent pointer-events-none" />
      
      <div className="max-w-4xl mx-auto px-6 lg:px-12 relative">
        {/* Section header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-cream-100 border border-navy-100 mb-6">
            <span className="w-2 h-2 bg-amber-500 rounded-full" />
            <span className="text-sm font-medium text-navy-600 tracking-wide">开始分析</span>
          </div>
          <h2 className="font-display text-4xl font-bold text-navy-900 mb-4">
            上传成绩单
          </h2>
          <p className="text-navy-500 max-w-lg mx-auto">
            上传 PDF 成绩单，AI 将自动识别你的年级班级并分析培养方案缺口
          </p>
        </div>

        {/* Main form card */}
        <div className="academic-card relative">
          {/* Decorative corners */}
          <div className="absolute -top-3 -left-3 w-6 h-6 border-t-2 border-l-2 border-amber-400" />
          <div className="absolute -top-3 -right-3 w-6 h-6 border-t-2 border-r-2 border-amber-400" />
          <div className="absolute -bottom-3 -left-3 w-6 h-6 border-b-2 border-l-2 border-amber-400" />
          <div className="absolute -bottom-3 -right-3 w-6 h-6 border-b-2 border-r-2 border-amber-400" />

          {/* Progress steps */}
          <div className="px-8 pt-8 pb-6 border-b border-navy-100">
            <div className="flex items-center justify-center">
              <StepIndicator 
                number={1} 
                label="上传成绩单" 
                active={true} 
                completed={!!file} 
              />
              <div className={cn(
                "w-16 h-px mx-4 transition-colors duration-500",
                isAnalyzing ? "bg-amber-400 animate-pulse" : "bg-navy-200"
              )} />
              <StepIndicator 
                number={2} 
                label="智能分析" 
                active={isAnalyzing} 
                completed={false} 
              />
            </div>
          </div>

          <div className="p-8">
            {/* File upload area */}
            <div className="space-y-3 mb-8">
              <label className="flex items-center gap-2 text-sm font-medium text-navy-700">
                <FileText className="w-4 h-4 text-amber-600" />
                成绩单 PDF
              </label>

              {!file ? (
                <div
                  {...getRootProps()}
                  className={cn(
                    'relative border-2 border-dashed rounded-none p-10 text-center cursor-pointer transition-all duration-300',
                    isDragActive
                      ? 'border-amber-500 bg-amber-50/50'
                      : 'border-navy-200 hover:border-navy-300 bg-cream-50/50'
                  )}
                >
                  <input {...getInputProps()} />
                  
                  {/* Decorative corner accents */}
                  <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-navy-200" />
                  <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-navy-200" />
                  <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-navy-200" />
                  <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-navy-200" />
                  
                  <div className="flex flex-col items-center">
                    <div className={cn(
                      "w-16 h-16 flex items-center justify-center mb-4 transition-colors duration-300",
                      isDragActive ? "bg-amber-100" : "bg-navy-100"
                    )}>
                      <Upload className={cn(
                        "w-8 h-8 transition-colors duration-300",
                        isDragActive ? "text-amber-600" : "text-navy-400"
                      )} />
                    </div>
                    <p className="font-medium text-navy-700 mb-1">
                      {isDragActive ? '松开以上传文件' : '点击或拖拽上传成绩单'}
                    </p>
                    <p className="text-sm text-navy-400">支持 PDF 格式，建议文件小于 10MB</p>
                  </div>
                </div>
              ) : (
                <div className="relative border-2 border-amber-300 bg-amber-50/30 p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-navy-800 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-7 h-7 text-cream-50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-navy-800 truncate">{file.name}</p>
                      <p className="text-sm text-navy-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    {!isAnalyzing && (
                      <button
                        onClick={handleClearFile}
                        className="p-2 hover:bg-navy-100 transition-colors"
                      >
                        <X className="w-5 h-5 text-navy-500" />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-8 p-4 bg-red-50 border-l-4 border-red-400 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Progress bar */}
            {isAnalyzing && (
              <div className="mb-8 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-navy-700">正在分析...</span>
                  <span className="text-sm text-navy-500 font-mono">{Math.min(Math.round(progress), 99)}%</span>
                </div>
                <div className="h-2 bg-navy-100 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-navy-600 to-amber-500 transition-all duration-300"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                  />
                </div>
                <div className="flex items-center gap-3 text-sm text-navy-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>正在解析成绩单并进行智能分析，请稍候...</span>
                </div>
              </div>
            )}

            {/* Submit button */}
            <button
              onClick={handleAnalyze}
              disabled={!isReady || isAnalyzing}
              className={cn(
                'w-full py-5 font-medium flex items-center justify-center gap-3 transition-all duration-300',
                !isReady || isAnalyzing
                  ? 'bg-navy-200 text-navy-400 cursor-not-allowed'
                  : 'btn-primary'
              )}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  分析中...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  开始智能分析
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-8 text-center">
          <p className="text-sm text-navy-400">
            建议从教务系统导出 PDF 格式的成绩单，以获得最佳识别效果
          </p>
        </div>
      </div>
    </section>
  );
}

interface StepIndicatorProps {
  number: number;
  label: string;
  active: boolean;
  completed: boolean;
}

function StepIndicator({ number, label, active, completed }: StepIndicatorProps) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={cn(
          'w-10 h-10 flex items-center justify-center font-display font-bold text-lg transition-all duration-300',
          completed
            ? 'bg-amber-500 text-white'
            : active
            ? 'bg-navy-800 text-white'
            : 'bg-navy-100 text-navy-400'
        )}
      >
        {completed ? <CheckCircle className="w-5 h-5" /> : number}
      </div>
      <span
        className={cn(
          'text-xs font-medium transition-colors duration-300',
          active || completed ? 'text-navy-700' : 'text-navy-400'
        )}
      >
        {label}
      </span>
    </div>
  );
}
