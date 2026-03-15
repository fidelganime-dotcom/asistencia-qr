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
# ESTILOS CSS (MODO OSCURO + ANIMACIONES + MENÚ HORIZONTAL)
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
    }

    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }

    /* Menú horizontal con botones de colores */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 20px;
        background-color: var(--bg-card);
        padding: 15px 20px;
        border-radius: 50px;
        border: 1px solid var(--border);
        margin-bottom: 30px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    div.row-widget.stRadio > div label {
        color: var(--text-secondary) !important;
        font-size: 1.1rem;
        font-weight: 500;
        padding: 8px 20px;
        border-radius: 30px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        background-color: rgba(124, 58, 237, 0.1);
    }
    div.row-widget.stRadio > div label:hover {
        filter: brightness(1.2);
        border-color: currentColor;
    }
    /* Colores específicos para cada opción (inactivo) */
    div.row-widget.stRadio > div label:nth-child(1) {
        background-color: rgba(59, 130, 246, 0.2);
        border-color: #3b82f6;
    }
    div.row-widget.stRadio > div label:nth-child(2) {
        background-color: rgba(16, 185, 129, 0.2);
        border-color: #10b981;
    }
    div.row-widget.stRadio > div label:nth-child(3) {
        background-color: rgba(245, 158, 11, 0.2);
        border-color: #f59e0b;
    }
    div.row-widget.stRadio > div label:nth-child(4) {
        background-color: rgba(239, 68, 68, 0.2);
        border-color: #ef4444;
    }
    div.row-widget.stRadio > div label:nth-child(5) {
        background-color: rgba(139, 92, 246, 0.2);
        border-color: #8b5cf6;
    }
    /* Colores para la opción activa (checked) */
    div.row-widget.stRadio > div label:nth-child(1) input:checked + div {
        background: linear-gradient(135deg, #3b82f6, #60a5fa) !important;
        color: white !important;
    }
    div.row-widget.stRadio > div label:nth-child(2) input:checked + div {
        background: linear-gradient(135deg, #10b981, #34d399) !important;
        color: white !important;
    }
    div.row-widget.stRadio > div label:nth-child(3) input:checked + div {
        background: linear-gradient(135deg, #f59e0b, #fbbf24) !important;
        color: white !important;
    }
    div.row-widget.stRadio > div label:nth-child(4) input:checked + div {
        background: linear-gradient(135deg, #ef4444, #f87171) !important;
        color: white !important;
    }
    div.row-widget.stRadio > div label:nth-child(5) input:checked + div {
        background: linear-gradient(135deg, #8b5cf6, #a78bfa) !important;
        color: white !important;
    }

    /* Inputs, selects, botones, tablas */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
    }

    .stButton button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(124, 58, 237, 0.3);
        filter: brightness(1.1);
    }
    
    /* Botón deshabilitado */
    .stButton button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

    .stDataFrame {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border);
        overflow: hidden;
    }
    .stDataFrame table {
        color: var(--text-primary) !important;
    }
    .stDataFrame th {
        background-color: var(--bg-sidebar) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    .stDataFrame td {
        background-color: var(--bg-card) !important;
        color: var(--text-secondary) !important;
    }

    .stImage img {
        border-radius: 16px;
        border: 3px solid var(--accent);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    .stImage img:hover {
        transform: scale(1.02);
    }

    div.stMarkdown, div.stAlert {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    .stAlert {
        border-left: 4px solid;
        animation: slideIn 0.3s ease;
    }
    .stAlert.success { border-left-color: var(--success); }
    .stAlert.warning { border-left-color: var(--warning); }
    .stAlert.error { border-left-color: var(--error); }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-card);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--accent);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-light);
    }

    /* Cámara - TAMAÑO GRANDE Y NOTORIO (COMO EN EL ORIGINAL) */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 75vh !important;
        object-fit: cover;
        border-radius: 16px;
        border: 2px solid var(--accent);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stCameraInput"] {
        width: 100% !important;
    }

    /* Estilo para los uploaders */
    .uploader-box {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border);
        margin-bottom: 1rem;
    }
    
    /* Tarjeta de advertencia de duplicado */
    .duplicate-card {
        background-color: rgba(249, 115, 22, 0.1);
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
# TÍTULO Y MENÚ HORIZONTAL (CON BOTONES DE COLORES)
# ------------------------------------------------------------
st.title("📷 Sistema de Asistencia con QR")

opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia"
]

