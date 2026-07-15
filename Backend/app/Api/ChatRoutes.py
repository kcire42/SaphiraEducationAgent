#Maneja los WebSockets para el chat en tiempo real con el estudiante.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from app.Services.RagService import answer_question

chatRouter = APIRouter()

@chatRouter.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted.")
    try:
        while True:
            # Espera a recibir un mensaje del cliente (el prompt del estudiante)
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")
            # Procesa la pregunta usando el pipeline RAG y genera la respuesta
            answer = await run_in_threadpool(
                lambda: answer_question(question=data, collection_name="temario", top_k=5)
            )
            await websocket.send_json(answer)
    except WebSocketDisconnect:
        print("WebSocket connection closed by client.")