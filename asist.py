import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz
import io
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S.%f")[:-3]
    return fecha, hora

# ------------------------------------------------------------
# FUNCIÓN PARA VERIFICAR REGISTRO DUPLICADO
# ------------------------------------------------------------
def verificar_registro_duplicado(ru, fecha):
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
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# ESTILOS CSS (NUEVO ESTILO NEOMÓRFICO ELEGANTE)
# ------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --bg-main: #eef2f3;
        --bg-card: #ffffff;
        --bg-sidebar: #f8fafc;
        --text-primary: #1e2a3e;
        --text-secondary: #5b6e8c;
        --accent: #6fbf4c;
        --accent-light: #b8e0a8;
        --accent-dark: #4c8b2e;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 10px 15px -3px rgba(0,0,0,0.03), 0 4px 6px -2px rgba(0,0,0,0.02);
        --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.05), 0 10px 10px -5px rgba(0,0,0,0.02);
        --neomorph-white: inset 2px 2px 5px rgba(255,255,255,0.8), inset -2px -2px 5px rgba(0,0,0,0.05), 4px 4px 10px rgba(0,0,0,0.05), -2px -2px 5px rgba(255,255,255,0.8);
        --neomorph-inset: inset 2px 2px 5px rgba(0,0,0,0.05), inset -2px -2px 5px rgba(255,255,255,0.6);
        --border-radius: 1rem;
    }

    .stApp {
        background: var(--bg-main);
        color: var(--text-primary);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Título principal */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* Menú horizontal (radio) */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.75rem;
        background: var(--bg-card);
        padding: 0.5rem;
        border-radius: 3rem;
        box-shadow: var(--shadow-md);
        margin-bottom: 2rem;
        backdrop-filter: blur(2px);
        border: 1px solid rgba(255,255,255,0.4);
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 2rem;
        transition: all 0.2s ease;
        cursor: pointer;
        font-size: 0.9rem;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(111, 191, 76, 0.1);
        color: var(--accent-dark);
        transform: translateY(-1px);
    }

    /* Estilo para el botón seleccionado */
    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: var(--accent);
        color: white;
        box-shadow: var(--shadow-sm);
        border: none;
    }

    /* Botones generales */
    .stButton button {
        background: var(--accent);
        color: white;
        border: none;
        border-radius: 2rem;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.2);
    }

    .stButton button:hover {
        background: var(--accent-dark);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }

    .stButton button:active {
        transform: translateY(1px);
    }

    /* Inputs y selects */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: var(--bg-card);
        border: 1px solid #e2e8f0;
        border-radius: var(--border-radius);
        padding: 0.75rem 1rem;
        color: var(--text-primary);
        font-size: 0.9rem;
        box-shadow: var(--neomorph-inset);
        transition: all 0.2s;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--accent);
        outline: none;
        box-shadow: 0 0 0 2px rgba(111,191,76,0.3), var(--neomorph-inset);
    }

    /* Tarjetas neomórficas */
    .info-card, .student-info, .stDataFrame {
        background: var(--bg-card);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255,255,255,0.6);
        backdrop-filter: blur(2px);
        margin-bottom: 1.5rem;
        transition: transform 0.2s;
    }

    .student-info {
        border-left: 4px solid var(--accent);
        background: rgba(111,191,76,0.03);
    }

    /* Tablas */
    .stDataFrame {
        padding: 0;
        overflow: hidden;
    }

    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
        color: var(--text-primary);
    }

    .stDataFrame th {
        background: #f9fafb;
        color: var(--text-secondary);
        font-weight: 600;
        padding: 1rem;
        border-bottom: 1px solid #e2e8f0;
    }

    .stDataFrame td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f1f5f9;
        color: var(--text-primary);
    }

    /* Cámara */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 70vh !important;
        object-fit: cover;
        border-radius: var(--border-radius);
        border: 2px solid var(--accent);
        box-shadow: var(--shadow-lg);
    }

    /* Alertas neomórficas */
    .stAlert {
        background: var(--bg-card);
        border-left: 4px solid var(--accent);
        border-radius: var(--border-radius);
        padding: 1rem;
        box-shadow: var(--shadow-sm);
        color: var(--text-primary);
        font-size: 0.9rem;
    }

    /* Sidebar */
    .css-1d391kg, .css-1lcbmhc {
        background: var(--bg-sidebar);
        border-right: 1px solid #e2e8f0;
    }

    /* Animaciones suaves */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stAlert, .stButton, .stDataFrame {
        animation: fadeIn 0.3s ease-out;
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
    st.session_state.menu_actual = "📝 Registrar estudiante"
if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None

# ------------------------------------------------------------
# TÍTULO Y MENÚ HORIZONTAL
# ------------------------------------------------------------
st.title("🌿 Sistema de Asistencia")
st.markdown('<p style="color: #5b6e8c; margin-top: -10px; margin-bottom: 20px;">Gestión elegante con códigos QR · Estilo neomórfico</p>', unsafe_allow_html=True)

opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia"
]
menu = st.radio("", opciones_menu, horizontal=True, label_visibility="collapsed", key="menu_radio")
st.session_state.menu_actual = menu

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color: #5b6e8c;">Sube tus propios archivos para trabajar con ellos</p>', unsafe_allow_html=True)
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
        df = pd.read_excel(st.session_state.ruta_estudiantes)
        columnas_necesarias = ["RU", "Nombres", "Apellido_paterno", "Apellido_materno"]
        columnas_existentes = [col for col in columnas_necesarias if col in df.columns]
        df = df[columnas_existentes]
        return df
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno"])

