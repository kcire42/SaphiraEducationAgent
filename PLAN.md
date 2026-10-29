# PLAN — Saphira, asistente personal de IA

**Última actualización:** 2026-10-28

Estados: ✅ completada · 🚧 en curso · ⏳ pendiente

> Este archivo se actualiza cada vez que se completa una subtarea o una fase (ver la regla en `CLAUDE.md`).
>
> Las fases están numeradas en orden de ejecución. Hasta el 2026-10-28 la ingesta de YouTube era la Fase 4: los commits `Fase 4:` anteriores corresponden a la actual **Fase 3**.

## Resumen

| Fase | Nombre | Estado |
|---|---|---|
| 0 | Estructura del repositorio | ✅ |
| 1 | Cerebro RAG (Qdrant + embeddings) | ✅ |
| 2 | API y WebSockets (FastAPI + nginx) | ✅ |
| 3 | Ingesta de contenido de YouTube | 🚧 |
| 4 | Orquestación con Airflow | ⏳ |
| 5 | CI/CD con Jenkins → servidor local | ⏳ |
| 6 | Núcleo del agente (tool-calling + memoria) | ⏳ |
| 7 | Análisis de datos (pandas + Spark) | ⏳ |
| 8 | Traducción de libros PDF | ⏳ |
| 9 | Visión: reconocimiento de imágenes (TensorFlow + PyTorch) | ⏳ |
| 10 | Despliegue a la nube (AWS) con Jenkins | ⏳ |
| 11 | Mensajería: WhatsApp e Instagram | ⏳ |
| 12 | Plataforma de datos y ML del uso (Databricks Free Edition + Spark) | ⏳ |
| 13 | App Flutter, voz y control del teléfono | ⏳ |
| SQ1 | *Side quest:* ingesta de criptomonedas (Bitso) y predicción de precio | ⏳ |

> Las *side quests* son deseables pero no prioritarias: se trabajan en paralelo cuando haya tiempo y no bloquean ninguna fase.

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

## Fase 3 — Ingesta de contenido de YouTube 🚧
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
- [ ] Script para regresar un video a un estado anterior y reprocesarlo desde ahí (cualquier etapa, no solo `category`):
  - SP `youtube.reset_youtube_ingestion(p_video_id, p_status)` en `R__ResetYoutubeIngestion.sql`. Valida que el video exista y que el estado destino sea anterior al actual (el enum es ordenado, así que basta con comparar con `<`). También permite salir de `error`.
  - Wrapper `reset_youtube_ingestion(video_id, status)` en `DatabaseManager.py`.
  - CLI `docker exec ingest_data python -m app.reset_video --video-id <id> [--video-id <id> ...] --status <estado>`, que muestra el estado anterior y el nuevo.
  - Opcional: limpiar los datos derivados de las etapas posteriores (por ejemplo, regresar a `processed` reinicia `summary` y `category`).
- [ ] Recategorizar los videos existentes con la nueva lista (con el script anterior, regresándolos a `summary`).
- [ ] Vectorizar el resumen y la transcripción en `youtube.content` (pgvector, `output_dimensionality=1536`) → estado `vector`.
- [ ] Cargar los chunks a Qdrant (colección por categoría o con metadata) para el RAG → estado `learning`.
- [ ] Marcar `completed` y permitir preguntar sobre los videos desde `/ws/llm`.

> Spark / Databricks: **no** se usa en esta fase. El volumen es bajo y el cuello de botella es Whisper y el LLM, no el procesamiento de datos.

## Fase 4 — Orquestación con Airflow ⏳
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
- [ ] (Fase 8) DAG `book_translation`. (Fase 12) DAG de reentrenamiento y disparo de jobs de Databricks.

## Fase 5 — CI/CD con Jenkins → servidor local ⏳
Objetivo: cada push a `main` se prueba, construye y despliega automáticamente en el servidor local, que funciona como staging antes de la nube (Fase 10).

**Diseño propuesto**
- Jenkins en Docker en el servidor local (`docker-compose.jenkins.yml`, imagen LTS con versión fijada) con acceso a Docker para construir y desplegar.
- `Jenkinsfile` declarativo en la raíz del repo con las etapas:
  `checkout → lint → tests → build → migraciones → deploy → smoke tests → rollback (si falla)`.
