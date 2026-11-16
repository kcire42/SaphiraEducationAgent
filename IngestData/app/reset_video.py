"""
CLI para regresar uno o varios videos a un estado anterior del pipeline y reprocesarlos desde ahí.

Uso:
	docker exec ingest_data python -m app.reset_video --video-id <id> [--video-id <id> ...] --status <estado>

<estado> puede ser el nombre (por ejemplo, summary) o el código (por ejemplo, 5) de INGESTION_STATUS.
"""
import argparse
import logging
import sys

from app.YoutubeSource.Database.DatabaseManager import get_video_status
from app.YoutubeSource.IntegrityData.utilities import INGESTION_STATUS, return_status_youtube_ingestion

logger = logging.getLogger(__name__)


def resolve_status(value: str) -> int | None:
	"""
	Convierte el estado recibido (nombre o código) en su código de INGESTION_STATUS.

	Returns:
		int con el código, o None si el estado no existe.
	"""
	value = value.strip().lower()
	if value.isdigit():
		code = int(value)
		return code if code in INGESTION_STATUS else None
	return next((code for code, name in INGESTION_STATUS.items() if name == value), None)


def build_parser() -> argparse.ArgumentParser:
	valid_states = ", ".join(f"{code}={name}" for code, name in INGESTION_STATUS.items())
	parser = argparse.ArgumentParser(
		prog="python -m app.reset_video",
		description="Regresa videos a un estado anterior del pipeline de ingesta.",
	)
	parser.add_argument(
		"--video-id", dest="video_ids", action="append", required=True,
		help="ID del video. Se puede repetir para varios videos.",
	)
	parser.add_argument(
		"--status", required=True,
		help=f"Estado destino, por nombre o código ({valid_states}).",
	)
	return parser


def main(argv: list[str] | None = None) -> int:
	"""
	Ejecuta el CLI.

	Returns:
		int: 0 si todos los videos se regresaron correctamente, 1 si alguno falló.
	"""
	parser = build_parser()
	args = parser.parse_args(argv)

	status_code = resolve_status(args.status)
	if status_code is None:
		valid_states = ", ".join(f"{code}={name}" for code, name in INGESTION_STATUS.items())
		parser.error(f"estado inválido: '{args.status}'. Estados válidos: {valid_states}")
	target = INGESTION_STATUS[status_code]

	failures = 0
	for video_id in args.video_ids:
		previous = get_video_status(video_id)
		if return_status_youtube_ingestion(video_id, status_code):
			current = get_video_status(video_id)
			print(f"✅ {video_id}: {previous} → {current}")
		else:
			failures += 1
			print(f"❌ {video_id}: no se pudo regresar de '{previous}' a '{target}'")

	return 1 if failures else 0


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
	sys.exit(main())
