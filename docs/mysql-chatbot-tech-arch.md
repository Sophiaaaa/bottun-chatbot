# MySQL 聊天机器人 - 技术架构

## 1. 系统概述
该应用程序采用标准的客户端-服务器架构。
- **前端：** 基于 React 的单页应用程序 (SPA)。
- **后端：** Python (FastAPI) 服务器。
- **AI 引擎：** 本地 Ollama 实例 (Qwen3)。
- **数据源：** 外部 MySQL 数据库。

## 2. 技术栈

### 前端
- **框架：** React (Vite)
- **UI 库：** Tailwind CSS (用于样式), Lucide React (图标)。
- **组件：** Shadcn/UI (推荐用于下拉菜单、按钮、聊天布局)。
- **HTTP 客户端：** Axios 或 Fetch。

### 后端
- **框架：** Python FastAPI。
- **数据库驱动：** `mysql-connector-python` 或 `SQLAlchemy` (Core)。
- **AI 集成：** `ollama` Python 库或直接调用 Ollama API 的 HTTP 请求。
- **配置：** YAML 或 JSON 文件。

### 基础设施
- **本地部署：** 在本地运行前端、后端和 Ollama。

## 3. 架构图

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

## 4. 数据流

1.  **初始化：** 后端加载 `db_config.yaml`, `schema_config.yaml`, `kpi_config.yaml`。
2.  **用户查询：** 用户向后端发送文本。
3.  **意图分析：**
    - **关键词匹配：** 后端首先检查高优先级的关键词（例如：“fe人数分析” -> `fe_count`）以进行即时识别。
    - **AI 分析：** 如果没有直接匹配，则将提示词 + 用户查询发送给 Ollama。
    - **输出：** 包含 `{ intent, kpi, time_range, scope, missing_params }` 的 JSON 对象。
4.  **交互循环 (如果缺少参数)：**
    - 后端向前端返回 `missing_params` 标志。
    - 前端渲染按钮/下拉菜单。
    - **级联逻辑：** 前端在获取下一个维度值时，将 `current_selection` (例如 `["product:CT"]`) 发送给后端。
    - 后端过滤 SQL 查询，仅返回当前上下文的有效选项。
5.  **SQL 生成：**
    - 后端将确认的参数发送给 Ollama 以生成 SQL（或对标准 KPI 使用程序化生成）。
6.  **执行：**
    - 后端在 MySQL 上运行 SQL。
    - 将结果 (JSON) 返回给前端。
7.  **可视化/导出：**
    - 前端请求“导出”或“图表” -> 后端处理数据并返回文件/图表配置。

## 5. 配置文件结构 (草案)

### `db_config.yaml`
```yaml
host: "localhost"
port: 3306
user: "readonly_user"
password: "secure_password"
database: "analytics_db"
```

### `ui_mappings.yaml` (按钮配置)
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

## 6. API 端点 (草案)

- `GET /config/init`: 获取 UI 配置（按钮列表、常见问题）。
- `POST /config/dimension`: 获取维度的唯一值。
    - **Body:** `{ kpi, dimension_type, current_selection: ["category:value"] }`
    - 通过 `current_selection` 支持级联筛选。
- `POST /chat/analyze`: 发送用户消息，返回分析结果（意图/缺失参数）。
- `POST /chat/sql`: 根据确认的上下文生成并执行 SQL。
- `POST /chat/download`: 生成下载文件 (Excel/CSV)。
