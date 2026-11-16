from unittest.mock import MagicMock

import pytest
from app.YoutubeSource.IntegrityData import utilities
from app.YoutubeSource.IntegrityData.utilities import INGESTION_STATUS, return_status_youtube_ingestion
from tests.db_helpers import get_status, set_status


# ---------------------------------------------------------------------------
# Pruebas unitarias: la base de datos se reemplaza con mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def db_mocks(monkeypatch):
	"""Reemplaza los wrappers de BD que usa utilities por mocks (video existe y reset exitoso)."""
	get_metadata = MagicMock(return_value=("vid123", "Titulo"))
	reset = MagicMock(return_value=True)
	monkeypatch.setattr(utilities, "get_video_metadata", get_metadata)
	monkeypatch.setattr(utilities, "reset_youtube_ingestion", reset)
	return get_metadata, reset


@pytest.mark.parametrize("status", [0, -1, 12, 99])
def test_estado_invalido_no_toca_la_bd(db_mocks, status):
	get_metadata, reset = db_mocks
	assert return_status_youtube_ingestion("vid123", status) is False
	get_metadata.assert_not_called()
	reset.assert_not_called()


@pytest.mark.parametrize("metadata", [None, []])
def test_video_inexistente(db_mocks, metadata):
	get_metadata, reset = db_mocks
	get_metadata.return_value = metadata
	assert return_status_youtube_ingestion("vid123", 5) is False
	reset.assert_not_called()


def test_falla_el_reset(db_mocks):
	_, reset = db_mocks
	reset.return_value = False
	assert return_status_youtube_ingestion("vid123", 5) is False


def test_excepcion_en_la_bd(db_mocks):
	get_metadata, reset = db_mocks
	get_metadata.side_effect = RuntimeError("conexión perdida")
	assert return_status_youtube_ingestion("vid123", 5) is False
	reset.assert_not_called()


@pytest.mark.parametrize("status, status_name", INGESTION_STATUS.items())
def test_reset_exitoso_envia_el_nombre_del_estado(db_mocks, status, status_name):
	_, reset = db_mocks
	assert return_status_youtube_ingestion("vid123", status) is True
	reset.assert_called_once_with("vid123", status_name)


# ---------------------------------------------------------------------------
# Pruebas de integración: usan la base de datos real
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_mapa_de_estados_coincide_con_el_enum(db_conn):
	"""INGESTION_STATUS debe tener los mismos valores, en el mismo orden, que youtube.processing_status."""
	with db_conn.cursor() as cur:
		cur.execute("SELECT unnest(enum_range(NULL::youtube.processing_status))::text")
		enum_values = [row[0] for row in cur.fetchall()]
	assert [INGESTION_STATUS[k] for k in sorted(INGESTION_STATUS)] == enum_values


def code_of(status_name):
	"""Código de INGESTION_STATUS para un nombre de estado."""
	return next(k for k, v in INGESTION_STATUS.items() if v == status_name)


@pytest.mark.integration
@pytest.mark.parametrize("current, target", [
	("category", "summary"),
	("category", "pending"),
	("manual_review", "category"),  # aprobar una revisión manual
	("error", "summary"),           # salir de error
	("error", "manual_review"),
])
def test_reset_a_un_estado_anterior(db_conn, processed_video, current, target):
	video_id, _ = processed_video
	set_status(db_conn, video_id, current)

	assert return_status_youtube_ingestion(video_id, code_of(target)) is True
	assert get_status(db_conn, video_id) == target


@pytest.mark.integration
@pytest.mark.parametrize("current, target", [
	("category", "category"),       # mismo estado
	("category", "vector"),         # salto hacia adelante
	("summary", "completed"),
	("pending", "error"),           # 'error' no es un destino de reset
])
def test_reset_rechaza_estado_igual_o_posterior(db_conn, processed_video, current, target):
	video_id, _ = processed_video
	set_status(db_conn, video_id, current)

	assert return_status_youtube_ingestion(video_id, code_of(target)) is False
	assert get_status(db_conn, video_id) == current


@pytest.mark.integration
def test_video_inexistente_en_la_bd(db_conn):
	assert return_status_youtube_ingestion("NO_EXISTE_PYTEST", 5) is False
