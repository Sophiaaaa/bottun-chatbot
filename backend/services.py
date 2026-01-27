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

    def get_unique_values(self, table_name: str, column_name: str) -> List[str]:
        conn = self.get_connection()
        if not conn:
            # Mock values for demo
            if "Month" in column_name or "date" in column_name:
                return ["202501", "202412", "202411"]
            return ["Value 1", "Value 2", "Value 3"]
            
        cursor = conn.cursor()
        try:
            sql = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY {column_name} DESC LIMIT 100"
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
            return ""

    def analyze_intent(self, query: str, kpi_config: Dict, ui_mappings: Dict) -> Dict[str, Any]:
        # Construct a prompt to analyze the user's query
        kpi_info = {k: v.get('description', '') for k, v in kpi_config.get('kpi_definitions', {}).items()}
        
        prompt = f"""
        Analyze user query: "{query}"
        
        [Context]
        Available KPIs (key: description): {json.dumps(kpi_info, ensure_ascii=False)}
        Available Time types: {[t['value'] for t in ui_mappings.get('time_options', {}).get('types', [])]}
        Available Scopes categories: {[s['value'] for s in ui_mappings.get('scope_options', {}).get('categories', [])]}
        
        [Task]
        Identify the KPI, time range, and scope from the query.
        - If the query mentions "FE", "Field Engineer", "FE人数", it's likely "fe_count".
        - If the query mentions a department like "CT", "3DI", "SPS", it's a "product" scope.
        - Scopes MUST be formatted as "category:value" (e.g., "product:CT", "organization:SPS").
        
        [Output Format]
        Return JSON ONLY: {{"kpi": "key", "time_range": "val", "scope": ["category:value"], "missing_params": []}}
        If a parameter is not found, set to null and add to "missing_params".
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

    def generate_where_clause(self, kpi: str, time_range: str, scope: List[str], kpi_config: Dict) -> str:
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        table_name = kpi_def.get('table_name', "")
        time_col = kpi_def.get('time_column', "")
        scope_cols = kpi_def.get('scope_columns', {})
        
        prompt = f"""
        [Instruction]
        Generate ONLY the raw MySQL WHERE clause conditions. 
        NO explanations, NO conversational text, NO markdown code blocks, NO thought process.
        
        [Input]
        Table: {table_name}
        KPI: {kpi}
        Time: {time_range} (Column: {time_col})
        Scope: {scope} (Mapping: {json.dumps(scope_cols, ensure_ascii=False)})
        
        [Logic]
        1. If Time is provided, use `{time_col} = 'TIME_VALUE'`.
        2. If Time is null/missing, use `{time_col} = (SELECT MAX({time_col}) FROM {table_name})`.
        3. If Scope is provided, map category to column name.
        4. If multiple values for the SAME category exist, use `IN ('val1', 'val2')`.
        5. If values for DIFFERENT categories exist, use `AND`.
        
        [Example]
        Input Scope: ["product:3DI", "product:CT"], Time: "202506"
        Output: {time_col} = '202506' AND st_DeptName IN ('3DI', 'CT')
        
        [Output]
        (Your conditions here)
        """
        print(f"Generating WHERE clause for {kpi}...")
        raw_response = self.generate_response(prompt).strip()
        
        # Clean up <think> tags if present
        if "</think>" in raw_response:
            conditions = raw_response.split("</think>")[-1].strip()
        else:
            conditions = raw_response
            
        # Clean up any potential markdown or extra text
        if "```" in conditions:
            conditions = conditions.split("```")[1]
            if conditions.startswith("sql"):
                conditions = conditions[3:].strip()
        
        # Remove common "thinking" prefixes if they leak through
        if "Output:" in conditions:
            conditions = conditions.split("Output:")[-1].strip()
        
        # Ensure it's just a single line/block of conditions
        conditions = conditions.split('\n')[0] if '\n' in conditions else conditions
        
        # Remove surrounding quotes if AI added them
        conditions = conditions.strip().strip('"').strip("'")
        
        return conditions or "1=1"

    def generate_sql(self, kpi: str, time_range: str, scope: List[str], kpi_config: Dict) -> str:
        # Get SQL template for the KPI
        kpi_def = kpi_config.get('kpi_definitions', {}).get(kpi, {})
        template = kpi_def.get('sql_template', "")
        table_name = kpi_def.get('table_name', "")
        time_col = kpi_def.get('time_column', "")
        scope_cols = kpi_def.get('scope_columns', {})
        
        if not template:
            return ""
            
        prompt = f"""
        [Instruction]
        Generate ONLY the raw MySQL WHERE clause conditions. 
        If multiple values for the SAME scope category are provided, the user wants a breakdown.
        In that case, append a `GROUP BY` clause to the conditions.
        
        NO explanations, NO conversational text, NO markdown code blocks, NO thought process.
        
        [Input]
        Table: {table_name}
        KPI: {kpi}
        Time: {time_range} (Column: {time_col})
        Scope: {scope} (Mapping: {json.dumps(scope_cols, ensure_ascii=False)})
        
        [Logic]
        1. Basic WHERE: `{time_col} = '...' AND scope_col = '...'`.
        2. Multiple values in same category: Use `scope_col IN ('val1', 'val2')`.
        3. Breakdown Rule: ONLY IF Scope has MORE THAN ONE value in the SAME category (e.g., 2+ products), 
           append `GROUP BY scope_column_name` at the end.
        4. Single Value Rule: If only ONE value is provided for a category (e.g., just one product), 
           do NOT use `GROUP BY`.
        5. IMPORTANT: If grouping, the KPI template `SELECT COUNT(...)` will be handled by the system, 
           you just provide the `WHERE ... GROUP BY ...` part.
        
        [Example 1 - Multiple]
        Input Scope: ["product:3DI", "product:CT"], Time: "202506"
        Output: {time_col} = '202506' AND st_DeptName IN ('3DI', 'CT') GROUP BY st_DeptName
        
        [Example 2 - Single]
        Input Scope: ["product:CT"], Time: "202506"
        Output: {time_col} = '202506' AND st_DeptName = 'CT'
        
        [Output]
        (Your conditions here)
        """
        print(f"Generating SQL conditions for {kpi}...")
        raw_response = self.generate_response(prompt).strip()
        
        # Clean up <think> tags if present
        if "</think>" in raw_response:
            conditions = raw_response.split("</think>")[-1].strip()
        else:
            conditions = raw_response
            
        # Clean up any potential markdown or extra text
        if "```" in conditions:
            conditions = conditions.split("```")[1]
            if conditions.startswith("sql"):
                conditions = conditions[3:].strip()
        
        # Remove common "thinking" prefixes if they leak through
        if "Output:" in conditions:
            conditions = conditions.split("Output:")[-1].strip()
        
        # Ensure it's just a single line/block of conditions
        conditions = conditions.split('\n')[0] if '\n' in conditions else conditions
        
        # Remove surrounding quotes if AI added them (safely)
        conditions = conditions.strip()
        if (conditions.startswith('"') and conditions.endswith('"')) or \
           (conditions.startswith("'") and conditions.endswith("'")):
            conditions = conditions[1:-1].strip()
        
        # Check if we need to adjust the SELECT clause for GROUP BY
        final_sql = template.replace("{conditions}", conditions)
        
        if "GROUP BY" in conditions.upper():
            group_col = conditions.upper().split("GROUP BY")[1].strip()
            # If the template starts with SELECT COUNT, insert the group column
            if "SELECT COUNT" in final_sql.upper():
                final_sql = final_sql.replace("SELECT ", f"SELECT {group_col}, ")
        
        print(f"Final SQL: {final_sql}")
        return final_sql

    def summarize_result(self, kpi: str, time_range: str, scope: List[str], data: Any, kpi_config: Dict) -> str:
        kpi_desc = kpi_config.get('kpi_definitions', {}).get(kpi, {}).get('description', kpi)
        
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
