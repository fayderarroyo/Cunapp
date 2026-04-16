import streamlit as st
import pandas as pd
from scrape_play_store import get_play_store_data
import re
import os
import json
from openai import OpenAI
from datetime import datetime

# Directorio de la Base de Datos
DB_FILE = os.path.join(os.path.dirname(__file__), "database_apps.json")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_db(data):
    def datetime_handler(x):
        if hasattr(x, 'isoformat'):
            return x.isoformat()
        return str(x)

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=datetime_handler)

st.set_page_config(
    page_title="CUN | Inteligencia Competitiva App",
    page_icon="🤖",
    layout="wide",
)

st.title("🎯 CUN | Tracker de Inteligencia Competitiva")
st.markdown("#### Análisis Estratégico Uno a Uno de Aplicaciones Móviles")

if 'db' not in st.session_state:
    st.session_state.db = load_db()

def update_session_db():
    save_db(st.session_state.db)

# --- CONFIGURACIONES SUPERIORES ---
with st.expander("⚙️ Configuraciones de Motor IA y Scraper", expanded=False):
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        openai_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
        ai_model = st.selectbox("Modelo", ["deepseek-chat", "deepseek-reasoner"], index=0)
    with col_c2:
        lang = st.selectbox("Idioma", ["es", "en"], index=0)
        country = st.selectbox("País", ["co", "us", "mx"], index=0)
    with col_c3:
        max_revs = st.slider("Límite de reseñas (aplica al guardado)", 50, 500, 200)

st.markdown("---")

tab_gest, tab_res, tab_db = st.tabs(["📋 Gestión y Consultas", "📊 Resultados Individuales", "🗄️ Base de Datos Transaccional"])

