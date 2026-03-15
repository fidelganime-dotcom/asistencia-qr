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
    if len(asistencia) > 0:
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
# ESTILOS CSS PARA MENÚ COMPACTO MÓVIL
# ------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --bg-dark: #0e1117;
        --bg-card: #1e2128;
        --bg-sidebar: #1a1d24;
        --text-primary: #fafafa;
        --text-secondary: #b0b3b8;
        --accent: #7c3aed;
        --accent-light: #9f7aea;
        --border: #2d3138;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --duplicate: #f97316;
        --info: #3b82f6;
    }

    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }

    /* CONTENEDOR DEL MENÚ - UNA SOLA LÍNEA */
    .menu-container-mobile {
        display: flex;
        justify-content: space-between;
        gap: 5px;
        background: linear-gradient(145deg, #1a1d24, #15181f);
        padding: 8px 10px;
        border-radius: 50px;
        border: 1px solid rgba(124, 58, 237, 0.3);
        margin: 10px 0 20px 0;
        box-shadow: 0 5px 15px -3px rgba(0, 0, 0, 0.5);
        overflow-x: auto;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none; /* Firefox */
    }
    
    .menu-container-mobile::-webkit-scrollbar {
        display: none; /* Chrome, Safari, Edge */
    }
    
    /* BOTONES DEL MENÚ - COMPACTOS */
    .menu-button-mobile {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid transparent;
        color: var(--text-secondary);
        padding: 8px 12px;
        border-radius: 40px;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid;
        min-width: auto;
        text-align: center;
        flex: 1;
        white-space: nowrap;
    }
    
    /* Colores específicos para cada botón (inactivo) */
    .menu-button-mobile:nth-child(1) {
        background: linear-gradient(145deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
        border-color: #3b82f680;
    }
    .menu-button-mobile:nth-child(2) {
        background: linear-gradient(145deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
        border-color: #10b98180;
    }
    .menu-button-mobile:nth-child(3) {
        background: linear-gradient(145deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
        border-color: #f59e0b80;
    }
    .menu-button-mobile:nth-child(4) {
        background: linear-gradient(145deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
        border-color: #ef444480;
    }
    .menu-button-mobile:nth-child(5) {
        background: linear-gradient(145deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
        border-color: #8b5cf680;
    }
    
    /* Estilo para botón activo - color sólido */
    .menu-button-mobile.active:nth-child(1) {
        background: #3b82f6 !important;
        color: white !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 2px 8px #3b82f6 !important;
    }
    .menu-button-mobile.active:nth-child(2) {
        background: #10b981 !important;
        color: white !important;
        border-color: #10b981 !important;
        box-shadow: 0 2px 8px #10b981 !important;
    }
    .menu-button-mobile.active:nth-child(3) {
        background: #f59e0b !important;
        color: white !important;
        border-color: #f59e0b !important;
        box-shadow: 0 2px 8px #f59e0b !important;
    }
    .menu-button-mobile.active:nth-child(4) {
        background: #ef4444 !important;
        color: white !important;
        border-color: #ef4444 !important;
        box-shadow: 0 2px 8px #ef4444 !important;
    }
    .menu-button-mobile.active:nth-child(5) {
        background: #8b5cf6 !important;
        color: white !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 2px 8px #8b5cf6 !important;
    }
    
    /* Ocultar los botones reales de Streamlit */
    .stButton button {
        display: none;
    }
    
    /* Estilos para inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: linear-gradient(145deg, #1e2128, #1a1d24) !important;
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        font-size: 0.95rem !important;
    }
    
    /* Tablas responsivas */
    .stDataFrame {
        background: linear-gradient(145deg, #1e2128, #1a1d24);
        border-radius: 16px;
        padding: 0.8rem;
        border: 1px solid rgba(124, 58, 237, 0.2);
        overflow-x: auto;
    }
    
    /* Cámara para móvil */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
        max-height: 60vh;
        border-radius: 16px;
        border: 2px solid var(--accent);
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stAlert {
        animation: fadeIn 0.3s ease-out;
        border-radius: 12px;
        background: linear-gradient(145deg, #1e2128, #1a1d24);
    }
    
    /* Ajustes para móvil */
    @media (max-width: 768px) {
        .row-widget {
            margin-bottom: 10px !important;
        }
        
        .stButton button {
            font-size: 0.9rem !important;
            padding: 0.4rem 1rem !important;
        }
        
        h1 {
            font-size: 1.8rem !important;
        }
        
        h2, h3 {
            font-size: 1.3rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# INICIALIZAR SESSION STATE
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
    st.session_state.menu_actual = "Registrar"
if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None

# ------------------------------------------------------------
# FUNCIONES PARA CAMBIAR DE MENÚ
# ------------------------------------------------------------
def set_menu(menu_option):
    st.session_state.menu_actual = menu_option
    st.rerun()

# ------------------------------------------------------------
# TÍTULO Y MENÚ COMPACTO PARA MÓVIL
# ------------------------------------------------------------
st.title("📷 Asistencia QR")
st.markdown('<p style="color: #b0b3b8; margin-top: -10px; margin-bottom: 15px; font-size: 0.9rem;">Sistema de asistencia</p>', unsafe_allow_html=True)

# Crear menú compacto con JavaScript para cambio de color
menu_options = [
    {"id": "Registrar", "icon": "📝", "text": "Registrar"},
    {"id": "Lista", "icon": "📋", "text": "Lista"},
    {"id": "Escanear", "icon": "📸", "text": "Escanear"},
    {"id": "Manual", "icon": "✍️", "text": "Manual"},
    {"id": "Ver", "icon": "📊", "text": "Ver"}
]

# Contenedor del menú
st.markdown('<div class="menu-container-mobile" id="menu-mobile">', unsafe_allow_html=True)

# Crear columnas para los botones
cols = st.columns(5)

for i, (col, option) in enumerate(zip(cols, menu_options)):
    with col:
        # Determinar si está activo
        is_active = st.session_state.menu_actual == option["id"]
        active_class = "active" if is_active else ""
        
        # Botón visual con HTML
        st.markdown(f'''
            <div class="menu-button-mobile {active_class}" 
                 onclick="document.querySelectorAll('.menu-button-mobile').forEach(el => el.classList.remove('active')); 
                          this.classList.add('active');
                          document.getElementById('menu_{option["id"]}').click();">
                {option["icon"]} {option["text"]}
            </div>
        ''', unsafe_allow_html=True)
        
        # Botón oculto de Streamlit para funcionalidad
        if st.button(option["text"], key=f"menu_{option['id']}", help=f"Ir a {option['text']}"):
            set_menu(option["id"])

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Archivos")
    
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    archivo_est = st.file_uploader("📘 Estudiantes", type=["xlsx"], key="upload_est", label_visibility="collapsed")
    if archivo_est is not None:
        ruta_destino = os.path.join("uploads", archivo_est.name)
        with open(ruta_destino, "wb") as f:
            f.write(archivo_est.getbuffer())
        st.session_state.ruta_estudiantes = ruta_destino
        st.session_state.archivo_estudiantes_subido = archivo_est.name
        st.success(f"✅ {archivo_est.name}")

    archivo_asis = st.file_uploader("📗 Asistencia", type=["xlsx"], key="upload_asis", label_visibility="collapsed")
    if archivo_asis is not None:
        ruta_destino = os.path.join("uploads", archivo_asis.name)
        with open(ruta_destino, "wb") as f:
            f.write(archivo_asis.getbuffer())
        st.session_state.ruta_asistencia = ruta_destino
        st.session_state.archivo_asistencia_subido = archivo_asis.name
        st.success(f"✅ {archivo_asis.name}")

    st.markdown("---")
    if os.path.exists(st.session_state.ruta_estudiantes):
        with open(st.session_state.ruta_estudiantes, "rb") as f:
            st.download_button("📥 Estudiantes", data=f, file_name=os.path.basename(st.session_state.ruta_estudiantes), use_container_width=True)
    if os.path.exists(st.session_state.ruta_asistencia):
        with open(st.session_state.ruta_asistencia, "rb") as f:
            st.download_button("📥 Asistencia", data=f, file_name=os.path.basename(st.session_state.ruta_asistencia), use_container_width=True)

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

# ------------------------------------------------------------
# CONTENIDO SEGÚN EL MENÚ SELECCIONADO
# ------------------------------------------------------------

# REGISTRAR ESTUDIANTE
if st.session_state.menu_actual == "Registrar":
    st.subheader("📝 Nuevo estudiante")
    
    ru = st.text_input("RU", placeholder="Número de RU", label_visibility="collapsed")
    nombres = st.text_input("Nombres", placeholder="Nombres completos", label_visibility="collapsed")
    paterno = st.text_input("Ap. Paterno", placeholder="Apellido paterno", label_visibility="collapsed")
    materno = st.text_input("Ap. Materno", placeholder="Apellido materno", label_visibility="collapsed")

    if st.button("💾 Guardar", use_container_width=True):
        df = leer_estudiantes()
        if ru in df["RU"].astype(str).values:
            st.error("❌ RU ya existe")
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
            st.success("✅ Estudiante registrado")
            st.image(ruta_qr, width=250)
            with open(ruta_qr, "rb") as file:
                st.download_button("⬇️ QR", data=file, file_name=f"{ru}_qr.png", use_container_width=True)

# LISTA ESTUDIANTES
elif st.session_state.menu_actual == "Lista":
    st.subheader("📋 Estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Buscar")
        
        ru_ver = st.text_input("RU", placeholder="Ingrese RU", key="buscar_ru", label_visibility="collapsed")
        if st.button("🔍 Buscar", key="buscar_btn", use_container_width=True) and ru_ver:
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                st.markdown(f"**{estudiante.iloc[0]['Nombres']} {estudiante.iloc[0]['Apellido_paterno']}**")
                st.image(estudiante.iloc[0]["QR"], width=250)
            else:
                st.warning("❌ No encontrado")
    else:
        st.info("📭 No hay estudiantes")

# ESCANEAR QR
elif st.session_state.menu_actual == "Escanear":
    st.subheader("📸 Escanear QR")
    
    foto = st.camera_input("", label_visibility="collapsed")
    if foto is not None:
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
                fecha, hora = obtener_fecha_hora_exacta()

                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)

                if not tiene_registro:
                    nuevo = pd.DataFrame([[ru, nombres, paterno, "", fecha, hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = leer_asistencia()
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    st.success(f"✅ {nombres} - {hora}")
                else:
                    st.warning(f"⚠️ Ya registró a las {registro_existente['Hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó QR")

# REGISTRO MANUAL
elif st.session_state.menu_actual == "Manual":
    st.subheader("✍️ Registrar manual")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"]
        seleccionado = st.selectbox("", estudiantes["nombre_completo"], label_visibility="collapsed")
        ru = seleccionado.split(" - ")[0]
        estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"], label_visibility="collapsed")

        fecha, hora = obtener_fecha_hora_exacta()
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        
        if tiene_registro:
            st.warning(f"⚠️ Ya registró a las {registro_existente['Hora']}")
            st.button("✅ Registrar", disabled=True, use_container_width=True)
        else:
            if st.button("✅ Registrar", use_container_width=True):
                estudiante = estudiantes[estudiantes["RU"].astype(str) == ru].iloc[0]
                nombres = estudiante["Nombres"]
                paterno = estudiante["Apellido_paterno"]
                materno = estudiante["Apellido_materno"]

                asistencia = leer_asistencia()
                nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                                      columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                guardar_asistencia(asistencia)
                st.success(f"✅ Registrado a las {hora}")
    else:
        st.warning("⚠️ No hay estudiantes")

# VER ASISTENCIA
elif st.session_state.menu_actual == "Ver":
    st.subheader("📊 Asistencia")
    asistencia = leer_asistencia()
    
    if len(asistencia) > 0:
        st.dataframe(asistencia, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⬇️ Descargar hoy")
        hoy = str(datetime.now(ZONA_HORARIA).date())
        asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Excel del día", data=file, file_name=archivo_descarga, use_container_width=True)
    else: 
        st.info("📭 No hay registros")
        
