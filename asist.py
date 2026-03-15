import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz
import shutil

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')  # Cambia según tu ubicación

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S.%f")[:-3]  # Con milisegundos
    return fecha, hora

# ------------------------------------------------------------
# FUNCIÓN PARA VERIFICAR REGISTRO DUPLICADO
# ------------------------------------------------------------
def verificar_registro_duplicado(ru, fecha):
    """
    Verifica si un estudiante ya tiene registro de asistencia en la fecha actual
    Retorna: (tiene_registro, registro_existente)
    """
    asistencia = leer_asistencia()
    registro_existente = asistencia[(asistencia["RU"].astype(str) == str(ru)) & 
                                   (asistencia["Fecha"].astype(str) == str(fecha))]
    
    if len(registro_existente) > 0:
        return True, registro_existente.iloc[0]
    return False, None

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILOS CSS ELEGANTES (MODO OSCURO + BOTONES DE COLORES)
# ------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --bg-dark: #0a0c10;
        --bg-card: #1a1d24;
        --bg-sidebar: #13161c;
        --text-primary: #ffffff;
        --text-secondary: #a0a8b8;
        --accent: #6366f1;
        --accent-light: #818cf8;
        --border: #2d333b;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: #3b82f6;
        --duplicate: #f97316;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0c10 0%, #1a1d24 100%);
        color: var(--text-primary);
    }

    /* Menú horizontal con botones elegantes */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 15px;
        background: rgba(26, 29, 36, 0.7);
        backdrop-filter: blur(10px);
        padding: 12px 20px;
        border-radius: 40px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    div.row-widget.stRadio > div label {
        color: var(--text-secondary) !important;
        font-size: 1rem;
        font-weight: 500;
        padding: 10px 24px;
        border-radius: 30px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        background: transparent;
        letter-spacing: 0.3px;
        position: relative;
        overflow: hidden;
    }
    
    div.row-widget.stRadio > div label::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    div.row-widget.stRadio > div label:hover::before {
        opacity: 1;
    }
    
    div.row-widget.stRadio > div label:hover {
        transform: translateY(-2px);
        border-color: currentColor;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Colores específicos para cada opción - estilo elegante */
    div.row-widget.stRadio > div label:nth-child(1) {
        color: #60a5fa !important;
        border-color: #60a5fa;
        background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(96, 165, 250, 0) 100%);
    }
    div.row-widget.stRadio > div label:nth-child(2) {
        color: #34d399 !important;
        border-color: #34d399;
        background: linear-gradient(135deg, rgba(52, 211, 153, 0.1) 0%, rgba(52, 211, 153, 0) 100%);
    }
    div.row-widget.stRadio > div label:nth-child(3) {
        color: #fbbf24 !important;
        border-color: #fbbf24;
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(251, 191, 36, 0) 100%);
    }
    div.row-widget.stRadio > div label:nth-child(4) {
        color: #f87171 !important;
        border-color: #f87171;
        background: linear-gradient(135deg, rgba(248, 113, 113, 0.1) 0%, rgba(248, 113, 113, 0) 100%);
    }
    div.row-widget.stRadio > div label:nth-child(5) {
        color: #c084fc !important;
        border-color: #c084fc;
        background: linear-gradient(135deg, rgba(192, 132, 252, 0.1) 0%, rgba(192, 132, 252, 0) 100%);
    }
    
    /* Estilo para la opción seleccionada */
    div.row-widget.stRadio > div label:nth-child(1) input:checked + div {
        background: linear-gradient(135deg, #3b82f6, #60a5fa) !important;
        color: white !important;
        border: none;
        box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.5);
    }
    div.row-widget.stRadio > div label:nth-child(2) input:checked + div {
        background: linear-gradient(135deg, #10b981, #34d399) !important;
        color: white !important;
        border: none;
        box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.5);
    }
    div.row-widget.stRadio > div label:nth-child(3) input:checked + div {
        background: linear-gradient(135deg, #f59e0b, #fbbf24) !important;
        color: white !important;
        border: none;
        box-shadow: 0 8px 16px -4px rgba(245, 158, 11, 0.5);
    }
    div.row-widget.stRadio > div label:nth-child(4) input:checked + div {
        background: linear-gradient(135deg, #ef4444, #f87171) !important;
        color: white !important;
        border: none;
        box-shadow: 0 8px 16px -4px rgba(239, 68, 68, 0.5);
    }
    div.row-widget.stRadio > div label:nth-child(5) input:checked + div {
        background: linear-gradient(135deg, #a855f7, #c084fc) !important;
        color: white !important;
        border: none;
        box-shadow: 0 8px 16px -4px rgba(168, 85, 247, 0.5);
    }

    /* Inputs elegantes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: rgba(26, 29, 36, 0.8) !important;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: var(--text-primary) !important;
        border-radius: 12px;
        padding: 10px 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
        background: rgba(26, 29, 36, 0.95) !important;
    }
    
    .stTextInput input:hover, .stSelectbox div[data-baseweb="select"]:hover {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Botones elegantes */
    .stButton button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-transform: uppercase;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 20px -8px rgba(99, 102, 241, 0.6);
        filter: brightness(1.1);
    }
    
    .stButton button:active {
        transform: translateY(0) scale(0.98);
    }

    /* Botón deshabilitado */
    .stButton button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

    /* DataFrames elegantes */
    .stDataFrame {
        background: rgba(26, 29, 36, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    
    .stDataFrame table {
        color: var(--text-primary) !important;
    }
    
    .stDataFrame th {
        background: rgba(19, 22, 28, 0.9) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 12px !important;
        border-bottom: 2px solid var(--accent) !important;
    }
    
    .stDataFrame td {
        background: transparent !important;
        color: var(--text-secondary) !important;
        padding: 10px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Tarjetas elegantes */
    div.stMarkdown, div.stAlert {
        background: rgba(26, 29, 36, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    /* Alertas elegantes */
    .stAlert {
        border-left: 4px solid;
        animation: slideIn 0.3s ease;
        background: rgba(26, 29, 36, 0.9) !important;
    }
    
    .stAlert.success { 
        border-left-color: var(--success);
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(26, 29, 36, 0.9) 100%) !important;
    }
    
    .stAlert.warning { 
        border-left-color: var(--warning);
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, rgba(26, 29, 36, 0.9) 100%) !important;
    }
    
    .stAlert.error { 
        border-left-color: var(--error);
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(26, 29, 36, 0.9) 100%) !important;
    }
    
    .stAlert.info { 
        border-left-color: var(--info);
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, rgba(26, 29, 36, 0.9) 100%) !important;
    }
    
    .stAlert.duplicate { 
        border-left-color: var(--duplicate);
        background: linear-gradient(90deg, rgba(249, 115, 22, 0.1) 0%, rgba(26, 29, 36, 0.9) 100%) !important;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* Scrollbar elegante */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(26, 29, 36, 0.5);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        border-radius: 5px;
        border: 2px solid rgba(26, 29, 36, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--accent-light) 0%, var(--accent) 100%);
    }

    /* Cámara elegante */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        border-radius: 16px;
        border: 2px solid transparent;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) border-box;
        mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
        -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
        -webkit-mask-composite: xor;
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
    }
    
    div[data-testid="stCameraInput"] {
        width: 100% !important;
        padding: 3px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        border-radius: 19px;
    }

    /* Uploaders elegantes */
    .uploader-box {
        background: rgba(26, 29, 36, 0.7);
        backdrop-filter: blur(5px);
        border-radius: 12px;
        padding: 1rem;
        border: 2px dashed var(--accent);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .uploader-box:hover {
        border-color: var(--accent-light);
        background: rgba(26, 29, 36, 0.9);
    }

    /* Sidebar elegante */
    .css-1d391kg, .css-163ttbj {
        background: rgba(19, 22, 28, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Títulos elegantes */
    h1, h2, h3 {
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-light) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Imágenes elegantes */
    .stImage img {
        border-radius: 16px;
        border: 3px solid transparent;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) border-box;
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    .stImage img:hover {
        transform: scale(1.02);
        box-shadow: 0 30px 50px -15px rgba(99, 102, 241, 0.6);
    }

    /* Separadores elegantes */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        margin: 2rem 0;
    }
    
    /* Tarjeta de advertencia de duplicado */
    .duplicate-card {
        background: rgba(249, 115, 22, 0.1);
        border: 1px solid var(--duplicate);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .duplicate-card h4 {
        color: var(--duplicate);
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# INICIALIZAR SESSION STATE PARA RUTAS DE ARCHIVOS Y MENÚ
# ------------------------------------------------------------
if "ruta_estudiantes" not in st.session_state:
    st.session_state.ruta_estudiantes = "estudiantes.xlsx"
if "ruta_asistencia" not in st.session_state:
    st.session_state.ruta_asistencia = "asistencia.xlsx"
if "archivo_estudiantes_subido" not in st.session_state:
    st.session_state.archivo_estudiantes_subido = None
if "archivo_asistencia_subido" not in st.session_state:
    st.session_state.archivo_asistencia_subido = None
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "📝 Registrar estudiante"
if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None

# ------------------------------------------------------------
# TÍTULO Y MENÚ HORIZONTAL (CON BOTONES DE COLORES ELEGANTES)
# ------------------------------------------------------------
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>📷 Sistema de Asistencia con QR</h1>", unsafe_allow_html=True)

opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia"
]

# Crear columnas para centrar el menú
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    menu = st.radio(
        "",
        opciones_menu,
        horizontal=True,
        label_visibility="collapsed",
        key="menu_radio"
    )

st.session_state.menu_actual = menu

# ------------------------------------------------------------
# SIDEBAR: CARGAR ARCHIVOS EXCEL (ELEGANTE)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Gestión de Archivos")
    st.markdown("### Sube tus archivos Excel")
    
    with st.container():
        st.markdown('<div class="uploader-box">', unsafe_allow_html=True)
        if not os.path.exists("uploads"):
            os.makedirs("uploads")

        archivo_est = st.file_uploader("📘 Estudiantes", type=["xlsx"], key="upload_est")
        if archivo_est is not None:
            ruta_destino = os.path.join("uploads", archivo_est.name)
            with open(ruta_destino, "wb") as f:
                f.write(archivo_est.getbuffer())
            st.session_state.ruta_estudiantes = ruta_destino
            st.session_state.archivo_estudiantes_subido = archivo_est.name
            st.success(f"✅ Cargado: {archivo_est.name}")

        archivo_asis = st.file_uploader("📗 Asistencia", type=["xlsx"], key="upload_asis")
        if archivo_asis is not None:
            ruta_destino = os.path.join("uploads", archivo_asis.name)
            with open(ruta_destino, "wb") as f:
                f.write(archivo_asis.getbuffer())
            st.session_state.ruta_asistencia = ruta_destino
            st.session_state.archivo_asistencia_subido = archivo_asis.name
            st.success(f"✅ Cargado: {archivo_asis.name}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📁 Archivos activos")
    
    with st.container():
        st.info(f"📘 **Estudiantes:**\n`{os.path.basename(st.session_state.ruta_estudiantes)}`")
        st.info(f"📗 **Asistencia:**\n`{os.path.basename(st.session_state.ruta_asistencia)}`")

    st.markdown("---")
    st.markdown("### ⬇️ Descargar archivos")
    
    col_down1, col_down2 = st.columns(2)
    with col_down1:
        if os.path.exists(st.session_state.ruta_estudiantes):
            with open(st.session_state.ruta_estudiantes, "rb") as f:
                st.download_button("📘 Estudiantes", data=f, 
                                 file_name=os.path.basename(st.session_state.ruta_estudiantes),
                                 use_container_width=True)
    
    with col_down2:
        if os.path.exists(st.session_state.ruta_asistencia):
            with open(st.session_state.ruta_asistencia, "rb") as f:
                st.download_button("📗 Asistencia", data=f, 
                                 file_name=os.path.basename(st.session_state.ruta_asistencia),
                                 use_container_width=True)

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def leer_estudiantes():
    if os.path.exists(st.session_state.ruta_estudiantes):
        return pd.read_excel(st.session_state.ruta_estudiantes)
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])

def guardar_estudiantes(df):
    df.to_excel(st.session_state.ruta_estudiantes, index=False)

def leer_asistencia():
    if os.path.exists(st.session_state.ruta_asistencia):
        return pd.read_excel(st.session_state.ruta_asistencia)
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])

