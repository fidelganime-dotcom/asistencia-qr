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
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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
if "manual_auth" not in st.session_state:
    st.session_state.manual_auth = False
if "selected_student_manual" not in st.session_state:
    st.session_state.selected_student_manual = None

# ------------------------------------------------------------
# ESTILOS CSS (Dark + Glassmorphism + Neumorphism)
# ------------------------------------------------------------
st.markdown("""
<style>
    /* ========== DARK THEME + GLASS + NEUMORPH ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #111118;
        --bg-tertiary: #1a1a25;
        --glass-bg: rgba(26, 26, 37, 0.6);
        --glass-border: rgba(0, 255, 204, 0.15);
        --neon-green: #00ffcc;
        --neon-blue: #0066ff;
        --neon-purple: #9b59b6;
        --neon-pink: #ff6b6b;
        --text-primary: #ffffff;
        --text-secondary: #a0a0b0;
        --shadow-glow: 0 0 20px rgba(0, 255, 204, 0.2);
        --shadow-neu-outer: 20px 20px 40px rgba(0, 0, 0, 0.4), -10px -10px 20px rgba(255, 255, 255, 0.02);
        --shadow-neu-inner: inset 5px 5px 10px rgba(0, 0, 0, 0.3), inset -5px -5px 10px rgba(255, 255, 255, 0.02);
        --shadow-neu-card: 10px 10px 20px rgba(0, 0, 0, 0.3), -5px -5px 10px rgba(255, 255, 255, 0.02);
        --gradient-neon: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        --gradient-purple: linear-gradient(135deg, #9b59b6 0%, #0066ff 100%);
        --gradient-pink: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        --border-radius-xl: 28px;
        --border-radius-lg: 20px;
        --border-radius-md: 16px;
    }

    .stApp {
        background: radial-gradient(circle at 20% 30%, #0a0a0f 0%, #050508 100%);
        font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
    }

    /* ========== GLASSMORPHISM CARDS ========== */
    .glass-card, .stDataFrame, div[data-testid="stForm"], .student-search-card, .password-modal {
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        border-radius: var(--border-radius-xl);
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-neu-card);
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
    }

    .glass-card:hover, .stDataFrame:hover {
        transform: translateY(-4px);
        border-color: rgba(0, 255, 204, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), var(--shadow-glow);
    }

    /* Efecto de brillo en bordes */
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 204, 0.1), transparent);
        transition: left 0.8s;
        pointer-events: none;
    }

    .glass-card:hover::before {
        left: 100%;
    }

    /* ========== NEUMORPHIC BUTTONS ========== */
    .stButton button {
        background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
        color: var(--text-primary);
        border: none;
        border-radius: var(--border-radius-md);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        font-family: 'Space Grotesk', sans-serif;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-neu-outer);
        cursor: pointer;
        position: relative;
        overflow: hidden;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px rgba(0, 255, 204, 0.2), var(--shadow-neu-outer);
        background: linear-gradient(135deg, #00ffcc20, #0066ff20);
        border: 1px solid rgba(0, 255, 204, 0.3);
    }

    .stButton button:active {
        transform: translateY(1px);
        box-shadow: var(--shadow-neu-inner);
    }

    /* ========== KPI CARDS ========== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .kpi-card {
        background: linear-gradient(135deg, rgba(26, 26, 37, 0.8), rgba(17, 17, 24, 0.9));
        backdrop-filter: blur(12px);
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        border: 1px solid rgba(0, 255, 204, 0.2);
        box-shadow: var(--shadow-neu-card);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: var(--neon-green);
        box-shadow: 0 20px 40px rgba(0, 255, 204, 0.2);
    }

    .kpi-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: var(--gradient-neon);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin: 0.5rem 0;
    }

    .kpi-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }

    .kpi-trend {
        font-size: 0.8rem;
        margin-top: 0.5rem;
        color: var(--neon-green);
    }

    /* ========== MENU PÍLDORA NEUMORPHIC ========== */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 0.75rem;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        padding: 0.75rem;
        border-radius: 60px;
        box-shadow: var(--shadow-neu-outer);
        margin-bottom: 2rem;
        border: 1px solid var(--glass-border);
        flex-wrap: wrap;
    }

    div.row-widget.stRadio > div label {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.7rem 1.4rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.9rem;
        font-family: 'Space Grotesk', sans-serif;
    }

    div.row-widget.stRadio > div label:hover {
        background: rgba(0, 255, 204, 0.1);
        color: var(--neon-green);
        transform: translateY(-2px);
        box-shadow: var(--shadow-neu-outer);
    }

    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {
        background: var(--gradient-neon);
        color: #020617;
        box-shadow: 0 5px 15px rgba(0, 255, 204, 0.4);
        font-weight: 600;
    }

    /* ========== INPUTS NEUMORPHIC ========== */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextInput textarea {
        background: var(--bg-secondary) !important;
        border: 1px solid rgba(0, 255, 204, 0.2) !important;
        border-radius: var(--border-radius-md) !important;
        color: var(--text-primary) !important;
        padding: 0.8rem 1.2rem !important;
        box-shadow: inset 3px 3px 6px rgba(0, 0, 0, 0.3), inset -2px -2px 4px rgba(255, 255, 255, 0.02) !important;
        font-family: 'Space Grotesk', sans-serif;
    }

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--neon-green) !important;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3), inset 3px 3px 6px rgba(0, 0, 0, 0.3) !important;
    }

    /* ========== TABLAS MODERNAS ========== */
    .stDataFrame {
        padding: 0;
        overflow-x: auto;
    }

    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }

    .stDataFrame thead tr th {
        background: linear-gradient(135deg, #00ffcc20, #0066ff20) !important;
        color: var(--neon-green) !important;
        font-weight: 600;
        padding: 1rem !important;
        border: none !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stDataFrame tbody tr {
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(0, 255, 204, 0.1);
    }

    .stDataFrame tbody tr:hover {
        background: rgba(0, 255, 204, 0.05);
        transform: translateX(5px);
    }

    /* ========== TÍTULOS CON EFECTO NEON ========== */
    h1, h2, h3 {
        background: var(--gradient-neon);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: 700;
        letter-spacing: -0.02em;
        font-family: 'Space Grotesk', sans-serif;
    }

    h1 {
        font-size: 2.5rem;
        text-shadow: 0 0 30px rgba(0, 255, 204, 0.3);
    }

    /* ========== SCROLLBAR NEON ========== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--neon-green), var(--neon-blue));
        border-radius: 10px;
    }

    /* ========== ANIMACIONES ========== */
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 204, 0.4); }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .kpi-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        .kpi-value {
            font-size: 1.8rem;
        }
        div.row-widget.stRadio > div label {
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS NEON
# ------------------------------------------------------------
st.markdown("""
<script>
    function createNeonParticles() {
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '-1';
        document.body.appendChild(container);
        
        const colors = ['#00ffcc', '#0066ff', '#9b59b6', '#ff6b6b'];
        const particleCount = 100;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = (Math.random() * 4 + 1) + 'px';
            particle.style.height = particle.style.width;
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.borderRadius = '50%';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animation = `floatParticle ${Math.random() * 8 + 4}s infinite ease-in-out`;
            particle.style.animationDelay = Math.random() * 10 + 's';
            particle.style.opacity = Math.random() * 0.3 + 0.1;
            particle.style.filter = 'blur(2px)';
            container.appendChild(particle);
        }
    }
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes floatParticle {
            0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 0.1; }
            25% { transform: translate(15px, -20px) rotate(45deg); opacity: 0.3; }
            50% { transform: translate(-10px, -30px) rotate(90deg); opacity: 0.2; }
            75% { transform: translate(20px, -15px) rotate(135deg); opacity: 0.3; }
        }
    `;
    document.head.appendChild(style);
    window.addEventListener('load', createNeonParticles);
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🚀 Desarrollado por Josué")
    st.markdown('<p style="color: var(--text-secondary);">⚡ Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("✨ Sistema de Asistencia QR v2.0")

# ------------------------------------------------------------
# TÍTULO PRINCIPAL
# ------------------------------------------------------------
logo_path = "assets/logo.png"

col_logo, col_texto = st.columns([1, 6])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=70)
with col_texto:
    st.markdown("""
    <h1 style="margin: 0;">✨ SISTEMA DE ASISTENCIA QR</h1>
    <p style="color: var(--neon-green); margin-top: -5px; font-size: 0.9rem;">⚡ Dashboard Inteligente | Tiempo Real | Análisis Predictivo</p>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# MENÚ HORIZONTAL
# ------------------------------------------------------------
opciones_menu = [
    "📊 Dashboard",
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registro manual",
    "📈 Ver asistencia"
]
menu = st.radio("", opciones_menu, horizontal=True, label_visibility="collapsed", key="menu_radio")
st.session_state.menu_actual = menu

# ------------------------------------------------------------
# FUNCIÓN PARA CREAR TARJETA CUADRADA
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
# DASHBOARD PRINCIPAL (NUEVO)
# ------------------------------------------------------------
if st.session_state.menu_actual == "📊 Dashboard":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    # Obtener datos
    estudiantes_df = leer_estudiantes()
    asistencia_df = leer_asistencia()
    total_estudiantes = len(estudiantes_df)
    hoy = datetime.now(ZONA_HORARIA).date()
    
    # Métricas del día
    asistencia_hoy = asistencia_df[asistencia_df["fecha"] == hoy] if len(asistencia_df) > 0 else pd.DataFrame()
    registrados_hoy = asistencia_hoy["ru"].nunique() if len(asistencia_hoy) > 0 else 0
    faltantes_hoy = total_estudiantes - registrados_hoy
    tasa_asistencia = (registrados_hoy / total_estudiantes * 100) if total_estudiantes > 0 else 0
    
    # Estadísticas por estado
    if len(asistencia_hoy) > 0:
        estado_counts = asistencia_hoy["estado"].value_counts()
        presentes = estado_counts.get("Presente", 0)
        tarde = estado_counts.get("Tarde", 0)
        permiso = estado_counts.get("Permiso", 0)
        ausente = estado_counts.get("Ausente", 0)
    else:
        presentes = tarde = permiso = ausente = 0
    
    # KPIs con neón
    st.markdown("""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Total Estudiantes</div>
            <div class="kpi-trend">📊 Registrados en sistema</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">✅</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Asistencia Hoy</div>
            <div class="kpi-trend">📈 {:.1f}% del total</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">❌</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-label">Faltantes</div>
            <div class="kpi-trend">⚠️ Pendientes por registrar</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🎯</div>
            <div class="kpi-value">{:.0f}%</div>
            <div class="kpi-label">Tasa Asistencia</div>
            <div class="kpi-trend">🏆 Meta 95%</div>
        </div>
    </div>
    """.format(total_estudiantes, registrados_hoy, tasa_asistencia, faltantes_hoy, tasa_asistencia), unsafe_allow_html=True)
    
    # Gráficos interactivos con Plotly
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de dona para estados
        estados = ["Presente", "Tarde", "Permiso", "Ausente"]
        valores = [presentes, tarde, permiso, ausente]
        colores_neon = ['#00ffcc', '#ff6b6b', '#9b59b6', '#ffa500']
        
        fig_dona = go.Figure(data=[go.Pie(
            labels=estados,
            values=valores,
            hole=0.6,
            marker=dict(colors=colores_neon, line=dict(color='#0a0a0f', width=2)),
            textinfo='label+percent',
            textfont=dict(color='white', size=12, family='Space Grotesk'),
            hoverinfo='label+value+percent'
        )])
        
        fig_dona.update_layout(
            title=dict(text="📊 Distribución de Asistencia", font=dict(color='#00ffcc', size=18), x=0.5),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0.5)'),
            height=400,
            margin=dict(t=50, l=20, r=20, b=20)
        )
        
        st.plotly_chart(fig_dona, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Gráfico de barras: Asistencia últimos 7 días
        if len(asistencia_df) > 0:
            asistencia_df['fecha_str'] = pd.to_datetime(asistencia_df['fecha']).dt.date
            ultimos_7_dias = pd.date_range(end=hoy, periods=7, freq='D').date
            asistencia_semanal = []
            
            for dia in ultimos_7_dias:
                count = asistencia_df[asistencia_df['fecha_str'] == dia]['ru'].nunique()
                asistencia_semanal.append(count)
            
            fig_barras = go.Figure(data=[go.Bar(
                x=[d.strftime('%d/%m') for d in ultimos_7_dias],
                y=asistencia_semanal,
                marker=dict(color='#00ffcc', line=dict(color='#0066ff', width=1)),
                text=asistencia_semanal,
                textposition='outside',
                textfont=dict(color='white')
            )])
            
            fig_barras.update_layout(
                title=dict(text="📅 Asistencia Últimos 7 Días", font=dict(color='#00ffcc', size=18), x=0.5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Fecha"),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Estudiantes"),
                height=400,
                margin=dict(t=50, l=40, r=20, b=40)
            )
            
            st.plotly_chart(fig_barras, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📭 No hay datos de asistencia para mostrar")
    
    # Segunda fila de gráficos
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        # Top estudiantes con más asistencias
        if len(asistencia_df) > 0:
            top_estudiantes = asistencia_df.groupby(['ru', 'nombres', 'apellido_paterno']).size().reset_index(name='total')
            top_estudiantes = top_estudiantes.sort_values('total', ascending=True).tail(10)
            top_estudiantes['nombre_completo'] = top_estudiantes['nombres'] + " " + top_estudiantes['apellido_paterno']
            
            fig_top = go.Figure(data=[go.Bar(
                x=top_estudiantes['total'],
                y=top_estudiantes['nombre_completo'],
                orientation='h',
                marker=dict(color='#9b59b6', line=dict(color='#00ffcc', width=1)),
                text=top_estudiantes['total'],
                textposition='outside'
            )])
            
            fig_top.update_layout(
                title=dict(text="🏆 Top 10 Asistencias", font=dict(color='#9b59b6', size=18), x=0.5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Total Asistencias"),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                height=450,
                margin=dict(t=50, l=120, r=20, b=20)
            )
            
            st.plotly_chart(fig_top, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📭 No hay datos suficientes")
    
    with col4:
        # Indicadores circulares
        fig_indicadores = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=('Tasa Asistencia', 'Puntualidad', 'Permisos', 'Ausentismo')
        )
        
        fig_indicadores.add_trace(go.Indicator(
            mode="gauge+number",
            value=tasa_asistencia,
            title={'text': "%", 'font': {'color': 'white'}},
            gauge={'axis': {'range': [0, 100], 'tickcolor': 'white'},
                   'bar': {'color': "#00ffcc"},
                   'bgcolor': "rgba(0,0,0,0.3)",
                   'borderwidth': 1,
                   'bordercolor': "#00ffcc"},
            number={'font': {'color': '#00ffcc', 'size': 40}}
        ), row=1, col=1)
        
        puntualidad = (presentes / (presentes + tarde) * 100) if (presentes + tarde) > 0 else 0
        fig_indicadores.add_trace(go.Indicator(
            mode="gauge+number",
            value=puntualidad,
            title={'text': "%", 'font': {'color': 'white'}},
            gauge={'axis': {'range': [0, 100], 'tickcolor': 'white'},
                   'bar': {'color': "#ff6b6b"},
                   'bgcolor': "rgba(0,0,0,0.3)"},
            number={'font': {'color': '#ff6b6b', 'size': 40}}
        ), row=1, col=2)
        
        fig_indicadores.add_trace(go.Indicator(
            mode="number",
            value=permiso,
            title={'text': "Permisos", 'font': {'color': 'white'}},
            number={'font': {'color': '#9b59b6', 'size': 50}}
        ), row=2, col=1)
        
        fig_indicadores.add_trace(go.Indicator(
            mode="number",
            value=ausente,
            title={'text': "Ausentes", 'font': {'color': 'white'}},
            number={'font': {'color': '#ffa500', 'size': 50}}
        ), row=2, col=2)
        
        fig_indicadores.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Space Grotesk'),
            height=450,
            margin=dict(t=80, l=20, r=20, b=20)
        )
        
        st.plotly_chart(fig_indicadores, use_container_width=True, config={'displayModeBar': False})
    
    # Últimos registros
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>🔄 Últimos Registros de Asistencia</h3>", unsafe_allow_html=True)
    
    if len(asistencia_df) > 0:
        ultimos_10 = asistencia_df.tail(10).copy()
        ultimos_10['fecha'] = ultimos_10['fecha'].astype(str)
        ultimos_10['hora'] = ultimos_10['hora'].astype(str)
        st.dataframe(ultimos_10[['ru', 'nombres', 'apellido_paterno', 'fecha', 'hora', 'estado']].sort_values('fecha', ascending=False), 
                    use_container_width=True)
    else:
        st.info("📭 No hay registros de asistencia")

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📝 Registrar estudiante":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("<h2 style='text-align: center;'>📝 Registrar Nuevo Estudiante</h2>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form(key="registro_form"):
                ru = st.text_input("🔢 RU del Estudiante", placeholder="Ingrese el RU (solo números)")
                nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres completos")
                apellido_paterno = st.text_input("👨 Apellido Paterno", placeholder="Ingrese el apellido paterno")
                apellido_materno = st.text_input("👩 Apellido Materno", placeholder="Ingrese el apellido materno")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    submit = st.form_submit_button("💾 Guardar Estudiante", use_container_width=True)
                
                if submit:
                    if not ru or not ru.strip():
                        st.error("❌ El RU no puede estar vacío")
                    elif not ru.isdigit():
                        st.error("❌ El RU debe contener solo números")
                    else:
                        try:
                            existe = supabase.table("estudiantes").select("ru").eq("ru", ru).execute()
                            if existe.data:
                                st.error("❌ Este RU ya existe en el sistema")
                            else:
                                supabase.table("estudiantes").insert({
                                    "ru": ru,
                                    "nombres": nombres,
                                    "apellido_paterno": apellido_paterno,
                                    "apellido_materno": apellido_materno
                                }).execute()
                                st.success("✅ Estudiante registrado exitosamente")
                                
                                # Mostrar QR generado
                                qr_img = qrcode.make(ru)
                                buf = io.BytesIO()
                                qr_img.save(buf, format="PNG")
                                buf.seek(0)
                                
                                st.markdown("### 📱 Código QR del Estudiante")
                                st.image(qr_img, width=250)
                                st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png")
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {e}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("<h2 style='text-align: center;'>📋 Lista de Estudiantes</h2>", unsafe_allow_html=True)
    
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        
        st.markdown("---")
        st.markdown("<h3 style='text-align: center;'>🔍 Buscar Estudiante</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            ru_buscar = st.text_input("Ingrese el RU", placeholder="Código Único", key="buscar_ru")
            if st.button("🔍 Buscar", use_container_width=True):
                if ru_buscar:
                    estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_buscar]
                    if len(estudiante) > 0:
                        estudiante_data = estudiante.iloc[0]
                        nombre_completo = f"{estudiante_data['nombres']} {estudiante_data['apellido_paterno']}".upper()
                        
                        qr_img = qrcode.make(ru_buscar)
                        qr_buffer = io.BytesIO()
                        qr_img.save(qr_buffer, format='PNG')
                        qr_buffer.seek(0)
                        
                        st.markdown(f"""
                        <div class="student-search-card">
                            <div class="student-name">{nombre_completo}</div>
                            <div class="student-ru">RU: {ru_buscar}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.image(qr_img, width=250)
                        
                        col_download1, col_download2, col_download3 = st.columns(3)
                        with col_download1:
                            st.download_button("📥 QR", data=qr_buffer.getvalue(), file_name=f"{ru_buscar}_qr.png", mime="image/png")
                        with col_download2:
                            tarjeta_img = crear_tarjeta_estudiante(estudiante_data)
                            st.download_button("📇 Tarjeta", data=tarjeta_img, file_name=f"tarjeta_{ru_buscar}.png", mime="image/png")
                    else:
                        st.warning("⚠️ Estudiante no encontrado")
                else:
                    st.warning("⚠️ Ingrese un RU")
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("<h2 style='text-align: center;'>📸 Escanear Código QR</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--text-secondary);'>Toma una foto del código QR para registrar asistencia</p>", unsafe_allow_html=True)
    
    foto = st.camera_input("", label_visibility="collapsed")
    
    if foto is not None:
        img = Image.open(foto)
        decoded_objects = decode(img)
        
        if decoded_objects:
            ru = decoded_objects[0].data.decode('utf-8')
            estudiantes = leer_estudiantes()
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru]
            
            if len(estudiante) > 0:
                nombres = estudiante.iloc[0]["nombres"]
                paterno = estudiante.iloc[0]["apellido_paterno"]
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
                
                if not tiene_registro:
                    try:
                        supabase.table("asistencia").insert({
                            "ru": ru,
                            "nombres": nombres,
                            "apellido_paterno": paterno,
                            "apellido_materno": estudiante.iloc[0]["apellido_materno"],
                            "fecha": fecha.isoformat(),
                            "hora": hora,
                            "estado": "Presente"
                        }).execute()
                        st.success(f"✅ ¡Asistencia registrada! {nombres} {paterno} - {hora}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} ya registró hoy a las {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado en la base de datos")
        else:
            st.warning("⚠️ No se detectó ningún código QR")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registro manual":
    if not st.session_state.manual_auth:
        st.markdown("""
        <div class="password-modal">
            <h3>🔒 Acceso Restringido</h3>
            <p style="color: var(--text-secondary);">Ingrese la contraseña para continuar</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(key="password_form"):
            password = st.text_input("Contraseña", type="password", placeholder="********")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_password = st.form_submit_button("🔓 Ingresar", use_container_width=True)
        
        if submit_password:
            if password == "pocoyo123":
                st.session_state.manual_auth = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    else:
        st.markdown("<h2 style='text-align: center;'>✍️ Registrar Asistencia Manual</h2>", unsafe_allow_html=True)
        
        estudiantes = leer_estudiantes()
        if len(estudiantes) > 0:
            estudiantes["nombre_completo"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                seleccionado = st.selectbox("👤 Seleccionar Estudiante", estudiantes["nombre_completo"].tolist())
                estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                
                if seleccionado:
                    ru_seleccionado = seleccionado.split(" - ")[0]
                    estudiante_data = estudiantes[estudiantes["ru"].astype(str) == ru_seleccionado].iloc[0]
                    
                    st.markdown(f"""
                    <div class="student-detail-card">
                        <p><strong>📋 Datos:</strong> {estudiante_data['nombres']} {estudiante_data['apellido_paterno']}</p>
                        <p><strong>🔢 RU:</strong> {ru_seleccionado}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    fecha, hora = obtener_fecha_hora_exacta()
                    tiene_registro, _ = verificar_registro_duplicado(ru_seleccionado, fecha)
                    
                    if tiene_registro:
                        st.warning("⚠️ Este estudiante ya registró asistencia hoy")
                        st.button("✅ Registrar", disabled=True, use_container_width=True)
                    else:
                        if st.button("✅ Registrar Asistencia", use_container_width=True):
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
                                st.success(f"✅ Asistencia registrada a las {hora}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ No hay estudiantes registrados")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📈 Ver asistencia":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("<h2 style='text-align: center;'>📊 Registros de Asistencia</h2>", unsafe_allow_html=True)
    
    asistencia_df = leer_asistencia()
    
    if len(asistencia_df) > 0:
        # Filtros
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        with col_filtro1:
            fecha_filtro = st.date_input("📅 Filtrar por fecha", value=None)
        with col_filtro2:
            estado_filtro = st.selectbox("📌 Filtrar por estado", ["Todos", "Presente", "Tarde", "Permiso", "Ausente"])
        with col_filtro3:
            ru_filtro = st.text_input("🔢 Filtrar por RU", placeholder="Ingrese RU")
        
        # Aplicar filtros
        df_filtrado = asistencia_df.copy()
        if fecha_filtro:
            df_filtrado = df_filtrado[df_filtrado["fecha"] == fecha_filtro]
        if estado_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["estado"] == estado_filtro]
        if ru_filtro:
            df_filtrado = df_filtrado[df_filtrado["ru"].astype(str).str.contains(ru_filtro)]
        
        df_mostrar = df_filtrado.copy()
        df_mostrar['fecha'] = df_mostrar['fecha'].astype(str)
        df_mostrar['hora'] = df_mostrar['hora'].astype(str)
        
        st.dataframe(df_mostrar.drop(columns=['id']), use_container_width=True)
        
        # Exportar
        st.markdown("---")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp2:
            if st.button("📥 Exportar a Excel", use_container_width=True):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_mostrar.to_excel(writer, index=False, sheet_name='Asistencia')
                st.download_button("⬇️ Descargar Excel", data=output.getvalue(), file_name=f"asistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("📭 No hay registros de asistencia en el sistema")