- Las imágenes `api` e `ingest_data` se etiquetan con el SHA del commit, y el compose se parametriza con `IMAGE_TAG` (`image: saphira-api:${IMAGE_TAG}`).
- Los secretos viven en Jenkins Credentials y generan los `.env` al desplegar; dejan de estar sueltos en el servidor.

**Tareas**
- [ ] Levantar Jenkins con docker-compose (plugins: Pipeline, Git, Docker Pipeline, Credentials Binding).
- [ ] Lint con `ruff` y tests con `pytest` (depende de la tarea transversal de tests).
- [ ] Build de imágenes etiquetadas con el SHA del commit; compose parametrizado con `IMAGE_TAG`.
- [ ] Etapa de migraciones: `flyway validate` y luego `flyway migrate`.
- [ ] Deploy con `docker compose -f docker-compose.data.yml -f docker-compose.app.yml up -d`.
- [ ] Smoke tests: `/utilities/health`, `flyway info` y healthcheck de Postgres.
- [ ] Rollback automático a la etiqueta anterior si fallan los smoke tests.
- [ ] Disparo por push a `main`: webhook de GitHub (requiere exponer Jenkins, por ejemplo con Tailscale Funnel) o polling del SCM.
- [ ] Desplegar las DAGs de Airflow (Fase 4) en el mismo pipeline.
- [ ] Notificaciones del resultado del pipeline.

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
- [ ] **Spark para archivos grandes:** si el archivo supera un umbral (por ejemplo, 1 GB o que no quepa en memoria), la herramienta usa PySpark local o un job de Databricks en lugar de pandas.
- [ ] Generación de gráficas e insights en lenguaje natural.
- [ ] Reutilizar y ordenar `DataScience/` (notebooks y scripts).

## Fase 8 — Traducción de libros PDF ⏳
- [ ] Extracción de texto con estructura (PyMuPDF): capítulos, párrafos e imágenes.
- [ ] Segmentación por capítulo o bloque respetando los límites de tokens del modelo.
- [ ] Traducción por lotes como job asíncrono (DAG de Airflow) con estado por bloque y reanudación.
- [ ] Glosario y memoria de traducción para mantener los términos consistentes en todo el libro.
- [ ] Varios idiomas destino en paralelo.
- [ ] Reconstrucción en PDF o EPUB y notificación al terminar.

## Fase 9 — Visión: reconocimiento de imágenes (TensorFlow + PyTorch) ⏳
Objetivo: practicar visión por computadora con **modelos propios en TensorFlow y PyTorch**. Gemini multimodal queda como apoyo para descripciones abiertas.

- [ ] Endpoint de subida de imágenes y herramienta del agente que elige el modelo según la tarea.
- [ ] Casos de uso: describir, OCR o leer documentos y fotos de apuntes, identificar y clasificar objetos.
- [ ] Dataset propio etiquetado (por ejemplo, tipos de apuntes o documentos) con división train / val / test.
- [ ] **PyTorch:** transfer learning con `torchvision` (ResNet / EfficientNet / ViT) para clasificación, y detección de objetos (por ejemplo, Faster R-CNN o YOLO).
- [ ] **TensorFlow / Keras:** el mismo clasificador con `tf.keras.applications` (EfficientNet / MobileNet) para comparar ambos frameworks en precisión, latencia y tamaño.
- [ ] Experimentos registrados en MLflow; exportar a ONNX o TFLite (este último sirve para correr en el teléfono en la Fase 13).
- [ ] Servir los modelos: TorchServe / TF Serving o un servicio FastAPI propio; entrenamiento con GPU en EC2 (Fase 10).
- [ ] Probar desde `/docs` o desde la mensajería (Fase 11); la cámara del teléfono se integra en la Fase 13.

## Fase 10 — Despliegue a la nube (AWS) con Jenkins ⏳
Objetivo: promover a producción en AWS la misma imagen ya probada en el servidor local, y **poner en práctica Lambda, API Gateway, SQS, SNS, EKS, EC2 y S3** con usos reales del proyecto. Va antes de la mensajería porque los webhooks de Meta necesitan HTTPS público.

