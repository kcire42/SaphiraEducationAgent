def get_status(conn, video_id):
	"""Lee el estado actual de un video en youtube.processing."""
	with conn.cursor() as cur:
		cur.execute('SELECT status::text FROM "youtube".processing WHERE video_id = %s', (video_id,))
		return cur.fetchone()[0]


def set_status(conn, video_id, status):
	"""Fija el estado de un video directamente, sin pasar por el SP (para preparar o restaurar pruebas)."""
	with conn.cursor() as cur:
		cur.execute(
			'UPDATE "youtube".processing SET status = %s::youtube.processing_status WHERE video_id = %s',
			(status, video_id),
		)
	conn.commit()
