import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz  # Para zona horaria exacta

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA (cambiar según tu ubicación)
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')  # Ejemplo: Bolivia

def obtener_fecha_hora_exacta():
    """Retorna (fecha, hora_con_milisegundos) en la zona horaria configurada."""
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    # Formato con milisegundos (3 dígitos). Si no quieres milisegundos cambia a "%H:%M:%S"
    hora = ahora.strftime("%H:%M:%S.%f")[:-3]
    return fecha, hora

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS (MODO OSCURO + ANIMACIONES)
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
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

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar);
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] .stSelectbox label {
    color: var(--text-secondary) !important;
}

/* Inputs y selects */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
    background-color: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.stTextInput input:focus,
.stSelectbox div[data-baseweb="select"]:focus {
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
div.stMarkdown,
div.stAlert {
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

@keyframes slideIn {
    from {opacity:0; transform:translateY(-10px);}
    to {opacity:1; transform:translateY(0);}
}

/* Scroll */
::-webkit-scrollbar {width:8px;height:8px;}
::-webkit-scrollbar-track {background:var(--bg-card);}
::-webkit-scrollbar-thumb {background:var(--accent);border-radius:4px;}
::-webkit-scrollbar-thumb:hover {background:var(--accent-light);}

/* Cámara */
div[data-testid="stCameraInput"] video{
    width:100%!important;
    height:75vh!important;
    object-fit:cover;
    border-radius:16px;
    border:2px solid var(--accent);
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# ARCHIVOS Y CONSTANTES
# ------------------------------------------------------------
archivo_estudiantes = "estudiantes.xlsx"
archivo_asistencia = "asistencia.xlsx"

st.title("📷 Sistema de Asistencia con QR")

menu = st.sidebar.selectbox(
    "📌 Menú",
    [
        "📝 Registrar estudiante",
        "📋 Lista estudiantes",
        "📸 Escanear QR",
        "✍️ Registrar asistencia manual",
        "📊 Ver asistencia"
    ]
)

if not os.path.exists(archivo_estudiantes):
    df = pd.DataFrame(columns=["RU","Nombres","Apellido_paterno","Apellido_materno","QR"])
    df.to_excel(archivo_estudiantes,index=False)

if not os.path.exists(archivo_asistencia):
    df = pd.DataFrame(columns=["RU","Nombres","Apellido_paterno","Apellido_materno","Fecha","Hora","Estado"])
    df.to_excel(archivo_asistencia,index=False)

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if menu == "📝 Registrar estudiante":

    st.subheader("📝 Registrar nuevo estudiante")

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

            nuevo = pd.DataFrame(
                [[ru,nombres,paterno,materno,ruta_qr]],
                columns=["RU","Nombres","Apellido_paterno","Apellido_materno","QR"]
            )

            df = pd.concat([df,nuevo],ignore_index=True)
            df.to_excel(archivo_estudiantes,index=False)

            st.success("✅ Estudiante registrado")
            st.image(ruta_qr,width=350)

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------
elif menu == "📸 Escanear QR":

    st.subheader("📸 Escanear QR")

    foto = st.camera_input("Toma una foto del código QR")

    if foto is not None:

        file_bytes = np.asarray(bytearray(foto.read()),dtype=np.uint8)
        frame = cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)

        detector = cv2.QRCodeDetector()
        data,bbox,_ = detector.detectAndDecode(frame)

        if data:

            ru = data
            estudiantes = pd.read_excel(archivo_estudiantes)

            estudiante = estudiantes[estudiantes["RU"].astype(str)==ru]

            if len(estudiante)>0:

                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha,hora = obtener_fecha_hora_exacta()

                asistencia = pd.read_excel(archivo_asistencia)

                ya = asistencia[
                    (asistencia["RU"].astype(str)==ru) &
                    (asistencia["Fecha"].astype(str)==str(fecha))
                ]

                if len(ya)==0:

                    nuevo = pd.DataFrame(
                        [[ru,nombres,paterno,materno,fecha,hora,"Presente"]],
                        columns=["RU","Nombres","Apellido_paterno","Apellido_materno","Fecha","Hora","Estado"]
                    )

                    asistencia = pd.concat([asistencia,nuevo],ignore_index=True)
                    asistencia.to_excel(archivo_asistencia,index=False)

                    st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")

                else:
                    st.warning("⚠️ Ya registró asistencia hoy")

            else:
                st.error("❌ Estudiante no encontrado")

        else:
            st.warning("⚠️ No se detectó QR")
