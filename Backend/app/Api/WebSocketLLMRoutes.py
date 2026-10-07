#Maneja los WebSockets para el uso interno del LLM sin recuperar contexto de Qdrant.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from app.Services.RagService import execute_llm
from app.Services.DesicionService import callSimpleSystemOneJev


WSLLMRouter = APIRouter()

from functools import partial
from fastapi import WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool


@WSLLMRouter.websocket("/ws/llm")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint de WebSocket para manejar la comunicación en tiempo real con el LLM.
    """
    await websocket.accept()
    print("WebSocket connection accepted.")

    # Claves reservadas del protocolo del endpoint
    RESERVED_KEYS = {
        "query",
        "promptTemplate",
        "collectionName",
        "topK",
        "includeContextInResponse",
        "promptKwargs",
    }

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message from client: {data}")

            # 1. Extraer parámetros principales
            query = data.get("query")
            prompt_template = data.get("promptTemplate")
            collection_name = data.get("collectionName", None)
            top_k = data.get("topK", 5)
            include_context_in_response = data.get("includeContextInResponse", False)

            # Validación mínima de payload requerido
            if not query or not prompt_template:
                await websocket.send_json({"error": "Faltan campos obligatorios: 'query' o 'promptTemplate'"})
                continue

            # 2. Extraer prompt_kwargs:
            # Soporta tanto un sub-objeto {"promptKwargs": {...}}
            # como campos extra sueltos en la raíz del JSON
            prompt_kwargs = data.get("promptKwargs")
            if not isinstance(prompt_kwargs, dict):
                # Fallback: toma cualquier campo que no sea de los reservados
                prompt_kwargs = {k: v for k, v in data.items() if k not in RESERVED_KEYS}

            # 3. Ejecutar función bloqueante en threadpool usando functools.partial
            # partial es más seguro y limpio que un lambda con captura de clausuras
            task = partial(
                execute_llm,
                prompt_template=prompt_template,
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                include_context_in_response=include_context_in_response,
                **prompt_kwargs,  # <-- Se desempaquetan dinámicamente aquí
            )

            answer = await run_in_threadpool(task)

            # 4. Enviar respuesta al cliente (con fallback seguro por si la clave varía)
            payload_to_send = answer.get("text", answer)
            await websocket.send_json(payload_to_send)

    except WebSocketDisconnect:
        print("WebSocket connection closed by client.")
    except Exception as e:
        print(f"Error inesperado en WebSocket: {e}")
        await websocket.close()



@WSLLMRouter.websocket("/ws/decision")
async def websocket_decision_endpoint(websocket: WebSocket):
    """
    Endpoint de WebSocket para manejar la comunicación en tiempo real con el sistema de decisiones.
    Args:
        websocket (WebSocket): La conexión WebSocket con el cliente.
    """
    await websocket.accept()
    print("WebSocket connection accepted for decision system.")
    try:
        while True:
            # Espera a recibir un mensaje del cliente: {"idAnswer": "...", "type": "...", "state": "...", "instructions": "...", "criteria": {...}}
            data = await websocket.receive_json()
            id_answer = data["idAnswer"]
            question_type = data["type"]
            state = data["state"]
            instructions = data["instructions"]
            criteria = data.get("criteria", {})
            print(f"Received message from client for decision system: {data}")
            # Procesa la decisión usando el sistema de decisiones y genera la respuesta
            answer = await run_in_threadpool(
                lambda: callSimpleSystemOneJev(idAnswer=id_answer, type=question_type, state=state, instructions=instructions, criteria=criteria)
            )
            await websocket.send_json(answer)
    except WebSocketDisconnect:
        print("WebSocket connection closed by client for decision system.")