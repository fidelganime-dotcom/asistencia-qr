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
if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # dark o light

# ------------------------------------------------------------
# FUNCIÓN PARA ALTERNAR TEMA (se llama desde JavaScript)
# ------------------------------------------------------------
def set_theme():
    # Este callback se ejecutará cuando se reciba un parámetro de consulta
    # Lo manejaremos con st.query_params
    pass

# ------------------------------------------------------------
# ESTILOS CSS CON VARIABLES PARA AMBOS TEMAS
# ------------------------------------------------------------
st.markdown(f"""
<style>
    /* Variables para tema oscuro (por defecto) */
    :root {{
        --primary-color: #0066ff;
        --primary-hover: #0052cc;
        --secondary-color: #2d3748;
        --accent-color: #00ffcc;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --bg-dark: #0f172a;
        --bg-darker: #020617;
        --glass-bg: rgba(15, 23, 42, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --shadow-3d: 0 10px 25px -5px rgba(0, 102, 255, 0.2), 0 10px 10px -5px rgba(0, 102, 255, 0.1);
        --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.4);
        --success-gradient: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
        --danger-gradient: linear-gradient(135deg, #ff3366 0%, #ff0066 100%);
        --warning-gradient: linear-gradient(135deg, #ffcc00 0%, #ff9900 100%);
        --input-bg: rgba(15, 23, 42, 0.5);
        --input-bg-focus: rgba(15, 23, 42, 0.8);
        --table-header-bg: linear-gradient(135deg, rgba(0,102,255,0.8) 0%, rgba(0,51,204,0.8) 100%);
        --table-row-hover: rgba(0, 102, 255, 0.1);
        --badge-bg: var(--success-gradient);
        --badge-color: #020617;
    }}

    /* Variables para tema claro */
    [data-theme="light"] {{
        --primary-color: #0066ff;
        --primary-hover: #0052cc;
        --secondary-color: #e2e8f0;
        --accent-color: #00cc99;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --bg-dark: #f1f5f9;
        --bg-darker: #e2e8f0;
        --glass-bg: rgba(255, 255, 255, 0.8);
        --glass-border: rgba(0, 0, 0, 0.1);
        --shadow-3d: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.05);
        --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.2);
        --success-gradient: linear-gradient(135deg, #00cc99 0%, #0066ff 100%);
        --danger-gradient: linear-gradient(135deg, #ff3366 0%, #ff0066 100%);
        --warning-gradient: linear-gradient(135deg, #ffcc00 0%, #ff9900 100%);
        --input-bg: rgba(255, 255, 255, 0.8);
        --input-bg-focus: rgba(255, 255, 255, 1);
        --table-header-bg: linear-gradient(135deg, #0066ff 0%, #0052cc 100%);
        --table-row-hover: rgba(0, 102, 255, 0.05);
        --badge-bg: var(--success-gradient);
        --badge-color: white;
    }}

    /* Aplicar variables globales */
    .stApp {{
        background-color: var(--bg-dark);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        transition: background-color 0.3s ease;
    }}

    /* Sidebar estilo glass */
    .css-1d391kg, .css-1lcbmhc {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--glass-border) !important;
        box-shadow: var(--shadow-3d) !important;
        transition: all 0.3s ease;
    }}

    /* Títulos */
    h1, h2, h3 {{
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
        position: relative;
        display: inline-block;
    }}

    h1::after, h2::after {{
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
    }}

    h1:hover::after, h2:hover::after {{
        transform: scaleX(1);
    }}

    /* Tarjetas estilo glass */
    .info-card, .student-info, .stDataFrame {{
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
    }}

    .info-card::before, .student-info::before, .stDataFrame::before {{
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
    }}

    .info-card:hover::before, .student-info:hover::before, .stDataFrame:hover::before {{
        opacity: 1;
        animation: shine 3s infinite;
    }}

    @keyframes shine {{
        0% {{ transform: rotate(30deg) translate(-10%, -10%); }}
        100% {{ transform: rotate(30deg) translate(10%, 10%); }}
    }}

    .info-card:hover, .student-info:hover, .stDataFrame:hover {{
        transform: translateY(-5px);
        box-shadow: var(--shadow-hover);
        border-color: rgba(0, 102, 255, 0.3);
    }}

    /* Menú horizontal (radio) estilo moderno */
    div.row-widget.stRadio > div {{
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
    }}

    div.row-widget.stRadio > div label {{
        background: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.6rem 1.2rem;
        border-radius: 40px;
        transition: all 0.3s ease;
        cursor: pointer;
        font-size: 0.9rem;
        position: relative;
        overflow: hidden;
    }}

    div.row-widget.stRadio > div label:hover {{
        background: rgba(0, 102, 255, 0.2);
        color: var(--accent-color);
        transform: translateY(-2px);
    }}

    /* Estilo para el botón seleccionado */
    div.row-widget.stRadio > div label[data-testid="stRadioLabel"]:has(input:checked) {{
        background: var(--success-gradient);
        color: var(--badge-color);
        box-shadow: var(--shadow-3d);
        font-weight: 600;
    }}

    /* Botones modernos 3D */
    .stButton button {{
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
        transform-style: preserve-3d;
        perspective: 1000px;
    }}

    .stButton button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.7s;
    }}

    .stButton button:hover::before {{
        left: 100%;
    }}

    .stButton button:hover {{
        background: var(--primary-hover);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }}

    .stButton button:active {{
        transform: translateY(1px);
    }}

    /* Botones secundarios */
    .stButton button[data-testid="baseButton-secondary"] {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }}

    .stButton button[data-testid="baseButton-secondary"]:hover {{
        background: rgba(255, 255, 255, 0.2);
    }}

    /* Inputs estilo glass */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        background: var(--input-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(5px) !important;
    }}

    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {{
        background: var(--input-bg-focus) !important;
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2) !important;
        transform: scale(1.01);
    }}

    .stTextInput input::placeholder {{
        color: rgba(200, 200, 200, 0.6);
    }}

    /* Tablas estilo moderno */
    .stDataFrame {{
        padding: 0;
        overflow: hidden;
    }}

    .stDataFrame table {{
        width: 100%;
        border-collapse: collapse;
        color: var(--text-primary);
    }}

    .stDataFrame thead tr th {{
        background: var(--table-header-bg) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem 1rem !important;
        border: none !important;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
    }}

    .stDataFrame thead tr th::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: var(--accent-color);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }}

    .stDataFrame thead tr th:hover::after {{
        transform: scaleX(1);
    }}

    .stDataFrame tbody tr {{
        transition: all 0.3s ease;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}

    .stDataFrame tbody tr:hover {{
        background: var(--table-row-hover);
        transform: translateX(5px);
    }}

    .stDataFrame tbody td {{
        padding: 0.75rem 1rem !important;
        border: none !important;
        vertical-align: middle;
        position: relative;
    }}

    .stDataFrame tbody td::before {{
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 0;
        background: var(--primary-color);
        transition: all 0.3s ease;
    }}

    .stDataFrame tbody tr:hover td::before {{
        height: 60%;
    }}

    /* Badges */
    .badge {{
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background: var(--badge-bg);
        color: var(--badge-color);
        display: inline-block;
    }}

    /* Alertas estilo glass */
    .stAlert {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-3d) !important;
    }}

    /* Cámara */
    div[data-testid="stCameraInput"] video {{
        width: 100% !important;
        height: 70vh !important;
        object-fit: cover;
        border-radius: 16px;
        border: 2px solid var(--primary-color);
        box-shadow: var(--shadow-3d);
    }}

    /* Scrollbar personalizada */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.1);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--primary-color);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-hover);
    }}

    /* Animaciones */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .stAlert, .stButton, .stDataFrame, .info-card, .student-info {{
        animation: fadeInUp 0.5s ease-out;
    }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS Y SWITCH DE TEMA (JavaScript)
# ------------------------------------------------------------
st.markdown("""
<script>
    // Crear partículas flotantes
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
    
    // Insertar keyframes para la animación float
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
    
    // Función para cambiar el tema
    function setTheme(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        // Guardar preferencia en localStorage
        localStorage.setItem('theme', theme);
    }
    
    // Cargar tema guardado
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        setTheme('light');
    }
    
    // Escuchar mensajes desde Streamlit para cambiar tema
    window.addEventListener('message', function(event) {
        if (event.data.type === 'set_theme') {
            setTheme(event.data.theme);
        }
    });
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR CON SWITCH DE TEMA
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌓 Tema")
    # Usar un botón para alternar en lugar de checkbox para más control
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌙 Oscuro", use_container_width=True, key="dark_btn"):
            st.session_state.theme = "dark"
            # Enviar mensaje al frontend
            st.markdown(f"""
                <script>
                    window.parent.postMessage({{type: 'set_theme', theme: 'dark'}}, '*');
                </script>
            """, unsafe_allow_html=True)
    with col2:
        if st.button("☀️ Claro", use_container_width=True, key="light_btn"):
            st.session_state.theme = "light"
            st.markdown("""
                <script>
                    window.parent.postMessage({type: 'set_theme', theme: 'light'}, '*');
                </script>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color: var(--text-secondary);">Sube tus propios archivos para trabajar con ellos</p>', unsafe_allow_html=True)
    
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
# TÍTULO Y MENÚ HORIZONTAL
# ------------------------------------------------------------
st.title("🟨🟩 Sistema de Asistencia")
st.markdown('<p style="color: var(--text-secondary); margin-top: -10px; margin-bottom: 20px;">Gestión inteligente de asistencia mediante códigos QR · Estilo Glassmorphism</p>', unsafe_allow_html=True)

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
# FUNCIONES AUXILIARES (sin cambios)
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
# FUNCIÓN PARA CREAR TARJETA CUADRADA MEJORADA (sin cambios)
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    ru = str(estudiante["RU"])
    nombres = estudiante["Nombres"]
    paterno = estudiante["Apellido_paterno"]
    materno = estudiante["Apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    qr = qrcode.make(ru)
    qr_size = 350
    qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

    card_size = 550
    card = Image.new('RGB', (card_size, card_size), color=(10, 20, 30))
    draw = ImageDraw.Draw(card)

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

    if font_path:
        title_font = ImageFont.truetype(font_path, 32)
        ru_font = ImageFont.truetype(font_path, 28)
        name_font = ImageFont.truetype(font_path, 26)
        footer_font = ImageFont.truetype(font_path, 20)
    else:
        title_font = ImageFont.load_default()
        ru_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    border_color = (25, 80, 150)
    border_width = 5
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    title_text = "TARJETA DE IDENTIFICACIÓN"
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 25
    draw.text((title_x, title_y), title_text, fill=(255, 255, 255), font=title_font)

    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 50
    draw.text((ru_x, ru_y), ru_text, fill=(255, 255, 255), font=ru_font)

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

    qr_x = (card_size - qr_size) // 2
    qr_y = start_y + total_height + 20
    card.paste(qr, (qr_x, qr_y))

    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 20
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 28
        draw.text((x, y), line, fill=(220, 220, 220), font=footer_font)

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
