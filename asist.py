import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from supabase import create_client, Client

# ------------------------------------------------------------
# CONFIGURACIÓN DE SUPABASE
# ------------------------------------------------------------
SUPABASE_URL = "https://rwmxhbojhbscrktswmhg.supabase.co"
SUPABASE_KEY = "sb_publishable_Ukse6FwyRq-Qg1FW8zDbLA_QqLmtUTm"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S")
    return fecha, hora

# ------------------------------------------------------------
# FUNCIONES DE ACCESO A SUPABASE
# ------------------------------------------------------------
def leer_estudiantes():
    try:
        response = supabase.table("estudiantes").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            columnas = ["ru", "nombres", "apellido_paterno", "apellido_materno"]
            df = df[columnas]
            return df
        else:
            return pd.DataFrame(columns=["ru", "nombres", "apellido_paterno", "apellido_materno"])
    except Exception as e:
        st.error(f"Error al leer estudiantes: {e}")
        return pd.DataFrame(columns=["ru", "nombres", "apellido_paterno", "apellido_materno"])

def leer_asistencia():
    try:
        response = supabase.table("asistencia").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["hora"] = pd.to_datetime(df["hora"]).dt.time.astype(str)
            columnas = ["id", "ru", "nombres", "apellido_paterno", "apellido_materno", "fecha", "hora", "estado"]
            df = df[columnas]
            return df
        else:
            return pd.DataFrame(columns=["id", "ru", "nombres", "apellido_paterno", "apellido_materno", "fecha", "hora", "estado"])
    except Exception as e:
        st.error(f"Error al leer asistencia: {e}")
        return pd.DataFrame(columns=["id", "ru", "nombres", "apellido_paterno", "apellido_materno", "fecha", "hora", "estado"])

def verificar_registro_duplicado(ru, fecha):
    try:
        response = supabase.table("asistencia").select("*").eq("ru", ru).eq("fecha", fecha.isoformat()).execute()
        if response.data:
            return True, response.data[0]
        return False, None
    except Exception as e:
        st.error(f"Error al verificar duplicado: {e}")
        return False, None

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# INICIALIZAR SESSION STATE
# ------------------------------------------------------------
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "📝 Registrar estudiante"
if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None
if "confirmar_eliminar" not in st.session_state:
    st.session_state.confirmar_eliminar = None
if "confirmar_eliminar_asistencia" not in st.session_state:
    st.session_state.confirmar_eliminar_asistencia = None
if "confirmar_eliminar_todo_asistencia" not in st.session_state:
    st.session_state.confirmar_eliminar_todo_asistencia = False

