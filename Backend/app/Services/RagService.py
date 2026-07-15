#Lógica de LangChain y Qdrant.
#Toma la pregunta, busca en la base vectorial y devuelve contexto.
from qdrant_client import QdrantClient

from app.config import settings
from app.PreData.embeddings import get_embedding
from app.Services.LLMService import callLLM_Cloud

PROMPT_TEMPLATE = """Eres un tutor virtual. Responde la pregunta del estudiante \
usando únicamente el siguiente contexto extraído del temario del curso. \
Si el contexto no tiene la respuesta, dilo explícitamente en vez de inventar.

Contexto:
{context}

Pregunta:
{question}
"""


def retrieve_context(question: str, collection_name: str = "temario", top_k: int = 5) -> list[str]:
    """
    Vectoriza la pregunta y busca en Qdrant los chunks más relevantes.

    Args:
        question: Pregunta del estudiante.
        collection_name: Colección de Qdrant donde buscar.
        top_k: Cantidad de chunks a recuperar.
    """
    # Defino el vector de la pregunta usando el mismo modelo de embedding que se usó para los documentos.
    query_vector = get_embedding(question, task_type="retrieval_query")
    # Conecto con Qdrant y busco los chunks más cercanos al vector de la pregunta.
    client = QdrantClient(url=settings.QDRANT_URL) 
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
    )
    # Extraigo el texto de los chunks recuperados y lo devuelvo como contexto.
    return [point.payload["text"] for point in results.points]


def build_prompt(question: str, context_chunks: list[str]) -> str:
    """
    Arma el prompt final combinando el contexto recuperado y la pregunta.
    """
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(sin contexto disponible)"
    return PROMPT_TEMPLATE.format(context=context, question=question)


def answer_question(question: str, collection_name: str = "temario", top_k: int = 5) -> dict:
    """
    Pipeline completo de RAG: recupera contexto de Qdrant y genera la respuesta con el LLM.
    """
    context_chunks = retrieve_context(question, collection_name=collection_name, top_k=top_k)
    prompt = build_prompt(question, context_chunks)
    response = callLLM_Cloud(prompt)
    response["context"] = context_chunks
    return response



