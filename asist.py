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
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="collapsed")

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
# ESTILOS CSS RESPONSIVE PARA MÓVIL
# ------------------------------------------------------------
st.markdown("""
<style>
    /* Reset y variables */
    :root {
        --primary-color: #0066ff;
        --primary-hover: #0052cc;
        --accent-color: #00ffcc;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --bg-dark: #0f172a;
        --glass-bg: rgba(15, 23, 42, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --shadow-3d: 0 10px 25px -5px rgba(0, 102, 255, 0.2);
        --shadow-hover: 0 20px 50px -10px rgba(0, 102, 255, 0.4);
        --success-gradient: linear-gradient(135deg, #00ffcc 0%, #0066ff 100%);
    }

    /* Ocultar sidebar por defecto en móvil */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Ajustes generales para móvil */
    .stApp {
        background-color: var(--bg-dark);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .main > div {
        padding: 0.5rem;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0, 102, 255, 0.3);
        font-size: 1.5rem;
    }
    
    .subtitle-script {
        color: var(--text-secondary);
        font-family: 'Pacifico', 'Dancing Script', cursive;
        font-size: 0.85rem;
        margin-top: -5px;
    }
    
    /* ============ MENÚ TIPO TARJETAS PARA MÓVIL ============ */
    .mobile-menu-container {
        margin: 1rem 0 1.5rem 0;
    }
    
    .mobile-menu-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        padding: 0;
    }
    
    .menu-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(0, 102, 255, 0.1) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 16px 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .menu-card.active {
        background: var(--success-gradient);
        border-color: rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 25px rgba(0, 102, 255, 0.4);
        transform: scale(1.02);
    }
    
    .menu-card.active .menu-icon {
        transform: scale(1.1);
    }
    
    .menu-card.active .menu-text {
        color: #020617;
        font-weight: 700;
    }
    
    .menu-icon {
        font-size: 2rem;
        display: block;
        margin-bottom: 8px;
        transition: transform 0.3s ease;
    }
    
    .menu-text {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-primary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    
    .menu-subtext {
        font-size: 0.65rem;
        color: var(--text-secondary);
        margin-top: 4px;
        display: block;
    }
    
    /* Tarjetas de información */
    .info-card, .student-info, .stDataFrame {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Botones táctiles */
    .stButton button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.9rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton button:active {
        transform: scale(0.98);
    }
    
    /* Inputs táctiles */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
        font-size: 16px !important; /* Previene zoom en iOS */
    }
    
    /* Tablas responsive */
    .stDataFrame {
        overflow-x: auto;
    }
    
    .stDataFrame table {
        width: 100%;
        font-size: 0.8rem;
    }
    
    .stDataFrame td, .stDataFrame th {
        white-space: nowrap;
        padding: 0.5rem;
    }
    
    /* QR y tarjetas */
    .qr-container {
        display: flex;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .qr-container img {
        max-width: 100%;
        height: auto;
        border-radius: 16px;
    }
    
    /* Alertas */
    .stAlert {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        font-size: 0.85rem !important;
    }
    
    /* Scroll suave */
    html {
        scroll-behavior: smooth;
    }
    
    /* Animaciones */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .menu-card, .info-card, .stAlert {
        animation: fadeInUp 0.4s ease-out;
    }
    
    /* Media query para pantallas muy pequeñas */
    @media (max-width: 480px) {
        .menu-icon {
            font-size: 1.75rem;
        }
        .menu-text {
            font-size: 0.7rem;
        }
        .menu-subtext {
            font-size: 0.6rem;
        }
        h1 {
            font-size: 1.3rem;
        }
    }
    
    /* Partículas animadas */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS
# ------------------------------------------------------------
st.markdown("""
<div class="particles"></div>
<script>
    function createParticles() {
        const container = document.querySelector('.particles');
        if (!container) return;
        
        const particleCount = 50;
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
            particle.style.opacity = '0.4';
            container.appendChild(particle);
        }
    }
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 0.4; }
            25% { transform: translate(10px, -15px) rotate(45deg); opacity: 0.6; }
            50% { transform: translate(-5px, -25px) rotate(90deg); opacity: 0.8; }
            75% { transform: translate(15px, -10px) rotate(135deg); opacity: 0.6; }
        }
    `;
    document.head.appendChild(style);
    window.addEventListener('load', createParticles);
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO CON LOGO
# ------------------------------------------------------------
logo_path = "assets/logo.png"
col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=50)
with col2:
    st.markdown("### INGENIERÍA DE SISTEMAS")
    st.markdown('<p class="subtitle-script">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# MENÚ TIPO TARJETAS PARA MÓVIL
# ------------------------------------------------------------
# Definir las opciones del menú
opciones_menu = [
    {"id": "📝 Registrar estudiante", "icono": "📝", "texto": "REGISTRAR", "subtexto": "Estudiante"},
    {"id": "📋 Lista estudiantes", "icono": "📋", "texto": "LISTA", "subtexto": "Estudiantes"},
    {"id": "📸 Escanear QR", "icono": "📸", "texto": "ESCANEAR", "subtexto": "QR"},
    {"id": "✍️ Registrar asistencia manual", "icono": "✍️", "texto": "ASISTENCIA", "subtexto": "Manual"},
    {"id": "📊 Ver asistencia", "icono": "📊", "texto": "VER", "subtexto": "Asistencia"}
]

# Mostrar menú en grid de 2 columnas
st.markdown('<div class="mobile-menu-container">', unsafe_allow_html=True)
st.markdown('<div class="mobile-menu-grid">', unsafe_allow_html=True)

for opcion in opciones_menu:
    active_class = "active" if st.session_state.menu_actual == opcion["id"] else ""
    # Usar HTML con JavaScript para manejar clicks
    st.markdown(f"""
        <div class="menu-card {active_class}" onclick="document.querySelector('[data-testid=\"stMarkdownContainer\"] form').submit();" 
             style="cursor: pointer;">
            <span class="menu-icon">{opcion["icono"]}</span>
            <span class="menu-text">{opcion["texto"]}</span>
            <span class="menu-subtext">{opcion["subtexto"]}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Radio oculto para manejar la selección del menú
menu_seleccionado = st.radio(
    "",
    [op["id"] for op in opciones_menu],
    horizontal=False,
    label_visibility="collapsed",
    key="menu_radio_hidden"
)

# Actualizar session state
if menu_seleccionado:
    st.session_state.menu_actual = menu_seleccionado

# ------------------------------------------------------------
# FUNCIÓN PARA CREAR TARJETA CUADRADA
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    ru = str(estudiante["ru"])
    nombres = estudiante["nombres"]
    paterno = estudiante["apellido_paterno"]
    materno = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    qr = qrcode.make(ru, box_size=12, border=2)
    qr_size = 700
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
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    font_regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    
    title_font = None
    ru_font = None
    name_font = None
    footer_font = None

    for path in font_paths:
        if os.path.exists(path):
            try:
                title_font = ImageFont.truetype(path, 90)
                ru_font = ImageFont.truetype(path, 80)
                name_font = ImageFont.truetype(path, 72)
                break
            except:
                continue
    
    if title_font is None:
        for path in font_regular_paths:
            if os.path.exists(path):
                try:
                    title_font = ImageFont.truetype(path, 90)
                    ru_font = ImageFont.truetype(path, 80)
                    name_font = ImageFont.truetype(path, 72)
                    break
                except:
                    continue

    for path in font_regular_paths:
        if os.path.exists(path):
            try:
                footer_font = ImageFont.truetype(path, 48)
                break
            except:
                continue

    if title_font is None:
        title_font = ImageFont.load_default()
        ru_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    border_color = (0, 102, 255)
    border_width = 10
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    title_text = "TARJETA DE IDENTIFICACIÓN"
    bbox = draw.textbbox((0,0), title_text, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (card_size - title_width) // 2
    title_y = 50
    for offset in [(4,4), (-4,4), (4,-4), (-4,-4)]:
        draw.text((title_x+offset[0], title_y+offset[1]), title_text, fill=(0,0,0), font=title_font)
    draw.text((title_x, title_y), title_text, fill=(255,255,255), font=title_font)

    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    ru_width = bbox[2] - bbox[0]
    ru_x = (card_size - ru_width) // 2
    ru_y = title_y + 120
    for offset in [(3,3), (-3,3), (3,-3), (-3,-3)]:
        draw.text((ru_x+offset[0], ru_y+offset[1]), ru_text, fill=(0,0,0), font=ru_font)
    draw.text((ru_x, ru_y), ru_text, fill=(255,255,200), font=ru_font)

    max_width = card_size - 120
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

    line_spacing = 100
    total_height = len(lines) * line_spacing
    start_y = ru_y + 160
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=name_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = start_y + i * line_spacing
        for offset in [(3,3), (-3,3), (3,-3), (-3,-3)]:
            draw.text((x+offset[0], y+offset[1]), line, fill=(0,0,0), font=name_font)
        draw.text((x, y), line, fill=(255,255,255), font=name_font)

    espacio_restante = card_size - (start_y + total_height) - 120
    qr_y = start_y + total_height + (espacio_restante - qr_size) // 2 - 40
    qr_x = (card_size - qr_size) // 2
    background.paste(qr, (qr_x, qr_y))

    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    lines_footer = footer_text.split("\n")
    footer_y = qr_y + qr_size + 40
    for i, line in enumerate(lines_footer):
        bbox = draw.textbbox((0,0), line, font=footer_font)
        line_width = bbox[2] - bbox[0]
        x = (card_size - line_width) // 2
        y = footer_y + i * 60
        for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
            draw.text((x+offset[0], y+offset[1]), line, fill=(0,0,0), font=footer_font)
        draw.text((x, y), line, fill=(220, 220, 255), font=footer_font)

    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG', quality=100, dpi=(300,300))
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------------------------
# CONTENIDO DE CADA SECCIÓN (RESPONSIVE)
# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar estudiante")
    
    ru = st.text_input("🔢 RU", placeholder="Ingrese el RU (solo números)", key="reg_ru")
    nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres", key="reg_nombres")
    paterno = st.text_input("👨 Apellido paterno", placeholder="Ingrese el apellido paterno", key="reg_paterno")
    materno = st.text_input("👩 Apellido materno", placeholder="Ingrese el apellido materno", key="reg_materno")
    
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
                    
                    st.markdown("### Código QR generado")
                    st.image(img_bytes, width=300)
                    
                    buf = io.BytesIO()
                    qr_img.save(buf, format="PNG")
                    buf.seek(0)
                    st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

# LISTA ESTUDIANTES
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Buscar estudiante")
        ru_ver = st.text_input("Ingrese RU", placeholder="Ej: 2024001", key="buscar_ru")
        
        if ru_ver:
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                estudiante_data = estudiante.iloc[0]
                st.success(f"✅ Estudiante encontrado")
                
                qr_img = qrcode.make(ru_ver)
                qr_buffer = io.BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                st.image(qr_buffer, width=300)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 QR", data=qr_buffer.getvalue(), file_name=f"{ru_ver}_qr.png", mime="image/png", use_container_width=True)
                with col2:
                    tarjeta_img = crear_tarjeta_estudiante({
                        "ru": ru_ver,
                        "nombres": estudiante_data["nombres"],
                        "apellido_paterno": estudiante_data["apellido_paterno"],
                        "apellido_materno": estudiante_data["apellido_materno"]
                    })
                    st.download_button("📇 Tarjeta", data=tarjeta_img, file_name=f"tarjeta_{ru_ver}.png", mime="image/png", use_container_width=True)
            else:
                st.warning("⚠️ RU no encontrado")
    else:
        st.info("📭 No hay estudiantes registrados")

# ESCANEAR QR
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: var(--text-secondary);">Toma una foto del código QR</p>', unsafe_allow_html=True)
    
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
                        st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning(f"⚠️ Ya registró hoy a las {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó QR")

# REGISTRO MANUAL
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    st.subheader("✍️ Registrar asistencia manual")
    estudiantes = leer_estudiantes()
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = estudiantes["ru"].astype(str) + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
        seleccionado = st.selectbox("👤 Seleccionar estudiante", estudiantes["nombre_completo"])
        ru = seleccionado.split(" - ")[0]
        estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
        fecha, hora = obtener_fecha_hora_exacta()
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        if tiene_registro:
            st.warning(f"⚠️ Ya registró hoy a las {registro_existente['hora']}")
        elif st.button("✅ Registrar asistencia", use_container_width=True):
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru].iloc[0]
            try:
                supabase.table("asistencia").insert({
                    "ru": ru,
                    "nombres": estudiante["nombres"],
                    "apellido_paterno": estudiante["apellido_paterno"],
                    "apellido_materno": estudiante["apellido_materno"],
                    "fecha": fecha.isoformat(),
                    "hora": hora,
                    "estado": estado
                }).execute()
                st.success(f"✅ Asistencia registrada a las {hora}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ No hay estudiantes registrados")

# VER ASISTENCIA
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    asistencia = leer_asistencia()
    if len(asistencia) > 0:
        asistencia_mostrar = asistencia.copy()
        asistencia_mostrar['fecha'] = asistencia_mostrar['fecha'].astype(str)
        st.dataframe(asistencia_mostrar.drop(columns=['id']), use_container_width=True)
        
        st.markdown("---")
        st.subheader("⬇️ Descargar asistencia del día")
        hoy = str(datetime.now(ZONA_HORARIA).date())
        asistencia_hoy = asistencia[asistencia["fecha"].astype(str) == hoy].copy()
        if len(asistencia_hoy) > 0:
            archivo_descarga = f"asistencia_{hoy}.xlsx"
            asistencia_hoy.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel", data=file, file_name=archivo_descarga, use_container_width=True)
        else:
            st.info("📭 No hay registros para hoy")
    else:
        st.info("📭 No hay registros de asistencia")

# ------------------------------------------------------------
# SIDEBAR INFORMACIÓN (opcional)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown("Base de datos en la nube con Supabase")
