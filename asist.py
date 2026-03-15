import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA (cambiar según tu ubicación)
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')  # Ejemplo: Bolivia

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S.%f")[:-3]  # Con milisegundos
    return fecha, hora

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS (MODO OSCURO + ANIMACIONES + MENÚ HORIZONTAL)
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    layout="wide",
    initial_sidebar_state="collapsed"  # Ocultar sidebar por defecto
)

# Estilos CSS personalizados (incluye menú horizontal)
st.markdown("""
<style>
    /* Variables de color modo oscuro */
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

    /* Fondo general */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }

    /* Menú horizontal */
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
    }
    div.row-widget.stRadio > div label:hover {
        background-color: rgba(124, 58, 237, 0.1);
        color: var(--accent-light) !important;
    }
    div.row-widget.stRadio > div label[data-baseweb="radio"] input:checked + div {
        background-color: var(--accent);
        color: white !important;
    }
    div[role="radiogroup"] > label {
        background-color: transparent !important;
    }

    /* Inputs y selects */
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

    /* Botones */
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

    /* Dataframes */
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

    /* Imágenes QR */
    .stImage img {
        border-radius: 16px;
        border: 3px solid var(--accent);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    .stImage img:hover {
        transform: scale(1.02);
    }

    /* Tarjetas / contenedores */
    div.stMarkdown, div.stAlert {
        background-color: var(--bg-card);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    /* Mensajes */
    .stAlert {
        border-left: 4px solid;
        animation: slideIn 0.3s ease;
    }
    .stAlert.success {
        border-left-color: var(--success);
    }
    .stAlert.warning {
        border-left-color: var(--warning);
    }
    .stAlert.error {
        border-left-color: var(--error);
    }

    /* Animación */
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
# MENSAJE DE ADVERTENCIA SOBRE PERSISTENCIA EN STREAMLIT CLOUD
# ------------------------------------------------------------
st.warning("⚠️ **Nota sobre persistencia de datos:** Si ejecutas esta app en Streamlit Cloud, los archivos Excel se reiniciarán con cada nueva sesión. Para datos permanentes, considera usar una base de datos externa (Supabase, MongoDB) o ejecutar localmente.")

# ------------------------------------------------------------
# TÍTULO Y MENÚ HORIZONTAL
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
    label_visibility="collapsed"
)

# ------------------------------------------------------------
# ARCHIVOS Y CONSTANTES
# ------------------------------------------------------------
archivo_estudiantes = "estudiantes.xlsx"
archivo_asistencia = "asistencia.xlsx"

# Crear archivos si no existen
if not os.path.exists(archivo_estudiantes):
    df = pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
    df.to_excel(archivo_estudiantes, index=False)

if not os.path.exists(archivo_asistencia):
    df = pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
    df.to_excel(archivo_asistencia, index=False)

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
            df = pd.read_excel(archivo_estudiantes)
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
                df.to_excel(archivo_estudiantes, index=False)
                st.success("✅ Estudiante registrado")
                st.image(ruta_qr, width=350)
                with open(ruta_qr, "rb") as file:
                    st.download_button("⬇️ Descargar QR", data=file, file_name=f"{ru}_qr.png", mime="image/png")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif menu == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = pd.read_excel(archivo_estudiantes)
    st.dataframe(estudiantes, use_container_width=True)

    # Ver QR
    st.subheader("🔍 Ver QR del estudiante")
    ru_ver = st.text_input("Ingrese RU para ver QR")
    if ru_ver != "":
        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
        if len(estudiante) > 0:
            st.image(estudiante.iloc[0]["QR"], width=350)
        else:
            st.warning("⚠️ RU no encontrado")

    # Eliminar estudiante
    st.subheader("🗑️ Eliminar estudiante")
    if len(estudiantes) > 0:
        eliminar = st.number_input("Índice a eliminar", min_value=0, max_value=len(estudiantes)-1, key="eliminar_est")
        if st.button("🗑️ Eliminar"):
            estudiantes = estudiantes.drop(eliminar)
            estudiantes.to_excel(archivo_estudiantes, index=False)
            st.success("✅ Estudiante eliminado")

    # Descargar Excel
    st.subheader("⬇️ Descargar Excel estudiantes")
    archivo_descarga = "registro_estudiantes.xlsx"
    estudiantes.to_excel(archivo_descarga, index=False)
    with open(archivo_descarga, "rb") as file:
        st.download_button("📥 Descargar Excel", data=file, file_name=archivo_descarga)

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
            estudiantes = pd.read_excel(archivo_estudiantes)
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]

            if len(estudiante) > 0:
                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha, hora = obtener_fecha_hora_exacta()

                asistencia = pd.read_excel(archivo_asistencia)
                ya = asistencia[(asistencia["RU"].astype(str) == ru) & (asistencia["Fecha"].astype(str) == str(fecha))]

                if len(ya) == 0:
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    asistencia.to_excel(archivo_asistencia, index=False)
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
    estudiantes = pd.read_excel(archivo_estudiantes)
    estudiantes["nombre_completo"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"] + " " + estudiantes["Apellido_paterno"]
    seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
    ru = seleccionado.split(" - ")[0]
    estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])

    if st.button("✅ Registrar asistencia"):
        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]
        nombres = estudiante.iloc[0]["Nombres"]
        paterno = estudiante.iloc[0]["Apellido_paterno"]
        materno = estudiante.iloc[0]["Apellido_materno"]

        fecha, hora = obtener_fecha_hora_exacta()

        asistencia = pd.read_excel(archivo_asistencia)
        nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                              columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
        asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
        asistencia.to_excel(archivo_asistencia, index=False)
        st.success(f"✅ Asistencia registrada a las {hora}")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif menu == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    asistencia = pd.read_excel(archivo_asistencia)
    st.dataframe(asistencia, use_container_width=True)

    # Editar estado
    st.subheader("✏️ Editar estado")
    if len(asistencia) > 0:
        indice = st.number_input("Índice registro", min_value=0, max_value=len(asistencia)-1)
        nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"])
        if st.button("🔄 Actualizar estado"):
            asistencia.loc[indice, "Estado"] = nuevo_estado
            asistencia.to_excel(archivo_asistencia, index=False)
            st.success("✅ Estado actualizado")

    # Eliminar registro
    st.subheader("🗑️ Eliminar registro")
    if len(asistencia) > 0:
        eliminar = st.number_input("Índice eliminar", min_value=0, max_value=len(asistencia)-1, key="elim")
        if st.button("🗑️ Eliminar registro"):
            asistencia = asistencia.drop(eliminar)
            asistencia.to_excel(archivo_asistencia, index=False)
            st.success("✅ Registro eliminado")

    # Descargar Excel del día
    st.subheader("⬇️ Descargar asistencia del día")
    hoy = str(datetime.now(ZONA_HORARIA).date())
    asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
    archivo_descarga = f"asistencia_{hoy}.xlsx"
    asistencia_hoy.to_excel(archivo_descarga, index=False)
    with open(archivo_descarga, "rb") as file:
        st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga)