with tab_gest:
    st.markdown("### 1. Inscribir Aplicación en Cola")
    with st.form("add_app_form"):
        i_univ = st.text_input("Universidad a Investigar", placeholder="Ej: CUN")
        i_app_name = st.text_input("Nombre de la App", placeholder="Ej: CUN Virtual")
        i_url = st.text_input("URL de Google Play Store", placeholder="https://play.google.com/store/apps/details?id=...")
            
        submitted = st.form_submit_button("Agregar Aplicación")
        if submitted:
            if not i_univ or not i_app_name or not i_url:
                st.error("Todos los campos (Universidad, Nombre App y URL) son obligatorios.")
            else:
                if i_url in st.session_state.db:
                    st.warning("Esta URL de aplicación ya está registrada en la cola.")
                else:
                    st.session_state.db[i_url] = {
                        "universidad": i_univ.strip(),
                        "app_ingresada": i_app_name.strip(),
                        "url": i_url.strip(),
                        "fecha_consulta": "Pendiente",
                        "estado_analisis": "Pendiente"
                    }
                    update_session_db()
                    st.success(f"Aplicación '{i_app_name}' agregada exitosamente.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 2. Panel de Ejecución (Consultar / Actualizar)")
    
    pendientes = [url for url, info in st.session_state.db.items() if info.get("estado_analisis") == "Pendiente"]
    
    if not pendientes:
        st.success("🎉 Todas las aplicaciones en tu lista ya han sido iteradas y analizadas. ¡Agrega más arriba!")
    else:
        # Tomar la última agregada a la cola
        target_url = pendientes[-1]
        app_info = st.session_state.db[target_url]
        
        st.info(f"**App en Turno (Última Agregada):** {app_info.get('app_ingresada')} | **Universidad:** {app_info.get('universidad')}")
        st.write(f"Quedan **{len(pendientes)}** app(s) por procesar en la fila.")
        
        if st.button("🚀 Procesar App en Turno (Scraping + IA)"):
            if not openai_key:
                st.error("Por favor, ingresa tu DeepSeek API Key en las 'Configuraciones' (Arriba) antes de procesar.")
            else:
                with st.spinner("1. Extrayendo datos técnicos de Play Store..."):
                    match = re.search(r'id=([a-zA-Z0-9._]+)', target_url)
                    app_id = match.group(1) if match else target_url.strip()
                    
                    data = get_play_store_data(app_id, lang=lang, country=country, max_reviews=max_revs)
                    
                    if not data:
                        st.error("Error en extracción. Verifica que la URL exista en Google Play.")
                    else:
                        # Guardamos info básica requerida
                        st.session_state.db[target_url]["nombre"] = data["name"]
                        st.session_state.db[target_url]["descripcion"] = data["description"]
                        st.session_state.db[target_url]["calificacion"] = data["rating"]
                        st.session_state.db[target_url]["descargas"] = data["descargas"]
                        st.session_state.db[target_url]["resenas_extraidas"] = data["reviews"]
                        st.session_state.db[target_url]["fecha_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        update_session_db()
                        
                        st.success(f"Data extraída. Calificación: {data['rating']} ⭐ | Descargas: {data['descargas']}")
                        
                        st.info("2. Disparando DeepSeek para Análisis de Funcionalidades (JSON)...")
                        
                        revs_summary = "\n".join([f"- {r.get('content')}" for r in data.get('reviews', [])[:30]])
                        
                        prompt = f"""
                        Eres un ingeniero de Inteligencia Competitiva Analizando apps universitarias.
                        Analiza la app "{data['name']}" (Descripción y Reseñas) contra 6 pilares fijos.

                        1. GESTIÓN ACADÉMICA Y CURRICULAR
                        2. TRÁMITES Y SERVICIOS FINANCIEROS
                        3. IDENTIDAD Y ACCESO INSTITUCIONAL
                        4. COMUNICACIÓN Y NOTIFICACIONES
                        5. AGENDA Y VIDA UNIVERSITARIA
                        6. ATENCIÓN AL USUARIO Y SOPORTE

                        DESCRIPCIÓN: {data['description']}
                        RESEÑAS: {revs_summary if revs_summary else "N/A"}

                        INSTRUCCIÓN CRÍTICA: 
                        No retornes Markdown. No retornes explicaciones. 
                        Retorna ÚNICAMENTE un objeto JSON válido con esta estructura exacta para ser procesado:
                        {{
                          "pilares": [
                            {{
                              "nombre": "1. GESTIÓN ACADÉMICA Y CURRICULAR",
                              "funcionalidades": [
                                {{"funcionalidad": "Consulta de Calificaciones", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Progreso del Plan de Estudios", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Horarios", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Asistencia", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Historia Académica", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }},
                            {{
                              "nombre": "2. TRÁMITES Y SERVICIOS FINANCIEROS",
                              "funcionalidades": [
                                {{"funcionalidad": "Matrícula e Inscripción", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Portal de Pagos", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Gestión de Datos Personales", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }},
                            {{
                              "nombre": "3. IDENTIDAD Y ACCESO INSTITUCIONAL",
                              "funcionalidades": [
                                {{"funcionalidad": "Carnet Digital", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Control de Acceso (QR / Barras)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Disponibilidad de Espacios (Equipos/Salas)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Georreferenciación (Mapas/Rutas)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }},
                            {{
                              "nombre": "4. COMUNICACIÓN Y NOTIFICACIONES",
                              "funcionalidades": [
                                {{"funcionalidad": "Mensajería Privada (Chat)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Notificaciones Push", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Directorio y Contactos", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Integración Redes Sociales", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }},
                            {{
                              "nombre": "5. AGENDA Y VIDA UNIVERSITARIA",
                              "funcionalidades": [
                                {{"funcionalidad": "Calendario Académico", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Agenda de Eventos", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Módulos de Participación / Opinión", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }},
                            {{
                              "nombre": "6. ATENCIÓN AL USUARIO Y SOPORTE",
                              "funcionalidades": [
                                {{"funcionalidad": "Atención Virtual (Videoconferencia/Chat)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Gestión de Citas (Presencial)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}},
                                {{"funcionalidad": "Asesoría (Financiera/Académica)", "estado": "SÍ/NO/PARCIAL", "evidencia": "..."}}
                              ]
                            }}
                          ],
                          "puntaje_competitividad": "X.X / 10",
                          "sintesis": {{
                            "que_la_hace_unica": "Texto detallado...",
                            "que_le_falta_urgentemente": "Texto detallado...",
                            "conclusion": "Texto detallado..."
                          }}
                        }}
                        """
                        try:
                            client = OpenAI(api_key=openai_key, base_url="https://api.deepseek.com")
                            response = client.chat.completions.create(
                                model=ai_model,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.7
                            )
                            raw_result = response.choices[0].message.content
                            
                            # Limpiar strings raros si el LLM mete markdown
                            clean_json_str = raw_result.replace("```json", "").replace("```", "").strip()
                            
                            ai_list = json.loads(clean_json_str)
                            
                            st.session_state.db[target_url]["ai_analysis"] = ai_list
                            st.session_state.db[target_url]["estado_analisis"] = "Analizada"
                            update_session_db()
                            st.success("¡App Consultada, Analizada y Guardada con Éxito!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Fallo en la interpretación IA (El modelo no generó un JSON puro): {e}")
                            st.code(raw_result)

with tab_res:
    st.markdown("### 📊 Tablero de Resultados por Aplicación")
    st.caption("Visión profunda interactiva de funcionalidades, estados y evidencia detallada.")
    
    # Filtramos solo apps que ya tienen análisis
    apps_analizadas = {k: v for k, v in st.session_state.db.items() if v.get("estado_analisis") == "Analizada" and "ai_analysis" in v}
    
    if not apps_analizadas:
        st.info("No hay aplicaciones con análisis completado. Ve a 'Gestión y Consultas' para procesar una.")
    else:
        sel_app_res = st.selectbox(
            "Selecciona la App para ver el Informe Detallado:",
            options=list(apps_analizadas.keys()),
            format_func=lambda x: f"{apps_analizadas[x].get('app_ingresada')} ({apps_analizadas[x].get('universidad')})"
        )
        
        app_data = apps_analizadas[sel_app_res]
        
        st.markdown(f"#### 📱 {app_data.get('nombre', app_data.get('app_ingresada'))}")
        st.write(f"**Universidad:** {app_data.get('universidad')} | **Calificación:** {app_data.get('calificacion')} ⭐ | **Descargas:** {app_data.get('descargas')}")
        st.write(f"**Consulta:** {app_data.get('fecha_consulta')}")
        
        with st.expander("Ver Descripción Original", expanded=False):
            st.write(app_data.get('descripcion', 'N/A'))
            
        # Analizamos el formato nuevo complejo
        ai_data = app_data["ai_analysis"]
        
        if isinstance(ai_data, dict) and "pilares" in ai_data:
            col_mat, col_score = st.columns([6, 4])
            
            with col_mat:
                st.markdown("##### 🧠 Matriz Estratégica")
                for pilar in ai_data["pilares"]:
                    with st.expander(f"📌 {pilar.get('nombre', 'Pilar')}", expanded=True):
                        df_funcs = pd.DataFrame(pilar.get("funcionalidades", []))
                        if not df_funcs.empty:
                            df_funcs.rename(columns={"funcionalidad": "Funcionalidad", "estado": "Estado", "evidencia": "Evidencia/Detalle"}, inplace=True)
                            st.table(df_funcs)
                            
            with col_score:
                st.markdown("##### 🏆 Análisis de Competitividad")
                st.success(f"**PUNTAJE OBTENIDO:** {ai_data.get('puntaje_competitividad', 'N/A')}")
                
                sintesis = ai_data.get("sintesis", {})
                st.markdown("---")
                st.markdown("**💡 ¿Qué la hace única?**")
                st.info(sintesis.get('que_la_hace_unica', ''))
                
                st.markdown("**⚠️ ¿Qué le falta urgentemente?**")
                st.warning(sintesis.get('que_le_falta_urgentemente', ''))
                
                st.markdown("**🎯 Conclusión General**")
                st.error(sintesis.get('conclusion', ''))
            
        elif isinstance(ai_data, list):
            # Fallback para el formato JSON antiguo (plano)
            res_data = []
            for item in ai_data:
                res_data.append({
                    "Funcionalidad / Pilar": item.get("funcionalidad", ""),
                    "Estado": item.get("estado", ""),
                    "Evidencia / Detalle": item.get("evidencia", "")
                })
            st.dataframe(pd.DataFrame(res_data), use_container_width=True)

with tab_db:
    st.markdown("### Tabla Visual Matricial (Estilo Excel)")
    st.caption("Visión expandida donde cada aplicación es una fila y los pilares se agrupan en columnas superiores.")
    
    wide_data = []
    has_analyzed = False
    
    for url, info in st.session_state.db.items():
        if info.get("estado_analisis") == "Analizada" and "ai_analysis" in info:
            has_analyzed = True
            row = {
                ("INFORMACIÓN BASE", "Universidad"): info.get("universidad", "N/A"),
                ("INFORMACIÓN BASE", "Nombre de Aplicación"): info.get("nombre", info.get("app_ingresada")),
                ("INFORMACIÓN BASE", "Calificación"): info.get("calificacion", "N/A"),
            }
            
            ai_data = info["ai_analysis"]
            if isinstance(ai_data, dict) and "pilares" in ai_data:
                for pilar in ai_data["pilares"]:
                    pilar_name = pilar.get("nombre", "OTRO")
                    # Limpiamos el número inicial "1. ", "2. " del nombre del pilar si existe para que se vea mejor arriba
                    pilar_clean = re.sub(r'^\d+\.\s*', '', pilar_name)
                    for f in pilar.get("funcionalidades", []):
                        row[(pilar_clean, f.get("funcionalidad", ""))] = f.get("estado", "")
            
            wide_data.append(row)
        else:
            wide_data.append({
                ("INFORMACIÓN BASE", "Universidad"): info.get("universidad", "N/A"),
                ("INFORMACIÓN BASE", "Nombre de Aplicación"): info.get("app_ingresada", "N/A"),
                ("INFORMACIÓN BASE", "Calificación"): "Pendiente",
            })
            
    if wide_data:
        df_db = pd.DataFrame(wide_data)
        
        # Convertir a MultiIndex solo si hay al menos una app analizada (tuplas en claves)
        if has_analyzed:
            df_db.columns = pd.MultiIndex.from_tuples(df_db.columns)
            
        df_db = df_db.fillna("N/A")
        
        # Render the large matrix horizontally 
        st.dataframe(
            df_db,
            use_container_width=True,
            column_config={
                "Nombre de Aplicación": st.column_config.TextColumn(width="large"),
                "Universidad": st.column_config.TextColumn(width="medium")
            }
        )
        
        # Guardar / Descargar el JSON primario que tiene toda la info oculta (descargas, evidencias)
        def dt_handle(x):
            if hasattr(x, 'isoformat'):
                return x.isoformat()
            return str(x)
            
        json_string = json.dumps(st.session_state.db, ensure_ascii=False, indent=4, default=dt_handle)
        st.download_button(
            label="Descargar Base (JSON) con TODA la Data Desplegada",
            data=json_string,
            file_name="database_inteligencia.json",
            mime="application/json"
        )
    else:
        st.info("La Base de Datos está vacía por el momento.")

# Footer
st.markdown("---")
st.caption("CUN ® 2026 - Departamento de Inteligencia de Competencia")
