# Architecture & Pipeline Diagram

## AI Pipeline Flow

```mermaid
flowchart TD
    subgraph Ingestion["Document Ingestion"]
        A["User uploads PDF/TXT/MD"] --> B["Load document"]
        B --> C["Split into chunks"]
        C --> D["Generate embeddings<br/>(fastembed)"]
        D --> E["Store in ChromaDB"]
    end

    subgraph Chat["Chat Pipeline"]
        F["User sends message"] --> G["Load session memory"]
        G --> H["Retrieve context<br/>from ChromaDB"]
        H --> I["Send to LLM<br/>(Groq + history + context)"]
        I --> J{"LLM decides action"}
        J -->|"Tool call JSON"| K["Execute tool<br/>(order status / product search)"]
        J -->|"Knowledge answer"| L["Return answer<br/>with sources"]
        J -->|"Direct response"| M["Return response"]
        K --> N["LLM formats<br/>tool result"]
        N --> O["Update session memory"]
        L --> O
        M --> O
        O --> P["Return ChatResponse"]
    end
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
