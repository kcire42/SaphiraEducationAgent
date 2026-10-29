# PLAN — Saphira, asistente personal de IA

**Última actualización:** 2026-10-28

Estados: ✅ completada · 🚧 en curso · ⏳ pendiente

> Este archivo se actualiza cada vez que se completa una subtarea o una fase (ver la regla en `CLAUDE.md`).

## Resumen

| Fase | Nombre | Estado |
|---|---|---|
| 0 | Estructura del repositorio | ✅ |
| 1 | Cerebro RAG (Qdrant + embeddings) | ✅ |
| 2 | API y WebSockets (FastAPI + nginx) | ✅ |
| 3 | App móvil Flutter | ⏳ |
| 4 | Ingesta de contenido de YouTube | 🚧 |
| 5 | Orquestación con Airflow | ⏳ |
| 6 | Núcleo del agente (tool-calling + memoria) | ⏳ |
| 7 | Análisis de datos | ⏳ |
| 8 | Traducción de libros PDF | ⏳ |
| 9 | Visión: reconocimiento de imágenes | ⏳ |
| 10 | Mensajería: WhatsApp e Instagram | ⏳ |
| 11 | Voz y control del teléfono | ⏳ |
| 12 | Analítica y ML del uso | ⏳ |

---

## Fase 0 — Estructura del repositorio ✅
- [x] Carpetas y organización inicial (`Backend`, `IngestData`, `DataBase`, `DataScience`, `nginx`).

## Fase 1 — Cerebro RAG ✅
- [x] Qdrant en Docker.
- [x] Carga de PDF y TXT, limpieza y chunking (`Backend/app/PreData/`).
- [x] Embeddings con Gemini y seed a Qdrant con IDs deterministas.
- [x] Consulta con recuperación de contexto (`RagService.retrieve_context`).

## Fase 2 — API y WebSockets ✅
- [x] API FastAPI con `/utilities/health` y `/utilities/training`.
- [x] WebSocket `/ws/llm` con RAG opcional y plantillas de prompt dinámicas (`execute_llm`).
- [x] WebSocket `/ws/decision` con TypeSafe / JEV (`callSimpleSystemOneJev`).
- [x] nginx como reverse proxy (con WebSocket) y puertos internos ligados a `127.0.0.1`.

## Fase 3 — App móvil Flutter ⏳
- [ ] Crear el proyecto Flutter (carpeta `Mobile/`).
- [ ] Pantalla de chat conectada a `/ws/llm`.
- [ ] Historial de conversación y respuestas en streaming (requiere streaming en la api).
- [ ] Autenticación contra la api (depende de la Fase 6).
- [ ] Preparar la arquitectura para voz (Fase 11) y cámara (Fase 9).

## Fase 4 — Ingesta de contenido de YouTube 🚧
- [x] Esquema `youtube` y tablas (`channels`, `videos`, `content`, `processing`, `error_logs`).
- [x] Flyway en docker-compose.
- [x] SPs y funciones de registro, descarga, validación, transcripción, resumen y error.
- [x] Listado de videos del canal y descarga de audio (yt-dlp).
- [x] Validación de integridad de metadata.
- [x] Transcripción con Whisper.
- [x] Resumen vía `/ws/llm`.
- [x] SP `category_youtube_ingestion`, estado `category` (`V9`) y wrapper en `DatabaseManager.py`.
- [x] Corregir `CategoryServices.get_category_from_jev`: ahora envía `question_type="Choice"` y el diccionario de categorías.
- [x] `/ws/decision` devuelve la respuesta de JEV como JSON (`model_dump`) y se extrae solo el nombre de la categoría.
- [x] Conectar `category_youtube_ingestion` en `IngestData/app/main.py`.
- [x] Probar la categorización de punta a punta en Docker (6 videos categorizados, 0 errores).
- [ ] Ampliar las categorías de `CategoryServices.py`: agregar al menos "Series/Cine" y "Tecnología/IA" (hoy un video de Better Call Saul cae en *Psychology* y los de IA en *News*).
- [ ] Guardar la `confidence` de JEV: migración `V10` con la columna `category_confidence` en `youtube.content`, nuevo parámetro `p_category_confidence` en `category_youtube_ingestion` y en su wrapper.
- [ ] Usar la confidence: los videos por debajo de un umbral (por ejemplo, 0.6) se marcan para revisión manual.
- [ ] Recategorizar los videos existentes con la nueva lista.
- [ ] Vectorizar el resumen y la transcripción en `youtube.content` (pgvector, `output_dimensionality=1536`) → estado `vector`.
- [ ] Cargar los chunks a Qdrant (colección por categoría o con metadata) para el RAG → estado `learning`.
- [ ] Marcar `completed` y permitir preguntar sobre los videos desde `/ws/llm`.