def guardar_estudiantes(df):
    columnas_guardar = ["RU", "Nombres", "Apellido_paterno", "Apellido_materno"]
    df = df[columnas_guardar]
    df.to_excel(st.session_state.ruta_estudiantes, index=False)

def leer_asistencia():
    if os.path.exists(st.session_state.ruta_asistencia):
        return pd.read_excel(st.session_state.ruta_asistencia)
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])

def guardar_asistencia(df):
    df.to_excel(st.session_state.ruta_asistencia, index=False)

# ------------------------------------------------------------
# FUNCIÓN PARA CREAR TARJETA CUADRADA MEJORADA
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    """
    Crea una tarjeta cuadrada de 550x550 con:
    - Fondo oscuro, borde azul oscuro
    - Título "TARJETA DE IDENTIFICACIÓN" en negrita mayúsculas
    - QR grande (350x350)
    - RU y nombre completo con fuentes grandes
    - Texto inferior: "INGENIERÍA DE SISTEMAS - UAP"
    """
    ru = str(estudiante["RU"])
    nombres = estudiante["Nombres"]
    paterno = estudiante["Apellido_paterno"]
    materno = estudiante["Apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    # Generar QR
    qr = qrcode.make(ru)
    qr_size = 350
    qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

    # Tamaño de la tarjeta
    card_size = 550
    card = Image.new('RGB', (card_size, card_size), color=(10, 20, 30))
    draw = ImageDraw.Draw(card)

    # Intentar cargar fuente
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    # Definir fuentes
    if font_path:
        title_font = ImageFont.truetype(font_path, 32)          # Título
        ru_font = ImageFont.truetype(font_path, 28)            # RU
        name_font = ImageFont.truetype(font_path, 26)          # Nombre
        footer_font = ImageFont.truetype(font_path, 20)        # Pie
    else:
        title_font = ImageFont.load_default()
        ru_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # Borde azul oscuro
    border_color = (25, 80, 150)
    border_width = 5
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    # --- Título ---
    title_text = "TARJETA DE IDENTIFICACIÓN"
    # Calcular ancho para centrar
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 25
    draw.text((title_x, title_y), title_text, fill=(255, 255, 255), font=title_font)

    # --- RU ---
    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 50
    draw.text((ru_x, ru_y), ru_text, fill=(255, 255, 255), font=ru_font)

    # --- Nombre completo (con ajuste de líneas) ---
    max_width = card_size - 40
    words = nombre_completo.split()
    lines = []
    current_line = ""
    for w in words:
        test_line = current_line + (" " + w if current_line else w)
        bbox = draw.textbbox((0,0), test_line, font=name_font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = w
    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [nombre_completo]

    line_spacing = 35
    total_height = len(lines) * line_spacing
    start_y = ru_y + 55
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        draw.text((x, y), line, fill=(255, 255, 255), font=name_font)

    # --- QR ---
    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height + 20
    card.paste(qr, (qr_x, qr_y))

    # --- Texto inferior ---
    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 20
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 28
        draw.text((x, y), line, fill=(220, 220, 220), font=footer_font)

    # Guardar en buffer
    img_bytes = io.BytesIO()
    card.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            ru = st.text_input("🔢 RU", placeholder="Ingrese el RU del estudiante")
            nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres")
        with col2:
            paterno = st.text_input("👨 Apellido paterno", placeholder="Ingrese el apellido paterno")
            materno = st.text_input("👩 Apellido materno", placeholder="Ingrese el apellido materno")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("💾 Guardar estudiante", use_container_width=True):
                df = leer_estudiantes()
                if ru in df["RU"].astype(str).values:
                    st.error("❌ Este RU ya existe")
                else:
                    qr_img = qrcode.make(ru)
                    img_bytes = io.BytesIO()
                    qr_img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno"])
                    df = pd.concat([df, nuevo], ignore_index=True)
                    guardar_estudiantes(df)
                    st.success("✅ Estudiante registrado exitosamente")
                    col_img1, col_img2, col_img3 = st.columns([1,2,1])
                    with col_img2:
                        st.image(img_bytes, width=350, caption=f"QR de {nombres} {paterno}")
                        buf = io.BytesIO()
                        qr_img.save(buf, format="PNG")
                        buf.seek(0)
                        st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        st.markdown("---")
        st.subheader("🔍 Buscar estudiante")
        col1, col2, col3 = st.columns([3,1,3])
        with col1:
            ru_ver = st.text_input("Ingrese RU para buscar", placeholder="Ej: 2024001", key="buscar_ru")
        with col2:
            buscar_click = st.button("🔍 Buscar", key="buscar_btn", use_container_width=True)
        if buscar_click and ru_ver:
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                tarjeta_img = crear_tarjeta_estudiante(estudiante.iloc[0])
                st.markdown("### 🎓 Tarjeta Ejecutiva del Estudiante")
                st.image(tarjeta_img, use_container_width=False, width=550)
                st.download_button(
                    label="📥 Descargar Tarjeta (PNG)",
                    data=tarjeta_img,
                    file_name=f"tarjeta_{estudiante.iloc[0]['RU']}.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ RU no encontrado en la base de datos")
        elif buscar_click and not ru_ver:
            st.warning("⚠️ Por favor ingrese un RU para buscar")
        st.markdown("---")
        st.subheader("🗑️ Eliminar estudiante")
        if len(estudiantes) > 0:
            col1, col2, col3 = st.columns([2,1,2])
            with col1:
                eliminar = st.number_input("Índice del estudiante a eliminar", min_value=0, max_value=len(estudiantes)-1, key="eliminar_est")
            with col2:
                if st.button("🗑️ Eliminar", use_container_width=True):
                    estudiantes = estudiantes.drop(eliminar).reset_index(drop=True)
                    guardar_estudiantes(estudiantes)
                    st.success("✅ Estudiante eliminado correctamente")
                    st.rerun()
        st.markdown("---")
        st.subheader("⬇️ Descargar Excel estudiantes")
        if len(estudiantes) > 0:
            archivo_descarga = "registro_estudiantes_temp.xlsx"
            estudiantes.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel completo", data=file, file_name="estudiantes_exportados.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: #5b6e8c;">Toma una foto del código QR del estudiante para registrar su asistencia</p>', unsafe_allow_html=True)
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
                materno = estudiante.iloc[0]["Apellido_materno"]
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
                if not tiene_registro:
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = leer_asistencia()
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    st.session_state.ultimo_registro = {"RU": ru, "Nombres": nombres, "Hora": hora, "Fecha": fecha}
                    st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} YA REGISTRÓ ASISTENCIA HOY A LAS {registro_existente['Hora']}")
            else:
                st.error("❌ Estudiante no encontrado en la base de datos")
        else:
            st.warning("⚠️ No se detectó ningún código QR en la imagen")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    st.subheader("✍️ Registrar asistencia manual")
    estudiantes = leer_estudiantes()
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"] + " " + estudiantes["Apellido_paterno"]
        col1, col2 = st.columns(2)
        with col1:
            seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
            ru = seleccionado.split(" - ")[0]
        with col2:
            estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
        fecha, hora = obtener_fecha_hora_exacta()
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        if tiene_registro:
            st.warning(f"⚠️ Este estudiante ya registró hoy a las {registro_existente['Hora']} (Estado: {registro_existente['Estado']})")
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
            st.caption("Botón deshabilitado - Registro duplicado")
        else:
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("✅ Registrar asistencia", use_container_width=True):
                    estudiante = estudiantes[estudiantes["RU"].astype(str) == ru].iloc[0]
                    nombres = estudiante["Nombres"]
                    paterno = estudiante["Apellido_paterno"]
                    materno = estudiante["Apellido_materno"]
                    asistencia = leer_asistencia()
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    st.session_state.ultimo_registro = {"RU": ru, "Nombres": nombres, "Hora": hora, "Fecha": fecha}
                    st.success(f"✅ Asistencia registrada a las {hora}")
    else:
        st.warning("⚠️ No hay estudiantes registrados en el sistema")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    asistencia = leer_asistencia()
    if len(asistencia) > 0:
        st.dataframe(asistencia, use_container_width=True)
        st.markdown("---")
        st.subheader("🔍 Verificación de integridad")
        duplicados = asistencia.groupby(['RU', 'Fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        if len(duplicados) > 0:
            st.warning(f"⚠️ Se encontraron {len(duplicados)} casos de registros duplicados")
            if st.button("🧹 Limpiar duplicados (mantener primer registro)", use_container_width=True):
                asistencia_limpia = asistencia.drop_duplicates(subset=['RU', 'Fecha'], keep='first')
                guardar_asistencia(asistencia_limpia)
                st.success("✅ Duplicados eliminados correctamente")
                st.rerun()
        else:
            st.success("✅ No hay registros duplicados en el sistema")
        st.markdown("---")
        st.subheader("✏️ Editar estado de registro")
        if len(asistencia) > 0:
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                indice = st.number_input("Índice del registro", min_value=0, max_value=len(asistencia)-1)
            with col2:
                nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"])
            with col3:
                if st.button("🔄 Actualizar", use_container_width=True):
                    asistencia.loc[indice, "Estado"] = nuevo_estado
                    guardar_asistencia(asistencia)
                    st.success("✅ Estado actualizado correctamente")
                    st.rerun()
        st.markdown("---")
        st.subheader("🗑️ Eliminar registro")
        if len(asistencia) > 0:
            col1, col2, col3 = st.columns([2,1,2])
            with col1:
                eliminar = st.number_input("Índice del registro a eliminar", min_value=0, max_value=len(asistencia)-1, key="elim")
            with col2:
                if st.button("🗑️ Eliminar", use_container_width=True):
                    asistencia = asistencia.drop(eliminar).reset_index(drop=True)
                    guardar_asistencia(asistencia)
                    st.success("✅ Registro eliminado correctamente")
                    st.rerun()
        st.markdown("---")
        st.subheader("⬇️ Descargar asistencia del día")
        hoy = str(datetime.now(ZONA_HORARIA).date())
        asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga, use_container_width=True)
        else:
            st.info("📭 No hay registros para el día de hoy")
    else:
        st.info("📭 No hay registros de asistencia en el sistema")