**Base**
- [ ] Infraestructura como código con Terraform (estado remoto en S3).
- [ ] ECR como registry: Jenkins sube ahí las imágenes etiquetadas con el SHA.
- [ ] RDS Postgres con pgvector; Qdrant en EKS o Qdrant Cloud.
- [ ] Etapa `deploy-cloud` en el `Jenkinsfile`, después del deploy local, con aprobación manual (`input`).
- [ ] Dominio y HTTPS (Route 53 + ACM).

**Servicios de AWS y su uso en Saphira**
- [ ] **EKS:** cluster de Kubernetes donde corren la api, los workers de ingesta y Airflow (Helm). Jenkins despliega con Helm.
- [ ] **EC2:** node groups del cluster; instancias GPU (spot) para Whisper, traducción y entrenamiento de visión (Fase 9).
- [ ] **S3:** audios de YouTube, libros PDF y sus traducciones, imágenes subidas, artefactos de modelos y zona de aterrizaje del data lake (Fase 12).
- [ ] **SQS:** colas de trabajo que desacoplan la api de los workers (transcripción, traducción por capítulo, reconocimiento de imágenes), con dead-letter queue para los fallidos.
- [ ] **SNS:** notificaciones y fan-out (pipeline terminado o fallido, libro traducido, alarmas de CloudWatch), por email o SMS y hacia varias colas SQS.
- [ ] **Lambda:** funciones por eventos: un archivo nuevo en S3 encola su trabajo en SQS, recepción de webhooks de WhatsApp e Instagram (Fase 11), y un poller programado del ticker de Bitso (SQ1).
- [ ] **API Gateway:** entrada pública HTTPS para los webhooks y las Lambdas; la api principal queda detrás de un ALB Ingress en EKS.
- [ ] Autoescalado de los workers según el largo de las colas SQS (KEDA en EKS).

**Costos**
- [ ] Usar Free Tier donde aplique, AWS Budgets con alertas y `terraform destroy` de los entornos que no se usen (el control plane de EKS y las GPU cobran por hora).

## Fase 11 — Mensajería: WhatsApp e Instagram ⏳
- [ ] WhatsApp Business Cloud API: webhook para recibir mensajes y que el agente responda.
- [ ] Instagram Graph API (Messaging): webhook de DMs y publicación de contenido.
- [ ] Requisitos: cuenta Business o Creator, app en Meta for Developers, verificación y cumplimiento de políticas.
- [ ] Webhooks recibidos por API Gateway + Lambda (Fase 10), que encolan los mensajes en SQS para que el agente los procese.

## Fase 12 — Plataforma de datos y ML del uso (Databricks Free Edition + Spark) ⏳
**Databricks Free Edition es el data lake / lakehouse** del proyecto: Delta Lake con Unity Catalog para el almacenamiento, Spark para las transformaciones y MLflow para el ML, todo sin costo. `DataScience/Scripts/DataPipeline.py` ya anticipa Spark.

- [ ] Registrar logs de uso del agente (consultas, herramientas, latencia, costo en tokens).
- [ ] Workspace de Databricks Free Edition; revisar sus límites vigentes (cómputo serverless con cuotas diarias) antes de diseñar los jobs.
- [ ] Carga: exportes en Parquet subidos a un Volume de Unity Catalog e ingeridos con Auto Loader (o leídos desde S3, Fase 10, si la Free Edition lo permite).
- [ ] Arquitectura medallion en Delta Lake, con un esquema por capa en Unity Catalog (`saphira.bronze`, `saphira.silver`, `saphira.gold`):
  - **bronze:** logs de uso del agente, `youtube.processing` y `youtube.error_logs` en crudo;
  - **silver:** datos limpios;
  - **gold:** métricas y features.
- [ ] Transformaciones con PySpark y Spark SQL en notebooks o Lakeflow Declarative Pipelines (antes Delta Live Tables).
- [ ] Feature engineering con Spark y EDA en notebooks.
- [ ] Entrenar un modelo (recomendaciones, detección de temas de estudio débiles) con el MLflow integrado para experimentos y registro de modelos.
- [ ] Jobs de Databricks disparados desde Airflow (`DatabricksRunNowOperator`) y reentrenamiento programado.
- [ ] Endpoint de predicción en la api (el modelo se descarga del registro de MLflow).
- [ ] Desarrollo local con PySpark en Docker y Delta Lake (`delta-spark`) para no gastar la cuota de la Free Edition.

