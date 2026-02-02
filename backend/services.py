import yaml
import mysql.connector
import requests
import pandas as pd
import json
import os
import re
from typing import Dict, Any, List

# --- Config Service ---
class ConfigService:
    def __init__(self, config_dir: str = "../config"):
        self.config_dir = config_dir
        self.db_config = self._load_yaml("db_config.yaml")
        self.ui_mappings = self._load_yaml("ui_mappings.yaml")
        self.kpi_config = self._load_yaml("kpi_config.yaml")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.config_dir, filename)
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}

    def get_db_config(self):
        return self.db_config

    def get_ui_mappings(self):
        # Enhance UI mappings with KPI-specific allowed scopes from kpi_config
        import copy
        mappings = copy.deepcopy(self.ui_mappings)
        kpi_defs = self.kpi_config.get('kpi_definitions', {})
        
        # level2_mapping is nested inside kpi_levels
        kpi_levels = mappings.get('kpi_levels', {})
        level2_mapping = kpi_levels.get('level2_mapping', {})
        
        for category, kpis in level2_mapping.items():
            for kpi in kpis:
                kpi_val = kpi.get('value')
                if kpi_val in kpi_defs:
                    kpi['allowed_scopes'] = kpi_defs[kpi_val].get('allowed_scopes', [])
        
        return mappings

    def get_kpi_config(self):
        return self.kpi_config

