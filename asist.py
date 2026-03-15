import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
from PIL import Image
import io
import base64
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
import time

# CONFIGURACION DE PAGINA
st.set_page_config(
    page_title="⚡ QR Asistencia Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILOS CSS PERSONALIZADOS
st.markdown("""
<style>
    /* Estilos globales */
    .stApp {
        background: linear-gradient(135deg, #0a1929 0%, #0f2744 50%, #1a3a5c 100%);
    }
    
    /* Animaciones */
    @keyframes electricPulse {
        0% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.02); }
        100% { opacity: 0.3; transform: scale(1); }
    }
    
    @keyframes lightning {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* Fondo eléctrico */
    .electric-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(0, 191, 255, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(100, 149, 237, 0.05) 0%, transparent 50%);
        animation: electricPulse 8s infinite;
    }
    
    /* Líneas eléctricas */
    .electric-line {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            repeating-linear-gradient(
                90deg,
                transparent,
                transparent 50px,
                rgba(0, 255, 255, 0.03) 50px,
                rgba(0, 255, 255, 0.03) 51px
            ),
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 50px,
                rgba(0, 191, 255, 0.03) 50px,
                rgba(0, 191, 255, 0.03) 51px
            );
        pointer-events: none;
        z-index: 0;
    }
    
    /* Header */
    .header-container {
        text-align: center;
        padding: 30px;
        margin-bottom: 30px;
        position: relative;
        z-index: 1;
    }
    
    .header-title {
        font-size: 3.5em;
        font-weight: bold;
        color: #00ffff;
        text-shadow: 0 0 20px #00ffff, 0 0 40px #00b4db;
        margin-bottom: 10px;
        animation: electricPulse 3s infinite;
    }
    
    .header-subtitle {
        color: #ffffff;
        font-size: 1.2em;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: linear-gradient(90deg, transparent, #00ffff, transparent);
        padding: 10px;
        display: inline-block;
        border-radius: 30px;
    }
    
    /* Tarjetas */
    .card {
        background: linear-gradient(145deg, rgba(19, 47, 76, 0.9), rgba(10, 31, 51, 0.95));
        border: 1px solid #00ffff;
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
    }
    
    .card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 0 50px rgba(0, 255, 255, 0.4);
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 12px 30px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
        width: 100% !important;
        box-shadow: 0 0 20px rgba(0, 180, 219, 0.5) !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 40px #00ffff !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(10, 25, 41, 0.8) !important;
        border: 2px solid #00b4db !important;
        border-radius: 15px !important;
        color: white !important;
        font-size: 16px !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00ffff !important;
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.3) !important;
        transform: scale(1.02);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(10, 25, 41, 0.8) !important;
        border: 2px solid #00b4db !important;
        border-radius: 15px !important;
        color: white !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #00ffff !important;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }
    
    /* DataFrames */
    .dataframe {
        background: rgba(10, 25, 41, 0.9) !important;
        border: 1px solid #00ffff !important;
        border-radius: 15px !important;
        padding: 10px !important;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
    }
    
    .dataframe th {
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        color: white !important;
        border-bottom: 1px solid #00b4db !important;
        padding: 10px !important;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #132f4c, #0a1f33);
        border: 1px solid #00ffff;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        transition: all 0.3s ease;
        margin: 10px 0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 40px rgba(0, 255, 255, 0.4);
    }
    
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        color: #00ffff;
        text-shadow: 0 0 20px #00ffff;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 1em;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-icon {
        font-size: 2em;
        margin-bottom: 10px;
        animation: float 3s ease-in-out infinite;
    }
    
    /* Cámara */
    div[data-testid="stCameraInput"] {
        border: 3px solid #00ffff !important;
        border-radius: 20px !important;
        overflow: hidden !important;
        box-shadow: 0 0 40px rgba(0, 255, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stCameraInput"]:hover {
        transform: scale(1.02);
        box-shadow: 0 0 60px rgba(0, 255, 255, 0.5) !important;
    }
    
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 60vh !important;
        object-fit: cover !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(10, 25, 41, 0.8);
        padding: 10px;
        border-radius: 50px;
        border: 1px solid #00ffff;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
    }
    
    /* QR Image */
    .qr-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        background: white;
        border-radius: 20px;
        margin: 20px 0;
        animation: float 5s ease-in-out infinite;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid #00ffff;
        color: #00ffff;
        font-size: 0.9em;
    }
    
    /* Mensajes de éxito/error */
    .stAlert {
        border-radius: 15px !important;
        border: 1px solid #00ffff !important;
        animation: electricPulse 2s infinite !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0a1929 0%, #0f2744 100%) !important;
        border-right: 2px solid #00ffff !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a1929;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #00b4db, #0083b0);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00ffff;
    }
</style>

<div class="electric-bg"></div>
<div class="electric-line"></div>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ QR ASISTENCIA PRO ⚡</div>
    <div class="header-subtitle">SISTEMA INTELIGENTE DE CONTROL DE ASISTENCIA</div>
</div>
""", unsafe_allow_html=True)

# ARCHIVOS
archivo_estudiantes = "estudiantes.xlsx"
archivo_asistencia = "asistencia.xlsx"

# CREAR ARCHIVOS SI NO EXISTEN
if not os.path.exists(archivo_estudiantes):
    df = pd.DataFrame(columns=[
        "RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"
    ])
    df.to_excel(archivo_estudiantes, index=False)

if not os.path.exists(archivo_asistencia):
    df = pd.DataFrame(columns=[
        "RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"
    ])
    df.to_excel(archivo_asistencia, index=False)

# FUNCIONES DE CACHE
@st.cache_data(ttl=60)
def cargar_estudiantes():
    return pd.read_excel(archivo_estudiantes)

@st.cache_data(ttl=60)
def cargar_asistencia():
    return pd.read_excel(archivo_asistencia)

# MENU LATERAL
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: #00ffff; border: none; font-size: 2em;">⚡ MENÚ ⚡</h2>
    </div>
    """, unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=[
            "Dashboard",
            "Registrar Estudiante",
            "Lista Estudiantes",
            "Escanear QR",
            "Registro Manual",
            "Ver Asistencia"
        ],
        icons=[
            'graph-up',
            'person-plus-fill',
            'people-fill',
            'camera-fill',
            'pencil-fill',
            'calendar-check-fill'
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#0a1929"},
            "icon": {"color": "#00ffff", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "--hover-color": "#132f4c",
                "color": "#ffffff"
            },
            "nav-link-selected": {
                "background-color": "#00b4db",
                "color": "white",
                "font-weight": "bold"
            },
        }
    )
    
    # Información del sistema
    st.markdown("---")
    st.markdown("""
    <div style="padding: 10px;">
        <p style="color: #00ffff; font-size: 0.9em;">
            <strong>⚡ Sistema Activo</strong><br>
            Versión: 2.0<br>
            Modo: Online<br>
            Estado: Conectado
        </p>
    </div>
    """, unsafe_allow_html=True)

# DASHBOARD
if menu == "Dashboard":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 DASHBOARD DE ASISTENCIA")
        
        estudiantes = cargar_estudiantes()
        asistencia = cargar_asistencia()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">👥</div>
                <div class="metric-value">{len(estudiantes)}</div>
                <div class="metric-label">Total Estudiantes</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            hoy = datetime.now().date()
            asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == str(hoy)]
            presentes_hoy = len(asistencia_hoy[asistencia_hoy["Estado"] == "Presente"])
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">✅</div>
                <div class="metric-value">{presentes_hoy}</div>
                <div class="metric-label">Presentes Hoy</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_registros = len(asistencia)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📝</div>
                <div class="metric-value">{total_registros}</div>
                <div class="metric-label">Total Registros</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if len(estudiantes) > 0:
                porcentaje_asistencia = (presentes_hoy / len(estudiantes)) * 100
            else:
                porcentaje_asistencia = 0
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📊</div>
                <div class="metric-value">{porcentaje_asistencia:.1f}%</div>
                <div class="metric-label">Asistencia Hoy</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráficos
        if len(asistencia) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de asistencia por estado
                estado_counts = asistencia['Estado'].value_counts().reset_index()
                estado_counts.columns = ['Estado', 'Cantidad']
                
                fig = px.pie(
                    estado_counts,
                    values='Cantidad',
                    names='Estado',
                    title='📊 Distribución por Estado',
                    color_discrete_map={
                        'Presente': '#00ff00',
                        'Tarde': '#ffff00',
                        'Permiso': '#00ffff',
                        'Ausente': '#ff4444'
                    }
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    title_font_color='#00ffff'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gráfico de asistencia por fecha
                asistencia_por_fecha = asistencia.groupby('Fecha').size().reset_index(name='Cantidad')
                asistencia_por_fecha = asistencia_por_fecha.tail(10)
                
                fig = px.line(
                    asistencia_por_fecha,
                    x='Fecha',
                    y='Cantidad',
                    title='📈 Tendencia de Asistencia',
                    markers=True
                )
                fig.update_traces(line_color='#00ffff', marker_color='#00ffff')
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    title_font_color='#00ffff'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# REGISTRAR ESTUDIANTE
elif menu == "Registrar Estudiante":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📝 REGISTRAR NUEVO ESTUDIANTE")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ru = st.text_input("🎓 RU", placeholder="Ingrese el RU del estudiante")
            nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres completos")
        
        with col2:
            paterno = st.text_input("👨 Apellido paterno", placeholder="Ingrese apellido paterno")
            materno = st.text_input("👩 Apellido materno", placeholder="Ingrese apellido materno")
        
        if st.button("⚡ GENERAR QR Y GUARDAR", use_container_width=True):
            if ru and nombres and paterno:
                with st.spinner("⚡ Generando código QR..."):
                    df = cargar_estudiantes()
                    
                    if ru in df["RU"].astype(str).values:
                        st.error("❌ Este RU ya existe en el sistema")
                    else:
                        # Crear directorio qr si no existe
                        if not os.path.exists("qr"):
                            os.mkdir("qr")
                        
                        # Generar QR
                        ruta_qr = f"qr/{ru}.png"
                        qr = qrcode.QRCode(
                            version=1,
                            box_size=10,
                            border=5
                        )
                        qr.add_data(ru)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        img.save(ruta_qr)
                        
                        # Guardar en Excel
                        nuevo = pd.DataFrame([[ru, nombres, paterno, materno, ruta_qr]],
                                            columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
                        
                        df = pd.concat([df, nuevo], ignore_index=True)
                        df.to_excel(archivo_estudiantes, index=False)
                        
                        st.success("✅ Estudiante registrado exitosamente!")
                        
                        # Mostrar QR
                        col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                        with col_qr2:
                            st.markdown('<div class="qr-container">', unsafe_allow_html=True)
                            st.image(ruta_qr, width=300)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            with open(ruta_qr, "rb") as file:
                                st.download_button(
                                    label="📥 DESCARGAR QR",
                                    data=file,
                                    file_name=f"{ru}_qr.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
            else:
                st.warning("⚠️ Complete todos los campos")
        
        st.markdown('</div>', unsafe_allow_html=True)

# LISTA ESTUDIANTES
elif menu == "Lista Estudiantes":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 LISTA DE ESTUDIANTES")
        
        estudiantes = cargar_estudiantes()
        
        if len(estudiantes) > 0:
            # Búsqueda
            busqueda = st.text_input("🔍 Buscar estudiante (RU, Nombre, Apellido)", placeholder="Escriba para buscar...")
            
            if busqueda:
                estudiantes_filtrados = estudiantes[
                    estudiantes["RU"].astype(str).str.contains(busqueda, case=False) |
                    estudiantes["Nombres"].str.contains(busqueda, case=False) |
                    estudiantes["Apellido_paterno"].str.contains(busqueda, case=False) |
                    estudiantes["Apellido_materno"].str.contains(busqueda, case=False)
                ]
            else:
                estudiantes_filtrados = estudiantes
            
            st.dataframe(estudiantes_filtrados, use_container_width=True)
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(estudiantes_filtrados)}</div>
                    <div class="metric-label">Estudiantes Mostrados</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Pestañas de acciones
            tab1, tab2, tab3 = st.tabs(["✏️ Editar", "🗑️ Eliminar", "📥 Descargar"])
            
            with tab1:
                if len(estudiantes_filtrados) > 0:
                    indices = list(range(len(estudiantes_filtrados)))
                    idx_display = st.selectbox(
                        "Seleccionar estudiante",
                        indices,
                        format_func=lambda x: f"{estudiantes_filtrados.iloc[x]['RU']} - {estudiantes_filtrados.iloc[x]['Nombres']} {estudiantes_filtrados.iloc[x]['Apellido_paterno']}"
                    )
                    
                    with st.form("edit_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            ru_edit = st.text_input("RU", value=str(estudiantes_filtrados.iloc[idx_display]["RU"]))
                            nombres_edit = st.text_input("Nombres", value=estudiantes_filtrados.iloc[idx_display]["Nombres"])
                        with col2:
                            paterno_edit = st.text_input("Apellido paterno", value=estudiantes_filtrados.iloc[idx_display]["Apellido_paterno"])
                            materno_edit = st.text_input("Apellido materno", value=estudiantes_filtrados.iloc[idx_display]["Apellido_materno"])
                        
                        if st.form_submit_button("⚡ ACTUALIZAR"):
                            idx_real = estudiantes_filtrados.index[idx_display]
                            estudiantes.loc[idx_real, "RU"] = ru_edit
                            estudiantes.loc[idx_real, "Nombres"] = nombres_edit
                            estudiantes.loc[idx_real, "Apellido_paterno"] = paterno_edit
                            estudiantes.loc[idx_real, "Apellido_materno"] = materno_edit
                            estudiantes.to_excel(archivo_estudiantes, index=False)
                            st.success("✅ Estudiante actualizado!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
            
            with tab2:
                if len(estudiantes_filtrados) > 0:
                    idx_eliminar = st.selectbox(
                        "Seleccionar estudiante a eliminar",
                        range(len(estudiantes_filtrados)),
                        format_func=lambda x: f"{estudiantes_filtrados.iloc[x]['RU']} - {estudiantes_filtrados.iloc[x]['Nombres']} {estudiantes_filtrados.iloc[x]['Apellido_paterno']}"
                    )
                    
                    if st.checkbox("Confirmar eliminación"):
                        if st.button("🗑️ ELIMINAR ESTUDIANTE"):
                            idx_real = estudiantes_filtrados.index[idx_eliminar]
                            
                            # Eliminar archivo QR
                            try:
                                qr_path = estudiantes.loc[idx_real, "QR"]
                                if os.path.exists(qr_path):
                                    os.remove(qr_path)
                            except:
                                pass
                            
                            estudiantes = estudiantes.drop(idx_real)
                            estudiantes.to_excel(archivo_estudiantes, index=False)
                            st.success("✅ Estudiante eliminado!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
            
            with tab3:
                archivo_descarga = "registro_estudiantes.xlsx"
                estudiantes.to_excel(archivo_descarga, index=False)
                
                with open(archivo_descarga, "rb") as file:
                    st.download_button(
                        "📥 DESCARGAR EXCEL COMPLETO",
                        data=file,
                        file_name=archivo_descarga,
                        use_container_width=True
                    )
        else:
            st.info("ℹ️ No hay estudiantes registrados")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ESCANEAR QR
elif menu == "Escanear QR":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📸 ESCANEAR QR DE ASISTENCIA")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            foto = st.camera_input("📷 Enfoque el código QR del estudiante")
        
        with col2:
            st.markdown("""
            <div style="background: rgba(0,180,219,0.1); padding: 20px; border-radius: 15px;">
                <h4 style="color: #00ffff;">📌 Instrucciones:</h4>
                <ul style="color: white;">
                    <li>✅ Enfoque bien el código QR</li>
                    <li>💡 Asegure buena iluminación</li>
                    <li>🤳 Mantenga el QR estable</li>
                    <li>⚡ Espere la confirmación</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if foto is not None:
            with st.spinner("⚡ Procesando QR..."):
                # Convertir la imagen a formato OpenCV
                bytes_data = foto.getvalue()
                cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                
                # Detectar QR
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(cv2_img)
                
                if data:
                    ru = data
                    estudiantes = cargar_estudiantes()
                    estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]
                    
                    if len(estudiante) > 0:
                        nombres = estudiante.iloc[0]["Nombres"]
                        paterno = estudiante.iloc[0]["Apellido_paterno"]
                        materno = estudiante.iloc[0]["Apellido_materno"]
                        
                        ahora = datetime.now()
                        fecha = ahora.date()
                        hora = ahora.strftime("%H:%M:%S")
                        
                        asistencia = cargar_asistencia()
                        ya = asistencia[
                            (asistencia["RU"].astype(str) == ru) &
                            (asistencia["Fecha"].astype(str) == str(fecha))
                        ]
                        
                        if len(ya) == 0:
                            nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                                columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                            
                            asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                            asistencia.to_excel(archivo_asistencia, index=False)
                            
                            st.balloons()
                            st.success(f"""
                            ✅ **ASISTENCIA REGISTRADA!**
                            
                            **Estudiante:** {nombres} {paterno} {materno}
                            **RU:** {ru}
                            **Hora:** {hora}
                            """)
                        else:
                            st.warning(f"⚠️ Ya registró asistencia hoy a las {ya.iloc[0]['Hora']}")
                    else:
                        st.error("❌ Estudiante no encontrado")
                else:
                    st.error("❌ No se detectó QR válido")
        
        st.markdown('</div>', unsafe_allow_html=True)