# ------------------------------------------------------------
# ESTILOS CSS (igual que antes)
# ------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --primary-color: #0066ff;
        --primary-hover: #0052cc;
        --accent-color: #00ffcc;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --bg-dark: #0f172a;
        --glass-bg: rgba(15, 23, 42, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --shadow-3d: 0 10px 25px -5px rgba(0, 102, 255, 0.2), 0 10px 10px -5px rgba(0, 102, 255, 0.1);
        --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.4);
        --success-gradient: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        --input-bg: rgba(15, 23, 42, 0.5);
        --input-bg-focus: rgba(15, 23, 42, 0.8);
        --table-header-bg: linear-gradient(135deg, rgba(0,102,255,0.8) 0%, rgba(0,51,204,0.8) 100%);
        --table-row-hover: rgba(0, 102, 255, 0.1);
        --badge-bg: var(--success-gradient);
        --badge-color: #020617;
    }

    .stApp {
        background-color: var(--bg-dark);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    .css-1d391kg, .css-1lcbmhc {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
        box-shadow: var(--shadow-3d) !important;
    }

    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
        position: relative;
        display: inline-block;
    }

    h1::after, h2::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 100%;
        height: 3px;
        background: var(--success-gradient);
        border-radius: 3px;
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.3s ease;
    }

    h1:hover::after, h2:hover::after {
        transform: scaleX(1);
    }

    .subtitle-script {
        color: var(--text-secondary);
        margin-top: -10px;
        font-family: 'Pacifico', 'Dancing Script', 'Brush Script MT', cursive;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        font-weight: normal;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    /* Tarjeta de búsqueda */
    .student-search-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.3s ease;
    }
    .student-search-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(0, 102, 255, 0.3);
    }
    .student-name {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-color);
        margin-bottom: 0.5rem;
        text-shadow: 0 0 10px rgba(0,255,204,0.3);
        text-transform: uppercase;
    }
    .student-ru {
        font-size: 1.3rem;
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .qr-container {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0;
    }
    .qr-container img {
        border-radius: 16px;
        box-shadow: var(--shadow-3d);
        transition: transform 0.3s ease;
        max-width: 100%;
        height: auto;
    }
    .qr-container img:hover {
        transform: scale(1.02);
    }
    .download-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 1.5rem;
    }
    .info-card, .student-info, .stDataFrame {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-3d);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
    }

    .info-card::before, .student-info::before, .stDataFrame::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(0,102,255,0.1) 0%, rgba(0,102,255,0) 70%);
        transform: rotate(30deg);
        transition: all 0.5s ease;
        opacity: 0;
        pointer-events: none;
    }

    .info-card:hover::before, .student-info:hover::before, .stDataFrame:hover::before {
        opacity: 1;
        animation: shine 3s infinite;
    }

    @keyframes shine {
        0% { transform: rotate(30deg) translate(-10%, -10%); }
        100% { transform: rotate(30deg) translate(10%, 10%); }
    }

    .info-card:hover, .student-info:hover, .stDataFrame:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(0, 102, 255, 0.3);
    }

    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.75rem;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: var(--shadow-3d);
        margin-bottom: 2rem;
        border: 1px solid var(--glass-border);
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.9rem;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(0, 102, 255, 0.2);
        color: var(--accent-color);
        transform: translateY(-2px);
    }

    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: var(--success-gradient);
        color: var(--badge-color);
        box-shadow: var(--shadow-3d);
        font-weight: 600;
    }

    .stButton button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        border-bottom: 3px solid rgba(0, 0, 0, 0.2);
    }

    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.7s;
    }

    .stButton button:hover::before {
        left: 100%;
    }

    .stButton button:hover {
        background: var(--primary-hover);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: var(--input-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        backdrop-filter: blur(5px) !important;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        background: var(--input-bg-focus) !important;
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2) !important;
        transform: scale(1.01);
    }

    .stDataFrame {
        padding: 0;
        overflow: hidden;
    }

    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
        color: var(--text-primary);
    }

    .stDataFrame thead tr th {
        background: var(--table-header-bg) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem 1rem !important;
        border: none !important;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stDataFrame tbody tr {
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stDataFrame tbody tr:hover {
        background: var(--table-row-hover);
        transform: translateX(5px);
    }

    .stDataFrame tbody td {
        padding: 0.75rem 1rem !important;
        border: none !important;
    }

    .stAlert {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-3d) !important;
    }

    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 70vh !important;
        object-fit: cover;
        border-radius: 16px;
        border: 2px solid var(--primary-color);
        box-shadow: var(--shadow-3d);
    }

    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stAlert, .stButton, .stDataFrame, .info-card, .student-info {
        animation: fadeInUp 0.5s ease-out;
    }
    
    .qr-info {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--accent-color);
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        text-shadow: 0 0 8px rgba(0,255,204,0.3);
        text-transform: uppercase;
    }
    .qr-ru {
        font-size: 1.1rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS
# ------------------------------------------------------------
st.markdown("""
<script>
    function createParticles() {
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '-1';
        document.body.appendChild(container);
        
        const particleCount = 80;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = (Math.random() * 3 + 2) + 'px';
            particle.style.height = particle.style.width;
            particle.style.background = Math.random() > 0.66 ? '#00ffcc' : '#0066ff';
            particle.style.borderRadius = '50%';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `float ${Math.random() * 5 + 5}s infinite ease-in-out`;
            particle.style.animationDelay = Math.random() * 8 + 's';
            particle.style.opacity = '0.6';
            container.appendChild(particle);
        }
    }
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 0.6; }
            25% { transform: translate(10px, -15px) rotate(45deg); opacity: 0.8; }
            50% { transform: translate(-5px, -25px) rotate(90deg); opacity: 1; }
            75% { transform: translate(15px, -10px) rotate(135deg); opacity: 0.8; }
        }
    `;
    document.head.appendChild(style);
    window.addEventListener('load', createParticles);
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR (solo información del desarrollador)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color: var(--text-secondary);">Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO CON LOGO
# ------------------------------------------------------------
logo_path = "assets/logo.png"
header_cols = st.columns([1, 10])
with header_cols[0]:
    if os.path.exists(logo_path):
        st.image(logo_path, width=60)
    else:
        st.write("")
with header_cols[1]:
    st.title("INGENIERÍA DE SISTEMAS")
    st.markdown('<p class="subtitle-script">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# MENÚ HORIZONTAL
# ------------------------------------------------------------
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
# FUNCIÓN PARA CREAR TARJETA CUADRADA (VERSIÓN MEJORADA)
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    ru = str(estudiante["ru"])
    nombres = estudiante["nombres"]
    paterno = estudiante["apellido_paterno"]
    materno = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    # Generar QR más grande
    qr = qrcode.make(ru, box_size=10, border=2)
    qr_size = 500  # QR más grande
    qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

    # Tarjeta más grande
    card_size = 800
    # Fondo con gradiente (oscuro a azul)
    background = Image.new('RGB', (card_size, card_size), color=(10, 20, 40))
    # Crear un gradiente vertical
    gradient = Image.new('RGBA', (card_size, card_size), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(card_size):
        # Intensidad azul: más clara hacia abajo
        blue_intensity = int(60 * (1 - y / card_size))
        draw_grad.rectangle([0, y, card_size, y+1], fill=(0, 0, blue_intensity, 180))
    background = Image.alpha_composite(background.convert('RGBA'), gradient).convert('RGB')
    
    draw = ImageDraw.Draw(background)

    # Fuentes - buscar rutas comunes (priorizar negritas)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    font_regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    title_font = None
    ru_font = None
    name_font = None
    footer_font = None

    for path in font_paths:
        if os.path.exists(path):
            title_font = ImageFont.truetype(path, 38)
            ru_font = ImageFont.truetype(path, 40)
            name_font = ImageFont.truetype(path, 36)
            break
    for path in font_regular_paths:
        if os.path.exists(path):
            footer_font = ImageFont.truetype(path, 28)
            break
    if not title_font:
        title_font = ImageFont.load_default()
        ru_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # Borde decorativo
    border_color = (0, 102, 255)
    border_width = 8
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    # Título con sombra
    title_text = "TARJETA DE IDENTIFICACION"
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 20
    # Sombra
    draw.text((title_x+3, title_y+3), title_text, fill=(0,0,0,128), font=title_font)
    draw.text((title_x, title_y), title_text, fill=(255,255,255), font=title_font)

    # RU con sombra
    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 70
    draw.text((ru_x+2, ru_y+2), ru_text, fill=(0,0,0,128), font=ru_font)
    draw.text((ru_x, ru_y), ru_text, fill=(255,255,200), font=ru_font)

    # Nombre completo: manejo de multilínea con mayor espacio
    max_width = card_size - 80
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

    line_spacing = 50
    total_height = len(lines) * line_spacing
    start_y = ru_y + 90
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        # Sombra
        draw.text((x+2, y+2), line, fill=(0,0,0,128), font=name_font)
        draw.text((x, y), line, fill=(255,255,255), font=name_font)

    # Posicionar QR con más margen
    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height + 20
    background.paste(qr, (qr_x, qr_y))

    # Pie de página
    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 30
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 36
        draw.text((x+1, y+1), line, fill=(0,0,0,128), font=footer_font)
        draw.text((x, y), line, fill=(220, 220, 255), font=footer_font)

    # Guardar imagen
    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG')
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
            ru = st.text_input("🔢 RU", placeholder="Ingrese el RU del estudiante (solo números)")
            nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres")
        with col2:
            paterno = st.text_input("👨 Apellido paterno", placeholder="Ingrese el apellido paterno")
            materno = st.text_input("👩 Apellido materno", placeholder="Ingrese el apellido materno")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("💾 Guardar estudiante", use_container_width=True):
                if not ru or not ru.strip():
                    st.error("❌ El RU no puede estar vacío")
                elif not ru.isdigit():
                    st.error("❌ El RU debe contener solo números")
                else:
                    try:
                        existe = supabase.table("estudiantes").select("ru").eq("ru", ru).execute()
                        if existe.data:
                            st.error("❌ Este RU ya existe")
                        else:
                            supabase.table("estudiantes").insert({
                                "ru": ru,
                                "nombres": nombres,
                                "apellido_paterno": paterno,
                                "apellido_materno": materno
                            }).execute()
                            st.success("✅ Estudiante registrado exitosamente")
                            
                            qr_img = qrcode.make(ru)
                            img_bytes = io.BytesIO()
                            qr_img.save(img_bytes, format='PNG')
                            img_bytes.seek(0)
                            col_img1, col_img2, col_img3 = st.columns([1,2,1])
                            with col_img2:
                                nombre_upper = f"{nombres} {paterno}".upper()
                                st.markdown(f'<div class="qr-info">{nombre_upper}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="qr-ru">RU: {ru}</div>', unsafe_allow_html=True)
                                st.image(img_bytes, width=500, caption="Código QR del estudiante")
                                buf = io.BytesIO()
                                qr_img.save(buf, format="PNG")
                                buf.seek(0)
                                st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error al guardar estudiante: {e}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES (con nuevo orden: búsqueda arriba, gestión abajo)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        # Mostrar tabla
        st.dataframe(estudiantes, use_container_width=True)
        st.markdown("---")
        
        # ========== BÚSQUEDA DE ESTUDIANTE (ahora arriba) ==========
        st.subheader("🔍 Buscar estudiante")
        col1, col2, col3 = st.columns([3,1,3])
        with col1:
            ru_ver = st.text_input("Ingrese RU para buscar", placeholder="Código Único", key="buscar_ru")
        with col2:
            buscar_click = st.button("🔍 Buscar", key="buscar_btn", use_container_width=True)
        if buscar_click and ru_ver:
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                estudiante_data = estudiante.iloc[0]
                nombres = estudiante_data["nombres"]
                paterno = estudiante_data["apellido_paterno"]
                ru = estudiante_data["ru"]
                nombre_completo = f"{nombres} {paterno}".strip().upper()
                
                qr_img = qrcode.make(ru)
                qr_buffer = io.BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                qr_base64 = base64.b64encode(qr_buffer.read()).decode()
                
                st.markdown(f"""
                <div class="student-search-card">
                    <div class="student-name">{nombre_completo}</div>
                    <div class="student-ru">RU: {ru}</div>
                    <div class="qr-container">
                        <img src="data:image/png;base64,{qr_base64}" width="500" alt="QR Code">
                    </div>
                    <div class="download-buttons">
                        <div style="display: inline-block;" id="qr-download-btn"></div>
                        <div style="display: inline-block;" id="tarjeta-download-btn"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
                with col_btn1:
                    st.download_button(
                        label="📥 Descargar QR",
                        data=qr_buffer.getvalue(),
                        file_name=f"{ru}_qr.png",
                        mime="image/png",
                        key="download_qr_search",
                        use_container_width=True
                    )
                with col_btn2:
                    tarjeta_img = crear_tarjeta_estudiante(estudiante_data)
                    st.download_button(
                        label="📇 Descargar Tarjeta Ejecutiva",
                        data=tarjeta_img,
                        file_name=f"tarjeta_{ru}.png",
                        mime="image/png",
                        key="download_tarjeta_search",
                        use_container_width=True
                    )
                with col_btn3:
                    st.write("")
            else:
                st.warning("⚠️ RU no encontrado en la base de datos")
        elif buscar_click and not ru_ver:
            st.warning("⚠️ Por favor ingrese un RU para buscar")
        
        st.markdown("---")
        
        # ========== GESTIÓN DE ESTUDIANTES (editar/eliminar) ==========
        st.subheader("✏️ Gestionar estudiante")
        
        estudiantes_display = estudiantes.copy()
        estudiantes_display["nombre_completo"] = estudiantes_display["ru"] + " - " + estudiantes_display["nombres"] + " " + estudiantes_display["apellido_paterno"]
        opciones = estudiantes_display["nombre_completo"].tolist()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            seleccion = st.selectbox("Selecciona un estudiante", opciones, key="select_estudiante")
            ru_seleccionado = seleccion.split(" - ")[0]
        
        estudiante_data = estudiantes[estudiantes["ru"] == ru_seleccionado].iloc[0]
        
        with st.form(key="form_editar_estudiante"):
            nuevo_ru = st.text_input("RU", value=estudiante_data["ru"])
            nuevos_nombres = st.text_input("Nombres", value=estudiante_data["nombres"])
            nuevo_paterno = st.text_input("Apellido paterno", value=estudiante_data["apellido_paterno"])
            nuevo_materno = st.text_input("Apellido materno", value=estudiante_data["apellido_materno"])
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            with col_btn1:
                submit_actualizar = st.form_submit_button("🔄 Actualizar estudiante", use_container_width=True)
            with col_btn2:
                submit_eliminar = st.form_submit_button("🗑️ Eliminar estudiante", use_container_width=True)
        
        # Procesar actualización
        if submit_actualizar:
            if not nuevo_ru or not nuevo_ru.strip():
                st.error("❌ El RU no puede estar vacío")
            elif not nuevo_ru.isdigit():
                st.error("❌ El RU debe contener solo números")
            else:
                try:
                    if nuevo_ru != ru_seleccionado:
                        existe = supabase.table("estudiantes").select("ru").eq("ru", nuevo_ru).execute()
                        if existe.data:
                            st.error("❌ El nuevo RU ya existe en la base de datos")
                            st.stop()
                    supabase.table("estudiantes").update({
                        "ru": nuevo_ru,
                        "nombres": nuevos_nombres,
                        "apellido_paterno": nuevo_paterno,
                        "apellido_materno": nuevo_materno
                    }).eq("ru", ru_seleccionado).execute()
                    
                    if nuevo_ru != ru_seleccionado:
                        supabase.table("asistencia").update({"ru": nuevo_ru}).eq("ru", ru_seleccionado).execute()
                    
                    st.success("✅ Estudiante actualizado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al actualizar: {e}")
        
        # Procesar eliminación con confirmación
        if submit_eliminar:
            st.session_state.confirmar_eliminar = ru_seleccionado
        
        if st.session_state.confirmar_eliminar:
            ru_eliminar = st.session_state.confirmar_eliminar
            estudiante_eliminar = estudiantes[estudiantes["ru"] == ru_eliminar].iloc[0]
            nombre_eliminar = f"{estudiante_eliminar['nombres']} {estudiante_eliminar['apellido_paterno']}"
            st.warning(f"⚠️ ¿Estás seguro de eliminar a **{nombre_eliminar} (RU: {ru_eliminar})**? Se eliminarán también todos sus registros de asistencia.")
            col_confirm1, col_confirm2, _ = st.columns([1,1,3])
            with col_confirm1:
                if st.button("✅ Sí, eliminar", key="confirm_eliminar", use_container_width=True):
                    try:
                        supabase.table("asistencia").delete().eq("ru", ru_eliminar).execute()
                        supabase.table("estudiantes").delete().eq("ru", ru_eliminar).execute()
                        st.success("✅ Estudiante y sus registros de asistencia eliminados correctamente")
                        st.session_state.confirmar_eliminar = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al eliminar: {e}")
            with col_confirm2:
                if st.button("❌ No, cancelar", key="cancel_eliminar", use_container_width=True):
                    st.session_state.confirmar_eliminar = None
                    st.rerun()
        
        st.markdown("---")
        
        # ========== DESCARGAR EXCEL ESTUDIANTES ==========
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
    st.markdown('<p style="color: var(--text-secondary);">Toma una foto del código QR del estudiante para registrar su asistencia</p>', unsafe_allow_html=True)
    foto = st.camera_input("", label_visibility="collapsed")
    if foto is not None:
        file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(frame)
        if data:
            ru = data
            estudiantes = leer_estudiantes()
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru]
            if len(estudiante) > 0:
                nombres = estudiante.iloc[0]["nombres"]
                paterno = estudiante.iloc[0]["apellido_paterno"]
                materno = estudiante.iloc[0]["apellido_materno"]
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
                if not tiene_registro:
                    try:
                        supabase.table("asistencia").insert({
                            "ru": ru,
                            "nombres": nombres,
                            "apellido_paterno": paterno,
                            "apellido_materno": materno,
                            "fecha": fecha.isoformat(),
                            "hora": hora,
                            "estado": "Presente"
                        }).execute()
                        st.session_state.ultimo_registro = {"ru": ru, "nombres": nombres, "hora": hora, "fecha": fecha}
                        st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                    except Exception as e:
                        st.error(f"❌ Error al guardar asistencia: {e}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} YA REGISTRÓ ASISTENCIA HOY A LAS {registro_existente['hora']}")
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
        estudiantes["nombre_completo"] = estudiantes["ru"].astype(str) + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
        col1, col2 = st.columns(2)
        with col1:
            seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
            ru = seleccionado.split(" - ")[0]
        with col2:
            estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
        fecha, hora = obtener_fecha_hora_exacta()
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        if tiene_registro:
            st.warning(f"⚠️ Este estudiante ya registró hoy a las {registro_existente['hora']} (Estado: {registro_existente['estado']})")
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
            st.caption("Botón deshabilitado - Registro duplicado")
        else:
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("✅ Registrar asistencia", use_container_width=True):
                    estudiante = estudiantes[estudiantes["ru"].astype(str) == ru].iloc[0]
                    nombres = estudiante["nombres"]
                    paterno = estudiante["apellido_paterno"]
                    materno = estudiante["apellido_materno"]
                    try:
                        supabase.table("asistencia").insert({
                            "ru": ru,
                            "nombres": nombres,
                            "apellido_paterno": paterno,
                            "apellido_materno": materno,
                            "fecha": fecha.isoformat(),
                            "hora": hora,
                            "estado": estado
                        }).execute()
                        st.session_state.ultimo_registro = {"ru": ru, "nombres": nombres, "hora": hora, "fecha": fecha}
                        st.success(f"✅ Asistencia registrada a las {hora}")
                    except Exception as e:
                        st.error(f"❌ Error al guardar asistencia: {e}")
    else:
        st.warning("⚠️ No hay estudiantes registrados en el sistema")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    asistencia = leer_asistencia()
    if len(asistencia) > 0:
        # Mostrar tabla sin la columna id
        asistencia_mostrar = asistencia.copy()
        asistencia_mostrar['fecha'] = asistencia_mostrar['fecha'].astype(str)
        asistencia_mostrar['hora'] = asistencia_mostrar['hora'].astype(str)
        st.dataframe(asistencia_mostrar.drop(columns=['id']), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Verificación de integridad")
        duplicados = asistencia.groupby(['ru', 'fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        if len(duplicados) > 0:
            st.warning(f"⚠️ Se encontraron {len(duplicados)} casos de registros duplicados")
            if st.button("🧹 Limpiar duplicados (mantener primer registro)", use_container_width=True):
                try:
                    ids_a_conservar = asistencia.groupby(['ru', 'fecha'])['id'].first().tolist()
                    supabase.table("asistencia").delete().not_.in_("id", ids_a_conservar).execute()
                    st.success("✅ Duplicados eliminados correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al limpiar duplicados: {e}")
        else:
            st.success("✅ No hay registros duplicados en el sistema")
        
        st.markdown("---")
        st.subheader("✏️ Editar estado de registro")
        if len(asistencia) > 0:
            # Crear una descripción legible para el selector (no se muestra en tabla)
            asistencia["descripcion"] = (asistencia["ru"] + " - " + 
                                         asistencia["nombres"] + " " + 
                                         asistencia["apellido_paterno"] + " (" + 
                                         asistencia["fecha"].astype(str) + " " + 
                                         asistencia["hora"] + ")")
            opciones = asistencia["descripcion"].tolist()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                seleccion = st.selectbox("Selecciona un registro", opciones, key="select_asistencia")
                idx = asistencia[asistencia["descripcion"] == seleccion].index[0]
                id_registro = asistencia.loc[idx, "id"]
                estado_actual = asistencia.loc[idx, "estado"]
            with col2:
                nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"], 
                                            index=["Presente","Tarde","Permiso","Ausente"].index(estado_actual))
            
            if st.button("🔄 Actualizar estado", use_container_width=True):
                try:
                    supabase.table("asistencia").update({"estado": nuevo_estado}).eq("id", id_registro).execute()
                    st.success("✅ Estado actualizado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al actualizar: {e}")
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar todo el registro de asistencia")
        if st.button("⚠️ Eliminar TODOS los registros de asistencia", use_container_width=True):
            st.session_state.confirmar_eliminar_todo_asistencia = True
        
        if st.session_state.confirmar_eliminar_todo_asistencia:
            st.warning("⚠️ ¡Esta acción borrará TODOS los registros de asistencia! No se puede deshacer.")
            col_confirm1, col_confirm2, _ = st.columns([1,1,3])
            with col_confirm1:
                if st.button("✅ Sí, eliminar todos", key="confirm_eliminar_todo", use_container_width=True):
                    try:
                        supabase.table("asistencia").delete().neq("id", 0).execute()
                        st.success("✅ Todos los registros de asistencia han sido eliminados")
                        st.session_state.confirmar_eliminar_todo_asistencia = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al eliminar: {e}")
            with col_confirm2:
                if st.button("❌ No, cancelar", key="cancel_eliminar_todo", use_container_width=True):
                    st.session_state.confirmar_eliminar_todo_asistencia = False
                    st.rerun()
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar registro individual")
        if len(asistencia) > 0:
            # Usar la misma descripción para seleccionar individual
            seleccion_eliminar = st.selectbox("Selecciona un registro para eliminar", opciones, key="select_eliminar_asist")
            idx_elim = asistencia[asistencia["descripcion"] == seleccion_eliminar].index[0]
            id_eliminar = asistencia.loc[idx_elim, "id"]
            registro_info = asistencia.loc[idx_elim, "descripcion"]
            
            if st.button("🗑️ Eliminar este registro", use_container_width=True):
                st.session_state.confirmar_eliminar_asistencia = id_eliminar
            
            if st.session_state.confirmar_eliminar_asistencia:
                if st.session_state.confirmar_eliminar_asistencia == id_eliminar:
                    st.warning(f"⚠️ ¿Estás seguro de eliminar el registro **{registro_info}**?")
                    col_confirm1, col_confirm2, _ = st.columns([1,1,3])
                    with col_confirm1:
                        if st.button("✅ Sí, eliminar", key="confirm_eliminar_asist", use_container_width=True):
                            try:
                                supabase.table("asistencia").delete().eq("id", id_eliminar).execute()
                                st.success("✅ Registro eliminado correctamente")
                                st.session_state.confirmar_eliminar_asistencia = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {e}")
                    with col_confirm2:
                        if st.button("❌ No, cancelar", key="cancel_eliminar_asist", use_container_width=True):
                            st.session_state.confirmar_eliminar_asistencia = None
                            st.rerun()
        
        st.markdown("---")
        st.subheader("⬇️ Descargar asistencia del día")
        hoy = str(datetime.now(ZONA_HORARIA).date())
        asistencia_hoy = asistencia[asistencia["fecha"].astype(str) == hoy].copy()
        # Eliminar columnas innecesarias para el export (id y descripcion)
        columnas_a_eliminar = ["id", "descripcion"]
        for col in columnas_a_eliminar:
            if col in asistencia_hoy.columns:
                asistencia_hoy = asistencia_hoy.drop(columns=[col])
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga, use_container_width=True)
        else:
            st.info("📭 No hay registros para el día de hoy")
    else:
        st.info("📭 No hay registros de asistencia en el sistema")
