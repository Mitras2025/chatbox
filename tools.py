
import json
import math
from typing import Any, Dict

# ---- Example Tools ----
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression safely (supports +,-,*,/,**, parentheses)."""
    allowed = set('0123456789+-*/(). %')
    if not set(expression) <= allowed:
        return json.dumps({"error": "Only basic arithmetic is allowed."})
    try:
        # limit builtins
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

def python_eval(code: str) -> str:
    """Run tiny, restricted Python snippets (e.g., string ops, simple math)."""
    SAFE_GLOBALS = {"__builtins__": {"len": len, "range": range, "sum": sum, "min": min, "max": max, "abs": abs}}
    SAFE_LOCALS: Dict[str, Any] = {}
    try:
        # If it's an expression, eval; otherwise exec and return any 'result' variable.
        try:
            out = eval(code, SAFE_GLOBALS, SAFE_LOCALS)
            return json.dumps({"result": out})
        except SyntaxError:
            exec(code, SAFE_GLOBALS, SAFE_LOCALS)
            out = SAFE_LOCALS.get("result", "(no result variable set)")
            return json.dumps({"result": out})
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---- Registry & Schemas ----
TOOLS_REGISTRY = {
    "calculator": calculator,
    "python_eval": python_eval,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Safely evaluate a basic arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "An arithmetic expression, e.g., '2*(3+5)'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "python_eval",
            "description": "Run a restricted Python snippet (for quick helpers). Returns 'result'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code; set a 'result' variable or use an expression."}
                },
                "required": ["code"]
            }
        }
    }
]
