import React, { useState } from 'react';
import { Zap } from 'lucide-react';

interface HomePageProps {
  onSendMessage: (message: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onSendMessage }) => {
  const [input, setInput] = useState('');

  const suggestions = [
    {
      title: "FE人数统计",
      subtitle: "查询各个部门的 Field Engineer 数量"
    },
    {
      title: "机台数量分析",
      subtitle: "查看当前所有 Main Machine 的总数"
    },
    {
      title: "CT有多少FE",
      subtitle: "查询 CT 部门的 Field Engineer 数量"
    }
  ];

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 bg-white animate-in fade-in duration-700">
      {/* Logo & Title */}
      <div className="flex items-center gap-4 mb-16">
        <div className="w-14 h-14 bg-blue-500 rounded-full shadow-lg shadow-blue-100">
        </div>
        <h1 className="text-5xl font-bold text-gray-800 tracking-tight">Demo</h1>
      </div>

      {/* Search Input Box */}
      <div className="w-full max-w-3xl mb-16">
        <form 
          onSubmit={handleSubmit}
          className="bg-white rounded-[32px] shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-gray-100 p-4 transition-all hover:shadow-[0_8px_40px_rgb(0,0,0,0.08)]"
        >
          <div className="px-5 py-10 flex items-center">
            <input
              type="text"
              placeholder="有什么我能帮您的吗？"
              className="w-full text-2xl outline-none text-gray-700 placeholder-gray-400 bg-transparent"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </div>
        </form>
      </div>

      {/* Suggestions */}
      <div className="w-full max-w-3xl">
        <div className="flex items-center gap-2 text-gray-400 mb-6 px-1">
          <Zap size={14} fill="currentColor" />
          <span className="text-xs font-bold tracking-widest uppercase">建议</span>
        </div>
        
        <div className="flex flex-col gap-4">
          {suggestions.map((item, index) => (
            <button
              key={index}
              onClick={() => onSendMessage(item.title)}
              className="group text-left p-4 hover:bg-gray-50 rounded-2xl transition-all duration-200"
            >
              <div className="text-base font-bold text-gray-700 group-hover:text-blue-600 transition-colors">
                {item.title}
              </div>
              <div className="text-sm text-gray-400">
                {item.subtitle}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
