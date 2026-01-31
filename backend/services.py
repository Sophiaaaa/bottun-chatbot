import yaml
import mysql.connector
import requests
import pandas as pd
import json
import os
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
        return self.ui_mappings

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

    def analyze_intent(self, query: str, kpi_config: Dict, ui_mappings: Dict) -> Dict[str, Any]:
        # 1. Pre-check for direct KPI matches (Exact or Keyword based)
        kpi_definitions = kpi_config.get('kpi_definitions', {})
        matched_kpi = None
        
        # Priority mapping for common queries (ordered by specificity)
        priority_keywords = [
            # Full label matches (highest priority)
            ("fe人数统计", "fe_count"),
            ("os人数统计", "os_count"),
            ("机台数量统计", "machine_count"),
            ("chamber数量统计", "chamber_count"),

            # Analysis Intent matches
            ("fe人数分析", "fe_count"),
            ("os人数分析", "os_count"),
            ("机台数量分析", "machine_count"),
            ("chamber数量分析", "chamber_count"),
            
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

        # Check for priority keywords first
        query_lower = query.lower()
        for kw, kpi_key in priority_keywords:
            if kw in query_lower:
                matched_kpi = kpi_key
                print(f"Priority keyword match: {kw} -> {kpi_key}")
                break

        # Manual scope extraction for common products to be safe
        found_scopes = []
        known_products = ["CT", "3DI", "SPS", "ES", "SPS", "SSP", "TPS"]
        for prod in known_products:
            if prod.lower() in query_lower:
                found_scopes.append(f"product:{prod}")
                print(f"Manual scope match: {prod}")

        # If still no match, check descriptions
        if not matched_kpi:
            for k, v in kpi_definitions.items():
                desc = v.get('description', '').lower()
                if query_lower == k.lower() or query_lower in desc:
                    matched_kpi = k
                    print(f"Description match found for KPI: {k}")
                    break
        
        # If we have a strong match, only short-circuit if the query is VERY simple 
        # (e.g. just the keyword itself) to avoid missing other params like "CT" in "CT有多少FE"
        is_exact_match = any(query_lower == kw for kw, _ in priority_keywords)
        
        # If we found both KPI and some scopes manually, we can also short-circuit
        if matched_kpi and (is_exact_match or len(query) < 5 or found_scopes):
            # Extract time if possible (simple YYYYMM pattern or YYYYMM-YYYYMM range)
            import re
            
            # Check for range first: YYYYMM-YYYYMM
            range_match = re.search(r'\b(20\d{4})-(20\d{4})\b', query)
            if range_match:
                extracted_time = f"{range_match.group(1)}-{range_match.group(2)}"
            else:
                # Check for single YYYYMM
                time_match = re.search(r'\b(20\d{4})\b', query)
                extracted_time = time_match.group(1) if time_match else None
            
            missing = []
            if not extracted_time: missing.append("time_range")
            if not found_scopes: missing.append("scope")
            
            return {
                "kpi": matched_kpi, 
                "time_range": extracted_time, 
                "scope": found_scopes, 
                "missing_params": missing
            }
        
        # Construct a prompt to analyze the user's query
        kpi_info = {k: v.get('description', '') for k, v in kpi_definitions.items()}
        
        prompt = f"""
        [Role]
        你是一个专业的数据分析助手，负责从用户查询中提取关键参数。
        
        [User Query]
        "{query}"
        
        [Context]
        1. Available KPIs (key: description): {json.dumps(kpi_info, ensure_ascii=False)}
        2. Available Time types: {[t['value'] for t in ui_mappings.get('time_options', {}).get('types', [])]}
        3. Available Scopes categories: {[s['value'] for s in ui_mappings.get('scope_options', {}).get('categories', [])]}
        
        [Instruction]
        从查询中识别 KPI、时间范围 (time_range) 和维度范围 (scope)。
        
        [Rules]
        1. KPI 识别优先级：
           - 如果用户提到 "FE", "Field Engineer", "FE人数", "FE数量", "FE人数分析", 匹配 "fe_count"。
           - 如果用户提到 "OS", "Outsourced", "外协", "OS人数分析", 匹配 "os_count"。
           - 如果用户提到 "机台", "机器", "Machine", "机台数量分析", 匹配 "machine_count"。
           - 如果用户提到 "Chamber", "小室", "Chamber数量分析", 匹配 "chamber_count"。
           - 默认的人数统计匹配 "headcount"。
        2. Scope 识别：
           - 部门（如 "CT", "3DI", "SPS", "ES"）属于 "product" 维度。
           - 范围格式必须为 "category:value" (例如 "product:CT", "organization:SPS")。
        3. 如果已经识别出 KPI 为 "{matched_kpi if matched_kpi else 'None'}"，请优先确认。
        
        [Output Format]
        Return JSON ONLY:
        {{
            "kpi": "kpi_key",
            "time_range": "time_value_or_null",
            "scope": ["category:value", ...],
            "missing_params": ["kpi", "time_range", "scope"]
        }}
        如果没有找到对应参数，将其设为 null 并加入 missing_params 列表。
        """
        print(f"Analyzing intent for: {query}")
        response_text = self.generate_response(prompt)
        print(f"AI Response: {response_text}")
        
        # Attempt to parse JSON from response (simple cleanup)
        try:
            # Find first { and last }
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                print(f"Parsed Analysis: {result}")
                return result
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            pass
        
        # Fallback if parsing fails
        return {"kpi": None, "time_range": None, "scope": None, "missing_params": ["kpi", "time_range", "scope"]}

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
        
        # Check if we need GROUP BY
        has_multiple_values = False
        group_col = None
        if scope:
            scope_map = {}
            for s in scope:
                if ":" in s:
                    cat, val = s.split(":", 1)
                    scope_map.setdefault(cat, []).append(val)
            
            for cat, values in scope_map.items():
                if len(values) > 1:
                    has_multiple_values = True
                    group_col = scope_cols.get(cat)
                    break
        
        if has_multiple_values and group_col:
            conditions += f" GROUP BY {group_col}"

        # Final assembly
        if conditions:
            if conditions.upper().strip().startswith("GROUP BY"):
                final_sql = template.replace("{conditions}", conditions)
            else:
                final_sql = template.replace("{conditions}", f" AND {conditions}")
        else:
            final_sql = template.replace("{conditions}", "")
        
        # Adjust SELECT for GROUP BY
        if group_col and "GROUP BY" in conditions.upper():
            if "SELECT COUNT" in final_sql.upper() and group_col not in final_sql.split("FROM")[0]:
                final_sql = final_sql.replace("SELECT ", f"SELECT {group_col}, ", 1)
        
        print(f"Final SQL (Programmatic): {final_sql}")
        return final_sql



    def summarize_result(self, kpi: str, time_range: str, scope: List[str], data: Any, kpi_config: Dict) -> str:
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        kpi_desc = kpi_def.get('description', kpi).split(',')[0].split('.')[0].strip()
        scope_cols = kpi_def.get('scope_columns', {})
        
        # Reverse mapping for columns to friendly names
        col_to_label = {v: k.capitalize() for k, v in scope_cols.items()}
        # Common database columns to friendly names
        friendly_names = {
            "st_WrMonth": "月份",
            "st_DeptName": "产品组",
            "st_OrgName": "组织架构",
            "st_EmpNameCN": "姓名",
            "st_ProductLine": "产品线",
            "st_BU": "业务单元",
            "st_SN": "序列号",
            "st_EmpID": "工号",
            "st_ClassName": "岗位类别",
            "st_WorkLocation": "工作地点",
            "st_LEOName": "用工类型"
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
