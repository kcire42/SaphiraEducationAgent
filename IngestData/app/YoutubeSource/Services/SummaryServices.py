import json
import websockets
from app.config import settings

async def ask_internal_llm(question: str, prompt_template: str) -> str:
    async with websockets.connect(settings.API_WS_URL) as ws:
        await ws.send(json.dumps({
            "question": question,
            "promptTemplate": prompt_template
        }))
        response = await ws.recv()
        return json.loads(response)

if __name__ == "__main__":
    import asyncio
    question = "¿Cuál es la capital de Francia?"
    prompt_template = "Responde de manera concisa. Pregunta: {question}"
    answer = asyncio.run(ask_internal_llm(question, prompt_template))
    print(f"Respuesta del LLM interno: {answer}")
