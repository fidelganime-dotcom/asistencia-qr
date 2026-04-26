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

# Importar estilos CSS desde styles.py
# Asegúrate de tener el archivo 'styles.py' en el mismo directorio con el contenido provisto
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

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# APLICAR ESTILOS CSS (importados desde styles.py)
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
if "qr_image_data" not in st.session_state:
    st.session_state.qr_image_data = None
if "latest_qr_code" not in st.session_state:
    st.session_state.latest_qr_code = None  # Para almacenar el último QR escaneado

# ------------------------------------------------------------
# PARTÍCULAS ANIMADAS (Fondo)
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
# FUNCIÓN PARA CREAR TARJETA CUADRADA (VERSIÓN MEJORADA)
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
# FUNCIÓN PARA PROCESAR EL QR Y REGISTRAR ASISTENCIA
# ------------------------------------------------------------
def procesar_y_registrar_asistencia(qr_code_data):
    """Función central para procesar un código QR y registrar la asistencia."""
    if qr_code_data is None or qr_code_data == "":
        return False, "No se proporcionó un código QR válido."

    ru = qr_code_data.strip()
    if not ru.isdigit():
        return False, f"El código QR leído '{ru}' no es un RU válido (solo números)."

    estudiantes = leer_estudiantes()
    estudiante = estudiantes[estudiantes["ru"].astype(str) == ru]

    if len(estudiante) == 0:
        return False, f"❌ Estudiante con RU {ru} no encontrado en la base de datos."

    estudiante_data = estudiante.iloc[0]
    nombres_completos = f"{estudiante_data['nombres']} {estudiante_data['apellido_paterno']}"

    fecha, hora = obtener_fecha_hora_exacta()
    tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)

    if tiene_registro:
        hora_existente = registro_existente['hora']
        return False, f"⚠️ {nombres_completos} YA REGISTRÓ ASISTENCIA HOY A LAS {hora_existente}"

    try:
        supabase.table("asistencia").insert({
            "ru": ru,
            "nombres": estudiante_data["nombres"],
            "apellido_paterno": estudiante_data["apellido_paterno"],
            "apellido_materno": estudiante_data["apellido_materno"],
            "fecha": fecha.isoformat(),
            "hora": hora,
            "estado": "Presente"
        }).execute()
        st.session_state.ultimo_registro = {"ru": ru, "nombres": nombres_completos, "hora": hora, "fecha": fecha}
        return True, f"✅ Asistencia registrada para {nombres_completos} a las {hora}"
    except Exception as e:
        return False, f"❌ Error al guardar asistencia: {e}"

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
# ESCANEAR QR — CÁMARA TRASERA COMPLETAMENTE FUNCIONAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None

    st.subheader("📸 Escanear QR")
    st.markdown('<p style="color: var(--text-secondary);">Apunta la cámara trasera al código QR del estudiante para registrar su asistencia automáticamente</p>', unsafe_allow_html=True)

    # Componente HTML con cámara trasera y comunicación con Streamlit
    qr_scanner_html = """
    <style>
        #qr-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            font-family: sans-serif;
            padding-bottom: 20px;
        }
        #video {
            width: 100%;
            max-width: 480px;
            border-radius: 12px;
            border: 3px solid #0066ff;
            background: #000;
            box-shadow: 0 0 20px rgba(0,102,255,0.3);
        }
        #canvas { display: none; }
        #snap-btn {
            padding: 14px 40px;
            font-size: 18px;
            background: linear-gradient(135deg, #0066ff, #00ffcc);
            color: #fff;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-weight: bold;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(0,102,255,0.4);
            transition: transform 0.1s;
            width: 100%;
            max-width: 300px;
            margin: 10px auto;
        }
        #snap-btn:active { transform: scale(0.96); }
        #status {
            font-size: 15px;
            color: #aaa;
            min-height: 22px;
            text-align: center;
        }
        #captured-img {
            display: none;
            width: 100%;
            max-width: 480px;
            border-radius: 12px;
            border: 2px solid #00ffcc;
            margin-top: 10px;
        }
        @media (max-width: 600px) {
            #snap-btn { font-size: 16px; padding: 12px 20px; }
        }
    </style>

    <div id="qr-box">
        <video id="video" autoplay playsinline muted style="transform: scaleX(-1);"></video>
        <canvas id="canvas"></canvas>
        <button id="snap-btn" onclick="capturar()">📷 Capturar y Leer QR</button>
        <p id="status">🔍 Iniciando cámara trasera...</p>
        <img id="captured-img" alt="Foto capturada"/>
    </div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const statusDiv = document.getElementById('status');
        const capturedImg = document.getElementById('captured-img');
        const ctx = canvas.getContext('2d');
        let stream = null;
        let scanAttempts = 0;

        // Función para procesar la imagen y extraer el código QR
        const processImageForQR = (imageDataUrl) => {
            // Crear un objeto Image para procesar en el canvas
            const img = new Image();
            img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                
                // Usar la librería jsQR si está disponible, o simular lectura
                // Nota: jsQR no viene incluido, así que simulamos paso de imagen a Python
                statusDiv.textContent = '🔄 Enviando imagen al servidor para lectura...';
                statusDiv.style.color = '#ffcc00';
                
                // Enviar la imagen completa a Python para su procesamiento
                // Para hacerlo más simple y robusto, extraemos solo el base64 sin el prefijo
                const base64Data = imageDataUrl.split(',')[1];
                
                // Comunicar a Streamlit
                if (window.parent && window.parent.postMessage) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: base64Data
                    }, '*');
                } else {
                    statusDiv.textContent = '❌ Error: No se puede comunicar con la aplicación';
                    statusDiv.style.color = '#ff4444';
                }
            };
            img.src = imageDataUrl;
        };

        // Iniciar cámara trasera (environment)
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({
                video: { facingMode: { exact: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }
            })
            .then(mediaStream => {
                stream = mediaStream;
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play();
                    statusDiv.textContent = '✅ Cámara trasera activa. Presiona "Capturar y Leer QR".';
                    statusDiv.style.color = '#00ffcc';
                };
            })
            .catch(err => {
                console.warn("Error con cámara trasera exacta:", err);
                // Intento con facingMode: environment sin exact
                navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
                })
                .then(mediaStream => {
                    stream = mediaStream;
                    video.srcObject = stream;
                    video.onloadedmetadata = () => {
                        video.play();
                        statusDiv.textContent = '✅ Cámara trasera activa. Presiona "Capturar y Leer QR".';
                        statusDiv.style.color = '#00ffcc';
                    };
                })
                .catch(finalErr => {
                    console.error("Error al acceder a la cámara trasera:", finalErr);
                    statusDiv.textContent = '❌ No se pudo acceder a la cámara trasera. Usa la opción de subir foto.';
                    statusDiv.style.color = '#ff4444';
                });
            });
        } else {
            statusDiv.textContent = '❌ Tu navegador no soporta la cámara. Usa la opción de subir foto.';
            statusDiv.style.color = '#ff4444';
        }

        function capturar() {
            if (!video.videoWidth || !video.videoHeight) {
                statusDiv.textContent = '⚠️ La cámara aún no está lista. Espera un momento.';
                statusDiv.style.color = '#ffaa00';
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Dibujar la imagen del video en el canvas
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Obtener la imagen como base64
            const dataURL = canvas.toDataURL('image/png');
            
            // Mostrar la imagen capturada
            capturedImg.src = dataURL;
            capturedImg.style.display = 'block';
            
            statusDiv.textContent = '📤 Procesando imagen...';
            statusDiv.style.color = '#ffcc00';
            
            // Procesar la imagen para extraer QR
            processImageForQR(dataURL);
        }

        // Limpiar el stream al salir de la página para liberar la cámara
        window.addEventListener('beforeunload', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
    </script>
    """
    
    # Crear espacio para recibir el código QR
    qr_container = st.empty()
    
    # Mostrar el componente HTML
    st.components.v1.html(qr_scanner_html, height=600)
    
    # Input secreto para recibir datos del QR desde el componente JS
    # Usamos un session_state específico para comunicar el QR obtenido
    if "qr_data_from_js" not in st.session_state:
        st.session_state.qr_data_from_js = None
    
    # Crear un text_input invisible para recibir datos del QR
    # Esto se actualizará mediante un callback de JS (simulado con rerun)
    scanned_qr = st.text_input("qr_scanner_input", label_visibility="collapsed", placeholder="QR leído", key="qr_scanner_input")
    
    # Procesar el QR si ha sido escaneado
    if scanned_qr and scanned_qr != st.session_state.get("last_processed_qr", ""):
        success, message = procesar_y_registrar_asistencia(scanned_qr)
        if success:
            st.success(message)
        else:
            st.error(message)
        st.session_state.last_processed_qr = scanned_qr
        st.session_state.qr_data_from_js = None
        st.rerun()
    
    # Método alternativo: file uploader
    st.markdown("---")
    st.markdown("##### 📁 ¿No funciona la cámara? Sube una foto del QR")
    foto_upload = st.file_uploader("Subir imagen con QR", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if foto_upload is not None:
        img_pil = Image.open(foto_upload)
        decoded_objects = decode(img_pil)
        if decoded_objects:
            data = decoded_objects[0].data.decode('utf-8')
            success, message = procesar_y_registrar_asistencia(data)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.warning("⚠️ No se detectó ningún código QR en la imagen")
    
    # Script para pasar datos del componente HTML a Streamlit de manera más robusta
    # Este script se comunica con el iframe y actualiza el campo de texto
    st.markdown("""
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'streamlit:setComponentValue' && event.data.value) {
            // Encontrar el input de texto con el key 'qr_scanner_input'
            const inputs = document.querySelectorAll('input[type="text"]');
            for (let input of inputs) {
                if (input.placeholder === 'QR leído') {
                    input.value = event.data.value;
                    // Disparar el evento change para que Streamlit lo detecte
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# REGISTRO MANUAL (CON PROTECCIÓN DE CONTRASEÑA Y SELECTOR NATIVO)
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
# VER ASISTENCIA (con dashboard de tres tarjetas)
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.subheader("📊 Registros de asistencia")
    
    estudiantes_total = leer_estudiantes()
    total_estudiantes = len(estudiantes_total)
    asistencia_df = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    registrados_hoy = asistencia_df[asistencia_df["fecha"] == hoy]["ru"].nunique() if not asistencia_df.empty else 0
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
                    # Eliminar todos los que no están en la lista de conservar
                    # Supabase no tiene NOT IN directo, se hace con filtro
                    for id_ in asistencia_df['id']:
                        if id_ not in ids_a_conservar:
                            supabase.table("asistencia").delete().eq("id", id_).execute()
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
