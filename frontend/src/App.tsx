import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Home } from 'lucide-react';
import { getUIConfig, analyzeQuery, generateAndExecuteSQL } from './api';
import { Message, UIConfig, AnalysisResponse } from './types';
import ChatBubble from './components/ChatBubble';
import ParameterSelector from './components/ParameterSelector';
import HomePage from './components/HomePage';
import ChartDisplay from './components/ChartDisplay';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [uiConfig, setUiConfig] = useState<UIConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHomeActive, setIsHomeActive] = useState(true);
  
  // Current conversation context
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse>({
    kpi: null,
    time_range: null,
    scope: null,
    missing_params: []
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load Config
    getUIConfig().then(setUiConfig).catch(console.error);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (customMessage?: string) => {
    const textToSend = customMessage || input;
    if (!textToSend.trim()) return;

    if (isHomeActive) {
      setIsHomeActive(false);
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Analyze Intent
      const analysis = await analyzeQuery(userMsg.text);
      setCurrentAnalysis(analysis);
      processAnalysisResult(analysis, userMsg.text);

    } catch (error) {
      console.error(error);
      addBotMessage("抱歉，分析您的请求时出现了错误。");
    } finally {
      setIsLoading(false);
    }
  };

  const processAnalysisResult = async (analysis: AnalysisResponse, originalQuery: string) => {
    const missing = analysis.missing_params;

    if (missing.length > 0) {
      // Ask for the first missing param
      const firstMissing = missing[0];
      let question = "";
      if (firstMissing === 'kpi') question = "您对哪个 KPI 指标感兴趣？";
      else if (firstMissing === 'time_range') question = "您想查询哪个时间段的数据？";
      else if (firstMissing === 'scope') question = "查询范围是什么（产品线、部门等）？";

      addBotMessage(question, { missingParams: missing }, analysis);
    } else {
      // All params present, execute SQL
      await executeSQL(analysis);
    }
  };

  const executeSQL = async (analysis: AnalysisResponse) => {
    setIsLoading(true);
    try {
      const result = await generateAndExecuteSQL(
        analysis.kpi!, 
        analysis.time_range!, 
        Array.isArray(analysis.scope) ? analysis.scope : (analysis.scope ? [analysis.scope] : [])
      );

      // Format result text
      let resultText = result.summary || "查询结果如下：\n";
      
      // If no summary was provided, or if we want to show a preview of data anyway
      if (!result.summary && result.result.data && result.result.data.length > 0) {
        const firstRow = result.result.data[0];
        resultText += JSON.stringify(firstRow, null, 2); 
        if (result.result.data.length > 1) {
           resultText += `\n...以及另外 ${result.result.data.length - 1} 条记录。`;
        }
      } else if (!result.summary) {
        resultText = "未找到符合条件的数据。";
      }

      addBotMessage(resultText, { 
        showChart: true, 
        showDownload: true, 
        data: result.result 
      }, analysis, result.sql);

    } catch (error) {
      addBotMessage("执行 SQL 查询时出错。");
    } finally {
      setIsLoading(false);
    }
  };

  const handleParameterSelect = async (paramType: string, value: string | string[]) => {
    // Update local context
    const updatedAnalysis = { ...currentAnalysis };
    
    if (paramType === 'kpi') updatedAnalysis.kpi = value as string;
    if (paramType === 'time') updatedAnalysis.time_range = value as string;
    if (paramType === 'scope') updatedAnalysis.scope = value as string[];

    // Remove from missing params
    updatedAnalysis.missing_params = updatedAnalysis.missing_params.filter(p => {
       if (paramType === 'kpi') return p !== 'kpi';
       if (paramType === 'time') return p !== 'time_range';
       if (paramType === 'scope') return p !== 'scope';
       return true;
    });

    setCurrentAnalysis(updatedAnalysis);

    // Add user selection as a message (optional, but good for flow)
    const selectionText = Array.isArray(value) ? value.join(', ') : value;
    setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'user',
        text: `Selected: ${selectionText}`,
        timestamp: new Date()
    }]);

    // Process next step
    setTimeout(() => {
        processAnalysisResult(updatedAnalysis, "");
    }, 500);
  };

  const handleViewChart = (data: any, status?: any) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      sender: 'bot',
      text: "已为您生成可视化图表：",
      timestamp: new Date(),
      actions: {
        data: {
          ...data,
          statusContext: status
        },
        chartType: 'bar' // Priority: Bar
      }
    }]);
  };

  const addBotMessage = (text: string, actions?: any, statusAnalysis?: AnalysisResponse, sql?: string) => {
    // Helper to get friendly KPI label
    const getKPILabel = (value?: string | null) => {
      if (!value || !uiConfig) return value;
      const mapping = uiConfig.kpi_levels.level2_mapping;
      for (const level of Object.keys(mapping)) {
        const found = mapping[level].find(k => k.value === value);
        if (found) return found.label;
      }
      return value;
    };

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      sender: 'bot',
      text,
      timestamp: new Date(),
      actions,
      status: statusAnalysis ? {
        kpi: getKPILabel(statusAnalysis.kpi) || undefined,
        timeRange: statusAnalysis.time_range || undefined,
        scope: statusAnalysis.scope ? (Array.isArray(statusAnalysis.scope) ? statusAnalysis.scope.join(', ') : statusAnalysis.scope) : undefined,
        sql: sql
      } : undefined
    }]);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-full">
          </div>
          <h1 className="text-xl font-bold text-gray-800">Demo</h1>
        </div>
        {!isHomeActive && (
          <button 
            onClick={() => {
              setIsHomeActive(true);
              setMessages([]);
            }}
            className="flex items-center gap-2 px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Home size={18} />
            <span className="text-sm font-medium">首页</span>
          </button>
        )}
      </header>

      {isHomeActive ? (
        <main className="flex-1 overflow-y-auto">
          <HomePage onSendMessage={(msg) => handleSend(msg)} />
        </main>
      ) : (
        <>
          {/* Chat Area */}
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            <div className="max-w-6xl mx-auto">
              {messages.map((msg, idx) => (
                <ChatBubble 
                  key={msg.id} 
                  message={msg}
                  onViewChart={() => handleViewChart(msg.actions?.data, msg.status)}
                >
                  {msg.actions?.chartType && msg.actions.data && (
                    <ChartDisplay data={msg.actions.data} preferredType={msg.actions.chartType} />
                  )}
                  {msg.actions?.missingParams && msg.actions.missingParams.length > 0 && uiConfig && (
                    <ParameterSelector 
                      type={
                        msg.actions.missingParams[0] === 'kpi' ? 'kpi' :
                        msg.actions.missingParams[0] === 'time_range' ? 'time' : 'scope'
                      }
                      config={uiConfig}
                      currentKpi={currentAnalysis.kpi}
                      onSelect={(val) => handleParameterSelect(
                        msg.actions!.missingParams![0] === 'time_range' ? 'time' : msg.actions!.missingParams![0], 
                        val
                      )}
                    />
                  )}
                </ChatBubble>
              ))}
              {isLoading && (
                <div className="flex justify-start mb-6">
                  <div className="bg-white p-4 rounded-2xl rounded-tl-none border border-gray-100 shadow-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </main>

          {/* Input Area */}
          <footer className="bg-white border-t border-gray-200 p-4">
            <div className="max-w-3xl mx-auto relative">
              <input
                type="text"
                className="w-full pl-4 pr-12 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                placeholder="咨询关于人数、机台或绩效的数据..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                disabled={isLoading}
              />
              <button
                className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
              >
                <Send size={20} />
              </button>
            </div>
          </footer>
        </>
      )}
    </div>
  );
};

export default App;
