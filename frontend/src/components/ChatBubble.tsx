import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../types';
import { Bot, User, FileText, BarChart, Loader2 } from 'lucide-react';
import { downloadDetail } from '../api';
import clsx from 'clsx';

interface ChatBubbleProps {
  message: Message;
  children?: React.ReactNode;
  onViewChart?: () => void;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ message, children, onViewChart }) => {
  const isBot = message.sender === 'bot';
  const isChart = !!message.actions?.chartType;
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (!message.status?.kpi || !message.status?.timeRange) return;
    
    setIsDownloading(true);
    try {
      const scopeArray = message.status.scope ? message.status.scope.split(', ') : [];
      await downloadDetail(
        message.status.kpi,
        message.status.timeRange,
        scopeArray
      );
    } catch (error) {
      console.error("Download failed:", error);
      alert("Download failed. Please check backend logs.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={clsx("flex w-full mb-6", isBot ? "justify-start" : "justify-end")}>
      <div className={clsx("flex", isChart ? "w-full" : "max-w-[80%]", isBot ? "flex-row" : "flex-row-reverse")}>
        {/* Avatar */}
        <div className={clsx(
          "flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center mx-2",
          isBot ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
        )}>
          {isBot ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Content */}
        <div className={clsx("flex flex-col", isChart ? "flex-1" : "")}>
          <div className={clsx(
            "p-4 rounded-2xl shadow-sm",
            isBot ? "bg-white border border-gray-100 rounded-tl-none text-gray-800" : "bg-blue-600 text-white rounded-tr-none",
            isChart ? "w-full" : ""
          )}>
            <div className={clsx(
              "markdown-content",
              isBot ? "prose-blue" : "prose-invert"
            )}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({node, ...props}) => (
                    <div className="overflow-x-auto my-2">
                      <table className="min-w-full border-collapse border border-gray-200 text-sm" {...props} />
                    </div>
                  ),
                  th: ({node, ...props}) => (
                    <th className="border border-gray-200 px-4 py-2 bg-gray-50 font-bold text-left" {...props} />
                  ),
                  td: ({node, ...props}) => (
                    <td className="border border-gray-200 px-4 py-2" {...props} />
                  ),
                  strong: ({node, ...props}) => (
                     <strong className={clsx("font-bold", isBot ? "text-blue-600" : "text-white underline underline-offset-2")} {...props} />
                   ),
                  p: ({node, ...props}) => (
                    <p className="mb-2 last:mb-0 leading-relaxed" {...props} />
                  )
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
            
            {/* Interactive Children (Selectors, Charts, etc.) */}
            {children && <div className="mt-3">{children}</div>}

            {/* Actions: Download / Chart */}
            {message.actions && (message.actions.showChart || message.actions.showDownload) && (
               <div className="flex gap-2 mt-4 pt-3 border-t border-gray-100">
                 {message.actions.showDownload && (
                   <button 
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="flex items-center gap-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded transition-colors disabled:opacity-50"
                   >
                     {isDownloading ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
                     下载明细
                   </button>
                 )}
                 {message.actions.showChart && (
                   <button 
                    onClick={onViewChart}
                    className="flex items-center gap-1 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded transition-colors"
                   >
                     <BarChart size={14} /> 查看图表
                   </button>
                 )}
               </div>
            )}
          </div>

          {/* Status / Context Display */}
          {isBot && message.status && (
            <div className="mt-2 ml-1 text-[11px] text-gray-400 italic space-y-0.5 border-l-2 border-gray-100 pl-2">
              {message.status.kpi && <p>查询指标: {message.status.kpi}</p>}
              {message.status.timeRange && <p>时间范围: {message.status.timeRange}</p>}
              {message.status.scope && <p>筛选维度: {message.status.scope}</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
