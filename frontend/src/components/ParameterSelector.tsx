import React, { useState, useEffect } from 'react';
import { UIConfig } from '../types';
import { ChevronDown, Loader2 } from 'lucide-react';
import { getDimensionValues } from '../api';
import clsx from 'clsx';

interface ParameterSelectorProps {
  type: 'kpi' | 'time' | 'scope';
  config: UIConfig;
  onSelect: (value: string | string[]) => void;
  currentKpi?: string | null;
}

const ParameterSelector: React.FC<ParameterSelectorProps> = ({ type, config, onSelect, currentKpi }) => {
  const [level1Kpi, setLevel1Kpi] = useState<string | null>(null);
  const [showLevel2, setShowLevel2] = useState(false);
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  
  // Dynamic values state
  const [dynamicValues, setDynamicValues] = useState<Record<string, string[]>>({});
  const [loadingType, setLoadingType] = useState<string | null>(null);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const fetchValues = async (dimensionType: string) => {
    if (!currentKpi) return;
    
    setOpenDropdown(prev => prev === dimensionType ? null : dimensionType);
    
    if (dynamicValues[dimensionType]) return; // Already fetched

    setLoadingType(dimensionType);
    try {
      const values = await getDimensionValues(currentKpi, dimensionType);
      setDynamicValues(prev => ({ ...prev, [dimensionType]: values }));
    } catch (error) {
      console.error("Error fetching dimension values:", error);
    } finally {
      setLoadingType(null);
    }
  };

  // KPI Selection Logic
  if (type === 'kpi') {
    if (!level1Kpi) {
      return (
        <div className="flex gap-2 flex-wrap mt-2">
          {config.kpi_levels.level1.map((item) => (
            <button
              key={item.value}
              className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full hover:bg-gray-200 text-sm transition-colors border border-gray-200"
              onClick={() => {
                setLevel1Kpi(item.value);
                setShowLevel2(true);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      );
    }

    if (showLevel2) {
      const level2Options = config.kpi_levels.level2_mapping[level1Kpi] || [];
      return (
        <div className="mt-2 p-2 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 mb-2">请选择具体的 {level1Kpi} 指标：</p>
          <div className="flex flex-col gap-1">
            {level2Options.map((item) => (
              <button
                key={item.value}
                className="text-left px-3 py-2 hover:bg-white rounded text-sm text-gray-800 flex justify-between items-center group"
                onClick={() => onSelect(item.value)}
              >
                {item.label}
                <ChevronDown className="w-4 h-4 opacity-0 group-hover:opacity-50" />
              </button>
            ))}
            <button 
              className="text-xs text-gray-500 mt-2 text-left hover:text-black transition-colors"
              onClick={() => setLevel1Kpi(null)}
            >
              ← 返回
            </button>
          </div>
        </div>
      );
    }
  }

  // Time Selection Logic
  if (type === 'time') {
    // Find supported time types for current KPI
    let supportedTimeTypes: string[] | undefined = undefined;
    if (currentKpi) {
      Object.values(config.kpi_levels.level2_mapping).forEach(items => {
        const found = items.find(item => item.value === currentKpi);
        if (found && found.time_types) {
          supportedTimeTypes = found.time_types;
        }
      });
    }

    const filteredTypes = supportedTimeTypes 
      ? config.time_options.types.filter(t => supportedTimeTypes!.includes(t.value))
      : config.time_options.types;

    return (
      <div className="flex flex-col gap-2 mt-2">
        <div className="flex gap-2 flex-wrap">
          {filteredTypes.map((item) => (
            <div key={item.value} className="relative">
              <button
                className={`px-3 py-1 rounded-full text-sm transition-colors flex items-center gap-1 border ${
                  openDropdown === 'time' 
                    ? 'bg-black text-white border-black' 
                    : 'bg-gray-100 text-gray-800 border-transparent hover:bg-gray-200'
                }`}
                onClick={() => fetchValues('time')}
              >
                {item.label}
                <ChevronDown size={14} className={clsx("transition-transform", openDropdown === 'time' && "rotate-180")} />
              </button>
              
              {openDropdown === 'time' && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-white shadow-xl rounded-md border border-gray-200 z-50 p-2 max-h-60 overflow-y-auto">
                   {loadingType === 'time' ? (
                     <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-gray-800" size={20} /></div>
                   ) : (
                     dynamicValues['time']?.length > 0 ? (
                       <div className="flex flex-col gap-1">
                         {dynamicValues['time'].map(val => (
                           <button 
                              key={val}
                              className="block w-full text-left px-3 py-2 hover:bg-gray-50 text-sm rounded transition-colors text-gray-800"
                              onClick={() => {
                                onSelect(val);
                                setOpenDropdown(null);
                              }}
                           >
                             {val}
                           </button>
                         ))}
                       </div>
                     ) : (
                       <p className="text-xs text-gray-400 p-3 text-center italic">暂无可用数据</p>
                     )
                   )}
                </div>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 italic">点击确认时间范围或者数据版本</p>
      </div>
    );
  }

  // Scope Selection Logic
  if (type === 'scope') {
    const toggleScope = (category: string, value: string) => {
      const scopeStr = `${category}:${value}`;
      setSelectedScopes(prev => 
        prev.includes(scopeStr) 
          ? prev.filter(s => s !== scopeStr) 
          : [...prev, scopeStr]
      );
    };

    return (
      <div className="mt-2 flex flex-col gap-3">
        <div className="flex gap-2 flex-wrap">
          {config.scope_options.categories.map((item) => {
            const hasSelectionInCategory = selectedScopes.some(s => s.startsWith(`${item.value}:`));
            
            return (
              <div key={item.value} className="relative">
                <button
                  className={clsx(
                    "px-3 py-1 rounded-full text-sm transition-colors border flex items-center gap-1",
                    openDropdown === item.value
                      ? 'bg-black text-white border-black'
                      : hasSelectionInCategory
                        ? 'bg-gray-100 text-gray-800 border-gray-300'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-gray-900'
                  )}
                  onClick={() => fetchValues(item.value)}
                >
                  {item.label}
                  <ChevronDown size={14} className={clsx("transition-transform", openDropdown === item.value && "rotate-180")} />
                </button>

                {openDropdown === item.value && (
                  <div className="absolute top-full left-0 mt-1 w-48 bg-white shadow-xl rounded-md border border-gray-200 z-50 p-2 max-h-60 overflow-y-auto">
                    {loadingType === item.value ? (
                      <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-gray-800" size={20} /></div>
                    ) : (
                      dynamicValues[item.value]?.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {dynamicValues[item.value].map(val => {
                            const isSelected = selectedScopes.includes(`${item.value}:${val}`);
                            return (
                              <button 
                                key={val}
                                className={clsx(
                                  "block w-full text-left px-3 py-2 text-sm rounded transition-colors",
                                  isSelected 
                                    ? "bg-gray-200 text-black font-medium" 
                                    : "hover:bg-gray-50 text-gray-700"
                                )}
                                onClick={() => toggleScope(item.value, val)}
                              >
                                {val}
                                {isSelected && <span className="float-right">✓</span>}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 p-3 text-center italic">暂无可用数据</p>
                      )
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Selected Summary and Confirm Button */}
        {selectedScopes.length > 0 && (
          <div className="flex flex-col gap-2 p-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex flex-wrap gap-1">
              {selectedScopes.map(s => (
                <span key={s} className="px-2 py-0.5 bg-white text-gray-800 text-[10px] rounded border border-gray-300 flex items-center gap-1">
                  {s.split(':')[1]}
                  <button onClick={() => setSelectedScopes(prev => prev.filter(ps => ps !== s))} className="hover:text-red-500">×</button>
                </span>
              ))}
            </div>
            <button
              onClick={() => onSelect(selectedScopes)}
              className="w-full py-2 bg-black text-white rounded-md text-sm font-medium hover:bg-gray-800 transition-colors shadow-sm"
            >
              确认选择 ({selectedScopes.length})
            </button>
          </div>
        )}
        <p className="text-xs text-gray-400 italic">支持跨类别选择多个范围，完成后点击确认</p>
      </div>
    );
  }

  return null;
};

export default ParameterSelector;