## Fase 5 — Orquestación con Airflow ⏳
Objetivo: reemplazar la ejecución manual (`docker exec ... python -m app.main`) por pipelines programados, con reintentos y monitoreo.

**Diseño propuesto**
- Airflow 2.x con `LocalExecutor` en `docker-compose.airflow.yml` (webserver, scheduler, init) dentro de `saphira_network`.
- Metadatos de Airflow en una base `airflow` del mismo Postgres, separada del esquema `youtube`.
- Las DAGs viven en `Orchestration/dags/` y reutilizan el código de `IngestData` (imagen propia basada en la de `IngestData` o paquete instalable).
- DAG `youtube_ingestion`, una tarea por etapa de la máquina de estados:
  `register → download → validate → transcribe → summarize → categorize → vectorize → learn`.
- Cada tarea obtiene sus videos con `db_get_videos_by_status(<estado>)` y procesa cada uno con **dynamic task mapping** (`.expand()`). La máquina de estados hace que las tareas sean idempotentes y reanudables.
- Recursos pesados: pool `whisper` con 1 slot para transcribir, y límites de concurrencia para las llamadas al LLM.

**Tareas**
- [ ] Refactorizar `IngestData/app/main.py` en funciones por etapa (`run_register`, `run_download`, ...) invocables desde Airflow y desde CLI.
- [ ] Configurar logging real (`logging.basicConfig` / logging de Airflow).
- [ ] Levantar Airflow con docker-compose y crear la base `airflow`.
- [ ] DAG `youtube_ingestion` con dynamic task mapping, `retries` y `retry_delay`.
- [ ] Canales configurables (tabla `youtube.channels` con flag `active` o Airflow Variables) en lugar del canal hardcodeado.
- [ ] Alertas de fallo (callback a log, email o, más adelante, WhatsApp).
- [ ] DAG de mantenimiento: reintentar videos en `error` y limpiar mp3 ya procesados.
- [ ] (Fase 8) DAG `book_translation`. (Fase 12) DAG de reentrenamiento.

## Fase 6 — Núcleo del agente ⏳
- [ ] Implementar `AgentService` con tool-calling (el LLM decide qué herramienta usar).
- [ ] Herramientas iniciales: búsqueda RAG en documentos, conocimiento de videos de YouTube y decisión o clasificación con JEV.
- [ ] Endpoint `/ws/chat` del agente (separado de `/ws/llm`, que queda para uso interno).
- [ ] Memoria de conversación y preferencias del usuario en Postgres (esquema `assistant`).
- [ ] Autenticación (JWT) y restringir CORS (hoy `allow_origins=["*"]`).
- [ ] Registro de herramientas extensible, para que cada fase siguiente agregue la suya.

## Fase 7 — Análisis de datos ⏳
- [ ] Endpoint de subida de archivos (CSV o Excel) con almacenamiento local o en un bucket.
- [ ] Herramienta del agente que genera y ejecuta código pandas en un sandbox aislado (contenedor con límites).
- [ ] Generación de gráficas e insights en lenguaje natural.
- [ ] Reutilizar y ordenar `DataScience/` (notebooks y scripts).