# REGISTRO MANUAL
elif menu == "Registro Manual":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("✏️ REGISTRO MANUAL DE ASISTENCIA")
        
        estudiantes = cargar_estudiantes()
        
        if len(estudiantes) > 0:
            estudiantes["nombre_completo"] = (
                estudiantes["RU"].astype(str) + " - " +
                estudiantes["Nombres"] + " " +
                estudiantes["Apellido_paterno"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                seleccionado = st.selectbox(
                    "👤 Seleccionar estudiante",
                    estudiantes["nombre_completo"]
                )
                
                estado = st.selectbox(
                    "📊 Estado de asistencia",
                    ["Presente", "Tarde", "Permiso", "Ausente"]
                )
            
            with col2:
                st.markdown("""
                <div style="background: rgba(0,180,219,0.1); padding: 20px; border-radius: 15px;">
                    <h4 style="color: #00ffff;">📝 Leyenda:</h4>
                    <ul style="color: white; list-style: none;">
                        <li>✅ Presente - Llegó a tiempo</li>
                        <li>⏰ Tarde - Llegó después</li>
                        <li>📋 Permiso - Autorizado</li>
                        <li>❌ Ausente - No asistió</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("⚡ REGISTRAR ASISTENCIA", use_container_width=True):
                ru = seleccionado.split(" - ")[0]
                estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]
                
                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]
                
                ahora = datetime.now()
                fecha = ahora.date()
                hora = ahora.strftime("%H:%M:%S")
                
                asistencia = cargar_asistencia()
                
                nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                                    columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                
                asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                asistencia.to_excel(archivo_asistencia, index=False)
                
                st.success(f"✅ Asistencia registrada: {nombres} {paterno} - {estado}")
        else:
            st.info("ℹ️ No hay estudiantes registrados")
        
        st.markdown('</div>', unsafe_allow_html=True)

# VER ASISTENCIA
elif menu == "Ver Asistencia":
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 REGISTROS DE ASISTENCIA")
        
        asistencia = cargar_asistencia()
        
        if len(asistencia) > 0:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fechas_unicas = ["Todas"] + sorted(asistencia["Fecha"].unique().tolist(), reverse=True)
                fecha_filter = st.selectbox("📅 Filtrar por fecha", fechas_unicas)
            
            with col2:
                estados_unicos = ["Todos"] + asistencia["Estado"].unique().tolist()
                estado_filter = st.selectbox("📊 Filtrar por estado", estados_unicos)
            
            with col3:
                busqueda = st.text_input("🔍 Buscar", placeholder="RU o nombre...")
            
            # Aplicar filtros
            datos_filtrados = asistencia.copy()
            
            if fecha_filter != "Todas":
                datos_filtrados = datos_filtrados[datos_filtrados["Fecha"] == fecha_filter]
            
            if estado_filter != "Todos":
                datos_filtrados = datos_filtrados[datos_filtrados["Estado"] == estado_filter]
            
            if busqueda:
                datos_filtrados = datos_filtrados[
                    datos_filtrados["RU"].astype(str).str.contains(busqueda, case=False) |
                    datos_filtrados["Nombres"].str.contains(busqueda, case=False) |
                    datos_filtrados["Apellido_paterno"].str.contains(busqueda, case=False)
                ]
            
            st.dataframe(datos_filtrados, use_container_width=True)
            
            # Resumen
            st.subheader("📈 Resumen")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(datos_filtrados)}</div>
                    <div class="metric-label">Registros</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                presentes = len(datos_filtrados[datos_filtrados["Estado"] == "Presente"])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{presentes}</div>
                    <div class="metric-label">Presentes</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                tarde = len(datos_filtrados[datos_filtrados["Estado"] == "Tarde"])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{tarde}</div>
                    <div class="metric-label">Tarde</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                ausentes = len(datos_filtrados[datos_filtrados["Estado"] == "Ausente"])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{ausentes}</div>
                    <div class="metric-label">Ausentes</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Exportar
            if st.button("📥 DESCARGAR EXCEL FILTRADO"):
                archivo_descarga = f"asistencia_filtrada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                datos_filtrados.to_excel(archivo_descarga, index=False)
                
                with open(archivo_descarga, "rb") as file:
                    st.download_button(
                        "📥 HAGA CLIC PARA DESCARGAR",
                        data=file,
                        file_name=archivo_descarga,
                        use_container_width=True
                    )
        else:
            st.info("ℹ️ No hay registros de asistencia")
        
        st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div class="footer">
    <p>⚡ Sistema de Asistencia QR Pro v2.0 | Desarrollado con tecnología de punta ⚡</p>
    <p style="font-size: 0.8em;">© 2024 - Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