# --- Database Service ---
class DatabaseService:
    def __init__(self, db_config: Dict[str, Any]):
        self.config = db_config

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                database=self.config.get("database", "")
            )
        except Exception as e:
            print(f"DB Connection Error: {e}")
            return None

    def init_exception_table(self):
        """Creates the exception table if it doesn't exist."""
        sql_create = """
        CREATE TABLE IF NOT EXISTS unsupported_kpi_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            user_query TEXT,
            time_range VARCHAR(50),
            scope TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql_create)
                
                # Check if user_id column exists (for migration)
                cursor.execute("SHOW COLUMNS FROM unsupported_kpi_logs LIKE 'user_id'")
                result = cursor.fetchone()
                if not result:
                    print("Adding missing column 'user_id' to unsupported_kpi_logs...")
                    cursor.execute("ALTER TABLE unsupported_kpi_logs ADD COLUMN user_id VARCHAR(50) AFTER id")
                
                conn.commit()
                print("Exception table initialized/verified.")
            except Exception as e:
                print(f"Error initializing exception table: {e}")
            finally:
                conn.close()

    def log_exception(self, query: str, time_range: str, scope: List[str]):
        """Logs unsupported KPI requests."""
        sql = "INSERT INTO unsupported_kpi_logs (user_query, time_range, scope) VALUES (%s, %s, %s)"
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                scope_str = json.dumps(scope, ensure_ascii=False) if scope else "[]"
                cursor.execute(sql, (query, time_range, scope_str))
                conn.commit()
                print(f"Logged unsupported KPI request: {query}")
            except Exception as e:
                print(f"Error logging exception: {e}")
            finally:
                conn.close()

    def get_unique_values(self, table_name: str, column_name: str, filters: Dict[str, List[str]] = None) -> List[str]:
        conn = self.get_connection()
        if not conn:
            # Mock values for demo
            if "Month" in column_name or "date" in column_name:
                return ["202501", "202412", "202411"]
            return ["Value 1", "Value 2", "Value 3"]
            
        cursor = conn.cursor()
        try:
            where_clause = f"{column_name} IS NOT NULL"
            
            # Add cascading filters
            if filters:
                for col, vals in filters.items():
                    if not vals: continue
                    if len(vals) == 1:
                        where_clause += f" AND {col} = '{vals[0]}'"
                    else:
                        vals_str = ", ".join([f"'{v}'" for v in vals])
                        where_clause += f" AND {col} IN ({vals_str})"
            
            # Search query logic is handled in frontend/API for simplicity, 
            # but usually we'd add 'LIKE %query%' here if needed.
            
            sql = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {where_clause} ORDER BY {column_name} ASC LIMIT 100"
            cursor.execute(sql)
            results = cursor.fetchall()
            return [str(row[0]) for row in results]
        except Exception as e:
            print(f"Error fetching unique values: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def execute_query(self, sql: str) -> Dict[str, Any]:
        conn = self.get_connection()
        if not conn:
            # Fallback to Mock Data for Demo purposes
            print("Using Mock Data (DB Connection Failed)")
            return {
                "data": [
                    {"kpi": "mrr", "value": 15000, "date": "2023-10-01", "product": "Product A"},
                    {"kpi": "mrr", "value": 16500, "date": "2023-11-01", "product": "Product A"},
                    {"kpi": "mrr", "value": 18000, "date": "2023-12-01", "product": "Product A"},
                ],
                "columns": ["kpi", "value", "date", "product"]
            }
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            return {"data": results, "columns": cursor.column_names}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_df_from_query(self, sql: str) -> pd.DataFrame:
        conn = self.get_connection()
        if not conn:
            # Mock DF
            return pd.DataFrame([
                {"kpi": "mrr", "value": 15000, "date": "2023-10-01", "product": "Product A"},
                {"kpi": "mrr", "value": 16500, "date": "2023-11-01", "product": "Product A"},
            ])
        try:
            return pd.read_sql(sql, conn)
        except Exception as e:
            print(f"Error reading SQL to DF: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

# --- AI Service (OpenAI Compatible / Accelerated) ---
class AIService:
    def __init__(self, model: str = "qwen2.5-coder:1.5b", base_url: str = "http://localhost:11434/v1"):
        self.model = model
        self.base_url = base_url

    def generate_response(self, prompt: str) -> str:
        try:
            print(f"Calling Accelerated AI Service with model {self.model}...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个精确的数据分析助手。请始终使用中文进行回复。只在要求返回 JSON 时返回原始 JSON 数据。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()['choices'][0]['message']['content'].strip()
            print("AI Service responded successfully.")
            return result
        except Exception as e:
            print(f"AI Service Error: {e}")
            if isinstance(e, requests.exceptions.ConnectionError):
                print("Connection Error: Is Ollama running at localhost:11434?")
            return ""

    def analyze_intent(self, query: str, kpi_config: Dict, ui_mappings: Dict, context: Dict = None, db_service: Any = None) -> Dict[str, Any]:
        # 0. Initialize from context if provided
        context = context or {}
        context_kpi = context.get('kpi')
        context_time = context.get('time_range')
        context_scope = context.get('scope') or []

        # 1. Pre-check for direct KPI matches (Exact or Keyword based)
        kpi_definitions = kpi_config.get('kpi_definitions', {})
        
        # Priority mapping for common queries (ordered by specificity)
        priority_keywords = [
            # Full label matches (highest priority)
            ("fe人数统计", "fe_count"),
            ("os人数统计", "os_count"),
            ("工程师人数统计", "fe_count"),
            ("外包人数统计", "os_count"),
            ("机台数量统计", "machine_count"),
            ("chamber数量统计", "chamber_count"),

            # Analysis Intent matches
            ("fe人数分析", "fe_count"),
            ("os人数分析", "os_count"),
            ("工程师人数分析", "fe_count"),
            ("外包人数分析", "os_count"),
            ("机台数量分析", "machine_count"),
            ("chamber数量分析", "chamber_count"),
            
            # SU Hour per Tool
            ("su hour per tool", "su_hour_per_tool"),
            ("startup hour per tool", "su_hour_per_tool"),
            ("su hour", "su_hour_per_tool"),
            ("su工时", "su_hour_per_tool"),
            ("平均装机时间", "su_hour_per_tool"),
            ("装机时间", "su_hour_per_tool"),
            ("装机工时", "su_hour_per_tool"),
            ("平均每台的装机结果", "su_hour_per_tool"),
            ("平均每台装机结果", "su_hour_per_tool"),
            ("机台装机时间", "su_hour_per_tool"),
            ("每机台装机时间", "su_hour_per_tool"),
            
            # Keywords
            ("fe人数", "fe_count"),
            ("fe数量", "fe_count"),
            ("fe", "fe_count"),
            ("field engineer", "fe_count"),
            ("外协", "os_count"),
            ("os", "os_count"),
            ("机台", "machine_count"),
            ("机器", "machine_count"),
            ("machine", "machine_count"),
            ("chamber", "chamber_count"),
            ("小室", "chamber_count"),
            ("人数统计", "headcount"),
            ("人数", "headcount"),
            ("人员", "headcount")
        ]

        # Check if the query contains a NEW KPI
        query_lower = query.lower()
        new_kpi = None
        for kw, kpi_key in priority_keywords:
            if kw in query_lower:
                new_kpi = kpi_key
                break
        
        # Reset Logic: If a new KPI is detected, we treat it as a fresh question
        # UNLESS the new KPI is the same as the context KPI, then it might be a refinement.
        if new_kpi and new_kpi != context_kpi:
            print(f"New KPI detected: {new_kpi}. Resetting context.")
            matched_kpi = new_kpi
            found_scopes = []
            extracted_time = None # Time might need re-extraction
        else:
            # Continue with context
            matched_kpi = context_kpi or new_kpi
            found_scopes = context_scope
            extracted_time = context_time

        # 2. Extract Time and Scope manually
        import re
        known_products = ["CT", "3DI", "SPS", "ES", "SSP", "TPS", "TS", "FSI", "Certas", "SD", "Epion", "FPD"]
        
        # 2a. Extract Time first to avoid misidentifying it as SN
        new_time = None
        range_match = re.search(r'(20\d{4})-(20\d{4})', query)
        if range_match:
            new_time = f"{range_match.group(1)}-{range_match.group(2)}"
        else:
            time_match = re.search(r'(20\d{4})', query)
            if not time_match:
                time_match = re.search(r'(FY\d{2})', query, re.IGNORECASE)
            if time_match:
                new_time = time_match.group(1).upper()
        
        if new_time:
            extracted_time = new_time

        # 2b. Extract Scopes
        new_scopes = []
        for prod in known_products:
            if prod.lower() in query_lower:
                new_scopes.append(f"product:{prod}")

        # Manual SN extraction (6 digits)
        # Avoid numbers starting with '20' if they look like the extracted time
        sn_matches = re.findall(r'\b(\d{6})\b', query)
        for sn in sn_matches:
            # If the 6-digit number is part of the extracted_time, skip it
            if extracted_time and sn in extracted_time:
                continue
            # If it starts with '20' and is likely a YYYYMM, skip it (unless we are sure it's an SN)
            if sn.startswith('20') and (202001 <= int(sn) <= 203012):
                continue
            new_scopes.append(f"tools:{sn}")

        # Update found_scopes
        if new_kpi and new_kpi != context_kpi:
            found_scopes = new_scopes
        else:
            for s in new_scopes:
                if s not in found_scopes:
                    found_scopes.append(s)

        # 4. AI Analysis (Improved for natural language scope)
        kpi_info = {k: v.get('description', '') for k, v in kpi_definitions.items()}
        all_categories = ui_mappings.get('scope_options', {}).get('categories', [])
        
        if matched_kpi and matched_kpi in kpi_definitions:
            allowed_scope_keys = list(kpi_definitions[matched_kpi].get('scope_columns', {}).keys())
            available_scopes = [s['value'] for s in all_categories if s['value'] in allowed_scope_keys]
        else:
            available_scopes = [s['value'] for s in all_categories]

        prompt = f"""
        [Role]
        你是一个专业的数据分析助手，负责从用户查询中提取关键参数。
        
        [Context]
        1. 当前已识别参数 (Current Context):
           - KPI: {matched_kpi}
           - Time Range: {extracted_time}
           - Scope: {json.dumps(found_scopes, ensure_ascii=False)}
        2. 可选指标 (Available KPIs): {json.dumps(kpi_info, ensure_ascii=False)}
        3. 可选维度分类 (Available Scopes categories): {available_scopes}
        
        [User Query]
        "{query}"
        
        [Instruction]
        基于当前上下文和用户新的查询，更新并提取 KPI、时间范围 (time_range) 和维度范围 (scope)。同时判断用户是否已经表达了“完成选择”或“不需要更多”的意图。
        
        [Rules]
        1. KPI 识别：如果上下文已有 KPI 且查询未明确更改，请保持现状。
        2. Scope 识别:
           - 识别具体的部门、团队、机台序列号。
           - 部门（如 "CT", "3DI", "SPS", "ES"）映射为 "product"。
           - 团队名称映射为 "organization"。
           - 机台 SN（如 100367）映射为 "tools"。
           - 格式必须为 "category:value"。
        3. 否定意图识别 (Negative Intent Recognition):
           - **重点**: 如果用户回答“没有”、“不用了”、“不需要”、“就这样”、“没了”、“所有”、“全部”、“跳过”等词汇，说明其不想再补充维度了。
           - 在这种情况下，JSON 必须返回 `"finished_selection": true`。
        4. 合并: 将新提取的内容与上下文合并。
        
        [Output Format]
        Return JSON ONLY:
        {{
            "kpi": "kpi_key",
            "time_range": "time_value_or_null",
            "scope": ["category:value", ...],
            "finished_selection": true/false
        }}
        """
        print(f"Analyzing intent with context for: {query}")
        response_text = self.generate_response(prompt)
        
        result = {"kpi": matched_kpi, "time_range": extracted_time, "scope": found_scopes, "missing_params": [], "finished_selection": False}
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end != -1:
                ai_result = json.loads(response_text[start:end])
                if ai_result.get('kpi'): result['kpi'] = ai_result['kpi']
                if ai_result.get('time_range'): result['time_range'] = ai_result['time_range']
                if ai_result.get('scope'): 
                    result['scope'] = list(set(result.get('scope', []) + ai_result['scope']))
                if ai_result.get('finished_selection'):
                    result['finished_selection'] = True
        except: pass

        # --- Proactive Missing Params Logic ---
        missing = []
        
        # 1. Check Time
        if not result['time_range']: 
            missing.append('time_range')

        # 2. Check Scope
        negative_keywords = ["没有", "不用", "不需要", "没", "没了", "就这样", "所有", "全部", "all", "nothing", "skip", "no", "无"]
        is_finished_selection = result['finished_selection'] or any(word in query_lower for word in negative_keywords)
        
        if is_finished_selection:
            result['finished_selection'] = True

        if result['kpi'] and result['kpi'] in kpi_definitions:
            kpi_def = kpi_definitions[result['kpi']]
            allowed = kpi_def.get('allowed_scopes', [])
            current_categories = set(s.split(':')[0] for s in result.get('scope', []) if ':' in s)
            missing_categories = [c for c in allowed if c not in current_categories]
            
            if not current_categories and not is_finished_selection:
                missing.append('scope')
            elif current_categories and missing_categories and not is_finished_selection:
                result['is_proactive_scope'] = True
                result['missing_scope_categories'] = missing_categories
                if 'scope' not in missing:
                    missing.append('scope')
        else:
            # KPI Unknown: We need context (Time + Scope/Finished) before we fail.
            has_scope = len(result.get('scope', [])) > 0
            if not has_scope and not is_finished_selection:
                 missing.append('scope')

        # 3. Handle KPI and Exception Logic
        if not result['kpi']:
            if missing:
                # If time or scope is missing, we ask for those first.
                pass 
            else:
                # Context is complete, but KPI is unknown -> Log and Error.
                if db_service:
                    db_service.log_exception(query, result['time_range'], result['scope'])
                
                result['response_message'] = "暂未支持这个KPI的开发，已收集这个问题，并告知项目负责人。"
                missing = []
                    
        result['missing_params'] = missing
        return result

    def _build_conditions_programmatically(self, kpi: str, time_range: str, scope: List[str], kpi_config: Dict) -> str:
        """Constructs WHERE clause conditions programmatically as a fallback."""
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        time_col = kpi_def.get('time_column', "")
        scope_cols = kpi_def.get('scope_columns', {})
        
        conditions = []
        
        # 1. Handle Time
        if time_range:
            if '-' in time_range:
                start, end = time_range.split('-', 1)
                conditions.append(f"{time_col} >= '{start}' AND {time_col} <= '{end}'")
            else:
                conditions.append(f"{time_col} = '{time_range}'")
        else:
            conditions.append(f"{time_col} = (SELECT MAX({time_col}) FROM {kpi_def.get('table_name')})")
            
        # 2. Handle Scope
        if scope:
            # Group scope values by category
            scope_map = {}
            for s in scope:
                if ":" in s:
                    cat, val = s.split(":", 1)
                    if cat in scope_map:
                        scope_map[cat].append(val)
                    else:
                        scope_map[cat] = [val]
            
            for cat, values in scope_map.items():
                col = scope_cols.get(cat)
                if col:
                    if len(values) == 1:
                        conditions.append(f"{col} = '{values[0]}'")
                    else:
                        vals_str = ", ".join([f"'{v}'" for v in values])
                        conditions.append(f"{col} IN ({vals_str})")
        
        return " AND ".join(conditions)

    def generate_where_clause(self, kpi: str, time_range: str, scope: List[str], kpi_config: Dict) -> str:
        """Generates WHERE clause. Skips AI if parameters are clear to save time."""
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        if not kpi_def:
            return ""

        # Programmatic generation is much faster and reliable for clear params
        print(f"Generating conditions programmatically for {kpi}...")
        conditions = self._build_conditions_programmatically(kpi, time_range, scope, kpi_config)
        
        if not conditions.upper().startswith("AND "):
            return f" AND {conditions}"
        return f" {conditions}"

    def generate_sql(self, kpi: str, time_range: str, scope: List[str], kpi_config: Dict) -> str:
        """Generates full SQL. Skips AI if parameters are clear to save time."""
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        template = kpi_def.get('sql_template', "")
        scope_cols = kpi_def.get('scope_columns', {})
        
        if not template:
            return ""

        print(f"Generating SQL programmatically for {kpi}...")
        conditions = self._build_conditions_programmatically(kpi, time_range, scope, kpi_config)
        
        # Determine group columns. 
        # User requested ONLY monthly breakdown for ALL KPIs.
        time_col = kpi_def.get('time_column')
        # If time_column is st_FY, we prefer st_Month for the grouping as per user request
        month_col = time_col
        if time_col == 'st_FY':
            month_col = 'st_Month'
        
        group_cols = [month_col] if month_col else []
        
        if group_cols:
            group_by_clause = f" GROUP BY {', '.join(group_cols)}"
            # Remove any existing GROUP BY if it somehow got in there
            if "GROUP BY" in conditions.upper():
                conditions = re.split(r'GROUP BY', conditions, flags=re.IGNORECASE)[0].strip()
            conditions += group_by_clause

        # Final assembly
        if conditions:
            # Handle the case where conditions only contains GROUP BY
            if conditions.upper().strip().startswith("GROUP BY"):
                final_sql = template.replace("{conditions}", conditions)
            else:
                final_sql = template.replace("{conditions}", f" AND {conditions}")
        else:
            final_sql = template.replace("{conditions}", "")
        
        # Adjust SELECT to include ONLY the month column
        if group_cols:
            select_part = final_sql.split("FROM")[0]
            # Add month column if not already in SELECT
            for col in reversed(group_cols):
                if col not in select_part:
                    final_sql = final_sql.replace("SELECT ", f"SELECT {col}, ", 1)
        
        print(f"Final SQL (Programmatic): {final_sql}")
        return final_sql



    def summarize_result(self, kpi: str, time_range: str, scope: List[str], data: Any, kpi_config: Dict) -> str:
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        # Use description directly but clean it up more aggressively if needed
        # Or just use the KPI name if description is too long/complex
        kpi_desc = kpi_def.get('description', kpi)
        
        # Split by comma or period to get the main title, avoiding formula details
        if "Keywords:" in kpi_desc:
            kpi_desc = kpi_desc.split("Keywords:")[0]
        
        kpi_desc = kpi_desc.split('。')[0].strip()
        
        scope_cols = kpi_def.get('scope_columns', {})
        
        # Reverse mapping for columns to friendly names
        col_to_label = {v: k.capitalize() for k, v in scope_cols.items()}
        # Common database columns to friendly names
        friendly_names = {
            "st_WrMonth": "月份",
            "st_Month": "月份",
            "st_DeptName": "产品组",
            "st_OrgName": "组织架构",
            "st_EmpNameCN": "姓名",
            "st_ProductLine": "产品线",
            "st_BU": "业务单元",
            "st_SN": "序列号",
            "st_EmpID": "工号",
            "st_ClassName": "岗位类别",
            "st_WorkLocation": "工作地点",
            "st_LEOName": "用工类型",
            "st_sn_org_teamname": "团队名称",
            "Hour": "总工时",
            "Sets": "总台数",
            "SUHourperTool": "平均每台装机工时",
            "total_startup_hours": "总Startup工时",
            "total_prewarranty_hours": "总Pre-warranty工时"
        }
        col_to_label.update(friendly_names)

        def get_friendly_name(col):
            if col in col_to_label:
                return col_to_label[col]
            if "COUNT" in col.upper():
                return "数量"
            return col

        # Programmatic summary for simple data to save time
        if isinstance(data, list):
            if len(data) == 0:
                return "当前系统中暂无相关数据。"
            
            if len(data) == 1:
                row = data[0]
                if len(row) == 1:
                    val = list(row.values())[0]
                    return f"为您查到，{kpi_desc}的结果是：**{val}**。"
                else:
                    details = "，".join([f"{get_friendly_name(k)}为 {v}" for k, v in row.items()])
                    return f"为您查到：{details}。"

            # Multiple rows - Format as a Markdown Table
            columns = list(data[0].keys())
            friendly_cols = [get_friendly_name(c) for c in columns]
            
            # Header
            table = f"为您查到以下 **{kpi_desc}** 统计结果：\n\n"
            table += "| " + " | ".join(friendly_cols) + " |\n"
            table += "| " + " | ".join(["---"] * len(columns)) + " |\n"
            
            # Rows
            for row in data:
                # Format values (e.g. bold numbers)
                row_values = []
                for c in columns:
                    val = row.get(c, "")
                    if isinstance(val, (int, float)):
                        row_values.append(f"**{val}**")
                    else:
                        row_values.append(str(val))
                table += "| " + " | ".join(row_values) + " |\n"
            
            return table

        # Fallback to AI for very complex data if needed
        prompt = f"""
        [Task]
        Summarize the data result in a natural, friendly Chinese sentence. 
        
        [Context]
        KPI: {kpi_desc}
        Time: {time_range}
        Scope: {scope}
        Data Result: {json.dumps(data, ensure_ascii=False)}
        
        [Example]
        - "经查询，CT的FE人数是9人。"
        - "为您查到，202506月SPS部门的机台总数是120台。"
        - "当前系统中暂无相关数据。"
        
        [Rules]
        - Be concise.
        - Use Chinese only.
        - Do not show internal IDs or JSON structures.
        """
        print(f"Summarizing result for {kpi}...")
        summary = self.generate_response(prompt).strip()
        
        # Clean up <think> tags if present
        if "</think>" in summary:
            summary = summary.split("</think>")[-1].strip()
            
        return summary or "查询完成。"
