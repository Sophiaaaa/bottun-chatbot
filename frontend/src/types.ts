export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
  status?: {
    kpi?: string;
    timeRange?: string;
    scope?: string;
    rawKpi?: string;
    rawTimeRange?: string;
    rawScope?: string[];
    sql?: string;
  };
  actions?: {
    missingParams?: string[];
    allowedCategories?: string[];
    showChart?: boolean;
    showDownload?: boolean;
    data?: any;
    chartType?: 'bar' | 'pie' | 'line';
  };
}

export interface UIConfig {
  kpi_levels: {
    level1: Array<{ label: string; value: string }>;
    level2_mapping: Record<string, Array<{ label: string; value: string; time_types?: string[]; allowed_scopes?: string[] }>>;
  };
  time_options: {
    types: Array<{ label: string; value: string }>;
  };
  scope_options: {
    categories: Array<{ label: string; value: string }>;
  };
}

export interface AnalysisResponse {
  kpi: string | null;
  time_range: string | null;
  scope: string[] | null;
  missing_params: string[];
  is_proactive_scope?: boolean;
  missing_scope_categories?: string[];
}

export interface SQLResponse {
  sql: string;
  result: {
    data: any[];
    columns: string[];
    error?: string;
  };
  summary?: string;
}