## Fase 8 — Traducción de libros PDF ⏳
- [ ] Extracción de texto con estructura (PyMuPDF): capítulos, párrafos e imágenes.
- [ ] Segmentación por capítulo o bloque respetando los límites de tokens del modelo.
- [ ] Traducción por lotes como job asíncrono (DAG de Airflow) con estado por bloque y reanudación.
- [ ] Glosario y memoria de traducción para mantener los términos consistentes en todo el libro.
- [ ] Varios idiomas destino en paralelo.
- [ ] Reconstrucción en PDF o EPUB y notificación al terminar.

## Fase 9 — Visión: reconocimiento de imágenes ⏳
- [ ] Endpoint de subida de imágenes y herramienta del agente con Gemini multimodal.
- [ ] Casos de uso: describir, OCR o leer documentos y fotos de apuntes, identificar objetos.
- [ ] Integrar la cámara en Flutter.

## Fase 10 — Mensajería: WhatsApp e Instagram ⏳
- [ ] WhatsApp Business Cloud API: webhook para recibir mensajes y que el agente responda.
- [ ] Instagram Graph API (Messaging): webhook de DMs y publicación de contenido.
- [ ] Requisitos: cuenta Business o Creator, app en Meta for Developers, verificación y cumplimiento de políticas.
- [ ] Exponer los webhooks con HTTPS (dominio + TLS en nginx, o un túnel).

## Fase 11 — Voz y control del teléfono ⏳
- [ ] Voz a texto (STT) y texto a voz (TTS) en Flutter.
- [ ] Comandos de voz enviados al agente.
- [ ] Acciones en el teléfono: Android Intents y App Actions; iOS App Intents y Shortcuts.
- [ ] Permisos y confirmación explícita antes de acciones sensibles (enviar mensajes, pagos, borrar).

## Fase 12 — Analítica y ML del uso ⏳
- [ ] Registrar logs de uso del agente (consultas, herramientas, latencia, costo en tokens).
- [ ] Limpieza y EDA en notebooks; entrenar un modelo (recomendaciones, detección de temas de estudio débiles).
- [ ] Endpoint de predicción y reentrenamiento programado en Airflow.

---

## Transversal (todas las fases)
- [ ] Tests con `pytest` para servicios y wrappers de DB (con un Postgres de prueba).
- [ ] CI con GitHub Actions: lint, tests y build de imágenes.
- [ ] Logging estructurado en lugar de `print`.
- [ ] Gestión de secretos (no depender de `.env` sueltos en producción).
- [ ] Observabilidad: healthchecks, métricas y costo de LLM por request.
- [ ] Actualizar el `README.md` a la nueva visión y numeración de fases.

## Deuda técnica
- [x] Los compose montaban `./Database`, pero la carpeta es `DataBase`: corregido a `./DataBase`.
- [x] `IngestData/DockerFile` renombrado a `Dockerfile` (también fallaba en macOS con BuildKit).
- [x] Healthcheck de postgres: ahora usa `$${POSTGRES_USER}` / `$${POSTGRES_DB}`, que se resuelven dentro del contenedor.
- [x] Versiones de imágenes fijadas: `qdrant/qdrant:v1.18.2`, `flyway/flyway:13.7.0`, `nginx:1.31.6-alpine`.
- [x] `/ws/llm` y `/ws/decision` bloqueados en nginx (403); solo se usan dentro de la red de docker.
- [x] Logging configurado en `IngestData` (`LOG_LEVEL`, por defecto `DEBUG`).
- [x] Puerto de Postgres en el host cambiado a `127.0.0.1:5434` (el 5433 lo usa otro proyecto).
- [ ] `IngestData` actualizado a Python 3.12 (igual que `Backend`): falta reconstruir la imagen y validar Whisper.
