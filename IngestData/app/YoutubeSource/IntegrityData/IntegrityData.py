import logging
from app.YoutubeSource.Database.DatabaseManager import file_get_video_metadata, get_video_metadata

logger = logging.getLogger(__name__)


def validate_video_metadata(video_id):
	json_data = file_get_video_metadata(video_id)
	db_tuple = get_video_metadata(video_id)
	# Comparar los diccionarios
	if not json_data:
		logger.error("❌ Falló: No se encontró el archivo JSON para '%s'", video_id)
		return False

	if not db_tuple:
		logger.error("❌ Falló: No se encontró el video en la DB para '%s'", video_id)
		return False

	db_data = {
		'id': str(db_tuple[0]),
		'title': db_tuple[1],
		'webpage_url': db_tuple[2],
		'duration': db_tuple[3],
		'view_count': db_tuple[4],
		'channel_id': db_tuple[5],
		'channel_name': db_tuple[6]
	}

	fields_to_check = ['id', 'channel_id', 'webpage_url']
	match_count = 0

	for field in fields_to_check:
		json_val = str(json_data.get(field))
		db_val = str(db_data.get(field))

		if json_val == db_val:
			logger.debug("✅ %s coincide: %s", field, json_val)
			match_count += 1
		else:
			logger.error("❌ ERROR en %s: JSON(%s) != DB(%s)", field, json_val, db_val)

	if match_count == len(fields_to_check):
		logger.info("⭐ RESULTADO: INTEGRIDAD CONFIRMADA para '%s' ⭐", video_id)
		return True
	else:
		logger.warning("⚠️ RESULTADO: DISCREPANCIA DE DATOS para '%s' ⚠️", video_id)
		return False

# if __name__ == "__main__":
# 	validate_video_metadata('Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR')
