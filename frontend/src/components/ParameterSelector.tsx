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
  allowedCategories?: string[];
}

const ParameterSelector: React.FC<ParameterSelectorProps> = ({ type, config, onSelect, currentKpi, allowedCategories }) => {
  const [level1Kpi, setLevel1Kpi] = useState<string | null>(null);
  const [showLevel2, setShowLevel2] = useState(false);
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  
  // Dynamic values state
  const [dynamicValues, setDynamicValues] = useState<Record<string, string[]>>({});
  const [loadingType, setLoadingType] = useState<string | null>(null);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [searchTerms, setSearchTerms] = useState<Record<string, string>>({});
  const dropdownRef = React.useRef<HTMLDivElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchValues = async (dimensionType: string) => {
    if (!currentKpi) return;
    
    setOpenDropdown(prev => prev === dimensionType ? null : dimensionType);
    
    // Always refetch if there are selected scopes (for cascading) or if not fetched yet
    // But optimize: if no selected scopes and already fetched, skip
    if (dynamicValues[dimensionType] && selectedScopes.length === 0) return; 

    setLoadingType(dimensionType);
    try {
      const values = await getDimensionValues(currentKpi, dimensionType, selectedScopes);
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
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 text-sm transition-colors"
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
                className="text-left px-3 py-2 hover:bg-white rounded text-sm text-gray-700 flex justify-between items-center group"
                onClick={() => onSelect(item.value)}
              >
                {item.label}
                <ChevronDown className="w-4 h-4 opacity-0 group-hover:opacity-50" />
              </button>
            ))}
            <button 
              className="text-xs text-blue-500 mt-2 text-left"
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
    // Determine Current FY and Half
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 1-12

    // FY logic: FY25 = Apr 2024 to Mar 2025.
    // If month >= 4, we are in FY(Year+1). e.g., Apr 2025 -> FY26.
    // If month < 4, we are in FY(Year). e.g., Jan 2025 -> FY25.
    const fyYear = currentMonth >= 4 ? currentYear + 1 : currentYear;
    const fyShort = fyYear.toString().slice(-2);
    
    // FY Range: Apr (FY-1) to Mar (FY)
    // e.g., FY25: 202404 - 202503
    const fyStart = `${fyYear - 1}04`;
    const fyEnd = `${fyYear}03`;
    const fyLabel = `当前财年FY${fyShort}`;

    // Half Logic
    // 1H: Apr - Sep (Months 4-9)
    // 2H: Oct - Mar (Months 10-12, 1-3)
    let halfLabel = "";
    let halfRange = "";
    
    // If currently in 1H (Apr-Sep)
    if (currentMonth >= 4 && currentMonth <= 9) {
       halfLabel = `当前半期FY${fyShort}-1H`;
       halfRange = `${fyYear - 1}04-${fyYear - 1}09`;
    } else {
       // Currently in 2H (Oct-Mar)
       halfLabel = `当前半期FY${fyShort}-2H`;
       // Range spans two calendar years: Oct (FY-1) to Mar (FY)
       halfRange = `${fyYear - 1}10-${fyYear}03`;
    }

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
      <div className="flex flex-col gap-3 mt-2">
        {/* Quick Actions for Time */}
        <div className="flex gap-2">
            <button
              className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors border border-blue-200"
              onClick={() => onSelect(`${fyStart}-${fyEnd}`)}
            >
              {fyLabel}
            </button>
            <button
              className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors border border-blue-200"
              onClick={() => onSelect(halfRange)}
            >
              {halfLabel}
            </button>
        </div>
        <p className="text-xs text-gray-400 italic">点击选择快捷时间段，或在对话框直接输入时间范围（如 202601-202606）</p>
      </div>
    );
  }

  if (type === 'scope') {
    const toggleScope = (category: string, value: string) => {
      const scopeStr = `${category}:${value}`;
      setSelectedScopes(prev => 
        prev.includes(scopeStr) 
          ? prev.filter(s => s !== scopeStr) 
          : [...prev, scopeStr]
      );
    };

    // Determine allowedScopes based on current KPI
    let allowedScopes: string[] | undefined = undefined;
    if (currentKpi) {
      Object.values(config.kpi_levels.level2_mapping).forEach(items => {
        const found = items.find(item => item.value === currentKpi);
        if (found && found.allowed_scopes) {
          allowedScopes = found.allowed_scopes;
        }
      });
    }

    const visibleCategories = config.scope_options.categories.filter(cat => {
      // 1. If explicitly restricted by allowedCategories (from proactive prompt)
      if (allowedCategories) {
        return allowedCategories.includes(cat.value);
      }

      // 2. If restricted by KPI definition
      if (allowedScopes) {
        return allowedScopes.includes(cat.value);
      }
      
      // Fallback logic if no allowedScopes is defined (backward compatibility)
      const isMachineKPI = currentKpi?.includes('machine') || currentKpi?.includes('chamber');
      if (cat.value === 'individual') return !isMachineKPI;
      if (cat.value === 'tools') return isMachineKPI;
      return true;
    });

    return (
      <div className="mt-2 flex flex-col gap-3">
        <div className="flex gap-2 flex-wrap" ref={dropdownRef}>
          {visibleCategories.map((item) => {
            const hasSelectionInCategory = selectedScopes.some(s => s.startsWith(`${item.value}:`));
            const isSearchable = item.value === 'individual' || item.value === 'tools' || item.value === 'sn' || item.value === 'organization';
            const currentSearchTerm = searchTerms[item.value] || "";
            
            return (
              <div key={item.value} className="relative">
                <button
                  className={clsx(
                    "px-3 py-1 rounded-full text-sm transition-colors border flex items-center gap-1",
                    openDropdown === item.value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : hasSelectionInCategory
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                  )}
                  onClick={() => fetchValues(item.value)}
                >
                  {item.label}
                  <ChevronDown size={14} className={clsx("transition-transform", openDropdown === item.value && "rotate-180")} />
                </button>

                {openDropdown === item.value && (
                  <div className="absolute top-full left-0 mt-1 w-56 bg-white shadow-xl rounded-md border border-gray-200 z-50 p-2 max-h-80 overflow-y-auto">
                    {/* Fuzzy Search Input */}
                    {isSearchable && (
                        <div className="mb-2 px-1">
                            <input
                                type="text"
                                placeholder={`搜索${item.label}...`}
                                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                                value={currentSearchTerm}
                                onChange={(e) => setSearchTerms(prev => ({ ...prev, [item.value]: e.target.value }))}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                            />
                        </div>
                    )}
                    
                    {loadingType === item.value ? (
                      <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-blue-600" size={20} /></div>
                    ) : (
                      dynamicValues[item.value]?.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {dynamicValues[item.value]
                            .filter(val => !currentSearchTerm || val.toLowerCase().includes(currentSearchTerm.toLowerCase()))
                            .map(val => {
                            const isSelected = selectedScopes.includes(`${item.value}:${val}`);
                            return (
                              <button 
                                key={val}
                                className={clsx(
                                  "block w-full text-left px-3 py-2 text-sm rounded transition-colors",
                                  isSelected 
                                    ? "bg-blue-100 text-blue-800 font-medium" 
                                    : "hover:bg-blue-50 text-gray-700"
                                )}
                                onClick={() => toggleScope(item.value, val)}
                              >
                                {val}
                                {isSelected && <span className="float-right">✓</span>}
                              </button>
                            );
                          })}
                          {dynamicValues[item.value].filter(val => !currentSearchTerm || val.toLowerCase().includes(currentSearchTerm.toLowerCase())).length === 0 && (
                              <p className="text-xs text-gray-400 p-2 text-center">无匹配结果</p>
                          )}
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
          <div className="flex flex-col gap-2 p-2 bg-blue-50 rounded-lg border border-blue-100">
            <div className="flex flex-wrap gap-1">
              {selectedScopes.map(s => (
                <span key={s} className="px-2 py-0.5 bg-white text-blue-600 text-[10px] rounded border border-blue-200 flex items-center gap-1">
                  {s.split(':')[1]}
                  <button onClick={() => setSelectedScopes(prev => prev.filter(ps => ps !== s))} className="hover:text-red-500">×</button>
                </span>
              ))}
            </div>
            <button
              onClick={() => onSelect(selectedScopes)}
              className="w-full py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
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
