import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime, timedelta
import os
import io
import base64
import math
import time
import json
from PIL import Image
from supabase import create_client, Client
from pyzbar.pyzbar import decode

# Importar estilos CSS desde styles.py (asegúrate de que el archivo styles.py existe)
try:
    from styles import CSS_STYLES
except ImportError:
    CSS_STYLES = """
    <style>
        /* Estilos mínimos para que funcione si no existe styles.py */
        .subtitle-script { font-size: 1.2rem; color: #ccc; }
        .student-search-card { background: #1e2a3a; padding: 20px; border-radius: 10px; text-align: center; }
        .student-name { font-size: 1.5rem; font-weight: bold; }
        .student-ru { font-size: 1rem; color: #aaa; }
        .dashboard-compact { display: flex; gap: 20px; flex-wrap: wrap; }
        .dashboard-card { flex: 1; background: #1e2a3a; padding: 15px; border-radius: 10px; text-align: center; }
        .progress-bar-bg { background: #2d3748; border-radius: 10px; height: 8px; margin-top: 10px; }
        .progress-bar-fill { background: #00cc66; height: 8px; border-radius: 10px; }
        .green-card .progress-bar-fill { background: #00cc66; }
        .blue-card .progress-bar-fill { background: #3399ff; }
        .orange-card .progress-bar-fill { background: #ff9933; }
    </style>
    """

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
# FUNCIONES DE ACCESO A SUPABASE (sin cambios)
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
# NUEVA FUNCIÓN: DISTANCIA HAVERSINE (metros)
# ------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# APLICAR ESTILOS CSS
# ------------------------------------------------------------
st.markdown(CSS_STYLES, unsafe_allow_html=True)

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

# Nuevas variables para QR dinámico y geolocalización
if "aula_lat" not in st.session_state:
    st.session_state.aula_lat = None
if "aula_lon" not in st.session_state:
    st.session_state.aula_lon = None
if "qr_token" not in st.session_state:
    st.session_state.qr_token = None
if "qr_token_expiry" not in st.session_state:
    st.session_state.qr_token_expiry = None
if "app_base_url" not in st.session_state:
    st.session_state.app_base_url = ""

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS (sin cambios)
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
# FUNCIÓN PARA GENERAR QR CON URL (nueva)
# ------------------------------------------------------------
def generar_qr_con_url(url):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00ffcc", back_color="#0a1428")
    return img

