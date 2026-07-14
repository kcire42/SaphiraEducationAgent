import uuid

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.PreData.embeddings import get_embeddings_batch
from app.PreData.text_chunker import (
    calculate_chunk_size,
    clean_text,
    optimize_chunks,
    split_into_chunks,
)

EMBEDDING_MODEL = "Gemini Embedding 2B"

# Namespace fijo para generar IDs determinísticos por contenido de chunk.
# Con esto, re-ingerir el mismo texto sobreescribe el punto existente en vez de duplicarlo.
_CHUNK_ID_NAMESPACE = uuid.UUID("2f3b1a6e-6e7a-4e2a-9b8e-5a5f7b6c9d10")


def _chunk_id(collection_name, chunk):
    return str(uuid.uuid5(_CHUNK_ID_NAMESPACE, f"{collection_name}:{chunk}"))


def loadData(route):
    """
    Carga un archivo (PDF o texto plano) desde la ruta especificada.

    Args:
        route (str): La ruta del archivo a cargar.
    """
    print(f"Cargando datos desde: {route}")
    extension = Path(route).suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(route)
    elif extension == ".txt":
        loader = TextLoader(route, encoding="utf8")
    else:
        raise ValueError(f"Extensión no soportada: '{extension}'. Usa .pdf o .txt")

    return loader.load()


def chuking_file(data, source="docs"):
    """
    Une el texto de las páginas del PDF y lo divide en chunks.

    Args:
        data (list): Documentos devueltos por el loader (uno por página).
        source (str): Tipo de limpieza a aplicar (ver text_chunker.clean_text).
    """
    full_text = "\n\n".join(page.page_content for page in data)
    cleaned_text = clean_text(full_text, source=source)
    chunk_size, chunk_overlap = calculate_chunk_size(cleaned_text, EMBEDDING_MODEL)
    chunks = split_into_chunks(cleaned_text, chunk_size, chunk_overlap)
    optimized_chunks = optimize_chunks(chunks)
    print(f"Total de chunks optimizados: {len(optimized_chunks)}")
    return optimized_chunks


def generate_embeddings(optimized_chunks):
    """
    Genera embeddings para los chunks utilizando la API de Gemini.

    Args:
        optimized_chunks (list): Lista de chunks optimizados.
    """
    embeddings = get_embeddings_batch(
        optimized_chunks, model_name=EMBEDDING_MODEL, task_type="retrieval_document"
    )
    print(f"Embeddings generados para {len(embeddings)} chunks.")
    return embeddings


def insert_into_qdrant(collection_name, optimized_chunks, embeddings):
    """
    Inserta los chunks y sus embeddings en la colección de Qdrant especificada.

    Args:
        collection_name (str): Nombre de la colección en Qdrant.
        optimized_chunks (list): Lista de chunks optimizados (se guardan como payload).
        embeddings (list): Lista de embeddings ya calculados para cada chunk.
    """
    client = QdrantClient(url=settings.QDRANT_URL)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
        )
        print(f"Colección '{collection_name}' creada en Qdrant.")
    else:
        print(f"Colección '{collection_name}' ya existe en Qdrant.")

    points = [
        PointStruct(id=_chunk_id(collection_name, chunk), vector=vector, payload={"text": chunk})
        for chunk, vector in zip(optimized_chunks, embeddings)
    ]
    client.upsert(collection_name=collection_name, points=points)
    print(f"{len(points)} embeddings insertados en la colección '{collection_name}' de Qdrant.")


def seed(route, collection_name):
    """
    Pipeline completo: carga el PDF, lo chunkea, genera embeddings y los sube a Qdrant.

    Args:
        route (str): Ruta del PDF a procesar.
        collection_name (str): Colección destino en Qdrant.
    """
    data = loadData(route)
    print(f"Datos cargados desde {route}. Total de páginas: {len(data)}")
    chunks = chuking_file(data)
    print(f"Chunks generados: {len(chunks)}")
    embeddings = generate_embeddings(chunks)
    print(f"Embeddings generados: {len(embeddings)}")
    insert_into_qdrant(collection_name, chunks, embeddings)
    print(f"Proceso de seed completado para la colección '{collection_name}'.")


if __name__ == "__main__":
    seed("app/Data/How_AI_Ruined_the_Classroom.txt", "temario")
