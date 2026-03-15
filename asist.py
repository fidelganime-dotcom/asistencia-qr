import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz

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
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILOS CSS (MODO OSCURO + ANIMACIONES + BOTONES DE MENÚ ELEGANTES)
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
    }

    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }

    /* Estilos para los botones del menú (dentro de columnas) */
    div[data-testid="column"] .stButton button {
        background: linear-gradient(135deg, #2a2f3a 0%, #1e2128 100%);
        border: 1px solid #3d4350 !important;
        border-radius: 50px !important;
        padding: 12px 20px !important;
        color: #b0b3b8 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
        width: 100%;
        border: none;
        margin: 0;
    }
    div[data-testid="column"] .stButton button:hover {
        transform: translateY(-2px) !important;
        background: linear-gradient(135deg, #353b48 0%, #2a2f3a 100%) !important;
        border-color: var(--accent) !important;
        color: white !important;
        box-shadow: 0 8px 15px rgba(124, 58, 237, 0.3) !important;
    }
    div[data-testid="column"] .stButton button:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px var(--accent) !important;
    }

    /* Estilo para otros botones (guardar, descargar, etc.) */
    .stButton button:not(div[data-testid="column"] .stButton button) {
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
    .stButton button:hover:not(div[data-testid="column"] .stButton button) {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(124, 58, 237, 0.3);
        filter: brightness(1.1);
    }

    /* Inputs, selects, etc. */
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

    /* Editor de datos */
    .stDataFrame, div[data-testid="stDataEditor"] {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid var(--border);
        overflow: hidden;
    }
    .stDataFrame table, .stDataEditor table {
        color: var(--text-primary) !important;
    }
    .stDataFrame th, .stDataEditor th {
        background-color: var(--bg-sidebar) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    .stDataFrame td, .stDataEditor td {
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

    /* Cámara */
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

opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia"
]
if "menu_opcion" not in st.session_state:
    st.session_state.menu_opcion = opciones_menu[0]

# ------------------------------------------------------------
# TÍTULO
# ------------------------------------------------------------
st.title("📷 Sistema de Asistencia con QR")

# ------------------------------------------------------------
# MENÚ DE BOTONES HORIZONTALES (ELEGANTES)
# ------------------------------------------------------------
cols = st.columns(len(opciones_menu))
for i, opcion in enumerate(opciones_menu):
    with cols[i]:
        if st.button(opcion, key=f"menu_{i}", use_container_width=True):
            st.session_state.menu_opcion = opcion
            st.rerun()

menu = st.session_state.menu_opcion

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
# FUNCIONES AUXILIARES PARA LEER/GUARDAR DATAFRAMES (CON GESTIÓN DE TIPOS)
# ------------------------------------------------------------
def leer_estudiantes():
    if os.path.exists(st.session_state.ruta_estudiantes):
        df = pd.read_excel(st.session_state.ruta_estudiantes)
    else:
        df = pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
    
    # Asegurar tipos de datos para evitar errores en data_editor
    # Convertir todas las columnas a string para simplificar (excepto si RU es numérico, pero lo dejamos string)
    df = df.astype(str)
    # Reemplazar 'nan' por cadena vacía
    df = df.replace('nan', '')
    return df

def guardar_estudiantes(df):
    # Antes de guardar, restaurar los tipos originales (opcional)
    # Pero el Excel guardará como texto, lo cual es aceptable
    df.to_excel(st.session_state.ruta_estudiantes, index=False)

def leer_asistencia():
    if os.path.exists(st.session_state.ruta_asistencia):
        df = pd.read_excel(st.session_state.ruta_asistencia)
    else:
        df = pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
    
    # Asegurar tipos
    df = df.astype(str)
    df = df.replace('nan', '')
    return df

def guardar_asistencia(df):
    df.to_excel(st.session_state.ruta_asistencia, index=False)

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if menu == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    with st.container():
        ru = st.text_input("🔢 RU")
        nombres = st.text_input("👤 Nombres")
        paterno = st.text_input("👨 Apellido paterno")
        materno = st.text_input("👩 Apellido materno")

        if st.button("💾 Guardar estudiante"):
            df = leer_estudiantes()
            if ru in df["RU"].values:
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
# LISTA ESTUDIANTES (CON EDITOR)
# ------------------------------------------------------------
elif menu == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes (editable)")

    estudiantes = leer_estudiantes()

    # Configurar columnas: deshabilitar edición en QR
    column_config = {
        "RU": st.column_config.TextColumn("RU", required=True),
        "Nombres": st.column_config.TextColumn("Nombres", required=True),
        "Apellido_paterno": st.column_config.TextColumn("Apellido paterno", required=True),
        "Apellido_materno": st.column_config.TextColumn("Apellido materno", required=True),
        "QR": st.column_config.TextColumn("QR", disabled=True, help="Ruta del código QR (no editable)")
    }

    edited_df = st.data_editor(
        estudiantes,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_estudiantes"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("💾 Guardar cambios", key="guardar_est"):
            # Asegurar que los datos sean strings y reemplazar vacíos
            edited_df = edited_df.astype(str).replace('nan', '')
            guardar_estudiantes(edited_df)
            st.success("✅ Cambios guardados correctamente")
    with col2:
        st.caption("Puedes editar celdas, agregar filas (al final) o eliminar filas seleccionándolas y presionando Supr.")

    # Ver QR
    st.subheader("🔍 Ver QR del estudiante")
    ru_ver = st.text_input("Ingrese RU para ver QR")
    if ru_ver != "":
        estudiante = estudiantes[estudiantes["RU"] == ru_ver]
        if len(estudiante) > 0:
            ruta_qr = estudiante.iloc[0]["QR"]
            if os.path.exists(ruta_qr):
                st.image(ruta_qr, width=350)
            else:
                st.warning("⚠️ Archivo QR no encontrado")
        else:
            st.warning("⚠️ RU no encontrado")

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------
elif menu == "📸 Escanear QR":
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
            estudiante = estudiantes[estudiantes["RU"] == ru]

            if len(estudiante) > 0:
                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha, hora = obtener_fecha_hora_exacta()

                asistencia = leer_asistencia()
                ya = asistencia[(asistencia["RU"] == ru) & (asistencia["Fecha"] == str(fecha))]

                if len(ya) == 0:
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, str(fecha), hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                else:
                    st.warning("⚠️ Ya registró asistencia hoy")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó QR")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif menu == "✍️ Registrar asistencia manual":
    st.subheader("✍️ Registrar asistencia manual")
    estudiantes = leer_estudiantes()
    if len(estudiantes) == 0:
        st.warning("No hay estudiantes registrados. Primero registra estudiantes.")
    else:
        estudiantes["nombre_completo"] = estudiantes["RU"] + " - " + estudiantes["Nombres"] + " " + estudiantes["Apellido_paterno"]
        seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
        ru = seleccionado.split(" - ")[0]
        estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])

        if st.button("✅ Registrar asistencia"):
            estudiante = estudiantes[estudiantes["RU"] == ru]
            nombres = estudiante.iloc[0]["Nombres"]
            paterno = estudiante.iloc[0]["Apellido_paterno"]
            materno = estudiante.iloc[0]["Apellido_materno"]

            fecha, hora = obtener_fecha_hora_exacta()

            asistencia = leer_asistencia()
            nuevo = pd.DataFrame([[ru, nombres, paterno, materno, str(fecha), hora, estado]],
                                  columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
            asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
            guardar_asistencia(asistencia)
            st.success(f"✅ Asistencia registrada a las {hora}")

# ------------------------------------------------------------
# VER ASISTENCIA (CON EDITOR)
# ------------------------------------------------------------
elif menu == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia (editable)")

    asistencia = leer_asistencia()

    # Configurar columnas: todas editables, pero podemos definir tipos
    column_config_asis = {
        "RU": st.column_config.TextColumn("RU", required=True),
        "Nombres": st.column_config.TextColumn("Nombres", required=True),
        "Apellido_paterno": st.column_config.TextColumn("Apellido paterno", required=True),
        "Apellido_materno": st.column_config.TextColumn("Apellido materno", required=True),
        "Fecha": st.column_config.TextColumn("Fecha", required=True),
        "Hora": st.column_config.TextColumn("Hora", required=True),
        "Estado": st.column_config.SelectboxColumn("Estado", options=["Presente", "Tarde", "Permiso", "Ausente"], required=True)
    }

    edited_asis = st.data_editor(
        asistencia,
        column_config=column_config_asis,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_asistencia"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("💾 Guardar cambios", key="guardar_asis"):
            edited_asis = edited_asis.astype(str).replace('nan', '')
            guardar_asistencia(edited_asis)
            st.success("✅ Cambios guardados correctamente")
    with col2:
        st.caption("Puedes editar celdas, agregar filas o eliminar filas seleccionándolas y presionando Supr.")

    # Descargar asistencia del día
    st.subheader("⬇️ Descargar asistencia del día")
    hoy = str(datetime.now(ZONA_HORARIA).date())
    asistencia_hoy = asistencia[asistencia["Fecha"] == hoy]
    if len(asistencia_hoy) > 0:
        archivo_descarga = f"asistencia_{hoy}.xlsx"
        asistencia_hoy.to_excel(archivo_descarga, index=False)
        with open(archivo_descarga, "rb") as file:
            st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga)
    else:
        st.info("No hay registros para hoy.")
