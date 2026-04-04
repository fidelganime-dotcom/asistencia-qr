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
from pyzbar.pyzbar import decode

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
            df = df.sort_values(by="id", ascending=True).reset_index(drop=True)
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
st.set_page_config(page_title="Sistemas UAP | Asistencia QR", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")

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
if "manual_auth" not in st.session_state:
    st.session_state.manual_auth = False
if "selected_student_manual" not in st.session_state:
    st.session_state.selected_student_manual = None

# ------------------------------------------------------------
# ESTILOS GLOBALES MODERNOS (FULL REDISEÑO)
# ------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, .stApp {
        background: radial-gradient(circle at 10% 20%, #0a0f1e, #03050b);
        font-family: 'Inter', sans-serif;
        color: #f1f5f9;
    }

    /* Scrollbar elegante */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #2563eb, #0891b2);
    }

    /* Contenedor principal con max-width para móvil */
    .main .block-container {
        padding: 1.2rem 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Títulos con efecto neón */
    h1, h2, h3, .custom-title {
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    h1::after, h2::after {
        display: none;
    }
    .subtitle-script {
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 400;
        border-left: 3px solid #3b82f6;
        padding-left: 12px;
        margin-top: -5px;
    }

    /* Navegación estilo moderno (segmented control) */
    .stRadio > div {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5rem;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        border-radius: 48px;
        padding: 0.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(59,130,246,0.3);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .stRadio > div label {
        background: transparent;
        border-radius: 40px;
        padding: 0.5rem 1.2rem;
        font-weight: 500;
        font-size: 0.85rem;
        color: #cbd5e1;
        transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .stRadio > div label:hover {
        background: rgba(59,130,246,0.2);
        color: white;
        transform: translateY(-2px);
    }
    .stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        box-shadow: 0 4px 12px rgba(59,130,246,0.4);
        text-shadow: 0 0 2px rgba(0,0,0,0.2);
    }
    /* Ocultar el círculo del radio */
    .stRadio > div label input {
        display: none;
    }

    /* Tarjetas con efecto glassmorphism + hover */
    .info-card, .student-info, .stDataFrame, .student-search-card, .student-detail-card, .password-modal {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(16px);
        border-radius: 28px;
        border: 1px solid rgba(59,130,246,0.25);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    .info-card:hover, .student-info:hover, .student-search-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
        box-shadow: 0 20px 35px -10px rgba(59,130,246,0.4);
    }

    /* Botones modernos con gradiente y animación */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6, #1e40af);
        border: none;
        border-radius: 40px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        font-size: 0.9rem;
        color: white;
        transition: all 0.25s ease;
        box-shadow: 0 6px 14px rgba(0,0,0,0.3);
        width: 100%;
        cursor: pointer;
        letter-spacing: 0.3px;
    }
    .stButton button:hover {
        transform: scale(1.02) translateY(-2px);
        background: linear-gradient(135deg, #2563eb, #1e3a8a);
        box-shadow: 0 12px 20px rgba(59,130,246,0.4);
    }
    .stButton button:active {
        transform: scale(0.98);
    }

    /* Inputs con borde luminoso */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: rgba(0,0,0,0.4);
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 0.7rem 1rem;
        color: #f1f5f9;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
        outline: none;
    }

    /* Tabla de datos (DataFrame) elegante */
    .stDataFrame {
        padding: 0;
        overflow-x: auto;
        border-radius: 24px;
    }
    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }
    .stDataFrame thead tr th {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #e2e8f0;
        font-weight: 600;
        padding: 12px 10px;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stDataFrame tbody tr {
        border-bottom: 1px solid rgba(255,255,255,0.05);
        transition: background 0.2s;
    }
    .stDataFrame tbody tr:hover {
        background: rgba(59,130,246,0.1);
    }
    .stDataFrame tbody td {
        padding: 10px 8px;
        color: #cbd5e1;
    }

    /* Dashboard cards compactas */
    .dashboard-compact {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1rem 0;
    }
    .dashboard-card {
        flex: 1;
        min-width: 130px;
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(12px);
        border-radius: 28px;
        padding: 1rem 0.8rem;
        text-align: center;
        border: 1px solid rgba(59,130,246,0.3);
        transition: all 0.2s;
    }
    .dashboard-card:hover {
        transform: translateY(-4px);
        border-color: #3b82f6;
    }
    .dashboard-card .title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
        margin-bottom: 0.4rem;
    }
    .dashboard-card .value {
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.2;
        color: white;
    }
    .dashboard-card .percentage {
        font-size: 0.7rem;
        color: #94a3b8;
    }
    .progress-bar-bg {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        height: 6px;
        width: 100%;
        margin-top: 10px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 20px;
        transition: width 0.5s ease;
    }
    .green-card .progress-bar-fill { background: linear-gradient(90deg, #10b981, #34d399); }
    .blue-card .progress-bar-fill { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .orange-card .progress-bar-fill { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

    /* Cámara y QR */
    div[data-testid="stCameraInput"] video {
        border-radius: 28px;
        border: 2px solid #3b82f6;
        box-shadow: 0 0 15px rgba(59,130,246,0.3);
    }
    .qr-container img {
        border-radius: 24px;
        background: white;
        padding: 8px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
    }

    /* Mensajes de éxito/error con animación */
    .stAlert {
        border-radius: 20px !important;
        backdrop-filter: blur(12px) !important;
        background: rgba(15,23,42,0.9) !important;
        border-left: 4px solid #3b82f6 !important;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Modal de contraseña centrado */
    .password-modal {
        max-width: 400px;
        margin: 2rem auto;
        text-align: center;
    }

    /* Ajustes móviles */
    @media (max-width: 640px) {
        .stRadio > div label {
            padding: 0.4rem 0.9rem;
            font-size: 0.7rem;
        }
        .dashboard-card .value {
            font-size: 1.3rem;
        }
        .stButton button {
            padding: 0.5rem 1rem;
        }
    }

    /* Partículas flotantes sutiles */
    .particle {
        position: fixed;
        background: radial-gradient(circle, #3b82f6, #06b6d4);
        border-radius: 50%;
        pointer-events: none;
        z-index: -1;
        opacity: 0.2;
    }
</style>
<script>
    function addParticles() {
        const body = document.body;
        for(let i=0; i<50; i++) {
            let particle = document.createElement('div');
            particle.classList.add('particle');
            let size = Math.random() * 4 + 2;
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `float ${Math.random() * 10 + 8}s infinite ease-in-out`;
            body.appendChild(particle);
        }
    }
    const styleSheet = document.createElement("style");
    styleSheet.textContent = `
        @keyframes float {
            0% { transform: translateY(0px) rotate(0deg); opacity: 0.2; }
            50% { transform: translateY(-20px) rotate(180deg); opacity: 0.6; }
            100% { transform: translateY(0px) rotate(360deg); opacity: 0.2; }
        }
    `;
    document.head.appendChild(styleSheet);
    window.addEventListener('load', addParticles);
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# CABECERA CON LOGO
# ------------------------------------------------------------
logo_path = "assets/logo.png"
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=70)
    else:
        st.markdown('<i class="fas fa-university" style="font-size: 48px; color: #3b82f6;"></i>', unsafe_allow_html=True)
with col_titulo:
    st.markdown("""
    <div>
        <h1 style="margin:0;">INGENIERÍA DE SISTEMAS</h1>
        <p class="subtitle-script">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# MENÚ HORIZONTAL MODERNO (con iconos)
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
# FUNCIÓN PARA CREAR TARJETA EJECUTIVA (sin cambios)
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    ru = str(estudiante["ru"])
    nombres = estudiante["nombres"]
    paterno = estudiante["apellido_paterno"]
    materno = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    qr = qrcode.make(ru, box_size=10, border=2)
    qr_size = 920
    qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

    card_size = 1000
    background = Image.new('RGB', (card_size, card_size), color=(10, 20, 40))
    gradient = Image.new('RGBA', (card_size, card_size), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(card_size):
        blue_intensity = int(60 * (1 - y / card_size))
        draw_grad.rectangle([0, y, card_size, y+1], fill=(0, 0, blue_intensity, 180))
    background = Image.alpha_composite(background.convert('RGBA'), gradient).convert('RGB')
    
    draw = ImageDraw.Draw(background)

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
            title_font = ImageFont.truetype(path, 88)
            ru_font = ImageFont.truetype(path, 50)
            name_font = ImageFont.truetype(path, 66)
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

    border_color = (0, 102, 255)
    border_width = 8
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    title_text = nombre_completo
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 15
    draw.text((title_x+3, title_y+3), title_text, fill=(0,0,0,128), font=title_font)
    draw.text((title_x, title_y), title_text, fill=(255,255,255), font=title_font)

    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 20
    draw.text((ru_x+2, ru_y+2), ru_text, fill=(0,0,0,128), font=ru_font)
    draw.text((ru_x, ru_y), ru_text, fill=(255,255,200), font=ru_font)

    max_width = card_size - 60
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

    line_spacing = 10
    total_height = len(lines) * line_spacing
    start_y = ru_y + 30
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        draw.text((x+2, y+2), line, fill=(0,0,0,128), font=name_font)
        draw.text((x, y), line, fill=(355,355,355), font=name_font)

    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height -15
    background.paste(qr, (qr_x, qr_y))

    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 30
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 36
        draw.text((x+2, y+2), line, fill=(0,0,0,128), font=footer_font)
        draw.text((x, y), line, fill=(220, 220, 255), font=footer_font)

    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE (diseño mejorado)
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.subheader("📝 Registrar nuevo estudiante")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            ru = st.text_input("🔢 RU", placeholder="Ej: 202412345")
            nombres = st.text_input("👤 Nombres", placeholder="Nombres completos")
        with col2:
            paterno = st.text_input("👨 Apellido paterno", placeholder="Primer apellido")
            materno = st.text_input("👩 Apellido materno", placeholder="Segundo apellido")
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
                                st.markdown(f'<div class="qr-info" style="font-weight:700; text-align:center; color:#3b82f6;">{nombre_upper}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div style="text-align:center; margin-bottom:10px;">RU: {ru}</div>', unsafe_allow_html=True)
                                st.image(img_bytes, width=300)
                                buf = io.BytesIO()
                                qr_img.save(buf, format="PNG")
                                buf.seek(0)
                                st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error al guardar estudiante: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# LISTA ESTUDIANTES (con diseño mejorado)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        st.markdown("---")
        
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
                    <div class="student-name" style="font-size:1.8rem; font-weight:700;">{nombre_completo}</div>
                    <div class="student-ru">RU: {ru}</div>
                    <div class="qr-container">
                        <img src="data:image/png;base64,{qr_base64}" width="250" alt="QR Code">
                    </div>
                    <div class="download-buttons" style="display:flex; gap:12px; justify-content:center; margin-top:15px;">
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
                with col_btn1:
                    st.download_button(
                        label="📥 QR",
                        data=qr_buffer.getvalue(),
                        file_name=f"{ru}_qr.png",
                        mime="image/png",
                        key="download_qr_search",
                        use_container_width=True
                    )
                with col_btn2:
                    tarjeta_img = crear_tarjeta_estudiante(estudiante_data)
                    st.download_button(
                        label="📇 Tarjeta",
                        data=tarjeta_img,
                        file_name=f"tarjeta_{ru}.png",
                        mime="image/png",
                        key="download_tarjeta_search",
                        use_container_width=True
                    )
                with col_btn3:
                    st.write("")
            else:
                st.warning("⚠️ RU no encontrado")
        elif buscar_click and not ru_ver:
            st.warning("⚠️ Ingrese un RU")
        
        st.markdown("---")
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
                submit_actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
            with col_btn2:
                submit_eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
        
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
                            st.error("❌ El nuevo RU ya existe")
                            st.stop()
                    supabase.table("estudiantes").update({
                        "ru": nuevo_ru,
                        "nombres": nuevos_nombres,
                        "apellido_paterno": nuevo_paterno,
                        "apellido_materno": nuevo_materno
                    }).eq("ru", ru_seleccionado).execute()
                    
                    if nuevo_ru != ru_seleccionado:
                        supabase.table("asistencia").update({"ru": nuevo_ru}).eq("ru", ru_seleccionado).execute()
                    
                    st.success("✅ Estudiante actualizado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        if submit_eliminar:
            st.session_state.confirmar_eliminar = ru_seleccionado
        
        if st.session_state.confirmar_eliminar:
            ru_eliminar = st.session_state.confirmar_eliminar
            estudiante_eliminar = estudiantes[estudiantes["ru"] == ru_eliminar].iloc[0]
            nombre_eliminar = f"{estudiante_eliminar['nombres']} {estudiante_eliminar['apellido_paterno']}"
            st.warning(f"⚠️ ¿Eliminar a **{nombre_eliminar} (RU: {ru_eliminar})**? También se borrarán sus asistencias.")
            col_confirm1, col_confirm2, _ = st.columns([1,1,3])
            with col_confirm1:
                if st.button("✅ Sí, eliminar", key="confirm_eliminar", use_container_width=True):
                    try:
                        supabase.table("asistencia").delete().eq("ru", ru_eliminar).execute()
                        supabase.table("estudiantes").delete().eq("ru", ru_eliminar).execute()
                        st.success("✅ Eliminado correctamente")
                        st.session_state.confirmar_eliminar = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            with col_confirm2:
                if st.button("❌ No, cancelar", key="cancel_eliminar", use_container_width=True):
                    st.session_state.confirmar_eliminar = None
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
# ESCANEAR QR (mejorado visualmente)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: #94a3b8;">Toma una foto del código QR del estudiante</p>', unsafe_allow_html=True)
    foto = st.camera_input("", label_visibility="collapsed")
    if foto is not None:
        img = Image.open(foto)
        decoded_objects = decode(img)
        
        if decoded_objects:
            data = decoded_objects[0].data.decode('utf-8')
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
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} ya registró hoy a las {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó ningún código QR")

# ------------------------------------------------------------
# REGISTRO MANUAL (con modal de contraseña mejorado)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        with st.container():
            st.markdown("""
            <div class="password-modal">
                <i class="fas fa-lock" style="font-size: 48px; color: #3b82f6;"></i>
                <h3>🔒 Acceso restringido</h3>
                <p style="color: #94a3b8;">Ingrese la contraseña para registrar asistencia manual</p>
            </div>
            """, unsafe_allow_html=True)
            with st.form(key="password_form"):
                password = st.text_input("Contraseña", type="password", placeholder="********")
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    submit_password = st.form_submit_button("🔓 Ingresar", use_container_width=True)
            if submit_password:
                if password == "pocoyo123":
                    st.session_state.manual_auth = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
    else:
        st.subheader("✍️ Registrar asistencia manual")
        estudiantes = leer_estudiantes()
        if len(estudiantes) > 0:
            estudiantes["nombre_completo"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            opciones = estudiantes["nombre_completo"].tolist()
            
            seleccionado = st.selectbox("👤 Seleccionar estudiante", opciones, key="select_manual")
            
            if seleccionado:
                ru_seleccionado = seleccionado.split(" - ")[0]
                estudiante_data = estudiantes[estudiantes["ru"].astype(str) == ru_seleccionado].iloc[0]
                
                st.markdown(f"""
                <div class="student-detail-card">
                    <h4>📋 Datos del estudiante</h4>
                    <p><strong>RU:</strong> {estudiante_data['ru']}</p>
                    <p><strong>Nombres:</strong> {estudiante_data['nombres']}</p>
                    <p><strong>Apellido Paterno:</strong> {estudiante_data['apellido_paterno']}</p>
                    <p><strong>Apellido Materno:</strong> {estudiante_data['apellido_materno']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru_seleccionado, fecha)
                
                if tiene_registro:
                    st.warning(f"⚠️ Ya registró hoy a las {registro_existente['hora']} (Estado: {registro_existente['estado']})")
                    col1, col2, col3 = st.columns([1,2,1])
                    with col2:
                        st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
                else:
                    col1, col2, col3 = st.columns([1,2,1])
                    with col2:
                        if st.button("✅ Registrar asistencia", use_container_width=True):
                            try:
                                supabase.table("asistencia").insert({
                                    "ru": ru_seleccionado,
                                    "nombres": estudiante_data["nombres"],
                                    "apellido_paterno": estudiante_data["apellido_paterno"],
                                    "apellido_materno": estudiante_data["apellido_materno"],
                                    "fecha": fecha.isoformat(),
                                    "hora": hora,
                                    "estado": estado
                                }).execute()
                                st.session_state.ultimo_registro = {"ru": ru_seleccionado, "nombres": estudiante_data["nombres"], "hora": hora, "fecha": fecha}
                                st.success(f"✅ Asistencia registrada a las {hora}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
            else:
                st.info("👆 Selecciona un estudiante")
        else:
            st.warning("⚠️ No hay estudiantes registrados")

# ------------------------------------------------------------
# VER ASISTENCIA (dashboard mejorado)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📊 Registros de asistencia")
    
    estudiantes_total = leer_estudiantes()
    total_estudiantes = len(estudiantes_total)
    asistencia_df = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    registrados_hoy = asistencia_df[asistencia_df["fecha"] == hoy]["ru"].nunique()
    faltantes = total_estudiantes - registrados_hoy
    
    if total_estudiantes > 0:
        porcentaje_registrados = (registrados_hoy / total_estudiantes * 100)
        porcentaje_faltantes = (faltantes / total_estudiantes * 100)
    else:
        porcentaje_registrados = 0
        porcentaje_faltantes = 0
    
    st.markdown(f"""
    <div class="dashboard-compact">
        <div class="dashboard-card green-card">
            <div class="title"><i class="fas fa-users"></i> Total estudiantes</div>
            <div class="value">{total_estudiantes}</div>
            <div class="percentage">100%</div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:100%"></div></div>
        </div>
        <div class="dashboard-card blue-card">
            <div class="title"><i class="fas fa-check-circle"></i> Ya registrados</div>
            <div class="value">{registrados_hoy}</div>
            <div class="percentage">{porcentaje_registrados:.1f}%</div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:{porcentaje_registrados}%"></div></div>
        </div>
        <div class="dashboard-card orange-card">
            <div class="title"><i class="fas fa-hourglass-half"></i> Faltantes</div>
            <div class="value">{faltantes}</div>
            <div class="percentage">{porcentaje_faltantes:.1f}%</div>
            <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:{porcentaje_faltantes}%"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(asistencia_df) > 0:
        asistencia_mostrar = asistencia_df.copy()
        asistencia_mostrar['fecha'] = asistencia_mostrar['fecha'].astype(str)
        asistencia_mostrar['hora'] = asistencia_mostrar['hora'].astype(str)
        st.dataframe(asistencia_mostrar.drop(columns=['id']), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Verificación de integridad")
        duplicados = asistencia_df.groupby(['ru', 'fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        if len(duplicados) > 0:
            st.warning(f"⚠️ Se encontraron {len(duplicados)} registros duplicados")
            if st.button("🧹 Limpiar duplicados (mantener primer registro)", use_container_width=True):
                try:
                    ids_a_conservar = asistencia_df.groupby(['ru', 'fecha'])['id'].first().tolist()
                    supabase.table("asistencia").delete().not_.in_("id", ids_a_conservar).execute()
                    st.success("✅ Duplicados eliminados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.success("✅ No hay registros duplicados")
        
        st.markdown("---")
        st.subheader("✏️ Editar estado de registro")
        if len(asistencia_df) > 0:
            asistencia_df["descripcion"] = (asistencia_df["ru"] + " - " + 
                                           asistencia_df["nombres"] + " " + 
                                           asistencia_df["apellido_paterno"] + " (" + 
                                           asistencia_df["fecha"].astype(str) + " " + 
                                           asistencia_df["hora"] + ")")
            opciones = asistencia_df["descripcion"].tolist()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                seleccion = st.selectbox("Selecciona un registro", opciones, key="select_asistencia")
                idx = asistencia_df[asistencia_df["descripcion"] == seleccion].index[0]
                id_registro = asistencia_df.loc[idx, "id"]
                estado_actual = asistencia_df.loc[idx, "estado"]
            with col2:
                nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"], 
                                            index=["Presente","Tarde","Permiso","Ausente"].index(estado_actual))
            
            if st.button("🔄 Actualizar estado", use_container_width=True):
                try:
                    supabase.table("asistencia").update({"estado": nuevo_estado}).eq("id", id_registro).execute()
                    st.success("✅ Estado actualizado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar todo el registro de asistencia")
        if st.button("⚠️ Eliminar TODOS los registros", use_container_width=True):
            st.session_state.confirmar_eliminar_todo_asistencia = True
        
        if st.session_state.confirmar_eliminar_todo_asistencia:
            st.warning("⚠️ ¡Esta acción borrará TODOS los registros de asistencia! No se puede deshacer.")
            col_confirm1, col_confirm2, _ = st.columns([1,1,3])
            with col_confirm1:
                if st.button("✅ Sí, eliminar todos", key="confirm_eliminar_todo", use_container_width=True):
                    try:
                        supabase.table("asistencia").delete().neq("id", 0).execute()
                        st.success("✅ Todos los registros eliminados")
                        st.session_state.confirmar_eliminar_todo_asistencia = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            with col_confirm2:
                if st.button("❌ No, cancelar", key="cancel_eliminar_todo", use_container_width=True):
                    st.session_state.confirmar_eliminar_todo_asistencia = False
                    st.rerun()
        
        st.markdown("---")
        st.subheader("🗑️ Eliminar registro individual")
        if len(asistencia_df) > 0:
            seleccion_eliminar = st.selectbox("Selecciona un registro para eliminar", opciones, key="select_eliminar_asist")
            idx_elim = asistencia_df[asistencia_df["descripcion"] == seleccion_eliminar].index[0]
            id_eliminar = asistencia_df.loc[idx_elim, "id"]
            registro_info = asistencia_df.loc[idx_elim, "descripcion"]
            
            if st.button("🗑️ Eliminar este registro", use_container_width=True):
                st.session_state.confirmar_eliminar_asistencia = id_eliminar
            
            if st.session_state.confirmar_eliminar_asistencia:
                if st.session_state.confirmar_eliminar_asistencia == id_eliminar:
                    st.warning(f"⚠️ ¿Eliminar el registro **{registro_info}**?")
                    col_confirm1, col_confirm2, _ = st.columns([1,1,3])
                    with col_confirm1:
                        if st.button("✅ Sí, eliminar", key="confirm_eliminar_asist", use_container_width=True):
                            try:
                                supabase.table("asistencia").delete().eq("id", id_eliminar).execute()
                                st.success("✅ Registro eliminado")
                                st.session_state.confirmar_eliminar_asistencia = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    with col_confirm2:
                        if st.button("❌ No, cancelar", key="cancel_eliminar_asist", use_container_width=True):
                            st.session_state.confirmar_eliminar_asistencia = None
                            st.rerun()
        
        st.markdown("---")
        st.subheader("⬇️ Descargar asistencia del día")
        hoy_str = str(hoy)
        asistencia_hoy = asistencia_df[asistencia_df["fecha"].astype(str) == hoy_str].copy()
        columnas_a_eliminar = ["id", "descripcion"]
        for col in columnas_a_eliminar:
            if col in asistencia_hoy.columns:
                asistencia_hoy = asistencia_hoy.drop(columns=[col])
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy_str}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel del día", data=file, file_name=archivo_descarga, use_container_width=True)
        else:
            st.info("📭 No hay registros para hoy")
    else:
        st.info("📭 No hay registros de asistencia en el sistema")
