import React from 'react';
import ReactECharts from 'echarts-for-react';

interface ChartDisplayProps {
  data: {
    data: any[];
    columns: string[];
    statusContext?: {
      scope?: string;
      kpi?: string;
    };
  };
  preferredType?: 'bar' | 'pie' | 'line';
}

const ChartDisplay: React.FC<ChartDisplayProps> = ({ data, preferredType = 'bar' }) => {
  if (!data || !data.data || data.data.length === 0) {
    return <div className="p-4 text-center text-gray-400 italic">暂无图表数据</div>;
  }

  // Auto-detect dimensions and metrics
  const columns = data.columns;
  const firstRow = data.data[0];
  
  let dimension: string | null = null;
  let metric: string | null = null;

  for (const col of columns) {
    const val = firstRow[col];
    // A good dimension is a string that isn't the column name itself (if column name is generic)
    if (!dimension && (typeof val === 'string' || val instanceof String)) {
      dimension = col;
    } else if (!metric && typeof val === 'number') {
      metric = col;
    }
  }

  // Final fallback for metric if not detected
  if (!metric) metric = columns[columns.length - 1];

  // Fallback dimension logic:
  // If no dimension found, or if it's the same as metric, try to use scope from context
  let fallbackName = "数值";
  if (!dimension || dimension === metric) {
    if (data.statusContext?.scope) {
      // Extract the value from "category:value"
      const scopes = data.statusContext.scope.split(', ');
      const productScope = scopes.find(s => s.startsWith('product:'));
      if (productScope) {
        fallbackName = productScope.split(':')[1];
      } else {
        fallbackName = scopes[0].split(':')[1] || scopes[0];
      }
    }
  }

  const chartData = data.data.map(item => ({
    name: dimension ? String(item[dimension] || '') : fallbackName,
    value: item[metric!]
  }));

  // Clean up metric name for display
  const displayName = metric?.includes('(') ? (data.statusContext?.kpi || '数值') : metric;

  let option: any = {};

  if (preferredType === 'pie') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'center',
        textStyle: { fontSize: 10 }
      },
      series: [
        {
          name: displayName,
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: chartData
        }
      ]
    };
  } else if (preferredType === 'line') {
    option = {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.name),
        axisLabel: { rotate: 45, fontSize: 10 }
      },
      yAxis: { type: 'value' },
      series: [{
        name: displayName,
        data: chartData.map(d => d.value),
        type: 'line',
        smooth: true,
        symbolSize: 8,
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(59, 130, 246, 0.3)' }, { offset: 1, color: 'rgba(59, 130, 246, 0)' }]
          }
        }
      }]
    };
  } else { // Default to Bar
    option = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.name),
        axisLabel: { rotate: 45, fontSize: 10 }
      },
      yAxis: { type: 'value' },
      series: [{
        name: displayName,
        type: 'bar',
        data: chartData.map(d => d.value),
        itemStyle: {
          color: '#3b82f6',
          borderRadius: [4, 4, 0, 0]
        },
        barMaxWidth: 40
      }]
    };
  }

  return (
    <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm mt-2">
      <h4 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
        <span className="w-1 h-4 bg-blue-600 rounded-full"></span>
        {displayName} 分析图表
      </h4>
      <ReactECharts 
        option={option} 
        style={{ height: '400px', width: '100%' }}
        opts={{ renderer: 'svg' }}
      />
    </div>
  );
};

export default ChartDisplay;
