import json
import websockets
from app.config import settings

async def ask_internal_llm(query: str, prompt_template: str, content: str) -> str:
    async with websockets.connect(settings.API_WS_URL) as ws:
        await ws.send(json.dumps({
            "query": query,
            "promptTemplate": prompt_template,
            "content": content,
        }))
        response = await ws.recv()
        return json.loads(response)

