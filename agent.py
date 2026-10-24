import json
from rich.console import Console
from rich.markdown import Markdown
from llm_utils import client
from tools import web_search, search_documents

MODEL = "gpt-5.6-luna"  # same as llm_utils

INSTRUCTIONS = """You are Jarvis. Use the tools you are provided with to answer the user's question
Do not get creative and execute your own code. Any response must have a valid citation or a reference. If the results don't answer it, say you don't know."""

FUNCS = {"web_search": web_search, "search_documents": search_documents}

TOOLS = [
    {
        "type": "function",
        "name": "web_search",
        "description": "Search the web for current or external info. Returns title, url, snippet.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "search_documents",
        "description": "Search the user's ingested policy documents. Returns relevant chunks.",
        "parameters": {
            "type": "object",
            "properties": {"user_query": {"type": "string"}},
            "required": ["user_query"],
        },
    },
]

def run_agent(question: str, max_turns: int = 5) -> tuple[str,str]:
    items = [{"role": "user", "content": question}]
    for i in range(max_turns):
        print(f"Turn {i+1} \n\n")
        resp = client.responses.create(
            model=MODEL, instructions=INSTRUCTIONS, input=items, tools=TOOLS
        )
        items += resp.output
        calls = [o for o in resp.output if o.type == "function_call"]
        if not calls:
            return resp.output_text,i+1
        for c in calls:
            result = FUNCS[c.name](**json.loads(c.arguments))
            items.append({
                "type": "function_call_output",
                "call_id": c.call_id,
                "output": json.dumps(result, default=str),
            })
            print(f"Function {c.name} called with arguments \n{c.arguments}. \nResult: {result} \n\n")
    return "Stopped: too many tool calls.",max_turns+1

ans,turns = run_agent("What was the entitlement in the archived policy?",max_turns=5)
print(f"Number of turns {turns}")
Console().print(Markdown(ans))


