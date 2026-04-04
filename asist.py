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
st.set_page_config(page_title="Sistema de Asistencia Premium", layout="wide", initial_sidebar_state="expanded")

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
# ESTILOS CSS - DISEÑO PREMIUM VERDE PLOMO / ESMERALDA / TURQUESA / PÚRPURA
# ------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&display=swap');
    
    :root {
        --verde-plomo: #2d6a4f;
        --verde-esmeralda: #40916c;
        --verde-menta: #95d5b2;
        --turquesa: #74c69d;
        --purpura: #7b2cbf;
        --purpura-claro: #9d4edd;
        --dorado: #ffd60a;
        --dorado-suave: #ffea8c;
        --fondo-oscuro: #0a0c10;
        --fondo-card: rgba(13, 17, 23, 0.85);
        --texto-primario: #e8f0fe;
        --texto-secundario: #a8c7bb;
        --glass-border: rgba(64, 145, 108, 0.25);
        --gradiente-verde: linear-gradient(135deg, #2d6a4f 0%, #52b788 50%, #74c69d 100%);
        --gradiente-purpura: linear-gradient(135deg, #7b2cbf 0%, #9d4edd 50%, #c77dff 100%);
        --gradiente-dorado: linear-gradient(135deg, #ffd60a 0%, #ffea8c 50%, #fff3b0 100%);
        --shadow-premium: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(64, 145, 108, 0.2);
        --shadow-neon-verde: 0 0 20px rgba(82, 183, 136, 0.3);
        --shadow-neon-purpura: 0 0 20px rgba(123, 44, 191, 0.3);
        --shadow-hover: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(82, 183, 136, 0.4);
    }

    .stApp {
        background: linear-gradient(135deg, #0a0c10 0%, #0f1218 50%, #0d1117 100%);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Efecto de partículas en el fondo */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: radial-gradient(circle at 25% 40%, rgba(82, 183, 136, 0.08) 0%, transparent 50%),
                          radial-gradient(circle at 75% 60%, rgba(157, 78, 221, 0.06) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* Mensajes de éxito premium */
    .stAlert[data-testid="stAlert"] {
        background: linear-gradient(135deg, rgba(45, 106, 79, 0.2), rgba(82, 183, 136, 0.1)) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(82, 183, 136, 0.4) !important;
        border-radius: 20px !important;
        box-shadow: var(--shadow-neon-verde) !important;
        animation: slideInDown 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1) !important;
        color: #b8f2d0 !important;
    }

    @keyframes slideInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Sidebar premium */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 12, 16, 0.95) 0%, rgba(13, 17, 23, 0.95) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
        box-shadow: 5px 0 30px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--texto-primario) !important;
    }

    /* Títulos con efecto neón */
    h1, h2, h3 {
        background: var(--gradiente-verde);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        font-weight: 800;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(82, 183, 136, 0.3);
        position: relative;
        display: inline-block;
    }

    h1::after, h2::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 60px;
        height: 3px;
        background: var(--gradiente-verde);
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    h1:hover::after, h2:hover::after {
        width: 100%;
    }

    .subtitle-script {
        background: var(--gradiente-dorado);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        font-family: 'Inter', cursive;
        font-size: 1rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* Tarjetas premium */
    .info-card, .student-info, .stDataFrame, .student-search-card, .student-detail-card, .password-modal {
        background: var(--fondo-card) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 28px !important;
        border: 1px solid var(--glass-border) !important;
        box-shadow: var(--shadow-premium) !important;
        transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1) !important;
        position: relative;
        overflow: hidden;
    }

    .info-card:hover, .student-info:hover, .stDataFrame:hover, .student-search-card:hover {
        transform: translateY(-8px) scale(1.01);
        box-shadow: var(--shadow-hover);
        border-color: rgba(82, 183, 136, 0.5);
    }

    /* Efecto de brillo en tarjetas */
    .info-card::before, .student-info::before, .student-search-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(82, 183, 136, 0.1) 0%, transparent 70%);
        transform: rotate(30deg);
        transition: all 0.5s ease;
        opacity: 0;
        pointer-events: none;
    }

    .info-card:hover::before, .student-info:hover::before, .student-search-card:hover::before {
        opacity: 1;
        animation: shine 2s infinite;
    }

    @keyframes shine {
        0% { transform: rotate(30deg) translate(-10%, -10%); opacity: 0; }
        50% { opacity: 0.5; }
        100% { transform: rotate(30deg) translate(10%, 10%); opacity: 0; }
    }

    /* Menú horizontal premium */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.5rem;
        background: var(--fondo-card);
        backdrop-filter: blur(20px);
        padding: 0.5rem;
        border-radius: 60px;
        box-shadow: var(--shadow-premium);
        margin-bottom: 2rem;
        border: 1px solid var(--glass-border);
        flex-wrap: wrap;
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--texto-secundario);
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.85rem;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(82, 183, 136, 0.2);
        color: var(--verde-menta);
        transform: translateY(-2px);
    }

    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: var(--gradiente-verde);
        color: #0a0c10;
        box-shadow: var(--shadow-neon-verde);
        font-weight: 700;
    }

    /* Botones premium con gradientes */
    .stButton button {
        background: var(--gradiente-verde);
        color: #0a0c10;
        border: none;
        border-radius: 16px;
        padding: 0.7rem 1.8rem;
        font-weight: 700;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(45, 106, 79, 0.3);
        cursor: pointer;
    }

    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }

    .stButton button:hover::before {
        left: 100%;
    }

    .stButton button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(82, 183, 136, 0.4);
    }

    /* Inputs premium */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background: rgba(13, 17, 23, 0.8) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        color: var(--texto-primario) !important;
        padding: 0.8rem 1rem !important;
        backdrop-filter: blur(5px) !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus, .stTextArea textarea:focus {
        border-color: var(--verde-esmeralda) !important;
        box-shadow: 0 0 0 3px rgba(82, 183, 136, 0.2) !important;
        transform: scale(1.01);
    }

    /* Tablas premium */
    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }

    .stDataFrame thead tr th {
        background: var(--gradiente-verde) !important;
        color: #0a0c10 !important;
        font-weight: 700;
        padding: 1rem !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stDataFrame tbody tr {
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(64, 145, 108, 0.1);
    }

    .stDataFrame tbody tr:hover {
        background: rgba(82, 183, 136, 0.1) !important;
        transform: translateX(5px);
    }

    .stDataFrame tbody td {
        padding: 0.8rem 1rem !important;
        color: var(--texto-secundario) !important;
    }

    /* Dashboard de tres tarjetas premium */
    .dashboard-compact {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .dashboard-card {
        flex: 1;
        min-width: 120px;
        background: var(--fondo-card);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 1rem;
        text-align: center;
        border: 1px solid var(--glass-border);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-neon-verde);
    }

    .dashboard-card .title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .dashboard-card .value {
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.2;
    }

    .dashboard-card .percentage {
        font-size: 0.7rem;
        margin-top: 0.3rem;
    }

    .progress-bar-bg {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        height: 6px;
        width: 100%;
        margin-top: 0.8rem;
        overflow: hidden;
    }

    .progress-bar-fill {
        height: 100%;
        border-radius: 20px;
        transition: width 0.6s cubic-bezier(0.2, 0.9, 0.4, 1.1);
    }

    .green-card .progress-bar-fill {
        background: linear-gradient(90deg, var(--verde-plomo), var(--turquesa));
        box-shadow: 0 0 8px var(--turquesa);
    }
    .green-card .title, .green-card .value, .green-card .percentage { color: var(--verde-menta); }

    .purple-card .progress-bar-fill {
        background: linear-gradient(90deg, var(--purpura), var(--purpura-claro));
        box-shadow: 0 0 8px var(--purpura-claro);
    }
    .purple-card .title, .purple-card .value, .purple-card .percentage { color: #c77dff; }

    .gold-card .progress-bar-fill {
        background: linear-gradient(90deg, var(--dorado), var(--dorado-suave));
        box-shadow: 0 0 8px var(--dorado);
    }
    .gold-card .title, .gold-card .value, .gold-card .percentage { color: var(--dorado-suave); }

    .green-card { border-left: 3px solid var(--verde-esmeralda); }
    .purple-card { border-left: 3px solid var(--purpura); }
    .gold-card { border-left: 3px solid var(--dorado); }

    /* QR y contenedores */
    .qr-container img {
        border-radius: 24px;
        box-shadow: var(--shadow-premium);
        transition: all 0.3s ease;
        max-width: 100%;
        height: auto;
    }

    .qr-container img:hover {
        transform: scale(1.02);
        box-shadow: var(--shadow-neon-verde);
    }

    .qr-info, .student-name {
        background: var(--gradiente-verde);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent !important;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .qr-ru, .student-ru {
        color: var(--texto-secundario);
        font-weight: 500;
    }

    /* Cámara */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 60vh !important;
        object-fit: cover;
        border-radius: 24px;
        border: 2px solid var(--verde-esmeralda);
        box-shadow: var(--shadow-premium);
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(13, 17, 23, 0.8); border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: var(--gradiente-verde); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--gradiente-purpura); }

    /* Animaciones */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stAlert, .stButton, .stDataFrame, .info-card, .student-info, .student-search-card {
        animation: fadeInUp 0.5s ease-out;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .dashboard-card .value { font-size: 1.4rem; }
        .dashboard-card { min-width: 90px; padding: 0.7rem; }
        div.row-widget.stRadio > div label { padding: 0.4rem 0.8rem; font-size: 0.7rem; }
        .stButton button { padding: 0.5rem 1rem; font-size: 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS DE FONDO
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
        container.style.zIndex = '0';
        document.body.appendChild(container);
        
        const colors = ['#2d6a4f', '#40916c', '#52b788', '#74c69d', '#95d5b2', '#7b2cbf', '#9d4edd', '#ffd60a'];
        
        for (let i = 0; i < 60; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = (Math.random() * 4 + 2) + 'px';
            particle.style.height = particle.style.width;
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.borderRadius = '50%';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `float ${Math.random() * 8 + 6}s infinite ease-in-out`;
            particle.style.animationDelay = Math.random() * 10 + 's';
            particle.style.opacity = Math.random() * 0.4 + 0.2;
            particle.style.filter = 'blur(1px)';
            container.appendChild(particle);
        }
    }
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            25% { transform: translate(15px, -20px) rotate(45deg); }
            50% { transform: translate(-10px, -35px) rotate(90deg); }
            75% { transform: translate(20px, -15px) rotate(135deg); }
        }
    `;
    document.head.appendChild(style);
    window.addEventListener('load', createParticles);
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR PREMIUM
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="width: 60px; height: 60px; margin: 0 auto 1rem auto; background: var(--gradiente-verde); border-radius: 20px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 2rem;">✨</span>
        </div>
        <h3 style="font-size: 1.2rem;">Sistema Premium</h3>
        <p style="color: var(--texto-secundario); font-size: 0.8rem;">Asistencia Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📂 Desarrollado por")
    st.markdown('<p style="color: var(--verde-menta); font-weight: 600;">Josué</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--texto-secundario); font-size: 0.7rem;">Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO PRINCIPAL
# ------------------------------------------------------------
logo_path = "assets/logo.png"

with st.container():
    col_logo, col_texto = st.columns([1, 8])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=80)
        else:
            st.markdown('<div style="width: 60px; height: 60px; background: var(--gradiente-verde); border-radius: 18px; display: flex; align-items: center; justify-content: center;"><span style="font-size: 2rem;">🎓</span></div>', unsafe_allow_html=True)
    with col_texto:
        st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <h1 style="margin: 0; line-height: 1.2;">INGENIERÍA DE SISTEMAS</h1>
            <p class="subtitle-script">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>
        </div>
        """, unsafe_allow_html=True)

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
# FUNCIÓN PARA CREAR TARJETA CUADRADA (VERSIÓN PREMIUM)
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
    background = Image.new('RGB', (card_size, card_size), color=(10, 12, 16))
    
    # Gradiente premium verde
    gradient = Image.new('RGBA', (card_size, card_size), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(card_size):
        green_intensity = int(80 * (1 - y / card_size))
        purple_intensity = int(40 * (y / card_size))
        draw_grad.rectangle([0, y, card_size, y+1], fill=(45, 106, 79, green_intensity))
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

    # Borde dorado
    border_color = (255, 214, 10)
    border_width = 8
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    title_text = nombre_completo
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 15
    draw.text((title_x+3, title_y+3), title_text, fill=(0,0,0,128), font=title_font)
    draw.text((title_x, title_y), title_text, fill=(82, 183, 136), font=title_font)

    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 100
    draw.text((ru_x+2, ru_y+2), ru_text, fill=(0,0,0,128), font=ru_font)
    draw.text((ru_x, ru_y), ru_text, fill=(255, 218, 10), font=ru_font)

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

    line_spacing = 85
    total_height = len(lines) * line_spacing
    start_y = ru_y + 80
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        draw.text((x+2, y+2), line, fill=(0,0,0,128), font=name_font)
        draw.text((x, y), line, fill=(200, 230, 220), font=name_font)

    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height - 40
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
        draw.text((x, y), line, fill=(180, 200, 190), font=footer_font)

    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
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
                                st.markdown(f'<div class="qr-info" style="text-align: center; font-size: 1.5rem;">{nombre_upper}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="qr-ru" style="text-align: center;">RU: {ru}</div>', unsafe_allow_html=True)
                                st.image(img_bytes, width=400, caption="Código QR del estudiante")
                                buf = io.BytesIO()
                                qr_img.save(buf, format="PNG")
                                buf.seek(0)
                                st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error al guardar estudiante: {e}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
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
                <div class="student-search-card" style="padding: 2rem; text-align: center;">
                    <div class="student-name" style="font-size: 1.8rem;">{nombre_completo}</div>
                    <div class="student-ru" style="font-size: 1.2rem;">RU: {ru}</div>
                    <div class="qr-container" style="margin: 1.5rem 0;">
                        <img src="data:image/png;base64,{qr_base64}" width="400" alt="QR Code">
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
        
        st.subheader("⬇️ Descargar Excel estudiantes")
        if len(estudiantes) > 0:
            archivo_descarga = "registro_estudiantes_temp.xlsx"
            estudiantes.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel completo", data=file, file_name="estudiantes_exportados.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR (MEJORADO CON pyzbar)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: var(--texto-secundario);">Toma una foto del código QR del estudiante para registrar su asistencia</p>', unsafe_allow_html=True)
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
                        st.error(f"❌ Error al guardar asistencia: {e}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} YA REGISTRÓ ASISTENCIA HOY A LAS {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado en la base de datos")
        else:
            st.warning("⚠️ No se detectó ningún código QR en la imagen")

# ------------------------------------------------------------
# REGISTRO MANUAL (CON PROTECCIÓN DE CONTRASEÑA)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        with st.container():
            st.markdown("""
            <div class="password-modal" style="max-width: 450px; margin: 2rem auto; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                <h3 style="background: var(--gradiente-purpura); -webkit-background-clip: text; background-clip: text; color: transparent;">Acceso restringido</h3>
                <p style="color: var(--texto-secundario);">Ingrese la contraseña para registrar asistencia manual</p>
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
                <div class="student-detail-card" style="padding: 1.5rem;">
                    <h4 style="background: var(--gradiente-verde); -webkit-background-clip: text; background-clip: text; color: transparent;">📋 Datos del estudiante</h4>
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
                    st.warning(f"⚠️ Este estudiante ya registró hoy a las {registro_existente['hora']} (Estado: {registro_existente['estado']})")
                    col1, col2, col3 = st.columns([1,2,1])
                    with col2:
                        st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
                    st.caption("Botón deshabilitado - Registro duplicado")
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
                                st.error(f"❌ Error al guardar asistencia: {e}")
            else:
                st.info("👆 Selecciona un estudiante de la lista")
        else:
            st.warning("⚠️ No hay estudiantes registrados en el sistema")

# ------------------------------------------------------------
# VER ASISTENCIA (con dashboard de tres tarjetas premium)
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
    
    # Dashboard premium con tres tarjetas coloridas
    st.markdown(f"""
    <div class="dashboard-compact">
        <div class="dashboard-card green-card">
            <div class="title">📋 Total estudiantes</div>
            <div class="value">{total_estudiantes}</div>
            <div class="percentage">100% del sistema</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: 100%;"></div>
            </div>
        </div>
        <div class="dashboard-card purple-card">
            <div class="title">✅ Ya registrados</div>
            <div class="value">{registrados_hoy}</div>
            <div class="percentage">{porcentaje_registrados:.1f}% del total</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {porcentaje_registrados}%;"></div>
            </div>
        </div>
        <div class="dashboard-card gold-card">
            <div class="title">⏳ Faltantes</div>
            <div class="value">{faltantes}</div>
            <div class="percentage">{porcentaje_faltantes:.1f}% sin registrar</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {porcentaje_faltantes}%;"></div>
            </div>
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
            st.warning(f"⚠️ Se encontraron {len(duplicados)} casos de registros duplicados")
            if st.button("🧹 Limpiar duplicados (mantener primer registro)", use_container_width=True):
                try:
                    ids_a_conservar = asistencia_df.groupby(['ru', 'fecha'])['id'].first().tolist()
                    supabase.table("asistencia").delete().not_.in_("id", ids_a_conservar).execute()
                    st.success("✅ Duplicados eliminados correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al limpiar duplicados: {e}")
        else:
            st.success("✅ No hay registros duplicados en el sistema")
        
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
        if len(asistencia_df) > 0:
            seleccion_eliminar = st.selectbox("Selecciona un registro para eliminar", opciones, key="select_eliminar_asist")
            idx_elim = asistencia_df[asistencia_df["descripcion"] == seleccion_eliminar].index[0]
            id_eliminar = asistencia_df.loc[idx_elim, "id"]
            registro_info = asistencia_df.loc[idx_elim, "descripcion"]
            
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
        hoy_str = str(hoy)
        asistencia_hoy = asistencia_df[asistencia_df["fecha"].astype(str) == hoy_str].copy()
        columnas_a_eliminar = ["id", "descripcion"]
        for col in columnas_a_eliminar:
            if col in asistencia_hoy.columns:
                asistencia_hoy = asistencia_hoy.drop(columns=[col])
        if len(asistencia_hoy) > 0:
            asistencia_hoy['fecha'] = pd.to_datetime(asistencia_hoy['fecha']).dt.strftime('%d-%m-%Y')
            nombre_archivo = f"asistencia_{hoy.strftime('%d-%m-%Y')}.xlsx"
            asistencia_hoy.to_excel(nombre_archivo, index=False)
            with open(nombre_archivo, "rb") as file:
                st.download_button("📥 Descargar Excel del día", data=file, file_name=nombre_archivo, use_container_width=True)
        else:
            st.info("📭 No hay registros para el día de hoy")
    else:
        st.info("📭 No hay registros de asistencia en el sistema")