## Fase 13 — App Flutter, voz y control del teléfono ⏳
Va al final: consume todo lo anterior. Hasta entonces la interacción es por `/docs` y por la mensajería (Fase 11).

- [ ] Crear el proyecto Flutter (carpeta `Mobile/`).
- [ ] Pantalla de chat conectada a `/ws/chat` (Fase 6), con autenticación.
- [ ] Historial de conversación y respuestas en streaming (requiere streaming en la api).
- [ ] Cámara conectada a la visión de la Fase 9.
- [ ] Voz a texto (STT) y texto a voz (TTS).
- [ ] Comandos de voz enviados al agente.
- [ ] Acciones en el teléfono: Android Intents y App Actions; iOS App Intents y Shortcuts.
- [ ] Permisos y confirmación explícita antes de acciones sensibles (enviar mensajes, pagos, borrar).

---

## Side quests (deseables, no prioritarias)

### SQ1 — Ingesta de criptomonedas (Bitso) y predicción de precio ⏳
Objetivo: tener un volumen de datos real y creciente para practicar Spark, y explorar si se puede agregar una función de predicción de precio. Fuente: **API pública de Bitso** (REST v3 y WebSocket); no requiere cuenta para los datos de mercado.

Encaja mejor después de Airflow (Fase 4) y antes o junto con la plataforma de datos en Databricks (Fase 12), pero se puede empezar en cualquier momento con PySpark local.

**Ingesta**
- [ ] Servicio `CryptoData/` (mismo estilo que `IngestData`) con su propio contenedor.
- [ ] Catálogo de mercados desde `available_books` (por ejemplo `btc_mxn`, `eth_mxn`, `usd_mxn`); se elige cuáles seguir.
- [ ] Captura en tiempo real por WebSocket (canales `trades` y `diff-orders`): proceso de larga duración que escribe en bronze. Es la fuente principal de volumen.
- [ ] Carga incremental por REST (`trades` paginado, `ticker`, `order_book`) con checkpoint por mercado para retomar sin duplicar.
- [ ] Respetar los rate limits de la API de Bitso (revisar los vigentes en su documentación) con backoff y reintentos.
- [ ] Esquema `crypto` en Postgres solo para metadata: mercados seguidos, checkpoints y log de errores (migraciones Flyway, igual que `youtube`).
- [ ] DAG de Airflow `crypto_ingestion` para la carga incremental y la vigilancia del colector en tiempo real.

**Procesamiento con Spark en Databricks**
- [ ] El colector escribe Parquet particionado por mercado y fecha (en local y, después, en S3).
- [ ] **bronze (Delta):** trades y order book crudos, ingeridos con Auto Loader desde un Volume de Unity Catalog.
- [ ] **silver:** tipos correctos, deduplicación por `tid` y reconstrucción del order book desde los diffs.
- [ ] **gold:** velas OHLCV (1m, 5m, 1h, 1d), VWAP, volatilidad, volumen por lado y desequilibrio del order book.
- [ ] Jobs de Spark en local (PySpark + `delta-spark`) y, después, en Databricks disparados desde Airflow.
- [ ] Vigilar la cuota de la Free Edition: si el volumen la rebasa, procesar en Databricks solo una ventana de mercados o de fechas.

**Predicción de precio (experimental)**
- [ ] Baselines: precio anterior (naive) y media móvil; cualquier modelo tiene que superarlos.
- [ ] Modelos: gradient boosting (LightGBM) sobre features de gold; después probar series de tiempo (ARIMA/Prophet) o LSTM.
- [ ] Validación walk-forward (sin mezclar futuro con pasado) y métricas MAE, RMSE y acierto de dirección.
- [ ] Experimentos y modelos registrados en MLflow.
- [ ] Herramienta del agente (requiere la Fase 6): "¿cómo va BTC?" con el resumen del mercado y la predicción, aclarando que es un ejercicio educativo y no una recomendación financiera.

---

## Transversal (todas las fases)
- [ ] Tests con `pytest` para servicios y wrappers de DB (con un Postgres de prueba).
- [ ] CI/CD en Jenkins: lint, tests y build de imágenes (ver Fase 5).
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
