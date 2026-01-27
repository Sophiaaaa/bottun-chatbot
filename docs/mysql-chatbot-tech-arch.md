# MySQL Chatbot - Technical Architecture

## 1. System Overview
The application follows a standard Client-Server architecture.
- **Frontend:** React-based Single Page Application (SPA).
- **Backend:** Python (FastAPI) server.
- **AI Engine:** Local Ollama instance (Qwen3).
- **Data Source:** External MySQL Database.

## 2. Technology Stack

### Frontend
- **Framework:** React (Vite)
- **UI Library:** Tailwind CSS (for styling), Lucide React (Icons).
- **Components:** Shadcn/UI (recommended for dropdowns, buttons, chat layout).
- **HTTP Client:** Axios or Fetch.

### Backend
- **Framework:** Python FastAPI.
- **Database Driver:** `mysql-connector-python` or `SQLAlchemy` (Core).
- **AI Integration:** `ollama` python library or direct HTTP calls to Ollama API.
- **Configuration:** YAML or JSON files.

### Infrastructure
- **Local Deployment:** Run frontend, backend, and Ollama locally.

## 3. Architecture Diagram

```mermaid
graph TD
    User[User] -->|Interact| FE[Frontend (React)]
    FE -->|API Requests| BE[Backend (FastAPI)]
    
    subgraph "Backend Services"
        BE -->|Read Config| Config[Config Files (YAML/JSON)]
        BE -->|Generate SQL| AI[Ollama (Qwen3)]
        BE -->|Execute SQL| DB[(Target MySQL DB)]
    end
    
    Config -->|Define| Logic[Business Logic / Mappings]
```

## 4. Data Flow

1.  **Initialization:** Backend loads `db_config.yaml`, `schema_config.yaml`, `kpi_config.yaml`.
2.  **User Query:** User sends text to Backend.
3.  **Intent Analysis:**
    - Backend sends prompt + user query to Ollama.
    - Prompt includes schema summary and few-shot examples.
    - **Output:** JSON object containing `{ intent, kpi, time_range, scope, missing_params }`.
4.  **Interaction Loop (if missing params):**
    - Backend returns `missing_params` flag to Frontend.
    - Frontend renders buttons/dropdowns (populated from `kpi_config.yaml`).
    - User selects options -> sends back to Backend.
5.  **SQL Generation:**
    - Backend sends confirmed parameters to Ollama to generate SQL.
6.  **Execution:**
    - Backend runs SQL on MySQL.
    - Returns results (JSON) to Frontend.
7.  **Visualization/Export:**
    - Frontend requests "Export" or "Chart" -> Backend processes data and returns file/chart config.

## 5. Configuration File Structure (Draft)

### `db_config.yaml`
```yaml
host: "localhost"
port: 3306
user: "readonly_user"
password: "secure_password"
database: "analytics_db"
```

### `ui_mappings.yaml` (Button Config)
```yaml
kpi_levels:
  level1: ["Revenue", "Usage", "Performance"]
  level2_mapping:
    Revenue: ["MRR", "ARR", "Churn"]
    
time_options:
  types: ["FY", "Half", "Month"]
  
scope_options:
  categories: ["Product", "Organization", "Individual", "Tools"]
```

## 6. API Endpoints (Draft)

- `GET /config/init`: Get UI configurations (button lists, common questions).
- `POST /chat/analyze`: Send user message, returns analysis (intent/missing params).
- `POST /chat/sql`: Generate and execute SQL based on confirmed context.
- `POST /chat/export`: Generate download file.
```