menu = st.radio(
    "",
    opciones_menu,
    horizontal=True,
    label_visibility="collapsed",
    key="menu_radio"
)

st.session_state.menu_actual = menu

# ------------------------------------------------------------
# SIDEBAR: CARGAR ARCHIVOS EXCEL
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Cargar archivos Excel")
    st.markdown("Sube tus propios archivos para trabajar con ellos. Si no subes ninguno, se usarán los archivos por defecto (`estudiantes.xlsx` y `asistencia.xlsx`).")

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    archivo_est = st.file_uploader("📘 Estudiantes", type=["xlsx"], key="upload_est")
    if archivo_est is not None:
        ruta_destino = os.path.join("uploads", archivo_est.name)
        with open(ruta_destino, "wb") as f:
            f.write(archivo_est.getbuffer())
        st.session_state.ruta_estudiantes = ruta_destino
        st.session_state.archivo_estudiantes_subido = archivo_est.name
        st.success(f"✅ Archivo de estudiantes cargado: {archivo_est.name}")

    archivo_asis = st.file_uploader("📗 Asistencia", type=["xlsx"], key="upload_asis")
    if archivo_asis is not None:
        ruta_destino = os.path.join("uploads", archivo_asis.name)
        with open(ruta_destino, "wb") as f:
            f.write(archivo_asis.getbuffer())
        st.session_state.ruta_asistencia = ruta_destino
        st.session_state.archivo_asistencia_subido = archivo_asis.name
        st.success(f"✅ Archivo de asistencia cargado: {archivo_asis.name}")

    st.markdown("---")
    st.markdown("### 📁 Archivos en uso:")
    st.info(f"**Estudiantes:** `{st.session_state.ruta_estudiantes}`")
    st.info(f"**Asistencia:** `{st.session_state.ruta_asistencia}`")

    st.markdown("---")
    st.markdown("### ⬇️ Descargar archivos actualizados")
    if os.path.exists(st.session_state.ruta_estudiantes):
        with open(st.session_state.ruta_estudiantes, "rb") as f:
            st.download_button("📥 Descargar estudiantes", data=f, file_name=os.path.basename(st.session_state.ruta_estudiantes))
    if os.path.exists(st.session_state.ruta_asistencia):
        with open(st.session_state.ruta_asistencia, "rb") as f:
            st.download_button("📥 Descargar asistencia", data=f, file_name=os.path.basename(st.session_state.ruta_asistencia))

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
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    with st.container():
        ru = st.text_input("🔢 RU")
        nombres = st.text_input("👤 Nombres")
        paterno = st.text_input("👨 Apellido paterno")
        materno = st.text_input("👩 Apellido materno")

        if st.button("💾 Guardar estudiante"):
            df = leer_estudiantes()
            if ru in df["RU"].astype(str).values:
                st.error("❌ Este RU ya existe")
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
                st.image(ruta_qr, width=350)
                with open(ruta_qr, "rb") as file:
                    st.download_button("⬇️ Descargar QR", data=file, file_name=f"{ru}_qr.png", mime="image/png")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    st.dataframe(estudiantes, use_container_width=True)

    st.subheader("🔍 Ver información y QR del estudiante")
    ru_ver = st.text_input("Ingrese RU para ver información y QR")
    if ru_ver != "":
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

    st.subheader("🗑️ Eliminar estudiante")
    if len(estudiantes) > 0:
        eliminar = st.number_input("Índice a eliminar", min_value=0, max_value=len(estudiantes)-1, key="eliminar_est")
        if st.button("🗑️ Eliminar"):
            estudiantes = estudiantes.drop(eliminar)
            guardar_estudiantes(estudiantes)
            st.success("✅ Estudiante eliminado")

    st.subheader("⬇️ Descargar Excel estudiantes")
    if len(estudiantes) > 0:
        archivo_descarga = "registro_estudiantes_temp.xlsx"
        estudiantes.to_excel(archivo_descarga, index=False)
        with open(archivo_descarga, "rb") as file:
            st.download_button("📥 Descargar Excel", data=file, file_name="estudiantes_exportados.xlsx")

