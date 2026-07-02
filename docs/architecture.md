# Architecture & Pipeline Diagram

## AI Pipeline Flow

```mermaid
flowchart TD
    %% Styling definitions
    classDef ingest fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af;
    classDef storage fill:#f3e8ff,stroke:#7c3aed,stroke-width:2px,color:#6d28d9;
    classDef chat fill:#d1fae5,stroke:#059669,stroke-width:2px,color:#065f46;
    classDef llm fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;
    classDef tool fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef memory fill:#e2e8f0,stroke:#475569,stroke-width:2px,color:#1e293b;

    %% Ingestion Pipeline
    subgraph Ingestion["Document Ingestion Pipeline"]
        A[/"1. POST /api/v1/ingest<br/>(UploadFile)"/]:::ingest
        B{"2. Validate Extension<br/>(.pdf, .txt, .md)"}:::ingest
        C["3. Extract Text<br/>(PyPDF2 / utf-8 text)"]:::ingest
        D["4. Text Chunking<br/>(RecursiveCharacterTextSplitter)"/]:::ingest
        E["5. Generate Embeddings<br/>(fastembed BGE-small)"]:::ingest
    end

    A --> B
    B -->|Valid| C
    B -->|Invalid| B_Err["HTTP 400 Bad Request"]:::ingest
    C --> D
    D --> E

    %% Storage
    subgraph Storage["Vector DB Storage"]
        DB[("ChromaDB Collection<br/>(knowledge_base)")]:::storage
    end

    E -->|Upsert Chunks + Embeddings| DB

    %% Chat Pipeline
    subgraph ChatAPI["Chat API (POST /api/v1/chat)"]
        F[/"1. ChatRequest<br/>(message, session_id)"/]:::chat
        G["2. Load Session History<br/>(MemoryService)"/]:::memory
        H["3. Retrieve top-k context<br/>(ChromaDB Query)"]:::chat
    end

    F --> G
    F --> H
    DB -->|Similarity Search| H

    subgraph LLMOrchestration["AI Pipeline Orchestrator (llm.py)"]
        I["4. Compile Messages<br/>(System Prompt + History + Context + Query)"]:::llm
        J["5. First LLM Call<br/>(Groq Llama-3.3)"/]:::llm
        K{"6. Classify Intent"}:::llm
    end

    G --> I
    H --> I
    I --> J
    J --> K

    %% Tool Routing
    subgraph ToolCalling["Tool Calling Flow"]
        T_JSON["LLM outputs Tool JSON<br/>{'tool': '...', 'args': {...}}"]:::llm
        T_Exec{"Tool Router"}:::tool
        T_Order["get_order_status<br/>(orders.json)"]:::tool
        T_Prod["search_product<br/>(products.json fuzzy)"]:::tool
        T_Result["Tool Text Output"]:::tool
        LLM_Format["7. Second LLM Call<br/>(Format results naturally)"]:::llm
    end

    K -->|Tool Request JSON| T_JSON
    T_JSON --> T_Exec
    T_Exec -->|get_order_status| T_Order
    T_Exec -->|search_product| T_Prod
    T_Order --> T_Result
    T_Prod --> T_Result
    T_Result --> LLM_Format

    subgraph DirectRouting["RAG / Direct Conversation"]
        R_Text["Generate direct answer"]:::llm
        R_Fallback{"Context Check"}:::chat
        R_Context["Answer using Context<br/>+ Append Sources"]:::chat
        R_NoContext["'I couldn't find that information<br/>in the uploaded documents.'"]:::chat
    end

    K -->|General Conversation| R_Text
    K -->|RAG Question| R_Fallback
    R_Fallback -->|Found| R_Context
    R_Fallback -->|Not Found| R_NoContext

    %% Finalize & Return
    subgraph Output["Output & Memory Updates"]
        M_Update["8. Add messages to history<br/>(Auto-trimmed to last 20)"]:::memory
        M_Resp[/"9. ChatResponse<br/>(response, sources, tool_used)"/]:::chat
    end

    LLM_Format --> M_Update
    R_Text --> M_Update
    R_Context --> M_Update
    R_NoContext --> M_Update

    M_Update --> M_Resp
```

## Component Overview

| Layer | Component | Responsibility |
|-------|-----------|---------------|
| API | `endpoints/ingest.py` | File upload, validation |
| API | `endpoints/chat.py` | Message handling, orchestration |
| Service | `ingestion.py` | Load → chunk → embed → store |
| Service | `retrieval.py` | Semantic search over ChromaDB |
| Service | `llm.py` | LLM calls, tool call parsing |
| Service | `memory.py` | Session-scoped conversation history |
| Service | `tools.py` | Order status, product search |
| Data | ChromaDB | Vector storage (persistent) |
| Data | `orders.json` / `products.json` | Mock tool data |