def guardar_asistencia(df):
    df.to_excel(st.session_state.ruta_asistencia, index=False)

def verificar_registro_duplicado(ru, fecha):
    """
    Verifica si un estudiante ya tiene registro de asistencia en la fecha actual
    Retorna: (tiene_registro, registro_existente)
    """
    asistencia = leer_asistencia()
    if len(asistencia) > 0:
        registro_existente = asistencia[(asistencia["RU"].astype(str) == str(ru)) & 
                                       (asistencia["Fecha"].astype(str) == str(fecha))]
        
        if len(registro_existente) > 0:
            return True, registro_existente.iloc[0]
    return False, None

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE (ELEGANTE)
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    
    with st.container():
        col_form1, col_form2 = st.columns([2, 1])
        
        with col_form1:
            with st.container():
                ru = st.text_input("🔢 **RU**", placeholder="Ingrese el RU del estudiante")
                nombres = st.text_input("👤 **Nombres**", placeholder="Ingrese los nombres")
                paterno = st.text_input("👨 **Apellido paterno**", placeholder="Ingrese el apellido paterno")
                materno = st.text_input("👩 **Apellido materno**", placeholder="Ingrese el apellido materno")
        
        with col_form2:
            st.markdown("### 📋 Vista previa")
            if ru and nombres and paterno and materno:
                st.info(f"**RU:** {ru}\n\n**Estudiante:** {nombres} {paterno} {materno}")

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            if st.button("💾 GUARDAR ESTUDIANTE", use_container_width=True):
                df = leer_estudiantes()
                if ru in df["RU"].astype(str).values:
                    st.error("❌ Este RU ya existe en el sistema")
                else:
                    if not os.path.exists("qr"):
                        os.mkdir("qr")
                    ruta_qr = f"qr/{ru}.png"
                    qr = qrcode.make(ru)
                    qr.save(ruta_qr)

                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, ruta_qr]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
                    df = pd.concat([df, nuevo], ignore_index=True)
                    guardar_estudiantes(df)
                    st.success("✅ Estudiante registrado exitosamente")
                    
                    st.markdown("### 🎫 Código QR generado")
                    st.image(ruta_qr, width=300)
                    with open(ruta_qr, "rb") as file:
                        st.download_button("⬇️ DESCARGAR QR", data=file, 
                                         file_name=f"{ru}_qr.png", 
                                         mime="image/png",
                                         use_container_width=True)

