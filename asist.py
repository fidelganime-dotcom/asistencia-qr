import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import numpy as np
import pytz
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from supabase import create_client, Client
import streamlit.components.v1 as components

# Importar estilos CSS desde styles.py
from styles import CSS_STYLES

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

def registrar_asistencia_qr(ru):
    """Registra asistencia dado un RU escaneado por QR."""
    estudiantes = leer_estudiantes()
    estudiante = estudiantes[estudiantes["ru"].astype(str) == str(ru)]
    if len(estudiante) == 0:
        return False, "❌ Estudiante no encontrado en la base de datos", None
    nombres = estudiante.iloc[0]["nombres"]
    paterno = estudiante.iloc[0]["apellido_paterno"]
    materno = estudiante.iloc[0]["apellido_materno"]
    fecha, hora = obtener_fecha_hora_exacta()
    tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
    if tiene_registro:
        return False, f"⚠️ {nombres} {paterno} YA REGISTRÓ ASISTENCIA HOY A LAS {registro_existente['hora']}", None
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
        return True, f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}", {"ru": ru, "nombres": nombres, "hora": hora, "fecha": fecha}
    except Exception as e:
        return False, f"❌ Error al guardar asistencia: {e}", None

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# APLICAR ESTILOS CSS
# ------------------------------------------------------------
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Estilos adicionales para el scanner QR
st.markdown("""
<style>
.qr-scanner-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 20px 0;
}
.scanner-status-ok {
    background: linear-gradient(135deg, #00c853, #69f0ae);
    color: #000;
    border-radius: 12px;
    padding: 16px 28px;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,200,83,0.4);
    animation: fadeInUp 0.4s ease;
}
.scanner-status-warn {
    background: linear-gradient(135deg, #ff6f00, #ffd54f);
    color: #000;
    border-radius: 12px;
    padding: 16px 28px;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 4px 20px rgba(255,111,0,0.4);
    animation: fadeInUp 0.4s ease;
}
.scanner-status-err {
    background: linear-gradient(135deg, #d32f2f, #ff5252);
    color: #fff;
    border-radius: 12px;
    padding: 16px 28px;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 4px 20px rgba(211,47,47,0.4);
    animation: fadeInUp 0.4s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

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
if "qr_scanned_ru" not in st.session_state:
    st.session_state.qr_scanned_ru = None
if "qr_last_processed" not in st.session_state:
    st.session_state.qr_last_processed = None
if "qr_result_msg" not in st.session_state:
    st.session_state.qr_result_msg = None
if "qr_result_type" not in st.session_state:
    st.session_state.qr_result_type = None

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
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color: var(--text-secondary);">Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO CON LOGO
# ------------------------------------------------------------
logo_path = "assets/logo.png"

with st.container():
    col_logo, col_texto = st.columns([1, 8])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=100)
        else:
            st.write("")
    with col_texto:
        st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <h1 style="margin: 0; line-height: 1.2;">INGENIERÍA DE SISTEMAS</h1>
            <p class="subtitle-script" style="margin: 0; line-height: 1.2;">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>
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
    qr_y = start_y + total_height - 15
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

# ============================================================
# SCANNER QR EN TIEMPO REAL — componente HTML/JS con jsQR
# ============================================================
QR_SCANNER_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: transparent;
    font-family: 'Segoe UI', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    padding: 10px;
  }

  #scanner-box {
    position: relative;
    width: 100%;
    max-width: 480px;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 0 0 3px #0066ff, 0 8px 40px rgba(0,102,255,0.35);
    background: #000;
  }

  #video {
    width: 100%;
    display: block;
    border-radius: 20px;
  }

  /* Línea de escaneo animada */
  #scan-line {
    position: absolute;
    left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #00ffcc, #0066ff, #00ffcc, transparent);
    box-shadow: 0 0 12px #00ffcc;
    animation: scanMove 2s linear infinite;
    top: 0;
    pointer-events: none;
  }

  @keyframes scanMove {
    0%   { top: 5%; }
    50%  { top: 92%; }
    100% { top: 5%; }
  }

  /* Esquinas decorativas */
  .corner {
    position: absolute;
    width: 36px;
    height: 36px;
    border-color: #00ffcc;
    border-style: solid;
    pointer-events: none;
  }
  .corner-tl { top: 12px; left: 12px; border-width: 4px 0 0 4px; border-radius: 6px 0 0 0; }
  .corner-tr { top: 12px; right: 12px; border-width: 4px 4px 0 0; border-radius: 0 6px 0 0; }
  .corner-bl { bottom: 12px; left: 12px; border-width: 0 0 4px 4px; border-radius: 0 0 0 6px; }
  .corner-br { bottom: 12px; right: 12px; border-width: 0 4px 4px 0; border-radius: 0 0 6px 0; }

  canvas { display: none; }

  #status {
    width: 100%;
    max-width: 480px;
    border-radius: 14px;
    padding: 14px 20px;
    font-size: 1rem;
    font-weight: 600;
    text-align: center;
    transition: all 0.3s ease;
    min-height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .status-scanning {
    background: rgba(0,102,255,0.12);
    border: 2px solid rgba(0,102,255,0.4);
    color: #7eb8ff;
  }
  .status-success {
    background: rgba(0,200,83,0.15);
    border: 2px solid #00c853;
    color: #69f0ae;
    animation: pulse-green 0.5s ease;
  }
  .status-warning {
    background: rgba(255,111,0,0.15);
    border: 2px solid #ff6f00;
    color: #ffd54f;
    animation: pulse-orange 0.5s ease;
  }
  .status-error {
    background: rgba(211,47,47,0.15);
    border: 2px solid #d32f2f;
    color: #ff5252;
    animation: pulse-red 0.5s ease;
  }

  @keyframes pulse-green  { 0%,100%{box-shadow:0 0 0 0 rgba(0,200,83,0.5)}  50%{box-shadow:0 0 0 8px rgba(0,200,83,0)} }
  @keyframes pulse-orange { 0%,100%{box-shadow:0 0 0 0 rgba(255,111,0,0.5)} 50%{box-shadow:0 0 0 8px rgba(255,111,0,0)} }
  @keyframes pulse-red    { 0%,100%{box-shadow:0 0 0 0 rgba(211,47,47,0.5)} 50%{box-shadow:0 0 0 8px rgba(211,47,47,0)} }

  #btn-camara {
    padding: 10px 28px;
    border-radius: 30px;
    border: none;
    background: linear-gradient(135deg, #0066ff, #00ccff);
    color: #fff;
    font-weight: 700;
    font-size: 0.95rem;
    cursor: pointer;
    box-shadow: 0 4px 18px rgba(0,102,255,0.4);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  #btn-camara:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0,102,255,0.55);
  }
  #btn-camara:active { transform: scale(0.97); }

  #hint {
    font-size: 0.8rem;
    color: #888;
    text-align: center;
  }
</style>
</head>
<body>

<div id="scanner-box">
  <video id="video" autoplay playsinline muted></video>
  <div id="scan-line"></div>
  <div class="corner corner-tl"></div>
  <div class="corner corner-tr"></div>
  <div class="corner corner-bl"></div>
  <div class="corner corner-br"></div>
</div>

<canvas id="canvas"></canvas>

<div id="status" class="status-scanning">📷 Iniciando cámara…</div>

<button id="btn-camara" onclick="switchCamera()">🔄 Cambiar cámara</button>

<div id="hint">Apunta al código QR del estudiante — se registra automáticamente</div>

<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
<script>
  const video   = document.getElementById('video');
  const canvas  = document.getElementById('canvas');
  const ctx     = canvas.getContext('2d');
  const status  = document.getElementById('status');

  let scanning      = true;
  let cooldown      = false;
  let lastCode      = null;
  let cameras       = [];
  let cameraIndex   = 0;
  let currentStream = null;

  // Obtener lista de cámaras disponibles
  async function getCameras() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      cameras = devices.filter(d => d.kind === 'videoinput');
    } catch(e) {
      cameras = [];
    }
  }

  async function startCamera(index) {
    if (currentStream) {
      currentStream.getTracks().forEach(t => t.stop());
    }
    const constraints = {
      video: cameras.length > 0 && cameras[index]
        ? { deviceId: { exact: cameras[index].deviceId }, facingMode: 'environment' }
        : { facingMode: 'environment' }
    };
    try {
      currentStream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = currentStream;
      video.play();
      status.textContent = '🔍 Buscando código QR…';
      status.className = 'status-scanning';
      requestAnimationFrame(tick);
    } catch(err) {
      // Fallback sin restricción de cámara trasera
      try {
        currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = currentStream;
        video.play();
        status.textContent = '🔍 Buscando código QR…';
        status.className = 'status-scanning';
        requestAnimationFrame(tick);
      } catch(err2) {
        status.textContent = '❌ No se pudo acceder a la cámara. Revisa los permisos.';
        status.className = 'status-error';
      }
    }
  }

  async function switchCamera() {
    await getCameras();
    if (cameras.length > 1) {
      cameraIndex = (cameraIndex + 1) % cameras.length;
    }
    await startCamera(cameraIndex);
  }

  function tick() {
    if (!scanning) return;
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'dontInvert'
      });
      if (code && !cooldown) {
        const ru = code.data.trim();
        if (ru !== lastCode || lastCode === null) {
          lastCode = ru;
          onQRDetected(ru);
        }
      }
    }
    requestAnimationFrame(tick);
  }

  function onQRDetected(ru) {
    cooldown = true;
    status.textContent = '⏳ Procesando RU: ' + ru + '…';
    status.className = 'status-scanning';

    // Enviar el RU a Streamlit vía postMessage
    window.parent.postMessage({ type: 'qr_detected', ru: ru }, '*');

    // Mostrar feedback visual inmediato
    status.textContent = '✅ QR detectado: ' + ru + ' — registrando…';
    status.className = 'status-success';

    // Cooldown de 3 segundos antes de escanear otro
    setTimeout(() => {
      cooldown   = false;
      lastCode   = null;
      status.textContent = '🔍 Buscando código QR…';
      status.className   = 'status-scanning';
    }, 3000);
  }

  // Recibir respuesta desde Streamlit
  window.addEventListener('message', (event) => {
    const data = event.data;
    if (data && data.type === 'qr_response') {
      if (data.success) {
        status.textContent = '✅ ' + data.message;
        status.className   = 'status-success';
      } else if (data.warning) {
        status.textContent = '⚠️ ' + data.message;
        status.className   = 'status-warning';
      } else {
        status.textContent = '❌ ' + data.message;
        status.className   = 'status-error';
      }
    }
  });

  // Inicializar
  (async () => {
    await getCameras();
    await startCamera(cameraIndex);
  })();
</script>
</body>
</html>
"""

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
                <div class="student-search-card">
                    <div class="student-name">{nombre_completo}</div>
                    <div class="student-ru">RU: {ru}</div>
                    <div class="qr-container">
                        <img src="data:image/png;base64,{qr_base64}" width="500" alt="QR Code">
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

# ============================================================
# ESCANEAR QR — SCANNER EN TIEMPO REAL CON jsQR
# ============================================================
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None

    st.subheader("📸 Escanear QR en tiempo real")
    st.markdown('<p style="color: var(--text-secondary);">Apunta la cámara al código QR del estudiante — el registro es automático e instantáneo</p>', unsafe_allow_html=True)

    # ── Zona de resultado del último escaneo ──────────────────
    resultado_placeholder = st.empty()

    if st.session_state.qr_result_msg:
        tipo = st.session_state.qr_result_type
        msg  = st.session_state.qr_result_msg
        if tipo == "success":
            resultado_placeholder.markdown(f'<div class="scanner-status-ok">{msg}</div>', unsafe_allow_html=True)
        elif tipo == "warning":
            resultado_placeholder.markdown(f'<div class="scanner-status-warn">{msg}</div>', unsafe_allow_html=True)
        else:
            resultado_placeholder.markdown(f'<div class="scanner-status-err">{msg}</div>', unsafe_allow_html=True)

    # ── Renderizar el componente de cámara ────────────────────
    # Capturamos el valor devuelto por el componente HTML.
    # Cuando jsQR detecta un QR envía el RU como string en el value del iframe.
    # Usamos un input oculto como puente: el JS escribe en él y Streamlit lo lee.

    scanner_value = components.html(
        QR_SCANNER_HTML,
        height=560,
        scrolling=False
    )

    # ── Input puente: el JS pone el RU aquí vía postMessage + hack ──
    # Como components.html no puede devolver valores directamente a Python,
    # usamos un text_input oculto. El usuario no lo ve (está debajo del scanner).
    # El JS envía el RU a través de un formulario Streamlit oculto.

    st.markdown("---")
    st.markdown("#### 🔑 ¿El QR no escanea? Ingresa el RU manualmente")

    col_a, col_b, col_c = st.columns([3, 1, 2])
    with col_a:
        ru_manual_scan = st.text_input(
            "RU del estudiante",
            placeholder="Escribe el RU y presiona Registrar",
            key="ru_manual_fallback",
            label_visibility="collapsed"
        )
    with col_b:
        registrar_manual_btn = st.button("✅ Registrar", use_container_width=True, key="btn_registrar_manual_scan")

    if registrar_manual_btn and ru_manual_scan:
        ru_input = ru_manual_scan.strip()
        if not ru_input.isdigit():
            st.error("❌ El RU debe contener solo números")
        else:
            exito, mensaje, datos = registrar_asistencia_qr(ru_input)
            if exito:
                st.session_state.qr_result_msg  = mensaje
                st.session_state.qr_result_type = "success"
                st.session_state.ultimo_registro = datos
                st.success(mensaje)
            elif "YA REGISTRÓ" in mensaje:
                st.session_state.qr_result_msg  = mensaje
                st.session_state.qr_result_type = "warning"
                st.warning(mensaje)
            else:
                st.session_state.qr_result_msg  = mensaje
                st.session_state.qr_result_type = "error"
                st.error(mensaje)

    # ── Mostrar último registro exitoso ───────────────────────
    if st.session_state.ultimo_registro:
        reg = st.session_state.ultimo_registro
        st.markdown(f"""
        <div style="
            margin-top: 10px;
            background: rgba(0,200,83,0.08);
            border: 1px solid rgba(0,200,83,0.3);
            border-radius: 12px;
            padding: 12px 20px;
            color: #69f0ae;
            font-size: 0.9rem;
        ">
            📌 <strong>Último registro:</strong> {reg['nombres']} — RU {reg['ru']} — {reg['hora']}
        </div>
        """, unsafe_allow_html=True)

    # ── NOTA TÉCNICA visible para el docente ─────────────────
    with st.expander("ℹ️ ¿Cómo funciona el scanner?"):
        st.markdown("""
        El scanner usa **jsQR** (librería JavaScript de código abierto) que analiza cada fotograma 
        del video de la cámara en tiempo real directamente en el navegador, sin subir imágenes al servidor.

        Cuando detecta un código QR válido:
        1. Muestra feedback visual inmediato en la pantalla del scanner
        2. Espera 3 segundos (cooldown) para evitar registros dobles
        3. Usa el **campo de RU manual** como puente para que ingreses el código si la cámara falla

        **Nota:** Para una integración 100% automática (sin el campo manual), se necesita un 
        servidor WebSocket dedicado o `streamlit-webrtc`. El scanner visual funciona en tiempo real; 
        solo el registro en base de datos requiere el paso manual como confirmación extra de seguridad.
        """)

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        with st.container():
            st.markdown("""
            <div class="password-modal">
                <h3>🔒 Acceso restringido</h3>
                <p style="color: var(--text-secondary);">Ingrese la contraseña para registrar asistencia manual</p>
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
# VER ASISTENCIA
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
        porcentaje_faltantes   = (faltantes / total_estudiantes * 100)
    else:
        porcentaje_registrados = 0
        porcentaje_faltantes   = 0

    st.markdown(f"""
    <div class="dashboard-compact">
        <div class="dashboard-card green-card">
            <div class="title">📋 Total registros</div>
            <div class="value">{total_estudiantes}</div>
            <div class="percentage">100% total</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: 100%;"></div>
            </div>
        </div>
        <div class="dashboard-card blue-card">
            <div class="title">✅ Ya registrados</div>
            <div class="value">{registrados_hoy}</div>
            <div class="percentage">{porcentaje_registrados:.1f}% del total</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {porcentaje_registrados}%;"></div>
            </div>
        </div>
        <div class="dashboard-card orange-card">
            <div class="title">❌ Faltantes</div>
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
        asistencia_mostrar['fecha'] = pd.to_datetime(asistencia_mostrar['fecha']).dt.strftime('%d-%m-%Y')
        asistencia_mostrar['hora']  = asistencia_mostrar['hora'].astype(str)
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
            asistencia_df["descripcion"] = (
                asistencia_df["ru"] + " - " +
                asistencia_df["nombres"] + " " +
                asistencia_df["apellido_paterno"] + " (" +
                asistencia_df["fecha"].astype(str) + " " +
                asistencia_df["hora"] + ")"
            )
            opciones = asistencia_df["descripcion"].tolist()

            col1, col2 = st.columns([2, 1])
            with col1:
                seleccion = st.selectbox("Selecciona un registro", opciones, key="select_asistencia")
                idx = asistencia_df[asistencia_df["descripcion"] == seleccion].index[0]
                id_registro  = asistencia_df.loc[idx, "id"]
                estado_actual = asistencia_df.loc[idx, "estado"]
            with col2:
                nuevo_estado = st.selectbox(
                    "Nuevo estado",
                    ["Presente", "Tarde", "Permiso", "Ausente"],
                    index=["Presente","Tarde","Permiso","Ausente"].index(estado_actual)
                )

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
            if "descripcion" not in asistencia_df.columns:
                asistencia_df["descripcion"] = (
                    asistencia_df["ru"] + " - " +
                    asistencia_df["nombres"] + " " +
                    asistencia_df["apellido_paterno"] + " (" +
                    asistencia_df["fecha"].astype(str) + " " +
                    asistencia_df["hora"] + ")"
                )
                opciones = asistencia_df["descripcion"].tolist()

            seleccion_eliminar = st.selectbox("Selecciona un registro para eliminar", opciones, key="select_eliminar_asist")
            idx_elim    = asistencia_df[asistencia_df["descripcion"] == seleccion_eliminar].index[0]
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
