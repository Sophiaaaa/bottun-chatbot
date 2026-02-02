from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import uvicorn
import io
import os
import pandas as pd
from services import ConfigService, DatabaseService, AIService

app = FastAPI()

# CORS configuration
origins = ["*"] # Allow all for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
config_service = ConfigService()
db_service = DatabaseService(config_service.get_db_config())
# Ensure exception table exists
db_service.init_exception_table()

# Use a more likely model name or allow env override
model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
ai_service = AIService(model=model_name)

# --- Pydantic Models ---
class AnalysisContext(BaseModel):
    kpi: Optional[str] = None
    time_range: Optional[str] = None
    scope: Optional[List[str]] = None

class ChatRequest(BaseModel):
    query: str
    context: Optional[AnalysisContext] = None

class SQLGenerationRequest(BaseModel):
    kpi: str
    time_range: str
    scope: List[str]

class DimensionRequest(BaseModel):
    kpi: str
    dimension_type: str # 'time' or 'organization', 'product', etc.
    current_selection: Optional[List[str]] = [] # For cascading filters e.g. ["product:CT"]

# --- Helper Functions ---

def get_kpi_definition(kpi_name: str, kpi_config: Dict):
    """Finds KPI definition by key or fuzzy match on description."""
    kpi_definitions = kpi_config.get('kpi_definitions', {})
    
    # 1. Exact match
    if kpi_name in kpi_definitions:
        return kpi_name, kpi_definitions[kpi_name]
    
    # 2. Fuzzy match
    print(f"KPI '{kpi_name}' not found exactly. Trying fuzzy match...")
    for k, v in kpi_definitions.items():
        desc = v.get('description', '').lower()
        if kpi_name.lower() in k.lower() or kpi_name.lower() in desc:
            print(f"Fuzzy matched '{kpi_name}' to '{k}'")
            return k, v
            
    return None, None

# --- Endpoints ---

@app.get("/config/init")
def get_ui_config():
    """Returns the UI configurations for dropdowns and buttons."""
    return config_service.get_ui_mappings()

@app.post("/config/dimension")
def get_dimension_values(request: DimensionRequest):
    """Fetches unique values for a specific dimension of a KPI."""
    print(f"Dimension Request: {request}")
    kpi_config = config_service.get_kpi_config()
    
    kpi_key, kpi_def = get_kpi_definition(request.kpi, kpi_config)
    
    if not kpi_def:
        print(f"KPI '{request.kpi}' not found")
        raise HTTPException(status_code=404, detail="KPI not found")
    
    table_name = kpi_def.get('table_name')
    column_name = None
    
    if request.dimension_type == 'time':
        column_name = kpi_def.get('time_column')
    else:
        column_name = kpi_def.get('scope_columns', {}).get(request.dimension_type)
        
    if not table_name or not column_name:
        return {"values": []}
        
    # Pass filters to get_unique_values
    filters = {}
    if request.current_selection:
        scope_cols = kpi_def.get('scope_columns', {})
        for s in request.current_selection:
            if ":" in s:
                cat, val = s.split(":", 1)
                
                # Prevent self-filtering: Don't filter a dimension by itself
                # This allows users to see other options in the dropdown even if one is selected
                if cat == request.dimension_type:
                    continue
                    
                # Map category to actual column name
                filter_col = scope_cols.get(cat)
                if filter_col:
                     filters.setdefault(filter_col, []).append(val)

    values = db_service.get_unique_values(table_name, column_name, filters)
    return {"values": values}

@app.post("/chat/analyze")
def analyze_query(request: ChatRequest):
    """Analyzes user query to find intent and missing parameters."""
    kpi_config = config_service.get_kpi_config()
    ui_mappings = config_service.get_ui_mappings()
    
    # Convert context to dict if exists
    context_dict = request.context.dict() if request.context else {}
    
    analysis = ai_service.analyze_intent(request.query, kpi_config, ui_mappings, context_dict, db_service)
    return analysis

@app.post("/chat/sql")
def generate_and_execute_sql(request: SQLGenerationRequest):
    """Generates SQL based on confirmed params and executes it."""
    kpi_config = config_service.get_kpi_config()
    
    # 1. Generate SQL
    sql = ai_service.generate_sql(request.kpi, request.time_range, request.scope, kpi_config)
    
    # 2. Execute SQL
    # Note: In a real scenario, validate SQL or use read-only user
    result = db_service.execute_query(sql)
    
    # 3. Generate natural language summary
    summary = ai_service.summarize_result(
        request.kpi, 
        request.time_range, 
        request.scope, 
        result.get('data', []), 
        kpi_config
    )
    
    return {
        "sql": sql,
        "result": result,
        "summary": summary
    }

@app.post("/chat/download")
def download_detail(request: SQLGenerationRequest):
    """Generates a detailed SQL (SELECT *) and returns an Excel file."""
    kpi_config = config_service.get_kpi_config()
    
    # Use helper for robust KPI lookup
    kpi_key, kpi_def = get_kpi_definition(request.kpi, kpi_config)
    
    if not kpi_def:
        raise HTTPException(status_code=404, detail=f"KPI '{request.kpi}' not found")
        
    sql_template = kpi_def.get('sql_template')
    if not sql_template:
        raise HTTPException(status_code=400, detail="SQL template not found for KPI")
        
    # 1. Generate WHERE clause (using the matched kpi_key)
    conditions = ai_service.generate_where_clause(kpi_key, request.time_range, request.scope, kpi_config)
    
    # 2. Transform sql_template from SELECT COUNT... to SELECT *
    # Find the position of 'FROM'
    from_index = sql_template.upper().find('FROM')
    if from_index == -1:
        raise HTTPException(status_code=500, detail="Invalid SQL template format")
        
    base_sql = "SELECT * " + sql_template[from_index:]
    sql = base_sql.replace("{conditions}", conditions)
    print(f"Download Detail SQL: {sql}")
    
    # 3. Get Data as DataFrame
    df = db_service.get_df_from_query(sql)
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for the given criteria")
        
    # 4. Generate Excel in memory
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Details')
    except Exception as e:
        print(f"Excel Generation Error: {e}")
        # Fallback to CSV if Excel fails
        df.to_csv(output, index=False)
        filename = f"{kpi_key}_details.csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    xlsx_data = output.getvalue()
    
    # 5. Return Response
    filename = f"{kpi_key}_details.xlsx"
    return Response(
        content=xlsx_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/")
def read_root():
    return {"message": "MySQL Chatbot Backend is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
