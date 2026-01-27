# MySQL Chatbot - Product Requirements Document (PRD)

## 1. Product Overview
**Product Name:** MySQL Chatbot
**Description:** An intelligent chatbot interface for querying MySQL databases using natural language. It utilizes a local Ollama (Qwen3) model for intent understanding and SQL generation. The system is highly configurable via external configuration files.

## 2. User Roles
- **General User:** Can ask questions, interact with parameter selection buttons, view results, and download data.
- **Administrator:** Configures database connections, table structures, KPIs, and prompt templates via configuration files.

## 3. Core Features

### 3.1. Configuration Management
The system must read the following from configuration files:
- **Database Connection:** MySQL host, port, user, password, database name.
- **Table Structure:** Schema definitions relevant to the bot.
- **KPI Definitions:** Mapping of KPIs to database fields/logic.
- **Example SQLs:** Few-shot examples for the LLM.
- **Field Mappings:** Configuration for UI buttons (KPI categories, Time periods, Object scopes).

### 3.2. Chat Interface (OpenAI Style)
- **Home Page:**
    - Main chat window.
    - "Common Questions" quick-access buttons.
- **Chat Bubbles:**
    - User questions (Right aligned).
    - Bot responses (Left aligned).
    - Status/Context Display: Small grey italic text below bubbles showing:
        - *Confirmed KPI*
        - *Confirmed Time Range*
        - *Confirmed Object Scope*
        - *Generated SQL*

### 3.3. Interactive Query Logic
The bot analyzes user input to ensure all necessary parameters are present before generating SQL.

#### 3.3.1. Parameter Validation & Fallback UI
If the LLM detects missing information, it triggers specific UI elements below the chat bubble:

1.  **KPI Missing:**
    - Show **Level 1 KPI** buttons.
    - On click, show **Level 2 KPI** dropdown menu.
2.  **Time/Date Missing:**
    - Show **FY / Half-Year / Month** buttons.
    - On click, show corresponding dropdown for single selection.
3.  **Object Scope Missing:**
    - Show **Product / Organization / Individual / Tools** buttons.
    - On click, show dropdown for **Multi-selection**.

*Note: The content of these buttons and dropdowns is driven by the configuration file.*

#### 3.3.2. Query Execution & Results
- Once parameters are confirmed, the bot generates SQL.
- Executes SQL against the configured MySQL database.
- Displays text results in the chat.

#### 3.3.3. Follow-up Actions
- After showing results, the bot asks: "Do you need detailed data or charts?"
- Displays two buttons:
    1.  **Detail File**: Downloads the result set as a file (CSV/Excel).
    2.  **Charts**: Renders a visual chart of the data in the chat window.

## 4. Non-Functional Requirements
- **Model:** Local Ollama deployment using `qwen3`.
- **Performance:** SQL generation and execution should be reasonably fast.
- **Security:** Read-only database access recommended for the chatbot connection.
