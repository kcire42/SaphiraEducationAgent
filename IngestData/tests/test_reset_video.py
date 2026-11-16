from unittest.mock import MagicMock

import pytest
from app import reset_video
from app.reset_video import main, resolve_status
from tests.db_helpers import get_status, set_status


# ---------------------------------------------------------------------------
# Pruebas unitarias: la base de datos se reemplaza con mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def cli_mocks(monkeypatch):
	"""Reemplaza las llamadas a BD del CLI (reset exitoso y estado 'category' → 'summary')."""
	return_status = MagicMock(return_value=True)
	get_status_mock = MagicMock(side_effect=["category", "summary"] * 10)
	monkeypatch.setattr(reset_video, "return_status_youtube_ingestion", return_status)
	monkeypatch.setattr(reset_video, "get_video_status", get_status_mock)
	return return_status, get_status_mock


@pytest.mark.parametrize("value, expected", [
	("summary", 5),
	("5", 5),
	(" Summary ", 5),
	("manual_review", 7),
	("foo", None),
	("0", None),
	("12", None),
])
def test_resolve_status(value, expected):
	assert resolve_status(value) == expected


def test_nombre_y_codigo_envian_el_mismo_estado(cli_mocks):
	return_status, _ = cli_mocks
	assert main(["--video-id", "vid1", "--status", "summary"]) == 0
	assert main(["--video-id", "vid1", "--status", "5"]) == 0
	assert return_status.call_args_list[0] == return_status.call_args_list[1]
	return_status.assert_called_with("vid1", 5)


def test_estado_invalido_termina_con_error(cli_mocks):
	return_status, _ = cli_mocks
	with pytest.raises(SystemExit):
		main(["--video-id", "vid1", "--status", "foo"])
	return_status.assert_not_called()


def test_video_id_es_requerido(cli_mocks):
	with pytest.raises(SystemExit):
		main(["--status", "summary"])


def test_varios_videos_una_llamada_por_video(cli_mocks, capsys):
	return_status, _ = cli_mocks
	assert main(["--video-id", "vid1", "--video-id", "vid2", "--status", "summary"]) == 0
	assert [c.args for c in return_status.call_args_list] == [("vid1", 5), ("vid2", 5)]
	out = capsys.readouterr().out
	assert "✅ vid1: category → summary" in out
	assert "✅ vid2: category → summary" in out


def test_codigo_de_salida_1_si_alguno_falla(cli_mocks, capsys):
	return_status, _ = cli_mocks
	return_status.side_effect = [True, False]
	assert main(["--video-id", "vid1", "--video-id", "vid2", "--status", "summary"]) == 1
	assert "❌ vid2" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Pruebas de integración: usan la base de datos real
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_cli_regresa_el_video_en_la_bd(db_conn, processed_video, capsys):
	video_id, _ = processed_video
	set_status(db_conn, video_id, "category")

	assert main(["--video-id", video_id, "--status", "summary"]) == 0
	assert get_status(db_conn, video_id) == "summary"
	assert f"✅ {video_id}: category → summary" in capsys.readouterr().out


@pytest.mark.integration
def test_cli_rechaza_salto_hacia_adelante(db_conn, processed_video):
	video_id, _ = processed_video
	set_status(db_conn, video_id, "category")

	assert main(["--video-id", video_id, "--status", "vector"]) == 1
	assert get_status(db_conn, video_id) == "category"