# ------------------------------------------------------------
# ESCANEAR QR - EXACTAMENTE COMO EN EL ORIGINAL (GRANDE Y NOTORIO)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear QR")
    foto = st.camera_input("Toma una foto del código QR")
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
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha, hora = obtener_fecha_hora_exacta()

                # VERIFICAR SI YA TIENE REGISTRO HOY
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)

                if not tiene_registro:
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
                    
                    st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} ya registró asistencia hoy a las {registro_existente['Hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó QR")

# ------------------------------------------------------------
# REGISTRO MANUAL - CON VERIFICACIÓN DE DUPLICADOS
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    st.subheader("✍️ Registrar asistencia manual")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"] + " " + estudiantes["Apellido_paterno"]
        seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
        ru = seleccionado.split(" - ")[0]
        estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])

        fecha, hora = obtener_fecha_hora_exacta()
        
        # VERIFICAR SI YA TIENE REGISTRO HOY
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        
        if tiene_registro:
            st.warning(f"⚠️ Este estudiante ya registró hoy a las {registro_existente['Hora']} (Estado: {registro_existente['Estado']})")
            if st.button("✅ Registrar asistencia", disabled=True):
                pass
            st.caption("Botón deshabilitado - Registro duplicado")
        else:
            if st.button("✅ Registrar asistencia"):
                estudiante = estudiantes[estudiantes["RU"].astype(str) == ru].iloc[0]
                nombres = estudiante["Nombres"]
                paterno = estudiante["Apellido_paterno"]
                materno = estudiante["Apellido_materno"]

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
                
                st.success(f"✅ Asistencia registrada a las {hora}")
    else:
        st.warning("⚠️ No hay estudiantes registrados")

# ------------------------------------------------------------
# VER ASISTENCIA - CON VERIFICACIÓN DE INTEGRIDAD
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    asistencia = leer_asistencia()
    
    if len(asistencia) > 0:
        st.dataframe(asistencia, use_container_width=True)
        
        # Verificación de integridad
        st.subheader("🔍 Verificación de integridad")
        duplicados = asistencia.groupby(['RU', 'Fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        
        if len(duplicados) > 0:
            st.warning(f"⚠️ Se encontraron {len(duplicados)} casos de registros duplicados")
            if st.button("🧹 Limpiar duplicados (mantener primer registro)"):
                asistencia_limpia = asistencia.drop_duplicates(subset=['RU', 'Fecha'], keep='first')
                guardar_asistencia(asistencia_limpia)
                st.success("✅ Duplicados eliminados")
                st.rerun()
        else:
            st.success("✅ No hay registros duplicados")

        st.subheader("✏️ Editar estado")
        if len(asistencia) > 0:
            indice = st.number_input("Índice registro", min_value=0, max_value=len(asistencia)-1)
            nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"])
            if st.button("🔄 Actualizar estado"):
                asistencia.loc[indice, "Estado"] = nuevo_estado
                guardar_asistencia(asistencia)
                st.success("✅ Estado actualizado")

        st.subheader("🗑️ Eliminar registro")
        if len(asistencia) > 0:
            eliminar = st.number_input("Índice eliminar", min_value=0, max_value=len(asistencia)-1, key="elim")
            if st.button("🗑️ Eliminar registro"):
                asistencia = asistencia.drop(eliminar)
                guardar_asistencia(asistencia)
                st.success("✅ Registro eliminado")

        st.subheader("⬇️ Descargar asistencia del día")
        hoy = str(datetime.now(ZONA_HORARIA).date())
        asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga)
        else:
            st.info("No hay registros para hoy.")
    else:
        st.info("📭 No hay registros de asistencia")
