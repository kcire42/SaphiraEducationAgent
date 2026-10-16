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

async def ask_descion_system_one_jev(id_answer,question_type,state,instructions,criteria) -> str:
    async with websockets.connect(settings.API_WS_URL_DECISION) as ws:
        await ws.send(json.dumps({
            "idAnswer": id_answer,
            "type": question_type,
            "state": state,
            "instructions": instructions,
            "criteria": criteria
        }))
        response = await ws.recv()
        return json.loads(response)

