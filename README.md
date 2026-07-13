Es una Plataforma Educativa Inteligente (EdTech) donde los estudiantes interactúan con un tutor virtual desde su celular. El tutor resuelve dudas buscando en la documentación oficial del curso, mientras que en segundo plano, un motor de Machine Learning analiza el rendimiento del estudiante para predecir si está a punto de reprobar o abandonar el curso.

* Fase 1: El Cerebro RAG (Backend + Qdrant)

    1. Levanta Qdrant en Docker.

    2. Crea un script en Python que lea archivos PDF (ej. un temario), los vectorice y los suba a Qdrant.

    3. Crea un script básico de LangChain que haga preguntas y recupere el contexto.

* Fase 2: La API y el Agente (FastAPI)

    1. Envuelve tu lógica de LangChain en una API de FastAPI.

    2. Crea un endpoint de WebSocket para manejar el chat en tiempo real.

* Fase 3: La Interfaz (Flutter)

    1. Crea la app en Flutter.

    2. Conecta la app a tu WebSocket para tener un chat funcional y estético.

* Fase 4: El Análisis (Machine Learning)

    1. Exporta los logs de uso del chat a un archivo CSV o lee directo del SQL.

    2. Usa un Jupyter Notebook para limpiar los datos y entrenar tu modelo predictivo.

    3. Crea un nuevo endpoint en FastAPI /predict-risk que evalúe a un usuario y devuelva su riesgo.