import os
from google_play_scraper import app, reviews, Sort

# Configuración
APP_ID = "com.innovasof.ClassUpn"
OUTPUT_DIR = r"c:\Users\Fayder Arroyo Herazo\Desktop\Prueba Cun\Doble titulacion\app"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "play_store_results.txt")
MAX_REVIEWS = 200

def get_play_store_data(app_id, lang='es', country='co', max_reviews=200):
    print(f"Iniciando extracción para el APP_ID: {app_id}...")
    
    try:
        # 1. Obtener detalles de la app
        app_details = app(app_id, lang=lang, country=country)
        
        # 2. Obtener un lote amplio de reseñas para poder filtrar
        result_reviews, _ = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=1000  # Extraemos bastantes para asegurar que queden suficientes tras el filtro
        )
        
        # 3. Filtrar reseñas con contenido mayor a 5 caracteres
        filtered_reviews = [r for r in result_reviews if r.get('content') and len(str(r.get('content')).strip()) > 5]
        
        # 4. Limitar al máximo solicitado (ej: 200)
        final_reviews = filtered_reviews[:max_reviews]
        
        data = {
            "name": app_details.get('title', 'No encontrado'),
            "rating": app_details.get('score', 0),
            "rating_count": app_details.get('ratings', 0),
            "descargas": app_details.get('installs', 'N/A'),
            "description": app_details.get('description', 'No encontrado'),
            "reviews": final_reviews
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
