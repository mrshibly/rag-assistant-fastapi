# Architecture & Pipeline Diagram

## AI Pipeline Flow

```mermaid
flowchart TD
    %% Styling Definitions
    classDef ingest fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af;
    classDef chat fill:#d1fae5,stroke:#059669,stroke-width:2px,color:#065f46;
    classDef llm fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;

    %% 1. Document Ingestion Pipeline
    subgraph Ingestion ["1. DOCUMENT INGESTION PIPELINE"]
        direction LR
        I1["Upload Document<br/>(PDF / TXT / MD)"]:::ingest --> I2["Load Document<br/>(PyPDF2 / text)"]:::ingest
        I2 --> I3["Split into Chunks<br/>(RecursiveCharacter)"]:::ingest
        I3 --> I4["Generate Embeddings<br/>(fastembed BGE-small)"]:::ingest
        I4 --> I5["Store in Database<br/>(ChromaDB Collection)"]:::ingest
    end

    %% 2. Chat & Retrieval Pipeline
    subgraph Chat ["2. CHAT & RETRIEVAL PIPELINE"]
        direction TB
        C1["User Message<br/>(ChatRequest)"]:::chat --> C2["Load Session Memory<br/>(MemoryService)"]:::chat
        C2 --> C3["Retrieve Context<br/>(ChromaDB Query)"]:::chat
        C3 --> C4["Orchestrate LLM<br/>(Groq Llama-3.3)"]:::llm
        
        %% Decision Branches
        C4 --> B1["Execute Tool<br/>(orders.json / products.json)"]:::chat
        C4 --> B2["RAG Context Answer<br/>(From retrieved text)"]:::chat
        C4 --> B3["Direct Response<br/>(General / memory)"]:::chat
        
        %% Convergence
        B1 --> M1["Update Conversation Memory<br/>(add user/assistant messages)"]:::chat
        B2 --> M1
        B3 --> M1
        
        M1 --> R1["Return Response<br/>(ChatResponse)"]:::chat
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
