import { BookOpen } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen relative">
      {/* Noise overlay for texture */}
      <div className="noise-overlay" />
      
      {/* Decorative diagonal lines */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="diagonal-line left-[10%] top-[-50%]" />
        <div className="diagonal-line left-[30%] top-[-30%]" />
        <div className="diagonal-line right-[20%] top-[-40%]" />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50">
        <div className="glass">
          <div className="max-w-7xl mx-auto px-6 lg:px-12">
            <div className="flex items-center justify-between h-20">
              {/* Logo */}
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-12 h-12 bg-navy-800 flex items-center justify-center">
                    <BookOpen className="w-6 h-6 text-cream-50" strokeWidth={1.5} />
                  </div>
                  {/* Decorative corner */}
                  <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-amber-500" />
                  <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-amber-500" />
                </div>
                <div>
                  <h1 className="font-display text-xl font-bold text-navy-900 tracking-tight">
                    未央书院
                  </h1>
                  <p className="text-xs text-navy-500 tracking-widest uppercase">学业助手</p>
                </div>
              </div>

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-8">
                <a href="#" className="text-sm text-navy-600 hover:text-navy-900 transition-colors relative group">
                  使用指南
                  <span className="absolute -bottom-1 left-0 w-0 h-px bg-amber-500 transition-all group-hover:w-full" />
                </a>
                <a href="#" className="text-sm text-navy-600 hover:text-navy-900 transition-colors relative group">
                  关于
                  <span className="absolute -bottom-1 left-0 w-0 h-px bg-amber-500 transition-all group-hover:w-full" />
                </a>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-navy-100 mt-24">
        <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-navy-800 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-cream-50" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-display font-semibold text-navy-900">未央书院</p>
                <p className="text-xs text-navy-500">培养方案缺口分析助手</p>
              </div>
            </div>
            <p className="text-sm text-navy-400">
              基于 AI 的智能学业规划 · {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
