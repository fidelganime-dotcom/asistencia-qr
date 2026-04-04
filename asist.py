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
st.set_page_config(page_title="Sistema de Asistencia", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------------------------------------
# INICIALIZAR SESSION STATE
# ------------------------------------------------------------
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "estudiantes"
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
# ESTILOS CSS MODERNOS (Diseño iOS/Android)
# ------------------------------------------------------------
st.markdown("""
<style>
    /* Reset y variables modernas */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #000000;
        --bg-secondary: #0c0c0c;
        --bg-tertiary: #1c1c1e;
        --surface: #1c1c1e;
        --surface-secondary: #2c2c2e;
        --primary: #0a84ff;
        --primary-dark: #0066cc;
        --secondary: #5e5ce0;
        --success: #30d158;
        --warning: #ff9f0a;
        --danger: #ff453a;
        --text-primary: #ffffff;
        --text-secondary: #8e8e93;
        --text-tertiary: #636366;
        --border: #38383a;
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.5);
        --blur-bg: rgba(28,28,30,0.8);
    }
    
    /* Estilo base */
    .stApp {
        background: var(--bg-primary);
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif;
    }
    
    /* Ocultar sidebar */
    .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Contenedor principal */
    .main-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 16px;
        padding-bottom: 80px;
    }
    
    /* Header moderno */
    .app-header {
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        position: sticky;
        top: 0;
        z-index: 100;
        padding: 16px;
        margin: -16px -16px 16px -16px;
        border-bottom: 0.5px solid var(--border);
    }
    
    .app-title {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #0a84ff, #5e5ce0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    .app-subtitle {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    
    /* Navegación inferior estilo iOS */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(28,28,30,0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        display: flex;
        justify-content: space-around;
        padding: 8px 16px 20px 16px;
        border-top: 0.5px solid var(--border);
        z-index: 100;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        background: none;
        border: none;
        padding: 8px 12px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        flex: 1;
        max-width: 80px;
    }
    
    .nav-item.active {
        background: var(--primary);
    }
    
    .nav-icon {
        font-size: 24px;
    }
    
    .nav-label {
        font-size: 11px;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .nav-item.active .nav-label {
        color: var(--text-primary);
    }
    
    /* Tarjetas estilo iOS */
    .ios-card {
        background: var(--surface);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    .ios-card:active {
        transform: scale(0.98);
    }
    
    /* Botones modernos */
    .modern-btn {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: inherit;
        position: relative;
        overflow: hidden;
    }
    
    .modern-btn:active {
        transform: scale(0.97);
        opacity: 0.8;
    }
    
    .modern-btn-secondary {
        background: var(--surface-secondary);
        color: var(--primary);
    }
    
    .modern-btn-danger {
        background: var(--danger);
    }
    
    /* Inputs estilo iOS */
    .ios-input {
        background: var(--surface-secondary);
        border: 0.5px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px;
        color: var(--text-primary);
        font-size: 16px;
        width: 100%;
        font-family: inherit;
        transition: all 0.2s ease;
    }
    
    .ios-input:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(10,132,255,0.2);
    }
    
    .ios-input::placeholder {
        color: var(--text-tertiary);
    }
    
    /* Select estilo iOS */
    .ios-select {
        background: var(--surface-secondary);
        border: 0.5px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px;
        color: var(--text-primary);
        font-size: 16px;
        width: 100%;
        cursor: pointer;
        font-family: inherit;
    }
    
    /* Tabla estilo iOS */
    .ios-table {
        background: var(--surface);
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 16px;
    }
    
    .ios-table-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 0.5px solid var(--border);
        transition: background 0.2s ease;
    }
    
    .ios-table-item:active {
        background: var(--surface-secondary);
    }
    
    .ios-table-item:last-child {
        border-bottom: none;
    }
    
    /* Badges */
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
    }
    
    .badge-success {
        background: rgba(48,209,88,0.2);
        color: var(--success);
    }
    
    .badge-warning {
        background: rgba(255,159,10,0.2);
        color: var(--warning);
    }
    
    .badge-danger {
        background: rgba(255,69,58,0.2);
        color: var(--danger);
    }
    
    /* Dashboard cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background: var(--surface);
        border-radius: 16px;
        padding: 16px 8px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .stat-label {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
    }
    
    /* Modal de contraseña */
    .password-modal {
        background: var(--surface);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Utilidades */
    .text-center { text-align: center; }
    .mt-2 { margin-top: 8px; }
    .mt-3 { margin-top: 12px; }
    .mt-4 { margin-top: 16px; }
    .mb-2 { margin-bottom: 8px; }
    .mb-3 { margin-bottom: 12px; }
    .mb-4 { margin-bottom: 16px; }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 4px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }
    
    /* Ajustes Streamlit */
    .stAlert {
        background: var(--surface) !important;
        border-radius: 12px !important;
        border: 0.5px solid var(--border) !important;
        padding: 12px 16px !important;
        margin: 12px 0 !important;
    }
    
    div[data-testid="stCameraInput"] video {
        border-radius: 16px;
        margin-bottom: 16px;
    }
    
    .stSpinner > div {
        border-color: var(--primary) !important;
    }
</style>

<script>
    // Navegación inferior
    function setActiveNav(activeId) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            if (item.getAttribute('data-nav') === activeId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# FUNCIÓN PARA RENDERIZAR NAVEGACIÓN
# ------------------------------------------------------------
def render_bottom_nav():
    st.markdown(f"""
    <div class="bottom-nav">
        <button class="nav-item {'active' if st.session_state.menu_actual == 'estudiantes' else ''}" data-nav="estudiantes" onclick="setActiveNav('estudiantes');">
            <div class="nav-icon">📝</div>
            <div class="nav-label">Registrar</div>
        </button>
        <button class="nav-item {'active' if st.session_state.menu_actual == 'lista' else ''}" data-nav="lista" onclick="setActiveNav('lista');">
            <div class="nav-icon">📋</div>
            <div class="nav-label">Lista</div>
        </button>
        <button class="nav-item {'active' if st.session_state.menu_actual == 'escanear' else ''}" data-nav="escanear" onclick="setActiveNav('escanear');">
            <div class="nav-icon">📸</div>
            <div class="nav-label">Escanear</div>
        </button>
        <button class="nav-item {'active' if st.session_state.menu_actual == 'manual' else ''}" data-nav="manual" onclick="setActiveNav('manual');">
            <div class="nav-icon">✍️</div>
            <div class="nav-label">Manual</div>
        </button>
        <button class="nav-item {'active' if st.session_state.menu_actual == 'asistencia' else ''}" data-nav="asistencia" onclick="setActiveNav('asistencia');">
            <div class="nav-icon">📊</div>
            <div class="nav-label">Ver</div>
        </button>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <div class="app-title">Sistema de Asistencia</div>
    <div class="app-subtitle">Ingeniería de Sistemas - UAP</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# ------------------------------------------------------------
# MANEJO DE NAVEGACIÓN CON BOTONES
# ------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("📝", key="nav_reg", use_container_width=True):
        st.session_state.menu_actual = "estudiantes"
        st.rerun()
with col2:
    if st.button("📋", key="nav_list", use_container_width=True):
        st.session_state.menu_actual = "lista"
        st.rerun()
with col3:
    if st.button("📸", key="nav_scan", use_container_width=True):
        st.session_state.menu_actual = "escanear"
        st.rerun()
with col4:
    if st.button("✍️", key="nav_man", use_container_width=True):
        st.session_state.menu_actual = "manual"
        st.rerun()
with col5:
    if st.button("📊", key="nav_asist", use_container_width=True):
        st.session_state.menu_actual = "asistencia"
        st.rerun()

st.markdown("---")

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "estudiantes":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("### 📝 Nuevo Estudiante")
    
    with st.container():
        ru = st.text_input("RU", placeholder="Ingrese el RU (solo números)", key="ru_input")
        nombres = st.text_input("Nombres", placeholder="Ingrese los nombres", key="nombres_input")
        paterno = st.text_input("Apellido Paterno", placeholder="Ingrese el apellido paterno", key="paterno_input")
        materno = st.text_input("Apellido Materno", placeholder="Ingrese el apellido materno", key="materno_input")
        
        if st.button("💾 Guardar Estudiante", use_container_width=True):
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
                        
                        st.image(img_bytes, width=250, caption="Código QR")
                        buf = io.BytesIO()
                        qr_img.save(buf, format="PNG")
                        buf.seek(0)
                        st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "lista":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("### 📋 Lista de Estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        for _, est in estudiantes.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="ios-card">
                    <div style="font-weight: 600; font-size: 16px;">{est['nombres']} {est['apellido_paterno']}</div>
                    <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">RU: {est['ru']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 🔍 Buscar Estudiante")
        ru_buscar = st.text_input("Ingrese RU", placeholder="Código Único", key="buscar_ru")
        if st.button("Buscar", use_container_width=True) and ru_buscar:
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_buscar]
            if len(estudiante) > 0:
                est = estudiante.iloc[0]
                qr_img = qrcode.make(est['ru'])
                qr_buffer = io.BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                st.markdown(f"""
                <div class="ios-card" style="text-align: center;">
                    <div style="font-weight: 700; font-size: 20px; margin-bottom: 8px;">{est['nombres']} {est['apellido_paterno']}</div>
                    <div style="color: var(--text-secondary); margin-bottom: 16px;">RU: {est['ru']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.image(qr_buffer, width=200)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 QR", data=qr_buffer.getvalue(), file_name=f"{est['ru']}_qr.png", mime="image/png", use_container_width=True)
                with col2:
                    tarjeta_img = crear_tarjeta_estudiante(est)
                    st.download_button("📇 Tarjeta", data=tarjeta_img, file_name=f"tarjeta_{est['ru']}.png", mime="image/png", use_container_width=True)
            else:
                st.warning("⚠️ RU no encontrado")
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------
elif st.session_state.menu_actual == "escanear":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("### 📸 Escanear QR")
    st.caption("Toma una foto del código QR del estudiante")
    
    foto = st.camera_input("", label_visibility="collapsed")
    if foto is not None:
        img = Image.open(foto)
        decoded_objects = decode(img)
        
        if decoded_objects:
            ru = decoded_objects[0].data.decode('utf-8')
            estudiantes = leer_estudiantes()
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru]
            
            if len(estudiante) > 0:
                est = estudiante.iloc[0]
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
                
                if not tiene_registro:
                    try:
                        supabase.table("asistencia").insert({
                            "ru": ru,
                            "nombres": est["nombres"],
                            "apellido_paterno": est["apellido_paterno"],
                            "apellido_materno": est["apellido_materno"],
                            "fecha": fecha.isoformat(),
                            "hora": hora,
                            "estado": "Presente"
                        }).execute()
                        st.success(f"✅ {est['nombres']} registrado a las {hora}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning(f"⚠️ {est['nombres']} ya registró a las {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó código QR")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "manual":
    if not st.session_state.manual_auth:
        st.markdown("### 🔒 Acceso Restringido")
        with st.form(key="password_form"):
            password = st.text_input("Contraseña", type="password", placeholder="********")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if password == "pocoyo123":
                    st.session_state.manual_auth = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
    else:
        st.markdown("### ✍️ Registrar Asistencia Manual")
        estudiantes = leer_estudiantes()
        
        if len(estudiantes) > 0:
            estudiantes["display"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            opciones = estudiantes["display"].tolist()
            
            seleccionado = st.selectbox("Seleccionar estudiante", opciones, key="select_manual")
            
            if seleccionado:
                ru_seleccionado = seleccionado.split(" - ")[0]
                estudiante_data = estudiantes[estudiantes["ru"].astype(str) == ru_seleccionado].iloc[0]
                
                st.markdown(f"""
                <div class="ios-card">
                    <div style="font-weight: 600;">{estudiante_data['nombres']} {estudiante_data['apellido_paterno']}</div>
                    <div style="font-size: 13px; color: var(--text-secondary);">RU: {estudiante_data['ru']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, _ = verificar_registro_duplicado(ru_seleccionado, fecha)
                
                if tiene_registro:
                    st.warning("⚠️ Este estudiante ya registró hoy")
                    st.button("Registrar", disabled=True, use_container_width=True)
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
elif st.session_state.menu_actual == "asistencia":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown("### 📊 Registros de Asistencia")
    
    estudiantes_total = leer_estudiantes()
    total_estudiantes = len(estudiantes_total)
    asistencia_df = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    registrados_hoy = asistencia_df[asistencia_df["fecha"] == hoy]["ru"].nunique()
    faltantes = total_estudiantes - registrados_hoy
    
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_estudiantes}</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{registrados_hoy}</div>
            <div class="stat-label">Presentes</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{faltantes}</div>
            <div class="stat-label">Faltantes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(asistencia_df) > 0:
        st.markdown("### 📋 Últimos registros")
        for _, reg in asistencia_df.head(10).iterrows():
            estado_color = "success" if reg['estado'] == "Presente" else "warning" if reg['estado'] == "Tarde" else "danger"
            st.markdown(f"""
            <div class="ios-table-item">
                <div>
                    <div style="font-weight: 500;">{reg['nombres']} {reg['apellido_paterno']}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">RU: {reg['ru']} | {reg['fecha']}</div>
                </div>
                <div>
                    <span class="badge badge-{estado_color}">{reg['estado']}</span>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">{reg['hora']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(asistencia_df) > 0:
            st.markdown("### ⬇️ Exportar datos")
            archivo_descarga = "asistencia_temp.xlsx"
            asistencia_df.to_excel(archivo_descarga, index=False)
            with open(archivo_descarga, "rb") as file:
                st.download_button("📥 Descargar Excel", data=file, file_name=f"asistencia_{hoy}.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay registros de asistencia")

# ------------------------------------------------------------
# CIERRE DEL CONTENEDOR PRINCIPAL
# ------------------------------------------------------------
st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# FUNCIÓN PARA TARJETA DE ESTUDIANTE
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
