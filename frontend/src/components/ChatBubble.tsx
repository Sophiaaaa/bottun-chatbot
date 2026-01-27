import React, { useState } from 'react';
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
          isBot ? "bg-black text-white" : "bg-gray-200 text-gray-600"
        )}>
          {isBot ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Content */}
        <div className={clsx("flex flex-col", isChart ? "flex-1" : "")}>
          <div className={clsx(
            "p-4 rounded-2xl shadow-sm",
            isBot ? "bg-white border border-gray-100 rounded-tl-none" : "bg-black text-white rounded-tr-none",
            isChart ? "w-full" : ""
          )}>
            <p className="whitespace-pre-wrap">{message.text}</p>
            
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
                    className="flex items-center gap-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 px-3 py-2 rounded transition-colors"
                   >
                     <BarChart size={14} /> 查看图表
                   </button>
                 )}
               </div>
            )}
          </div>

          {/* Status / Context Display */}
          {isBot && message.status && (
            <div className="mt-1 ml-1 text-xs text-gray-400 italic space-y-0.5">
              {message.status.kpi && <p>已确认 KPI: {message.status.kpi}</p>}
              {message.status.timeRange && <p>已确认时间: {message.status.timeRange}</p>}
              {message.status.scope && <p>已确认范围: {message.status.scope}</p>}
              {message.status.sql && (
                <p className="font-mono text-[10px] mt-1 bg-gray-50 p-1 rounded border border-gray-100">
                  SQL: {message.status.sql}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
