from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
import re

def split_into_chunks(text:str, chunk_size:int=1000, chunk_overlap:int=200) -> list[str]:
    """
    Splits text into overlapping chunks using recursive character splitting.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]

    )
    return text_splitter.split_text(text)


def calculate_chunk_size(text:str,model_name:str) -> tuple[int,int]:
    """
    Defines the Chunk size based on the lenght of the text
    """
    model_info = settings.MODELS_EMBEDDINGS_REGISTRY.get(model_name)
    if not model_info:
        raise ValueError(f"Model '{model_name}' not found in registry.")

    max_tokens = model_info["max_tokens"]
    chars_per_token = model_info["chars_per_token"]

    max_chars = max_tokens * chars_per_token
    chunk_size = min(int(len(text) * 0.15), max_chars)
    chunk_size = max(chunk_size, 200)
    overlap = int(chunk_size * 0.2)
    return chunk_size,overlap

def clean_text(text,source="generic"):
    """
    Clean text based on the source, removing unwanted characters and formatting.
    """
    
    if source == "youtube":
        # Remueve timestamps: 12:34 o 1:23:45
        text = re.sub(r'\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b', '', text)
        # Remueve URLs
        text = re.sub(r'http[s]?://\S+', '', text)
    elif source == "docs":
       # Remueve referencias numéricas tipo [1], [40]
        text = re.sub(r'\[\d+\]', '', text)
        # Remueve referencias de letras tipo [a], [nota]
        text = re.sub(r'\[[a-zA-Z]+\]', '', text)
        # Remueve URLs
        text = re.sub(r'http[s]?://\S+', '', text)
    
    # --- REGLAS GLOBALES (Para todo texto) ---
    
    # 1. Eliminar caracteres invisibles (Zero-width spaces, etc.)
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)   
    
    # (OMITIDO INTENCIONALMENTE: No borrar [^\w\s] para conservar puntos y comas)
    
    # 2. Reemplazar múltiples espacios o tabs con un solo espacio
    text = re.sub(r'[ \t]+', ' ', text) 
    
    # 3. Limitar saltos de línea a un máximo de dos (vital para el Chunker)
    text = re.sub(r'\n{3,}', '\n\n', text) 
    
    # 4. Quitar espacios basura al inicio y al final
    return text.strip()

def optimize_chunks(chunks: list[str]) -> list[str]:
	"""
	Optimiza los chunks uniendo chunks pequeños con el siguiente chunk disponible.
	Si el chunk pequeño es el último, lo une con el chunk anterior.
	"""
	optimized_chunks: list[str] = []
	index = 0
	min_size = 100
	separator = "\n"

	while index < len(chunks):
		current_chunk = chunks[index]

		if len(current_chunk) < min_size and index + 1 < len(chunks):
			next_chunk = chunks[index + 1]

			print(f"Warning: Chunk of length {len(current_chunk)} is too short")

			optimized_chunks.append(
				current_chunk.rstrip() + separator + next_chunk.lstrip()
			)
			index += 2

		elif len(current_chunk) < min_size and index + 1 == len(chunks):
			print(
				f"Warning: Last chunk of length {len(current_chunk)} is too short. "
				"Merging with previous chunk."
			)

			if optimized_chunks:
				optimized_chunks[-1] = (
					optimized_chunks[-1].rstrip()
					+ separator
					+ current_chunk.lstrip()
				)
			else:
				optimized_chunks.append(current_chunk)

			index += 1

		else:
			optimized_chunks.append(current_chunk)
			index += 1

	return optimized_chunks