import os
from google_play_scraper import app, reviews, Sort

# Configuración
APP_ID = "com.innovasof.ClassUpn"
OUTPUT_DIR = r"c:\Users\Fayder Arroyo Herazo\Desktop\Prueba Cun\Doble titulacion\app"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "play_store_results.txt")
MAX_REVIEWS = 30

def get_play_store_data(app_id, lang='es', country='co', max_reviews=30):
    print(f"Iniciando extracción para el APP_ID: {app_id}...")
    
    try:
        # 1. Obtener detalles de la app
        app_details = app(app_id, lang=lang, country=country)
        
        # 2. Obtener reseñas
        result_reviews, _ = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=max_reviews
        )
        
        data = {
            "name": app_details.get('title', 'No encontrado'),
            "rating": app_details.get('score', 0),
            "rating_count": app_details.get('ratings', 0),
            "description": app_details.get('description', 'No encontrado'),
            "reviews": result_reviews
        }
        return data

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None

if __name__ == "__main__":
    # Esta parte se mantiene para ejecución por consola si se desea
    res = get_play_store_data(APP_ID)
    if res:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"NOMBRE DE LA APP: {res['name']}\n")
            f.write(f"CALIFICACIÓN: {res['rating']} ({res['rating_count']} valoraciones)\n\n")
            f.write(f"DESCRIPCIÓN:\n{res['description']}\n\n")
            f.write(f"RESEÑAS (Máx {MAX_REVIEWS}):\n")
            
            for i, r in enumerate(res['reviews'], 1):
                f.write(f"{i}. [{r.get('at', '')}] {r.get('userName', '')}: {r.get('content', '')}\n")
                f.write("-" * 50 + "\n")
        print(f"Resultados guardados en {OUTPUT_FILE}")
