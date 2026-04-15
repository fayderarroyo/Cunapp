import streamlit as st
import pandas as pd
from scrape_play_store import get_play_store_data
import re
import os
from openai import OpenAI

# Configuración de página con estética premium
st.set_page_config(
    page_title="CUN | AI Scraper",
    page_icon="🤖",
    layout="wide",
)

# Estilos CSS personalizados para WOW factor
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff2b2b;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }
    .ai-button>div>button {
        background-color: #7d26cd !important;
    }
    .ai-button>div>button:hover {
        background-color: #9b30ff !important;
        box-shadow: 0 4px 15px rgba(125, 38, 205, 0.4) !important;
    }
    .card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
    }
    .ai-card {
        background-color: #1e1e2e;
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #7d26cd;
        margin-bottom: 20px;
        color: #e0e0e0;
        line-height: 1.6;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #25293d 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    .review-box {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Función para análisis de IA con DeepSeek
def analyze_with_ai(api_key, model, app_name, description, reviews_text):
    try:
        # DeepSeek usa el mismo cliente de OpenAI pero con una base_url distinta
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        prompt = f"""
        Actúa como un experto en Inteligencia de Mercados para el sector educativo superior.
        Analiza la información de la aplicación "{app_name}" y genera una MATRIZ DE FUNCIONALIDADES basada estrictamente en estos 6 pilares:

        1. GESTIÓN ACADÉMICA Y CURRICULAR (Calificaciones, Plan de estudios, Horarios, Asistencia, Historia académica).
        2. TRÁMITES Y SERVICIOS FINANCIEROS (Matrícula, Portal de pagos, Becas, Gestión de datos personales).
        3. IDENTIDAD Y ACCESO INSTITUCIONAL (Carnet digital, Códigos QR/Barras, Disponibilidad de salas, Georreferenciación).
        4. COMUNICACIÓN Y NOTIFICACIONES (Mensajería privada, Notificaciones Push, Directorio, Redes sociales).
        5. AGENDA Y VIDA UNIVERSITARIA (Calendario académico, Eventos, Módulos de participación).
        6. ATENCIÓN AL USUARIO Y SOPORTE (CASAUR Virtual, Citas presenciales, Asesoramiento financiero/académico).

        INFORMACIÓN DE LA APP:
        DESCRIPCIÓN: {description}
        RESEÑAS: {reviews_text if reviews_text else "No hay reseñas."}

        INSTRUCCIONES DE RESPUESTA:
        - Para cada uno de los 6 pilares, indica si la app lo cumple ("SÍ", "PARCIALMENTE" o "NO IDENTIFICADO").
        - Describe brevemente CÓMO lo implementa según la información analizada.
        - Agrega una sección final de "CONCLUSIÓN ESTRATÉGICA" sobre el nivel de madurez digital de la app.
        
        Responde en formato Markdown profesional con tablas o listas claras.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en la conexión con DeepSeek: {str(e)}"

# Sidebar Branding & Config
with st.sidebar:
    st.image("https://www.cun.edu.co/wp-content/uploads/2021/04/LogoCun-1.png", width=150)
    st.title("Settings")
    
    st.markdown("### 🤖 Configuración IA (DeepSeek)")
    openai_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
    ai_model = st.selectbox("Modelo", ["deepseek-chat", "deepseek-reasoner"], index=0)
    
    st.markdown("---")
    st.markdown("### 🛠 Scraper")
    lang = st.selectbox("Idioma", ["es", "en"], index=0)
    country = st.selectbox("País", ["co", "us", "mx"], index=0)
    max_revs = st.slider("Máximo de reseñas", 10, 100, 30)

# Main Title
st.title("🚀 CUN | Intelligent Scraper")
st.markdown("#### Inteligencia Competitiva potenciada con IA")

# Input Layout
col1, col2 = st.columns(2)

with col1:
    uni_name = st.text_input("Nombre de la Universidad / Institución", placeholder="Ej: CUN")
    app_display_name = st.text_input("Nombre de la App (Referencia)", placeholder="Ej: CLASS UPN")

with col2:
    play_store_url = st.text_input("URL de Google Play Store", placeholder="https://play.google.com/store/apps/details?id=...")

# Lógica de extracción de APP_ID
def extract_app_id(url):
    match = re.search(r'id=([a-zA-Z0-9._]+)', url)
    return match.group(1) if match else None

# Variable de estado para guardar datos extraídos
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None

# Action Button
if st.button("INICIAR EXTRACCIÓN"):
    if not play_store_url:
        st.error("Por favor ingresa una URL válida.")
    else:
        app_id = extract_app_id(play_store_url)
        if not app_id:
            st.error("No se pudo identificar el ID.")
        else:
            with st.spinner(f"Extrayendo datos de {app_id}..."):
                st.session_state.scraped_data = get_play_store_data(app_id, lang=lang, country=country, max_reviews=max_revs)
                
# Mostrar resultados si existen
if st.session_state.scraped_data:
    data = st.session_state.scraped_data
    st.success("¡Extracción exitosa!")
    
    # Layout de Resultados
    st.markdown("---")
    res_col1, res_col2, res_col3 = st.columns(3)
    
    # Manejo seguro de la calificación para evitar errores de formato
    rating_val = data.get("rating")
    rating_display = f"{rating_val:.1f}" if isinstance(rating_val, (int, float)) else "0.0"
    
    with res_col1:
        st.markdown(f'<div class="metric-card"><h3>App</h3><h2>{data["name"]}</h2></div>', unsafe_allow_html=True)
    
    with res_col2:
        st.markdown(f'<div class="metric-card"><h3>Calificación</h3><h2>{rating_display} ⭐</h2></div>', unsafe_allow_html=True)
        
    with res_col3:
        st.markdown(f'<div class="metric-card"><h3>Total Ratings</h3><h2>{data.get("rating_count", 0):,}</h2></div>', unsafe_allow_html=True)
    
    # Tabs for Content
    tab_desc, tab_revs, tab_ai = st.tabs(["📄 Descripción", "💬 Reseñas", "✨ Análisis IA"])
    
    with tab_desc:
        st.markdown(f'<div class="card">{data["description"]}</div>', unsafe_allow_html=True)
    
    with tab_revs:
        if data["reviews"]:
            for r in data["reviews"]:
                st.markdown(f"""
                <div class="review-box">
                    <strong>{r.get('userName', 'Usuario')}</strong> ({r.get('score', 0)} ⭐) - <small>{r.get('at', '')}</small><br>
                    {r.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No se encontraron reseñas públicas.")
            
    with tab_ai:
        if not openai_key:
            st.warning("⚠️ Configura tu OpenAI API Key en el panel lateral para activar el análisis inteligente.")
        else:
            st.markdown('<div class="ai-button">', unsafe_allow_html=True)
            if st.button("GENERAR ANÁLISIS ESTRATÉGICO"):
                with st.spinner("La IA está analizando los datos con visión granular..."):
                    # Preparar texto de reseñas (ahora enviamos hasta 30 para mayor precisión)
                    revs_summary = "\n".join([f"- {r.get('content')}" for r in data['reviews'][:30]])
                    
                    # Prompt ultra-detallado con todos los sub-ítems
                    prompt = f"""
                    Actúa como un experto en Inteligencia de Mercados para el sector educativo superior.
                    Analiza la información de la aplicación "{data['name']}" y completa la siguiente MATRIZ DETALLADA DE FUNCIONALIDADES.
                    
                    Debes evaluar cada sub-ítem individualmente basándote en la DESCRIPCIÓN y las RESEÑAS.
                    
                    ESTRUCTURA DE EVALUACIÓN:
                    
                    1. GESTIÓN ACADÉMICA Y CURRICULAR:
                       - Consulta de Calificaciones
                       - Progreso del Plan de Estudios
                       - Horarios
                       - Asistencia
                       - Historia Académica
                       
                    2. TRÁMITES Y SERVICIOS FINANCIEROS:
                       - Matrícula e Inscripción
                       - Portal de Pagos
                       - Gestión de Datos Personales
                       
                    3. IDENTIDAD Y ACCESO INSTITUCIONAL:
                       - Carnet Digital
                       - Control de Acceso (QR / Barras)
                       - Disponibilidad de Espacios (Equipos/Salas)
                       - Georreferenciación (Mapas/Rutas)
                       
                    4. COMUNICACIÓN Y NOTIFICACIONES:
                       - Mensajería Privada (Chat)
                       - Notificaciones Push
                       - Directorio y Contactos
                       - Integración Redes Sociales
                       
                    5. AGENDA Y VIDA UNIVERSITARIA:
                       - Calendario Académico
                       - Agenda de Eventos
                       - Módulos de Participación / Opinión
                       
                    6. ATENCIÓN AL USUARIO Y SOPORTE:
                       - CASAUR Virtual (Videoconferencia/Chat)
                       - Gestión de Citas (Presencial)
                       - Asesoría (Financiera/Académica)

                    INFORMACIÓN PARA ANALIZAR:
                    DESCRIPCIÓN: {data['description']}
                    RESEÑAS RECIENTES: {revs_summary if revs_summary else "No hay reseñas."}

                    INSTRUCCIONES DE RESPUESTA:
                    - Genera una tabla por cada pilar.
                    - Columnas: [Funcionalidad | Estado (SÍ/NO/PARCIAL) | Evidencia/Detalle].
                    - Al final, proporciona un "PUNTAJE DE COMPETITIVIDAD" (1-10) y una breve síntesis de qué hace que esta app sea única o qué le falta urgentemente.
                    
                    Responde en formato Markdown profesional.
                    """
                    
                    analysis = analyze_with_ai(openai_key, ai_model, data["name"], data["description"], revs_summary) # Aquí usaremos el prompt local
                    
                    # Llamada directa con el nuevo prompt local
                    try:
                        client = OpenAI(api_key=openai_key, base_url="https://api.deepseek.com")
                        response = client.chat.completions.create(
                            model=ai_model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7
                        )
                        st.markdown(f'<div class="ai-card">{response.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error al generar el reporte detallado: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de Descarga
    output_text = f"APP: {data['name']}\nUNIVERSIDAD: {uni_name}\nCALIFICACIÓN: {data['rating']}\n\nDESC:\n{data['description']}\n"
    st.download_button(
        label="Descargar Informe (.txt)",
        data=output_text,
        file_name=f"reporte_{data['name']}.txt",
        mime="text/plain"
    )

# Footer
st.markdown("---")
st.caption("CUN ® 2026 - Departamento de Inteligencia de Mercados")

# Footer
st.markdown("---")
st.caption("CUN ® 2026 - Departamento de Inteligencia de Mercados")
