
# Local ChatGPT‑style Python Chatbot

A local chatbot that:
- Uses the **OpenAI GPT API**
- Provides a **web chat UI** (Streamlit) similar to ChatGPT (bubbles, markdown, code blocks)
- Supports **tools / function calling** (calculator + Python eval sample)
- Easy to extend to your own tools, databases, or APIs

## Quick Start (local)

1. **Install Python 3.10+**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install deps**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your API key**:
   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY`
   - Or set environment variable directly before launch

5. **Run the app**:
   ```bash
   streamlit run app.py
   ```

6. Open the local URL that Streamlit prints (usually http://localhost:8501).

## Features

- **Chat UI** with persistent history in session
- **Streaming** responses (toggle)
- **Markdown & code** rendering
- **File upload** (txt/markdown) to feed the model extra context
- **Tool calling** via OpenAI function-calling:
  - `calculator` — safe eval for arithmetic
  - `python_eval` — restricted Python eval for quick helpers (strings, math)
- **Easy extensibility** — add new tools in `tools.py` and register them

## Adding your own tools

1. Implement a Python function in `tools.py`. It must accept **only JSON-serializable arguments** and return a **string** result.
2. Add a matching JSON schema entry to `TOOLS_SPEC` (also in `tools.py`) so the model can discover and call it.
3. Register it in `TOOLS_REGISTRY` with the same name.

Example:
```python
def my_search(query: str, top_k: int = 3) -> str:
    # call your API here
    return json.dumps({"results": ["a", "b", "c"]})
```

Expose to the model:
```python
TOOLS_REGISTRY["my_search"] = my_search

TOOLS_SPEC.append({
    "type": "function",
    "function": {
        "name": "my_search",
        "description": "Run a search over my private docs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    }
})
```

## Notes

- This sample uses the modern OpenAI Python SDK.
- Default model is `gpt-4o-mini` for speed/cost. You can pick others in the sidebar.
- For DB integration, call your DB client from a tool function and return summarized results.

## Troubleshooting

- If you see auth errors, re-check your API key and `.env` load.
- If streaming freezes, disable streaming in the sidebar (some corporate proxies interfere).
- For Windows PowerShell, you may need: `setx OPENAI_API_KEY "sk-..."` then restart the shell.
