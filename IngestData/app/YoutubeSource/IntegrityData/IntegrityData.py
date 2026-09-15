
from app.YoutubeSource.Database.DatabaseManager import file_get_video_metadata, get_video_metadata

def validate_video_metadata(video_id):
    json_data = file_get_video_metadata(video_id)
    db_tuple = get_video_metadata(video_id)
        # Comparar los diccionarios
    if not json_data:
        print(f"❌ Falló: No se encontró el archivo JSON para '{video_id}'")
        return False
    
    if not db_tuple:
        print(f"❌ Falló: No se encontró el video en la DB para '{video_id}'")
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
            print(f"✅ {field} coincide: {json_val}")
            match_count += 1
        else:
            print(f"❌ ERROR en {field}: JSON({json_val}) != DB({db_val})")

    if match_count == len(fields_to_check):
        print("\n⭐ RESULTADO: INTEGRIDAD CONFIRMADA ⭐")
        return True

    else:
        print("\n⚠️ RESULTADO: DISCREPANCIA DE DATOS ⚠️")
        return False

# if __name__ == "__main__":
#     validate_video_metadata('Naruto： Kakashi Vs Pain - QUIÉN DEBIÓ GANAR')
