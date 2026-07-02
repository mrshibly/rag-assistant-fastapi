import json
import logging

from groq import Groq

from app.config import settings
from app.services.retrieval import retrieve
from app.services.tools import TOOL_DEFINITIONS, TOOL_REGISTRY

logger = logging.getLogger(__name__)

_client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = f"""You are a helpful AI assistant with access to tools and a knowledge base.

Available tools:
{json.dumps(TOOL_DEFINITIONS, indent=2)}

RULES (follow in this priority order):
1. TOOL CALLS TAKE PRIORITY. Before answering, check if the query matches a tool:
   - Order-related queries (status, tracking, delivery, "where is my order") → respond ONLY with:
     {{"tool": "get_order_status", "args": {{"order_id": "<ID>"}}}}
   - Product-related queries (availability, price, stock, "do you have", search) → respond ONLY with:
     {{"tool": "search_product", "args": {{"query": "<product name>"}}}}
2. When making a tool call, output ONLY the raw JSON object. No other text.
3. For general conversation (greetings, names, follow-ups), respond directly.
4. If knowledge context is provided, use it to answer. If the context doesn't contain the answer, say:
   "I couldn't find that information in the uploaded documents."
5. NEVER answer product or order questions from knowledge context — ALWAYS use the tool."""


async def generate_response(
    message: str,
    history: list[dict],
) -> dict:
    """Orchestrate: retrieve context → call LLM → handle tool calls if needed."""
    # Retrieve relevant context from knowledge base
    context_chunks = retrieve(message)
    context_text = ""
    sources = []
    if context_chunks:
        context_text = "\n\n---\n\n".join(c["text"] for c in context_chunks)
        sources = list({c["source"] for c in context_chunks})

    # Build messages for the LLM
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)

    user_content = message
    if context_text:
        user_content = f"Knowledge Context:\n{context_text}\n\nUser Question: {message}"

    messages.append({"role": "user", "content": user_content})

    try:
        response = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("LLM API call failed: %s", e)
        return {
            "response": "I'm having trouble connecting to the AI service. Please try again shortly.",
            "sources": None,
            "tool_used": None,
        }

    # Check if the LLM returned a tool call
    tool_result = _try_tool_call(answer)
    if tool_result:
        tool_name, result_text = tool_result
        logger.info("Tool called: %s", tool_name)
        # Second LLM call to format the tool result naturally
        messages.append({"role": "assistant", "content": answer})
        messages.append({
            "role": "user",
            "content": f"Tool '{tool_name}' returned:\n{result_text}\n\nPlease relay this information to the user in a natural, helpful way.",
        })
        try:
            final = _client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return {
                "response": final.choices[0].message.content.strip(),
                "sources": None,
                "tool_used": tool_name,
            }
        except Exception as e:
            logger.error("LLM formatting call failed: %s", e)
            return {
                "response": result_text,
                "sources": None,
                "tool_used": tool_name,
            }

    return {
        "response": answer,
        "sources": sources or None,
        "tool_used": None,
    }


def _try_tool_call(text: str) -> tuple[str, str] | None:
    """Parse LLM output for a JSON tool call and execute it."""
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(cleaned)
        tool_name = data.get("tool")
        args = data.get("args", {})
        if tool_name and tool_name in TOOL_REGISTRY:
            result = TOOL_REGISTRY[tool_name](**args)
            return tool_name, result
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    return None


from app.schemas.chat import ChatRequest, ChatResponse
from app.services.memory import memory_service


async def process_chat(request: ChatRequest) -> ChatResponse:
    """Coordinate chat history, LLM response, and memory updates."""
    logger.info("Chat request | session=%s", request.session_id)
    history = memory_service.get_history(request.session_id)

    result = await generate_response(
        message=request.message,
        history=history,
    )

    memory_service.add_message(request.session_id, "user", request.message)
    memory_service.add_message(request.session_id, "assistant", result["response"])

    return ChatResponse(**result)

