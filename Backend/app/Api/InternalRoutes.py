#Maneja los WebSockets para el uso interno del LLM sin recuperar contexto de Qdrant.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from app.Services.RagService import internal_answer_question


internalChatRouter = APIRouter()

@internalChatRouter.websocket("/ws/internal/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted.")
    try:
        while True:
            # Espera a recibir un mensaje del cliente: {"question": "...", "promptTemplate": "..."}
            data = await websocket.receive_json()
            question = data["question"]
            prompt_template = data["promptTemplate"]
            print(f"Received message from client: {data}")
            # Procesa la pregunta usando el pipeline RAG y genera la respuesta
            answer = await run_in_threadpool(
                lambda: internal_answer_question(question=question, promptTemplate=prompt_template)
            )
            await websocket.send_json(answer['text'])
    except WebSocketDisconnect:
        print("WebSocket connection closed by client.")