# ------------------------------------------------------------
# LISTA ESTUDIANTES (ELEGANTE)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True, height=400)
        
        tab1, tab2, tab3 = st.tabs(["🔍 Ver QR", "🗑️ Eliminar", "📥 Exportar"])
        
        with tab1:
            st.markdown("### 🔍 Ver QR del estudiante")
            col_qr1, col_qr2 = st.columns([1, 1])
            
            with col_qr1:
                ru_ver = st.text_input("Ingrese RU para ver su QR", placeholder="Ej: 2024001")
            
            with col_qr2:
                if st.button("🔍 Buscar", use_container_width=True):
                    if ru_ver:
                        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
                        if len(estudiante) > 0:
                            st.markdown(
                                f"*Datos del estudiante:* **RU:** {estudiante.iloc[0]['RU']}, "
                                f"**Nombres:** {estudiante.iloc[0]['Nombres']}, "
                                f"**Apellido paterno:** {estudiante.iloc[0]['Apellido_paterno']}, "
                                f"**Apellido materno:** {estudiante.iloc[0]['Apellido_materno']}"
                            )
                            st.image(estudiante.iloc[0]["QR"], width=350)
                        else:
                            st.warning("⚠️ RU no encontrado")
        
        with tab2:
            st.markdown("### 🗑️ Eliminar estudiante")
            col_del1, col_del2 = st.columns([2, 1])
            
            with col_del1:
                eliminar = st.number_input("Índice del estudiante a eliminar", 
                                          min_value=0, 
                                          max_value=len(estudiantes)-1,
                                          step=1)
            with col_del2:
                if st.button("🗑️ ELIMINAR", use_container_width=True, type="primary"):
                    estudiante_eliminado = estudiantes.iloc[eliminar]
                    estudiantes = estudiantes.drop(eliminar)
                    guardar_estudiantes(estudiantes)
                    st.success(f"✅ Estudiante {estudiante_eliminado['Nombres']} eliminado")
        
        with tab3:
            st.markdown("### 📥 Exportar datos")
            if st.button("📥 DESCARGAR EXCEL", use_container_width=True):
                archivo_descarga = "registro_estudiantes_temp.xlsx"
                estudiantes.to_excel(archivo_descarga, index=False)
                with open(archivo_descarga, "rb") as file:
                    st.download_button("📥 Confirmar descarga", data=file, 
                                     file_name="estudiantes_exportados.xlsx",
                                     use_container_width=True)
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR (ELEGANTE) - CON VERIFICACIÓN DE DUPLICADOS
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear QR de asistencia")
    
    col_cam1, col_cam2 = st.columns([2, 1])
    
    with col_cam1:
        foto = st.camera_input("Toma una foto del código QR", label_visibility="collapsed")
    
    with col_cam2:
        st.markdown("### 📋 Instrucciones")
        st.info("""
        1. Coloca el código QR frente a la cámara
        2. Asegúrate de que esté bien iluminado
        3. La foto se tomará automáticamente
        4. Espera la confirmación del registro
        """)
        
        # Mostrar el último registro si existe
        if st.session_state.ultimo_registro:
            st.markdown("### 🕒 Último registro")
            st.success(f"**RU:** {st.session_state.ultimo_registro['RU']}\n"
                      f"**Hora:** {st.session_state.ultimo_registro['Hora']}")
    
    if foto is not None:
        with st.spinner("🔍 Procesando QR..."):
            file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            ru = data
            estudiantes = leer_estudiantes()
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]

            if len(estudiante) > 0:
                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha, hora = obtener_fecha_hora_exacta()

                # VERIFICAR SI YA TIENE REGISTRO HOY
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)

                if not tiene_registro:
                    # No tiene registro, proceder con el registro
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = leer_asistencia()
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    
                    # Guardar en session state
                    st.session_state.ultimo_registro = {
                        "RU": ru,
                        "Nombres": nombres,
                        "Hora": hora,
                        "Fecha": fecha
                    }
                    
                    st.balloons()
                    st.success(f"""
                    ### ✅ Asistencia registrada
                    **Estudiante:** {nombres} {paterno} {materno}
                    **RU:** {ru}
                    **Hora:** {hora}
                    **Fecha:** {fecha}
                    """)
                else:
                    # YA TIENE REGISTRO - Mostrar advertencia
                    st.markdown("""
                    <div class="duplicate-card">
                        <h4>⚠️ REGISTRO DUPLICADO DETECTADO</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_dup1, col_dup2 = st.columns(2)
                    with col_dup1:
                        st.error(f"""
                        ### ❌ No se puede registrar
                        **Estudiante:** {nombres} {paterno} {materno}
                        **RU:** {ru}
                        **Motivo:** Ya tiene un registro hoy
                        """)
                    
                    with col_dup2:
                        st.warning(f"""
                        ### 📋 Registro existente
                        **Hora:** {registro_existente['Hora']}
                        **Estado:** {registro_existente['Estado']}
                        **Fecha:** {registro_existente['Fecha']}
                        
                        *Solo se permite un registro por día*
                        """)
            else:
                st.error("❌ Estudiante no encontrado en la base de datos")
        else:
            st.error("❌ No se pudo detectar un código QR válido")

# ------------------------------------------------------------
# REGISTRO MANUAL (ELEGANTE) - CON VERIFICACIÓN DE DUPLICADOS
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    st.subheader("✍️ Registrar asistencia manual")
    
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"] + " " + estudiantes["Apellido_paterno"]
        
        col_manual1, col_manual2 = st.columns([2, 1])
        
        with col_manual1:
            with st.container():
                seleccionado = st.selectbox("👤 **Seleccionar estudiante**", 
                                           estudiantes["nombre_completo"],
                                           help="Busca y selecciona un estudiante de la lista")
                ru = seleccionado.split(" - ")[0]
                
                estado = st.selectbox("📌 **Estado de asistencia**", 
                                     ["Presente", "Tarde", "Permiso", "Ausente"],
                                     help="Selecciona el estado correspondiente")
        
        with col_manual2:
            st.markdown("### 📝 Resumen")
            estudiante_sel = estudiantes[estudiantes["RU"].astype(str) == ru].iloc[0]
            st.info(f"""
            **RU:** {ru}
            **Nombres:** {estudiante_sel['Nombres']}
            **Apellidos:** {estudiante_sel['Apellido_paterno']} {estudiante_sel['Apellido_materno']}
            """)
            
            fecha, hora = obtener_fecha_hora_exacta()
            
            # VERIFICAR SI YA TIENE REGISTRO HOY
            tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
            
            if tiene_registro:
                # Mostrar advertencia de registro duplicado
                st.markdown("""
                <div class="duplicate-card">
                    <h4>⚠️ REGISTRO DUPLICADO DETECTADO</h4>
                </div>
                """, unsafe_allow_html=True)
                
                st.warning(f"""
                **Este estudiante ya tiene un registro hoy:**
                - **Hora:** {registro_existente['Hora']}
                - **Estado:** {registro_existente['Estado']}
                
                *Solo se permite un registro por día*
                """)
                
                # Botón deshabilitado si ya tiene registro
                if st.button("✅ REGISTRAR ASISTENCIA", use_container_width=True, disabled=True):
                    pass
                st.caption("⚠️ Botón deshabilitado - Registro duplicado")
            else:
                # No tiene registro, botón habilitado
                if st.button("✅ REGISTRAR ASISTENCIA", use_container_width=True):
                    nombres = estudiante_sel["Nombres"]
                    paterno = estudiante_sel["Apellido_paterno"]
                    materno = estudiante_sel["Apellido_materno"]

                    asistencia = leer_asistencia()
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    
                    # Guardar en session state
                    st.session_state.ultimo_registro = {
                        "RU": ru,
                        "Nombres": nombres,
                        "Hora": hora,
                        "Fecha": fecha
                    }
                    
                    st.balloons()
                    st.success(f"✅ Asistencia registrada correctamente a las {hora}")
    else:
        st.warning("⚠️ No hay estudiantes registrados. Primero debes registrar estudiantes.")

# ------------------------------------------------------------
# VER ASISTENCIA (ELEGANTE) - CON INDICADORES DE DUPLICADOS
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    
    asistencia = leer_asistencia()
    
    if len(asistencia) > 0:
        # Filtros
        st.markdown("### 🔍 Filtrar registros")
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            fechas_unicas = sorted(asistencia["Fecha"].astype(str).unique(), reverse=True)
            fecha_seleccionada = st.selectbox("📅 Filtrar por fecha", ["Todas"] + list(fechas_unicas))
        
        with col_filtro2:
            estados_unicos = asistencia["Estado"].unique()
            estado_seleccionado = st.selectbox("📌 Filtrar por estado", ["Todos"] + list(estados_unicos))
        
        with col_filtro3:
            ru_search = st.text_input("🔢 Buscar por RU", placeholder="Ingrese RU")
        
        # Aplicar filtros
        datos_filtrados = asistencia.copy()
        if fecha_seleccionada != "Todas":
            datos_filtrados = datos_filtrados[datos_filtrados["Fecha"].astype(str) == fecha_seleccionada]
        if estado_seleccionado != "Todos":
            datos_filtrados = datos_filtrados[datos_filtrados["Estado"] == estado_seleccionado]
        if ru_search:
            datos_filtrados = datos_filtrados[datos_filtrados["RU"].astype(str).str.contains(ru_search, case=False)]
        
        st.dataframe(datos_filtrados, use_container_width=True, height=400)
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas")
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            total_hoy = len(asistencia[asistencia["Fecha"].astype(str) == str(datetime.now(ZONA_HORARIA).date())])
            st.metric("📅 Registros hoy", total_hoy)
        
        with col_stats2:
            presentes_hoy = len(asistencia[(asistencia["Fecha"].astype(str) == str(datetime.now(ZONA_HORARIA).date())) & 
                                          (asistencia["Estado"] == "Presente")])
            st.metric("✅ Presentes hoy", presentes_hoy)
        
        with col_stats3:
            tardes_hoy = len(asistencia[(asistencia["Fecha"].astype(str) == str(datetime.now(ZONA_HORARIA).date())) & 
                                       (asistencia["Estado"] == "Tarde")])
            st.metric("⏰ Tardes hoy", tardes_hoy)
        
        with col_stats4:
            total_registros = len(asistencia)
            st.metric("📊 Total registros", total_registros)
        
        # Verificar duplicados por día (control de calidad)
        st.markdown("### 🔍 Verificación de integridad")
        
        # Agrupar por RU y Fecha para encontrar posibles duplicados
        duplicados = asistencia.groupby(['RU', 'Fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        
        if len(duplicados) > 0:
            st.warning(f"⚠️ Se encontraron {len(duplicados)} casos de múltiples registros para un mismo estudiante en el mismo día")
            
            # Mostrar los duplicados
            registros_duplicados = []
            for _, row in duplicados.iterrows():
                ru_dup = row['RU']
                fecha_dup = row['Fecha']
                registros = asistencia[(asistencia['RU'].astype(str) == str(ru_dup)) & 
                                      (asistencia['Fecha'].astype(str) == str(fecha_dup))]
                registros_duplicados.append(registros)
            
            if registros_duplicados:
                df_duplicados = pd.concat(registros_duplicados)
                st.dataframe(df_duplicados, use_container_width=True)
                
                if st.button("🧹 LIMPIAR DUPLICADOS (Mantener solo el primer registro)", use_container_width=True):
                    # Mantener solo el primer registro para cada combinación RU-Fecha
                    asistencia_limpia = asistencia.drop_duplicates(subset=['RU', 'Fecha'], keep='first')
                    guardar_asistencia(asistencia_limpia)
                    st.success("✅ Duplicados eliminados. Se mantuvo el primer registro de cada día.")
                    st.rerun()
        else:
            st.success("✅ No se encontraron registros duplicados. La base de datos está integra.")
        
        # Editar y eliminar
        tab_edit, tab_delete, tab_export = st.tabs(["✏️ Editar estado", "🗑️ Eliminar registro", "📥 Exportar"])
        
        with tab_edit:
            st.markdown("### ✏️ Editar estado de registro")
            col_edit1, col_edit2, col_edit3 = st.columns([2, 2, 1])
            
            with col_edit1:
                indice = st.number_input("Índice del registro", 
                                        min_value=0, 
                                        max_value=len(asistencia)-1,
                                        step=1,
                                        key="edit_idx")
            with col_edit2:
                nuevo_estado = st.selectbox("Nuevo estado", 
                                           ["Presente", "Tarde", "Permiso", "Ausente"],
                                           key="edit_estado")
            with col_edit3:
                if st.button("🔄 ACTUALIZAR", use_container_width=True):
                    registro = asistencia.loc[indice]
                    asistencia.loc[indice, "Estado"] = nuevo_estado
                    guardar_asistencia(asistencia)
                    st.success(f"✅ Estado actualizado para {registro['Nombres']}")
        
        with tab_delete:
            st.markdown("### 🗑️ Eliminar registro")
            col_del1, col_del2 = st.columns([3, 1])
            
            with col_del1:
                eliminar = st.number_input("Índice del registro a eliminar", 
                                          min_value=0, 
                                          max_value=len(asistencia)-1,
                                          step=1,
                                          key="del_idx")
            with col_del2:
                if st.button("🗑️ ELIMINAR", use_container_width=True, type="primary"):
                    registro_eliminado = asistencia.loc[eliminar]
                    asistencia = asistencia.drop(eliminar)
                    guardar_asistencia(asistencia)
                    st.success(f"✅ Registro de {registro_eliminado['Nombres']} eliminado")
        
        with tab_export:
            st.markdown("### 📥 Exportar registros")
            
            hoy = str(datetime.now(ZONA_HORARIA).date())
            asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                if len(asistencia_hoy) > 0:
                    archivo_descarga = f"asistencia_{hoy}.xlsx"
                    asistencia_hoy.to_excel(archivo_descarga, index=False)
                    with open(archivo_descarga, "rb") as file:
                        st.download_button("📥 DESCARGAR REGISTRO DEL DÍA", 
                                         data=file, 
                                         file_name=archivo_descarga,
                                         use_container_width=True)
            
            with col_exp2:
                if len(asistencia) > 0:
                    archivo_completo = "asistencia_completa.xlsx"
                    asistencia.to_excel(archivo_completo, index=False)
                    with open(archivo_completo, "rb") as file:
                        st.download_button("📥 DESCARGAR REGISTRO COMPLETO", 
                                         data=file, 
                                         file_name=archivo_completo,
                                         use_container_width=True)
    else:
        st.info("📭 No hay registros de asistencia")
