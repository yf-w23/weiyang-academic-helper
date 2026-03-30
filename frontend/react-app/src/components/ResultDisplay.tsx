import { CheckCircle, Download, RefreshCw, FileText, Sparkles } from 'lucide-react';
import { GapAnalysisResponse } from '../types';

interface ResultDisplayProps {
  result: GapAnalysisResponse;
  onReset: () => void;
}

export function ResultDisplay({ result, onReset }: ResultDisplayProps) {
  const handleDownload = () => {
    const blob = new Blob([result.analysis_result], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `培养方案缺口分析报告-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <section className="py-24 relative">
      <div className="max-w-5xl mx-auto px-6 lg:px-12">
        {/* Success header */}
        <div className="text-center mb-12 animate-fade-up">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-amber-400 to-amber-600 mb-6">
            <CheckCircle className="w-10 h-10 text-white" />
          </div>
          <h2 className="font-display text-4xl font-bold text-navy-900 mb-3">
            分析完成
          </h2>
          <p className="text-navy-500">{result.message}</p>
        </div>

        {/* Result card */}
        <div className="academic-card animate-scale-in">
          {/* Decorative corners */}
          <div className="absolute -top-3 -left-3 w-6 h-6 border-t-2 border-l-2 border-amber-400" />
          <div className="absolute -top-3 -right-3 w-6 h-6 border-t-2 border-r-2 border-amber-400" />
          <div className="absolute -bottom-3 -left-3 w-6 h-6 border-b-2 border-l-2 border-amber-400" />
          <div className="absolute -bottom-3 -right-3 w-6 h-6 border-b-2 border-r-2 border-amber-400" />

          {/* Card header */}
          <div className="px-8 py-6 border-b border-navy-100 bg-gradient-to-r from-navy-50/50 to-transparent">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-navy-800 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-cream-50" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold text-navy-900">分析报告</h3>
                  <p className="text-sm text-navy-500">基于 AI 智能分析生成</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDownload}
                  className="btn-secondary flex items-center gap-2 text-sm py-3 px-5"
                >
                  <Download className="w-4 h-4" />
                  下载报告
                </button>
                <button
                  onClick={onReset}
                  className="btn-primary flex items-center gap-2 text-sm py-3 px-5"
                >
                  <RefreshCw className="w-4 h-4" />
                  重新分析
                </button>
              </div>
            </div>
          </div>

          {/* Analysis content */}
          <div className="p-8">
            <div className="prose prose-slate max-w-none">
              <div
                className="markdown-content"
                dangerouslySetInnerHTML={{
                  __html: markdownToHtml(result.analysis_result),
                }}
              />
            </div>
          </div>

          {/* Card footer */}
          <div className="px-8 py-4 border-t border-navy-100 bg-cream-50/30">
            <div className="flex items-center justify-between text-sm text-navy-400">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>Markdown 格式报告</span>
              </div>
              <span>{new Date().toLocaleString('zh-CN')}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// Simple markdown to HTML converter
function markdownToHtml(markdown: string): string {
  if (!markdown) return '<p class="text-navy-500 italic">暂无分析结果</p>';

  let html = markdown
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Code
    .replace(/`(.*?)`/g, '<code>$1</code>')
    // Unordered lists
    .replace(/^\s*[-*] (.*$)/gim, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    // Ordered lists
    .replace(/^\s*\d+\. (.*$)/gim, '<li>$1</li>')
    // Blockquotes
    .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
    // Tables
    .replace(/\|(.+)\|/g, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      if (cells.length === 0) return '';
      const isHeader = cells[0].includes('--') || cells.some(c => c.trim() === '---');
      if (isHeader) return '';
      return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
    })
    // Paragraphs
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  // Wrap in paragraphs if not already wrapped
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }

  return html;
}
