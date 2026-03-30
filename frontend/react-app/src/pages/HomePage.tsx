import { useState } from 'react';
import { Hero } from '../components/Hero';
import { UploadForm } from '../components/UploadForm';
import { ResultDisplay } from '../components/ResultDisplay';
import { GapAnalysisResponse } from '../types';
import { BookOpen, Scan, Brain, ChevronDown } from 'lucide-react';

export function HomePage() {
  const [analysisResult, setAnalysisResult] = useState<GapAnalysisResponse | null>(null);

  const handleAnalysisComplete = (result: GapAnalysisResponse) => {
    setAnalysisResult(result);
    setTimeout(() => {
      const resultSection = document.getElementById('analysis-result');
      resultSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const handleReset = () => {
    setAnalysisResult(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div>
      <Hero />
      
      {!analysisResult ? (
        <UploadForm onAnalysisComplete={handleAnalysisComplete} />
      ) : (
        <div id="analysis-result">
          <ResultDisplay result={analysisResult} onReset={handleReset} />
        </div>
      )}

      {/* How it works section */}
      {!analysisResult && (
        <section className="py-24 relative">
          {/* Background accent */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-900 to-navy-900 pointer-events-none" />
          
          <div className="relative max-w-6xl mx-auto px-6 lg:px-12">
            {/* Section header */}
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-cream-100/10 border border-cream-100/20 mb-6">
                <span className="w-2 h-2 bg-amber-400 rounded-full" />
                <span className="text-sm font-medium text-cream-100 tracking-wide">工作流程</span>
              </div>
              <h2 className="font-display text-4xl font-bold text-cream-50 mb-4">
                三步完成分析
              </h2>
              <p className="text-navy-300 max-w-lg mx-auto">
                简单几步，即可获取个性化的培养方案缺口分析报告
              </p>
            </div>

            {/* Steps */}
            <div className="grid md:grid-cols-3 gap-8">
              <StepCard
                number="01"
                icon={<BookOpen className="w-6 h-6" />}
                title="上传成绩单"
                description="选择入学年份，输入班级名称，上传 PDF 格式的成绩单文件"
              />
              <StepCard
                number="02"
                icon={<Scan className="w-6 h-6" />}
                title="智能解析"
                description="使用 PaddleOCR 云端 API 精准提取成绩单内容，AI 识别已修课程"
              />
              <StepCard
                number="03"
                icon={<Brain className="w-6 h-6" />}
                title="缺口分析"
                description="对比培养方案要求，智能分析学分缺口，生成个性化选课建议"
              />
            </div>

            {/* Scroll indicator */}
            <div className="flex justify-center mt-16">
              <button 
                onClick={() => document.getElementById('faq')?.scrollIntoView({ behavior: 'smooth' })}
                className="flex flex-col items-center gap-2 text-navy-400 hover:text-cream-100 transition-colors"
              >
                <span className="text-sm">了解更多</span>
                <ChevronDown className="w-5 h-5 animate-bounce" />
              </button>
            </div>
          </div>
        </section>
      )}

      {/* FAQ section */}
      {!analysisResult && (
        <section id="faq" className="py-24 bg-cream-50">
          <div className="max-w-3xl mx-auto px-6 lg:px-12">
            {/* Section header */}
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-navy-100 mb-6">
                <span className="w-2 h-2 bg-amber-500 rounded-full" />
                <span className="text-sm font-medium text-navy-600 tracking-wide">常见问题</span>
              </div>
              <h2 className="font-display text-4xl font-bold text-navy-900 mb-4">
                有疑问？
              </h2>
            </div>

            {/* FAQ items */}
            <div className="space-y-4">
              <FAQItem
                question="支持哪些格式的成绩单？"
                answer="目前支持 PDF 格式的成绩单。建议从教务系统直接导出 PDF 文件，以获得最佳的识别效果。"
              />
              <FAQItem
                question="数据安全如何保障？"
                answer="成绩单仅用于分析，不会保存在服务器上。分析完成后，所有临时文件会被立即删除。"
              />
              <FAQItem
                question="分析结果准确吗？"
                answer="系统使用 AI 智能识别和对比分析，但建议您核对分析结果，最终选课请以教务系统为准。"
              />
              <FAQItem
                question="支持哪些年级？"
                answer="目前支持 2021 至 2025 级的未央书院学生。"
              />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

interface StepCardProps {
  number: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

function StepCard({ number, icon, title, description }: StepCardProps) {
  return (
    <div className="relative group">
      {/* Connector line */}
      <div className="hidden md:block absolute top-12 left-full w-full h-px bg-gradient-to-r from-amber-400/50 to-transparent" />
      
      <div className="relative bg-navy-800/50 backdrop-blur-sm border border-navy-700 p-8 hover:border-amber-400/50 transition-all duration-300 hover:-translate-y-1">
        {/* Number */}
        <div className="font-display text-5xl font-bold text-navy-600 mb-6">
          {number}
        </div>
        
        {/* Icon */}
        <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-white mb-6">
          {icon}
        </div>
        
        {/* Content */}
        <h3 className="font-display text-xl font-semibold text-cream-100 mb-3">
          {title}
        </h3>
        <p className="text-navy-300 text-sm leading-relaxed">
          {description}
        </p>
        
        {/* Decorative corner */}
        <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-navy-600 group-hover:border-amber-400/50 transition-colors" />
        <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-navy-600 group-hover:border-amber-400/50 transition-colors" />
      </div>
    </div>
  );
}

interface FAQItemProps {
  question: string;
  answer: string;
}

function FAQItem({ question, answer }: FAQItemProps) {
  return (
    <details className="group bg-white border border-navy-100 open:border-amber-200 transition-all">
      <summary className="flex items-center justify-between p-6 cursor-pointer list-none select-none">
        <span className="font-display font-semibold text-navy-800 pr-4">{question}</span>
        <span className="flex-shrink-0 w-8 h-8 bg-navy-50 flex items-center justify-center group-open:bg-amber-100 transition-colors">
          <svg 
            className="w-4 h-4 text-navy-600 transition-transform group-open:rotate-180" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </summary>
      <div className="px-6 pb-6 text-navy-600 leading-relaxed">
        {answer}
      </div>
    </details>
  );
}
