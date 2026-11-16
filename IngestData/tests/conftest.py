import pytest
from app.YoutubeSource.Database.DatabaseManager import get_connection
from tests.db_helpers import set_status


@pytest.fixture
def db_conn():
	"""
	Conexión real a postgres. Si la base no está disponible, la prueba se omite.
	"""
	try:
		conn = get_connection()
	except Exception as e:
		pytest.skip(f"Base de datos no disponible: {e}")
	yield conn
	conn.close()


@pytest.fixture
def processed_video(db_conn):
	"""
	Devuelve (video_id, estado_original) de un video ya registrado en youtube.processing
	y restaura su estado original al terminar la prueba.
	"""
	with db_conn.cursor() as cur:
		cur.execute('SELECT video_id, status::text FROM "youtube".processing ORDER BY video_id LIMIT 1')
		row = cur.fetchone()
	if row is None:
		pytest.skip("No hay videos en youtube.processing")
	video_id, original_status = row
	yield video_id, original_status
	set_status(db_conn, video_id, original_status)
