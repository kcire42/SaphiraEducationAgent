#Lógica de LangChain y Qdrant.
#Toma la pregunta, busca en la base vectorial y devuelve contexto.
from qdrant_client import QdrantClient
from typing import Any
from app.config import settings
from app.PreData.embeddings import get_embedding
from app.Services.LLMService import callLLM_Cloud

PROMPT_TEMPLATE = """Eres un tutor virtual. Responde la pregunta del estudiante \
usando únicamente el siguiente contexto extraído del temario del curso. \
Si el contexto no tiene la respuesta, dilo explícitamente en vez de inventar.
"""


def retrieve_context(query: str, collection_name: str = "temario", top_k: int = 5) -> list[str]:
    """
    Vectoriza la pregunta y busca en Qdrant los chunks más relevantes.

    Args:
        query: Pregunta del estudiante.
        collection_name: Colección de Qdrant donde buscar.
        top_k: Cantidad de chunks a recuperar.
    """
    # Defino el vector de la pregunta usando el mismo modelo de embedding que se usó para los documentos.
    query_vector = get_embedding(query, task_type="retrieval_query")
    # Conecto con Qdrant y busco los chunks más cercanos al vector de la pregunta.
    client = QdrantClient(url=settings.QDRANT_URL) 
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
    )
    # Extraigo el texto de los chunks recuperados y lo devuelvo como contexto.
    return [point.payload["text"] for point in results.points]


def build_prompt(
    template: str,
    context_chunks: list[str] | None = None,
    **placeholders: Any,
) -> str:
    """
    Formatea la plantilla inyectando el contexto consolidado
    y cualquier variable dinámica adicional (action, content, question, etc.).
    Args:
        template: Plantilla de prompt con placeholders.
        context_chunks: Lista de chunks de contexto recuperados.
        **placeholders: Variables dinámicas a inyectar en el prompt.
    """
    context = (
        "\n\n---\n\n".join(context_chunks)
        if context_chunks
        else "(sin contexto disponible)"
    )
    return template.format(context=context, **placeholders)


def execute_llm(
    prompt_template: str,
    query: str,
    collection_name: str | None = None,
    top_k: int = 5,
    include_context_in_response: bool = False,
    **prompt_kwargs: Any,
) -> dict[str, Any]:
    """
    Orquesta la ejecución del pipeline LLM con soporte opcional de RAG.

    Flujo operativo:
        1. Recuperación vectorial: Si `collection_name` está presente, consulta Qdrant
           usando `query` para obtener fragmentos semánticos.
        2. Modo directo/interno: Si `collection_name` es None o vacío, omite la búsqueda
           vectorial (ideal para llamadas entre microservicios o tareas sin contexto).
        3. Ensamblado: Inyecta el contexto recuperado y cualquier variable dinámica
           (`**prompt_kwargs`) en la plantilla `prompt_template`.
        4. Inferencia: Envía el prompt resultante al proveedor LLM y devuelve la respuesta.

    Args:
        prompt_template (str): Plantilla de texto con marcadores en formato `{variable}`.
            Nota: `{context}` es reservado para la inyección automática del contexto RAG.
        query (str): Texto de consulta del usuario o tarea a vectorizar en Qdrant.
        collection_name (str | None, optional): Nombre de la colección en Qdrant.
            Si es None, se salta la recuperación vectorial. Defaults to None.
        top_k (int, optional): Número máximo de fragmentos a recuperar de Qdrant.
            Defaults to 5.
        include_context_in_response (bool, optional): Si es True, incluye la lista
            de fragmentos recuperados en el payload retornado bajo la clave 'context'.
            Defaults to False.
        **prompt_kwargs (Any): Argumentos nombrados arbitrarios requeridos por
            los placeholders definidos en `prompt_template` (ej. role, tone, format_rules).

    Returns:
        dict[str, Any]: Diccionario con la respuesta del LLM y metadatos de ejecución.
            Ejemplo: `{"response": "...", "context": [...]}` (si include_context_in_response=True).

    Raises:
        KeyError: Si `prompt_template` contiene un placeholder `{variable}` que no fue
            proporcionado ni en los argumentos fijos ni en `**prompt_kwargs`.
        QdrantException: Si falla la conexión o búsqueda en la base vectorial.

    Example:
        >>> template = (
        ...     "Rol: {role}\\n"
        ...     "Contexto:\\n{context}\\n\\n"
        ...     "Pregunta: {query}\\n"
        ...     "Respuesta:"
        ... )
        >>> resultado = execute_llm_pipeline(
        ...     prompt_template=template,
        ...     query="¿Qué es una clave foránea?",
        ...     collection_name="docs_sql",
        ...     top_k=3,
        ...     role="Senior Data Engineer",
        ... )
        >>> print(resultado["response"])
    """
    # 1. Recuperación condicional de contexto
    context_chunks: list[str] = []
    if collection_name:
        context_chunks = retrieve_context(
            query=query,
            collection_name=collection_name,
            top_k=top_k,
        )

    # 2. Construcción de prompt
    prompt = build_prompt(
        template=prompt_template,
        context_chunks=context_chunks,
        query=query,
        **prompt_kwargs,
    )

    # 3. Invocación al modelo
    response = callLLM_Cloud(prompt)

    # 4. Adjuntar contexto si se requiere (ej. debug o consumo externo)
    if include_context_in_response:
        response["context"] = context_chunks

    return response