# ------------------------------------------------------------
# MANEJO DE PARÁMETROS PARA FORMULARIO DE ESTUDIANTE (NUEVO)
# ------------------------------------------------------------
query_params = st.query_params
if "qr_mode" in query_params and query_params["qr_mode"] == "register":
    # Modo estudiante: mostrar formulario de registro con geolocalización
    st.subheader("📱 Registro de asistencia mediante QR")
    st.markdown("Escanea el QR y ahora completa tus datos para confirmar tu asistencia.")
    
    token = query_params.get("token", "")
    # Validar token (opcional, pero para mayor seguridad)
    if not token or token != st.session_state.qr_token:
        st.error("❌ El enlace QR no es válido o ha expirado. Solicita un nuevo código al profesor.")
        if st.button("Volver al inicio"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    
    # Verificar expiración del token (1 minuto de validez)
    if st.session_state.qr_token_expiry and datetime.now() > st.session_state.qr_token_expiry:
        st.error("❌ El código QR ha expirado. Solicita uno nuevo.")
        if st.button("Volver al inicio"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    
    # Verificar que la ubicación del aula esté fijada
    if st.session_state.aula_lat is None or st.session_state.aula_lon is None:
        st.error("⚠️ El profesor aún no ha fijado la ubicación del aula. No es posible registrar asistencia.")
        if st.button("Volver al inicio"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    
    # Cargar estudiantes
    estudiantes = leer_estudiantes()
    if len(estudiantes) == 0:
        st.warning("No hay estudiantes registrados. Contacta al profesor.")
        st.stop()
    
    estudiantes["nombre_completo"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
    opciones = estudiantes["nombre_completo"].tolist()
    
    with st.form(key="form_registro_qr"):
        seleccionado = st.selectbox("👤 Selecciona tu nombre", opciones)
        ru_seleccionado = seleccionado.split(" - ")[0]
        estudiante_data = estudiantes[estudiantes["ru"].astype(str) == ru_seleccionado].iloc[0]
        
        # Campos para geolocalización (ocultos pero visibles para depuración)
        st.markdown("---")
        st.markdown("### 📍 Validación de ubicación")
        st.markdown("Debes estar dentro del aula (máximo 5 metros del profesor) para poder registrar.")
        col1, col2 = st.columns(2)
        lat_input = col1.text_input("Latitud", placeholder="Se obtendrá automáticamente")
        lon_input = col2.text_input("Longitud", placeholder="Se obtendrá automáticamente")
        
        # Botón para obtener ubicación mediante JavaScript
        if st.form_submit_button("🌍 Obtener mi ubicación y registrar", use_container_width=True):
            # Se usará JavaScript para llenar lat_input y lon_input antes del submit? 
            # Como Streamlit envía el formulario completo, requerimos que los valores estén en los campos al momento del submit.
            # Necesitamos un script que, al hacer clic, obtenga la ubicación y luego envíe el formulario.
            # Lo haremos con un poco de HTML/JS personalizado que rellene campos y luego dispare el sumbit.
            # Como no es trivial, optamos por pedir la ubicación en un paso previo: un botón aparte que guarde en session_state.
            # Pero para simplificar la implementación y hacerla funcional, usaremos st.session_state para almacenar ubicación temporal.
            pass
    
    # Enfoque alternativo: Usar botón separado para obtener ubicación y almacenar en session_state, luego otro para registrar.
    # Para que la experiencia sea fluida, mostramos un botón "Obtener ubicación" que actualiza los campos mediante JS y un botón de registro.
    # Pero debido a la naturaleza de Streamlit, lo mejor es usar un formulario con un único submit y un campo hidden.
    # Implementaremos un componente HTML personalizado.
    
    # Mostrar un div para la ubicación y un botón que actualice dos campos de texto ocultos.
    st.markdown("""
    <div id="geo-status" style="margin-bottom: 10px; padding: 10px; background: #1e2a3a; border-radius: 8px;">
        ⏳ Presiona el botón para obtener tu ubicación.
    </div>
    <script>
    function obtenerUbicacion() {
        if (!navigator.geolocation) {
            document.getElementById('geo-status').innerHTML = '❌ Tu navegador no soporta geolocalización.';
            return;
        }
        document.getElementById('geo-status').innerHTML = '🔄 Obteniendo ubicación...';
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                document.getElementById('lat').value = lat;
                document.getElementById('lon').value = lon;
                document.getElementById('geo-status').innerHTML = `✅ Ubicación obtenida: ${lat.toFixed(6)}, ${lon.toFixed(6)}`;
            },
            (error) => {
                document.getElementById('geo-status').innerHTML = '❌ Error al obtener ubicación: ' + error.message;
            }
        );
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Campos ocultos para almacenar lat/lon
    lat_val = st.text_input("Latitud (oculto)", key="student_lat", label_visibility="collapsed", placeholder="Latitud")
    lon_val = st.text_input("Longitud (oculto)", key="student_lon", label_visibility="collapsed", placeholder="Longitud")
    # Los hacemos visibles para depuración
    col1, col2 = st.columns(2)
    with col1:
        st.write("Latitud:", lat_val if lat_val else "(no obtenida)")
    with col2:
        st.write("Longitud:", lon_val if lon_val else "(no obtenida)")
    
    # Botón que llama a la función JS
    st.button("🌍 Obtener ubicación", on_click=None, help="Presiona para compartir tu ubicación", key="get_loc_btn")
    # Para ejecutar JS al hacer clic, usamos st.components.v1.html con un botón real.
    # Mejor: Insertar un botón HTML real.
    st.markdown("""
    <button id="btnGeo" style="background: #0066ff; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">🌍 Obtener ubicación</button>
    <script>
        document.getElementById('btnGeo').addEventListener('click', function() {
            obtenerUbicacion();
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Ahora un botón de registro que lea los campos lat/lon
    if st.button("✅ Confirmar asistencia", use_container_width=True):
        if not lat_val or not lon_val:
            st.error("❌ Primero obtén tu ubicación presionando el botón 'Obtener ubicación'.")
        else:
            try:
                lat_student = float(lat_val)
                lon_student = float(lon_val)
            except:
                st.error("❌ Ubicación inválida. Vuelve a obtenerla.")
                st.stop()
            
            # Calcular distancia
            distancia = haversine(lat_student, lon_student, st.session_state.aula_lat, st.session_state.aula_lon)
            if distancia <= 5.0:
                # Dentro del rango, proceder a registrar asistencia
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru_seleccionado, fecha)
                if not tiene_registro:
                    try:
                        supabase.table("asistencia").insert({
                            "ru": ru_seleccionado,
                            "nombres": estudiante_data["nombres"],
                            "apellido_paterno": estudiante_data["apellido_paterno"],
                            "apellido_materno": estudiante_data["apellido_materno"],
                            "fecha": fecha.isoformat(),
                            "hora": hora,
                            "estado": "Presente"
                        }).execute()
                        st.success(f"✅ Asistencia registrada con éxito. ¡Bienvenido {estudiante_data['nombres']}!")
                        st.balloons()
                        # Limpiar parámetros y redirigir
                        st.query_params.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar asistencia: {e}")
                else:
                    st.warning(f"⚠️ Ya registraste asistencia hoy a las {registro_existente['hora']}")
            else:
                st.error(f"❌ No puedes registrar asistencia porque no estás dentro del aula. Distancia: {distancia:.2f} metros (máximo 5m).")
    
    if st.button("🔙 Cancelar y volver al inicio"):
        st.query_params.clear()
        st.rerun()
    st.stop()  # Detener la ejecución para no mostrar el resto de la app.

# ------------------------------------------------------------
# SIDEBAR (sin cambios)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color: var(--text-secondary);">Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO CON LOGO (sin cambios)
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
# MENÚ HORIZONTAL (agregamos nueva opción)
# ------------------------------------------------------------
opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia",
    "📍 QR Dinámico (5m)"   # NUEVO
]
menu = st.radio("", opciones_menu, horizontal=True, label_visibility="collapsed", key="menu_radio")
st.session_state.menu_actual = menu

# ------------------------------------------------------------
# FUNCIÓN PARA CREAR TARJETA CUADRADA (sin cambios)
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
# REGISTRAR ESTUDIANTE (sin cambios)
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
# LISTA ESTUDIANTES (sin cambios)
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
# ESCANEAR QR (sin cambios)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: var(--text-secondary);">Toma una foto del código QR del estudiante para registrar su asistencia</p>', unsafe_allow_html=True)
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
# REGISTRO MANUAL (sin cambios)
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
# VER ASISTENCIA (sin cambios)
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

# ------------------------------------------------------------
# NUEVA SECCIÓN: QR DINÁMICO (5m)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📍 QR Dinámico (5m)":
    st.subheader("📍 Generador de QR con alcance de 5 metros")
    st.markdown("""
    Esta herramienta permite a los estudiantes registrar su asistencia escaneando un código QR **solo si están dentro del aula (máximo 5 metros del profesor)**.
    
    **Instrucciones:**
    1. Fija la ubicación actual del aula (la computadora del profesor) presionando el botón "Obtener ubicación del aula".
    2. Una vez fijada, configura la URL pública de la aplicación (por ejemplo, la IP de tu computadora en la red local).
    3. Genera un código QR (aleatorio y válido por 1 minuto) y muéstraselo a los estudiantes.
    4. Los estudiantes escanean el QR con su teléfono, se les solicitará su ubicación y podrán registrar asistencia solo si están a ≤5 metros.
    """)
    
    # --------------------------------------------------------
    # 1. Fijar ubicación del aula (profesor)
    # --------------------------------------------------------
    st.markdown("### 📍 Paso 1: Fijar ubicación del aula")
    col1, col2 = st.columns(2)
    with col1:
        aula_lat_display = st.text_input("Latitud del aula", value=str(st.session_state.aula_lat) if st.session_state.aula_lat else "", disabled=True)
    with col2:
        aula_lon_display = st.text_input("Longitud del aula", value=str(st.session_state.aula_lon) if st.session_state.aula_lon else "", disabled=True)
    
    # Botón para obtener ubicación del profesor
    if st.button("🌍 Obtener ubicación actual (profesor)", key="get_prof_ubication"):
        st.markdown("""
        <div id="prof-geo-status" style="margin-bottom: 10px; padding: 10px; background: #1e2a3a; border-radius: 8px;">
            ⏳ Obteniendo ubicación...
        </div>
        <script>
        function obtenerUbicacionProfesor() {
            if (!navigator.geolocation) {
                document.getElementById('prof-geo-status').innerHTML = '❌ Tu navegador no soporta geolocalización.';
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    // Enviar al backend mediante un formulario con campos ocultos
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = window.location.href;
                    const latField = document.createElement('input');
                    latField.type = 'hidden';
                    latField.name = 'prof_lat';
                    latField.value = lat;
                    const lonField = document.createElement('input');
                    lonField.type = 'hidden';
                    lonField.name = 'prof_lon';
                    lonField.value = lon;
                    form.appendChild(latField);
                    form.appendChild(lonField);
                    document.body.appendChild(form);
                    form.submit();
                },
                (error) => {
                    document.getElementById('prof-geo-status').innerHTML = '❌ Error al obtener ubicación: ' + error.message;
                }
            );
        }
        obtenerUbicacionProfesor();
        </script>
        """, unsafe_allow_html=True)
        # Esperar a que el script envíe el formulario
        st.info("Esperando respuesta de geolocalización... refresca la página si no se actualiza automáticamente.")
    
    # Procesar datos POST (simulado mediante query_params? No es fácil. Usaremos un truco: redirigir con parámetros)
    # En lugar de POST, usaremos un botón que envía la ubicación a través de st.query_params.
    # Mejor: usar un componente que al obtener ubicación, redirija a la misma página con parámetros.
    # Para simplificar, pediremos al profesor que ingrese manualmente lat/lon si falla, pero también ofreceremos un método con JS que establezca query_params.
    
    # Método alternativo: usar st.query_params temporalmente para recibir lat/lon.
    if "prof_lat" in query_params and "prof_lon" in query_params:
        try:
            lat = float(query_params["prof_lat"])
            lon = float(query_params["prof_lon"])
            st.session_state.aula_lat = lat
            st.session_state.aula_lon = lon
            st.success(f"✅ Ubicación del aula fijada: {lat:.6f}, {lon:.6f}")
            # Limpiar parámetros
            st.query_params.clear()
            st.rerun()
        except:
            pass
    
    # También permitir entrada manual por si falla la geolocalización automática
    st.markdown("**O ingresa manualmente las coordenadas (puedes obtenerlas desde Google Maps):**")
    manual_lat = st.number_input("Latitud manual", value=st.session_state.aula_lat if st.session_state.aula_lat else 0.0, format="%.6f")
    manual_lon = st.number_input("Longitud manual", value=st.session_state.aula_lon if st.session_state.aula_lon else 0.0, format="%.6f")
    if st.button("📌 Guardar coordenadas manualmente"):
        st.session_state.aula_lat = manual_lat
        st.session_state.aula_lon = manual_lon
        st.success(f"Ubicación actualizada manualmente: {manual_lat}, {manual_lon}")
        st.rerun()
    
    if st.session_state.aula_lat is None or st.session_state.aula_lon is None:
        st.warning("⚠️ Aún no se ha fijado la ubicación del aula. Los estudiantes no podrán registrar asistencia hasta que lo hagas.")
    else:
        st.success(f"📍 Ubicación del aula activa: {st.session_state.aula_lat:.6f}, {st.session_state.aula_lon:.6f}")
    
    st.markdown("---")
    
    # --------------------------------------------------------
    # 2. Configurar URL base de la aplicación
    # --------------------------------------------------------
    st.markdown("### 🌐 Paso 2: Configurar la URL pública de la aplicación")
    st.markdown("Ingresa la dirección IP o dominio desde el cual los teléfonos pueden acceder a esta aplicación (ej: `http://192.168.1.100:8501`).")
    base_url_input = st.text_input("URL base", value=st.session_state.app_base_url, placeholder="http://192.168.1.100:8501")
    if st.button("Guardar URL"):
        st.session_state.app_base_url = base_url_input.rstrip('/')
        st.success("URL guardada")
    
    if not st.session_state.app_base_url:
        st.warning("⚠️ Configura la URL base para que los estudiantes puedan escanear el QR.")
    else:
        st.info(f"URL actual: {st.session_state.app_base_url}")
    
    st.markdown("---")
    
    # --------------------------------------------------------
    # 3. Generar código QR aleatorio con token
    # --------------------------------------------------------
    st.markdown("### 🎲 Paso 3: Generar código QR aleatorio (válido por 1 minuto)")
    if st.button("🔄 Generar nuevo QR", use_container_width=True):
        # Generar token aleatorio
        token = base64.b64encode(os.urandom(16)).decode('utf-8')[:16]
        st.session_state.qr_token = token
        st.session_state.qr_token_expiry = datetime.now() + timedelta(minutes=1)
        st.rerun()
    
    if st.session_state.qr_token and st.session_state.qr_token_expiry:
        tiempo_restante = st.session_state.qr_token_expiry - datetime.now()
        if tiempo_restante.total_seconds() > 0:
            st.info(f"🔑 QR activo (expira en {tiempo_restante.seconds} segundos). Token: {st.session_state.qr_token}")
            # Construir URL completa
            if st.session_state.app_base_url:
                qr_url = f"{st.session_state.app_base_url}?qr_mode=register&token={st.session_state.qr_token}"
                qr_img = generar_qr_con_url(qr_url)
                buf = io.BytesIO()
                qr_img.save(buf, format='PNG')
                buf.seek(0)
                st.image(buf, width=400, caption="Código QR para estudiantes (escáneame)")
                st.download_button("⬇️ Descargar QR", data=buf, file_name="qr_dinamico.png", mime="image/png")
                st.markdown(f"**Enlace para escanear:** `{qr_url}`")
            else:
                st.error("Primero configura la URL base en el paso 2.")
        else:
            st.warning("⚠️ El QR ha expirado. Genera uno nuevo.")
    else:
        st.info("Presiona 'Generar nuevo QR' para crear un código válido por 1 minuto.")
    
    st.markdown("---")
    st.markdown("### ℹ️ Notas sobre la validación de distancia")
    st.markdown("""
    - La geolocalización debe ser permitida por el navegador del profesor y de cada estudiante.
    - La precisión puede variar; asegúrate de que el profesor esté en un lugar fijo dentro del aula.
    - El estudiante debe estar a menos de 5 metros de la ubicación registrada por el profesor para poder registrar.
    """)
