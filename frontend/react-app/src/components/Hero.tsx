import { ArrowDown, Sparkles, Target, BookMarked } from 'lucide-react';

export function Hero() {
  const scrollToForm = () => {
    document.getElementById('analysis-form')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Large geometric shapes */}
        <div className="absolute top-[10%] right-[5%] w-[600px] h-[600px] border border-navy-100 rounded-full opacity-30 animate-pulse-slow" />
        <div className="absolute top-[20%] right-[15%] w-[400px] h-[400px] border border-navy-100 rounded-full opacity-20" />
        <div className="absolute bottom-[10%] left-[5%] w-[300px] h-[300px] bg-gradient-to-br from-amber-100/50 to-transparent rounded-full blur-3xl" />
        
        {/* Floating accent shapes */}
        <div className="absolute top-[30%] left-[15%] w-4 h-4 bg-amber-400 rotate-45 animate-float" />
        <div className="absolute top-[60%] right-[25%] w-6 h-6 border-2 border-navy-300 rotate-12 animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-[30%] left-[30%] w-3 h-3 bg-navy-200 rotate-45 animate-float" style={{ animationDelay: '2s' }} />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #1f2839 1px, transparent 1px),
              linear-gradient(to bottom, #1f2839 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-20 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left content */}
          <div className="space-y-8">
            {/* Badge */}
            <div 
              className="inline-flex items-center gap-2 px-4 py-2 bg-cream-100 border border-navy-100 rounded-none opacity-0 animate-fade-in"
              style={{ animationFillMode: 'forwards' }}
            >
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-medium text-navy-700 tracking-wide">AI 驱动的智能分析</span>
            </div>

            {/* Main heading */}
            <div className="space-y-4">
              <h1 
                className="font-display text-5xl lg:text-7xl font-bold text-navy-900 leading-[1.1] opacity-0 animate-fade-up"
                style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}
              >
                培养方案
                <br />
                <span className="relative inline-block">
                  缺口分析
                  <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 200 8" fill="none">
                    <path 
                      d="M0 4C50 4 50 1 100 1C150 1 150 7 200 7" 
                      stroke="#d97706" 
                      strokeWidth="3" 
                      strokeLinecap="round"
                      className="opacity-0 animate-draw-line"
                      style={{ 
                        animationDelay: '800ms', 
                        animationFillMode: 'forwards',
                        strokeDasharray: 1000,
                        strokeDashoffset: 1000
                      }}
                    />
                  </svg>
                </span>
              </h1>
              
              <p 
                className="text-lg lg:text-xl text-navy-600 max-w-lg leading-relaxed opacity-0 animate-fade-up"
                style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}
              >
                上传成绩单 PDF，AI 自动识别已修课程，对比培养方案要求，
                智能分析学分缺口，为你提供个性化的选课建议
              </p>
            </div>

            {/* CTA Button */}
            <div 
              className="opacity-0 animate-fade-up"
              style={{ animationDelay: '300ms', animationFillMode: 'forwards' }}
            >
              <button 
                onClick={scrollToForm}
                className="btn-primary group flex items-center gap-3"
              >
                开始分析
                <ArrowDown className="w-5 h-5 transition-transform group-hover:translate-y-1" />
              </button>
            </div>

            {/* Stats */}
            <div 
              className="flex items-center gap-8 pt-4 opacity-0 animate-fade-up"
              style={{ animationDelay: '400ms', animationFillMode: 'forwards' }}
            >
              <div>
                <p className="font-display text-3xl font-bold text-navy-900">5</p>
                <p className="text-sm text-navy-500">支持年级</p>
              </div>
              <div className="w-px h-12 bg-navy-200" />
              <div>
                <p className="font-display text-3xl font-bold text-navy-900">OCR</p>
                <p className="text-sm text-navy-500">智能识别</p>
              </div>
              <div className="w-px h-12 bg-navy-200" />
              <div>
                <p className="font-display text-3xl font-bold text-navy-900">AI</p>
                <p className="text-sm text-navy-500">深度分析</p>
              </div>
            </div>
          </div>

          {/* Right content - Feature cards */}
          <div className="relative lg:pl-8">
            {/* Decorative frame */}
            <div className="absolute -top-4 -left-4 w-24 h-24 border-t-2 border-l-2 border-amber-400 opacity-0 animate-fade-in" style={{ animationDelay: '500ms', animationFillMode: 'forwards' }} />
            <div className="absolute -bottom-4 -right-4 w-24 h-24 border-b-2 border-r-2 border-navy-300 opacity-0 animate-fade-in" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }} />
            
            {/* Feature cards grid */}
            <div className="grid gap-6">
              <FeatureCard
                icon={<BookMarked className="w-6 h-6" />}
                title="智能解析"
                description="PaddleOCR 精准识别成绩单内容，自动提取课程信息"
                delay={500}
              />
              <FeatureCard
                icon={<Target className="w-6 h-6" />}
                title="缺口分析"
                description="自动对比培养方案，识别未修课程和学分缺口"
                delay={600}
              />
              <FeatureCard
                icon={<Sparkles className="w-6 h-6" />}
                title="AI 建议"
                description="基于 DeepSeek LLM，提供个性化选课指导"
                delay={700}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#fefdfb] to-transparent pointer-events-none" />
    </section>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}

function FeatureCard({ icon, title, description, delay }: FeatureCardProps) {
  return (
    <div 
      className="academic-card p-6 flex items-start gap-5 hover-lift opacity-0 animate-slide-in-right"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      <div className="flex-shrink-0 w-14 h-14 bg-gradient-to-br from-navy-800 to-navy-900 flex items-center justify-center text-cream-50">
        {icon}
      </div>
      <div>
        <h3 className="font-display text-lg font-semibold text-navy-900 mb-1">{title}</h3>
        <p className="text-sm text-navy-500 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
