# Saphira — Asistente personal de IA

## Objetivo del proyecto

Saphira es un **asistente personal de inteligencia artificial** para apoyarnos día con día: entiende contenido, conversa y **ejecuta tareas**. Se usa desde una app móvil (Flutter) y, más adelante, por voz y por apps de mensajería.

La primera capacidad es **ayudarnos a estudiar**. Ingiere contenido (documentos y videos de YouTube), lo transcribe, resume, categoriza y vectoriza, y responde preguntas sobre él con RAG. Sobre esa base se agregarán:

- **Análisis de datos**: subir CSV o Excel y pedir análisis y gráficas.
- **Traducción de libros PDF completos** a varios idiomas.
- **Reconocimiento de imágenes** (visión multimodal).
- **Interacción con WhatsApp e Instagram**.
- **Comandos de voz** y control de otras apps del teléfono.

La hoja de ruta por fases está en [`PLAN.md`](PLAN.md).

## Arquitectura

```
Flutter (pendiente) ──► nginx :80 ──► api (FastAPI :8000)
                                        ├─► Qdrant :6333     (vectores RAG)
                                        ├─► Postgres :5432   (pgvector, esquema youtube)
                                        ├─► Gemini           (LLM + embeddings)
                                        └─► TypeSafe / JEV   (decisiones: Choice, Score, Noul)

ingest_data (yt-dlp + Whisper) ──► Postgres (SPs)
              └── WebSocket interno ──► api /ws/llm (resumen), /ws/decision (categoría)

flyway ──► aplica las migraciones de DataBase/ al levantar
```

- Todos los contenedores comparten la red externa `saphira_network`.
- `docker-compose.data.yml`: qdrant y postgres (puertos ligados a `127.0.0.1`).
- `docker-compose.app.yml`: flyway, api, ingest_data y nginx (el único expuesto, en `:80`, con soporte de WebSocket).
- `docker-compose.yml`: versión todo-en-uno, más antigua.

## Estructura de carpetas

| Carpeta | Contenido |
|---|---|
| `Backend/app/` | API FastAPI (Python 3.12). `main.py` monta los routers. `config.py` define los registros de modelos LLM y de embeddings. |
| `Backend/app/Api/` | `Utilities.py` (`/utilities/health`, `/utilities/training`) y `WebSocketLLMRoutes.py` (`/ws/llm`, `/ws/decision`). |
| `Backend/app/Services/` | `RagService.py` (`execute_llm`: RAG opcional + plantilla de prompt), `LLMService.py` (Gemini), `DesicionService.py` (`callSimpleSystemOneJev`), `AgentService.py` (vacío, núcleo futuro del agente). |
| `Backend/app/PreData/` | Chunking, embeddings y seed de documentos a Qdrant. |
| `IngestData/app/` | Pipeline de ingesta de YouTube (Python 3.11). `main.py` ejecuta las etapas en secuencia. |
| `IngestData/app/YoutubeSource/` | `Services/` (YouTube, transcripción, resumen, categoría), `Database/DatabaseManager.py` (un wrapper por SP o función), `IntegrityData/`, `Utilities/`. |
| `IngestData/app/Api/` | Cliente WebSocket interno hacia la api. |
| `DataBase/` | Migraciones Flyway: `Tables/` (`V<n>__`), `StoreProcedures/`, `Functions/`, `Views/` y `Triggers/` (`R__`). |
| `DataScience/` | Notebooks y scripts de ML (esqueleto). |
| `nginx/` | Reverse proxy. |

## Pipeline de ingesta de YouTube

Cada video avanza por una máquina de estados en `youtube.processing.status` (enum `youtube.processing_status`):

```
pending → downloaded → validate → processed → summary → category → vector → learning → completed
                                (cualquier etapa) → error  (+ registro en youtube.error_logs)
```

Cada etapa consulta los videos de un estado con `db_get_videos_by_status(status)`, los procesa y llama a un SP que guarda el resultado y avanza el estado.

## Comandos

```bash
docker network create saphira_network
docker compose -f docker-compose.data.yml up -d
docker compose -f docker-compose.app.yml up -d --build

# Ejecutar la ingesta de YouTube
docker exec -it ingest_data python -m app.main
```

- API docs: http://localhost/docs
- Qdrant: http://localhost:6333/dashboard#/collections

## Convenciones

- Comentarios, docstrings, logs y documentación **en español**.
- **Base de datos**:
  - Las migraciones `V<n>__Descripcion.sql` son inmutables una vez aplicadas. Todo cambio va en una versión nueva.
  - Los SP y funciones van en `R__NombrePascalCase.sql` con `CREATE OR REPLACE`, en el esquema `youtube`, nombres `snake_case` y parámetros `p_<nombre>`.
  - Patrón de un SP de etapa: (1) actualizar o insertar en la tabla de datos; (2) upsert del estado en `youtube.processing` con `ON CONFLICT (video_id) DO UPDATE`.
  - Un estado nuevo requiere una migración `ALTER TYPE youtube.processing_status ADD VALUE ...`.
- **Wrappers Python de SP** (`DatabaseManager.py`): `get_connection()`, `CALL "youtube".sp(p_x := %s::text, ...)`, `commit` / `rollback`, `finally: conn.close()` y devolver `True` / `False`.
- Los modelos nuevos de LLM o embeddings se registran en `Backend/app/config.py`. No se escriben IDs de modelo en el código.
- La comunicación ingest → api va por los WebSockets internos (`IngestData/app/Api/InternalComunication.py`).
- **Nunca** commitear archivos `.env`, audios, modelos ni datos (ver `.gitignore`).

## Trampas conocidas

- `youtube.content.vector_*` es `vector(1536)`, pero `gemini-embedding-001` devuelve 3072 dimensiones por defecto. Hay que fijar `output_dimensionality=1536` al vectorizar.
- `DesicionService` espera el tipo `"Choice"` / `"Score"` / `"Noul"` con mayúscula inicial.
- nginx responde 403 a `/ws/llm` y `/ws/decision`: son de uso interno. Desde fuera de docker se prueban contra `api:8000` (por ejemplo con `docker exec api ...`).
- Postgres se expone en el host en `127.0.0.1:5434` (dentro de la red de docker es `postgres:5432`).
- El código de `Backend` se copia en la imagen: los cambios en la api requieren `--build`. `IngestData` se monta como volumen y no lo requiere, salvo que cambien las dependencias o el `Dockerfile`.

## Regla de trabajo: mantener `PLAN.md` al día

- Al completar una subtarea, marcar su casilla en `PLAN.md`.
- Al completar una fase, cambiar su estado a ✅, anotar la fecha de cierre y actualizar "Última actualización".
- Si aparece trabajo nuevo, agregarlo a la fase correspondiente o a "Deuda técnica".
- Hacer la actualización en el mismo commit que el trabajo.
- Los mensajes de commit siguen el formato `Fase N: descripción`.
