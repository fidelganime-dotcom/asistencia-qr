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
st.set_page_config(
    page_title="Sistema QR Attendance", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="📱"
)

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
# ✨ NUEVO CSS - DISEÑO MOBILE-FIRST DARK MODERNO ✨
# ------------------------------------------------------------
st.markdown("""
<style>
    /* ===== VARIABLES GLOBALES - SISTEMA DE DISEÑO ===== */
    :root {
        /* Colores base - Dark Mode nativo */
        --bg-primary: #09090b;
        --bg-secondary: #18181b;
        --bg-tertiary: #27272a;
        --bg-elevated: #3f3f46;
        
        /* Colores de acento - Sistema monocromático */
        --accent-primary: #ffffff;
        --accent-secondary: #a1a1aa;
        --accent-tertiary: #71717a;
        
        /* Colores de estado */
        --success: #22c55e;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: #3b82f6;
        
        /* Tipografía del sistema */
        --font-stack: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        
        /* Espaciado y bordes */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        --radius-full: 9999px;
        
        /* Sombras sutiles estilo sistema */
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -1px rgba(0,0,0,0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5), 0 4px 6px -2px rgba(0,0,0,0.4);
        
        /* Transiciones */
        --transition-fast: 150ms ease;
        --transition-normal: 250ms ease;
        --transition-slow: 400ms ease;
        
        /* Touch targets mobile */
        --touch-min: 44px;
    }

    /* ===== RESET Y BASE ===== */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    .stApp {
        background: var(--bg-primary);
        font-family: var(--font-stack);
        color: var(--accent-primary);
        -webkit-font-smoothing: antialiased;
    }

    /* ===== HEADER COMPACTO MOBILE ===== */
    [data-testid="stHeader"] {
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--bg-tertiary) !important;
        padding: 8px 16px !important;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    [data-testid="stHeader"] .stAppViewBlock {
        padding: 0 !important;
    }

    /* ===== TÍTULOS MINIMALISTAS ===== */
    h1, h2, h3, h4 {
        color: var(--accent-primary);
        font-weight: 600;
        letter-spacing: -0.025em;
        line-height: 1.3;
    }
    h1 { font-size: 1.5rem; margin: 0 0 12px; }
    h2 { font-size: 1.25rem; margin: 20px 0 12px; color: var(--accent-secondary); }
    h3 { font-size: 1.1rem; margin: 16px 0 8px; }

    /* ===== NAVIGATION MOBILE-FIRST ===== */
    .nav-container {
        display: flex;
        gap: 4px;
        padding: 8px;
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        margin: 12px 0 20px;
        overflow-x: auto;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .nav-container::-webkit-scrollbar { display: none; }
    
    .nav-item {
        flex: 0 0 auto;
        padding: 10px 16px;
        background: transparent;
        border: none;
        border-radius: var(--radius-md);
        color: var(--accent-tertiary);
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--transition-fast);
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 6px;
        min-height: var(--touch-min);
    }
    .nav-item:hover {
        background: var(--bg-tertiary);
        color: var(--accent-primary);
    }
    .nav-item.active {
        background: var(--accent-primary);
        color: var(--bg-primary);
        font-weight: 600;
    }
    
    /* Ocultar radio nativo de Streamlit para nav */
    div[data-testid="stRadio"] { display: none !important; }
    div[data-testid="stRadio"] + div { display: none !important; }

    /* ===== TARJETAS MODERNAS ===== */
    .card {
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--bg-tertiary);
        padding: 16px;
        margin: 12px 0;
        transition: all var(--transition-normal);
    }
    .card:hover {
        border-color: var(--bg-elevated);
        transform: translateY(-1px);
    }
    .card.elevated {
        background: var(--bg-tertiary);
        box-shadow: var(--shadow-md);
    }
    .card.compact {
        padding: 12px;
        margin: 8px 0;
    }

    /* ===== BOTONES SISTEMA - MOBILE OPTIMIZED ===== */
    .stButton > button {
        background: var(--accent-primary) !important;
        color: var(--bg-primary) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 12px 20px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        min-height: var(--touch-min) !important;
        min-width: var(--touch-min) !important;
        transition: all var(--transition-fast) !important;
        box-shadow: var(--shadow-sm) !important;
        width: 100% !important;
        font-family: var(--font-stack) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-md) !important;
        filter: brightness(0.95) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
        filter: brightness(0.9) !important;
    }
    .stButton > button[disabled] {
        background: var(--bg-tertiary) !important;
        color: var(--accent-tertiary) !important;
        cursor: not-allowed !important;
        transform: none !important;
    }
    
    /* Botones secundarios */
    .btn-secondary {
        background: var(--bg-tertiary) !important;
        color: var(--accent-primary) !important;
        border: 1px solid var(--bg-elevated) !important;
    }
    .btn-secondary:hover {
        background: var(--bg-elevated) !important;
    }
    
    /* Botones de estado */
    .btn-success { background: var(--success) !important; color: #000 !important; }
    .btn-warning { background: var(--warning) !important; color: #000 !important; }
    .btn-error { background: var(--error) !important; color: #fff !important; }

    /* ===== INPUTS MODERNOS ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--bg-elevated) !important;
        border-radius: var(--radius-md) !important;
        color: var(--accent-primary) !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        min-height: var(--touch-min) !important;
        transition: all var(--transition-fast) !important;
        font-family: var(--font-stack) !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(255,255,255,0.15) !important;
        background: var(--bg-elevated) !important;
    }
    .stTextInput label, .stSelectbox label {
        color: var(--accent-secondary) !important;
        font-size: 0.9rem !important;
        margin-bottom: 6px !important;
        font-weight: 500 !important;
    }

    /* ===== ALERTS Y MENSAJES ===== */
    .stAlert {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--bg-elevated) !important;
        border-radius: var(--radius-md) !important;
        color: var(--accent-primary) !important;
        padding: 12px 16px !important;
        margin: 12px 0 !important;
        font-size: 0.95rem !important;
    }
    .stAlert[data-testid="stAlert"]:has([data-testid="stAlertIcon"] svg:first-child) {
        border-left: 4px solid var(--info);
    }
    .stAlert[data-testid="stAlert"]:has([data-testid="stAlertIcon"] svg[stroke="currentColor"]):nth-child(2) {
        border-left: 4px solid var(--success);
    }
    .stAlert[data-testid="stAlert"]:has([data-testid="stAlertIcon"] svg[stroke="currentColor"]):nth-child(3) {
        border-left: 4px solid var(--warning);
    }
    .stAlert[data-testid="stAlert"]:has([data-testid="stAlertIcon"] svg[stroke="currentColor"]):nth-child(4) {
        border-left: 4px solid var(--error);
    }

    /* ===== TABLAS RESPONSIVAS ===== */
    .stDataFrame {
        background: var(--bg-secondary) !important;
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--bg-tertiary) !important;
        overflow: hidden !important;
        margin: 12px 0 !important;
    }
    .stDataFrame table {
        font-size: 0.9rem !important;
    }
    .stDataFrame thead th {
        background: var(--bg-tertiary) !important;
        color: var(--accent-secondary) !important;
        font-weight: 600 !important;
        padding: 12px !important;
        border-bottom: 1px solid var(--bg-elevated) !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em;
    }
    .stDataFrame tbody td {
        padding: 12px !important;
        border-bottom: 1px solid var(--bg-tertiary) !important;
        color: var(--accent-primary) !important;
    }
    .stDataFrame tbody tr:hover {
        background: var(--bg-tertiary) !important;
    }

    /* ===== QR Y TARJETAS VISUALES ===== */
    .qr-showcase {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        padding: 20px;
        background: var(--bg-secondary);
        border-radius: var(--radius-xl);
        margin: 16px 0;
    }
    .qr-image {
        border-radius: var(--radius-lg);
        border: 4px solid var(--bg-tertiary);
        box-shadow: var(--shadow-lg);
        max-width: 100%;
        height: auto;
    }
    .student-badge {
        text-align: center;
        padding: 8px 16px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-full);
        font-weight: 600;
        font-size: 0.9rem;
    }
    .student-ru {
        color: var(--accent-secondary);
        font-family: monospace;
        font-size: 0.85rem;
        margin-top: 4px;
    }

    /* ===== DASHBOARD CARDS ===== */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
        margin: 16px 0;
    }
    .stat-card {
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        padding: 16px;
        text-align: center;
        border: 1px solid var(--bg-tertiary);
        transition: all var(--transition-normal);
    }
    .stat-card:hover {
        border-color: var(--accent-primary);
        transform: translateY(-2px);
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--accent-primary);
        line-height: 1;
        margin: 4px 0;
    }
    .stat-label {
        font-size: 0.8rem;
        color: var(--accent-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    .stat-bar {
        height: 4px;
        background: var(--bg-tertiary);
        border-radius: var(--radius-full);
        margin-top: 12px;
        overflow: hidden;
    }
    .stat-fill {
        height: 100%;
        border-radius: var(--radius-full);
        transition: width var(--transition-slow);
    }
    .stat-fill.green { background: var(--success); }
    .stat-fill.blue { background: var(--info); }
    .stat-fill.orange { background: var(--warning); }

    /* ===== MODALES Y CONFIRMACIONES ===== */
    .modal-overlay {
        background: rgba(0,0,0,0.7);
        border-radius: var(--radius-lg);
        padding: 20px;
        margin: 16px 0;
        border: 1px solid var(--bg-elevated);
    }
    .modal-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ===== UTILIDADES ===== */
    .text-center { text-align: center; }
    .text-muted { color: var(--accent-secondary); }
    .text-success { color: var(--success); }
    .text-warning { color: var(--warning); }
    .text-error { color: var(--error); }
    .mt-0 { margin-top: 0; }
    .mb-0 { margin-bottom: 0; }
    .mt-2 { margin-top: 8px; }
    .mb-2 { margin-bottom: 8px; }
    .mt-4 { margin-top: 16px; }
    .mb-4 { margin-bottom: 16px; }
    
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    .items-center { align-items: center; }
    .justify-center { justify-content: center; }
    .justify-between { justify-content: space-between; }
    .gap-2 { gap: 8px; }
    .gap-4 { gap: 16px; }
    
    .w-full { width: 100%; }
    
    /* ===== RESPONSIVE MOBILE ===== */
    @media (max-width: 768px) {
        .stMainBlockContainer > div {
            padding: 12px !important;
        }
        h1 { font-size: 1.3rem; }
        h2 { font-size: 1.1rem; }
        .card { padding: 14px; border-radius: var(--radius-md); }
        .dashboard-grid { grid-template-columns: 1fr; }
        .nav-item { padding: 10px 12px; font-size: 0.8rem; }
    }

    /* ===== ANIMACIONES SUTILES ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .card, .stAlert, .stButton, .stDataFrame {
        animation: fadeIn var(--transition-normal) ease-out;
    }

    /* ===== SCROLLBAR PERSONALIZADO ===== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--bg-elevated);
        border-radius: var(--radius-full);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-tertiary);
    }

    /* ===== ICONOS MONOCROMÁTICOS SVG ===== */
    .icon {
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: currentColor;
        flex-shrink: 0;
    }
    .icon-lg { width: 24px; height: 24px; }
    .icon-sm { width: 16px; height: 16px; }
</style>

<!-- SVG Icons Library - Sistema monocromático -->
<script>
// Iconos SVG inline para consistencia visual
const icons = {
    register: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>',
    list: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>',
    scan: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>',
    manual: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>',
    stats: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>',
    calendar: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>',
    check: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>',
    warning: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
    error: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
    download: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>',
    search: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>',
    edit: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>',
    trash: '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
    lock: '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>'
};

// Inyectar iconos en botones después de cargar
document.addEventListener('DOMContentLoaded', function() {
    // Reemplazar emojis en navegación con iconos SVG
    document.querySelectorAll('.nav-item').forEach(btn => {
        const text = btn.textContent.trim();
        if (text.includes('📝')) btn.innerHTML = icons.register + ' Registrar';
        if (text.includes('📋')) btn.innerHTML = icons.list + ' Lista';
        if (text.includes('📸')) btn.innerHTML = icons.scan + ' Escanear';
        if (text.includes('✍️')) btn.innerHTML = icons.manual + ' Manual';
        if (text.includes('📊')) btn.innerHTML = icons.stats + ' Asistencia';
        if (text.includes('📅')) btn.innerHTML = icons.calendar + ' Por Fecha';
    });
});
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# NAVIGATION MOBILE-FIRST (Reemplaza sidebar)
# ------------------------------------------------------------
opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes", 
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia",
    "📅 Asistencia por fecha"
]

# Crear navegación horizontal con scroll
nav_html = '<div class="nav-container">'
for i, opcion in enumerate(opciones_menu):
    active_class = "active" if st.session_state.menu_actual == opcion else ""
    # Extraer texto sin emoji para mostrar
    texto = opcion.split(" ", 1)[1] if " " in opcion else opcion
    nav_html += f'<button class="nav-item {active_class}" data-value="{opcion}" onclick="selectMenu(\'{opcion}\')">{opcion}</button>'
nav_html += '</div>'

st.markdown(nav_html, unsafe_allow_html=True)

# Script para manejar navegación sin recargar toda la página
st.markdown("""
<script>
function selectMenu(value) {
    // Streamlit no permite cambio directo de session state desde JS,
    // pero podemos usar el radio oculto que Streamlit genera
    const radio = document.querySelector('input[data-testid="stRadioInput"][value="' + value + '"]');
    if (radio) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
    }
    // Actualizar visualmente
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
}
// Sincronizar estado inicial
document.addEventListener('DOMContentLoaded', function() {
    const current = localStorage.getItem('menu_actual') || '';
    if (current) {
        document.querySelectorAll('.nav-item').forEach(btn => {
            if (btn.dataset.value === current) btn.classList.add('active');
        });
    }
});
</script>
""", unsafe_allow_html=True)

# Mantener radio oculto para funcionalidad de Streamlit
menu = st.radio("", opciones_menu, horizontal=True, label_visibility="collapsed", key="menu_radio", index=0)
st.session_state.menu_actual = menu

# ------------------------------------------------------------
# FUNCIONES DE UI REUTILIZABLES
# ------------------------------------------------------------
def icon(icon_name):
    """Helper para iconos SVG monocromáticos"""
    icon_map = {
        'check': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>',
        'warning': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        'error': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        'download': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>',
        'search': '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>',
        'edit': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>',
        'trash': '<svg class="icon icon-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
        'lock': '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>'
    }
    return icon_map.get(icon_name, '')

def card(content, elevated=False, compact=False):
    """Wrapper para tarjetas con estilos consistentes"""
    classes = "card"
    if elevated: classes += " elevated"
    if compact: classes += " compact"
    return f'<div class="{classes}">{content}</div>'

# ------------------------------------------------------------
# HEADER COMPACTO
# ------------------------------------------------------------
with st.container():
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=50)
        else:
            st.markdown('<div style="width:50px;height:50px;background:var(--bg-tertiary);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.5rem">🎓</div>', unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <div>
            <h1 style="margin:0;font-size:1.3rem">INGENIERÍA DE SISTEMAS</h1>
            <p style="margin:2px 0 0;color:var(--accent-secondary);font-size:0.85rem">Sistema de Asistencia QR</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------
# 📝 REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<h2>Registrar nuevo estudiante</h2>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            ru = st.text_input("RU", placeholder="Solo números", key="reg_ru")
            nombres = st.text_input("Nombres", placeholder="Nombres completos", key="reg_nom")
        with col2:
            paterno = st.text_input("Apellido paterno", placeholder="Paterno", key="reg_pat")
            materno = st.text_input("Apellido materno", placeholder="Materno", key="reg_mat")
        
        col_btn, _, _ = st.columns([2, 1, 1])
        with col_btn:
            if st.button("💾 Guardar estudiante", use_container_width=True, key="btn_guardar"):
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
                                "ru": ru, "nombres": nombres,
                                "apellido_paterno": paterno, "apellido_materno": materno
                            }).execute()
                            st.success("✅ Estudiante registrado exitosamente")
                            
                            # Mostrar QR generado
                            qr_img = qrcode.make(ru)
                            img_bytes = io.BytesIO()
                            qr_img.save(img_bytes, format='PNG')
                            img_bytes.seek(0)
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="qr-showcase">
                                    <div class="student-badge">{nombres} {paterno}</div>
                                    <div class="student-ru">RU: {ru}</div>
                                    <img class="qr-image" src="data:image/png;base64,{base64.b64encode(img_bytes.getvalue()).decode()}" width="200">
                                </div>
                                """, unsafe_allow_html=True)
                                
                                col_dl1, col_dl2 = st.columns(2)
                                with col_dl1:
                                    buf = io.BytesIO()
                                    qr_img.save(buf, format="PNG")
                                    buf.seek(0)
                                    st.download_button("⬇️ QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

# ------------------------------------------------------------
# 📋 LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<h2>Lista de estudiantes</h2>', unsafe_allow_html=True)
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True, hide_index=True)
        
        st.markdown('<div class="mt-4 mb-2"><strong>🔍 Buscar estudiante</strong></div>', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            ru_ver = st.text_input("", placeholder="Ingrese RU para buscar", key="buscar_ru", label_visibility="collapsed")
        with col2:
            buscar_click = st.button("🔍", key="buscar_btn", use_container_width=True)
        
        if buscar_click and ru_ver:
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                ed = estudiante.iloc[0]
                nombre_completo = f"{ed['nombres']} {ed['apellido_paterno']}".strip().upper()
                
                qr_img = qrcode.make(ru_ver)
                qr_buffer = io.BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                st.markdown(f"""
                <div class="card elevated text-center">
                    <div class="student-badge" style="font-size:1.2rem">{nombre_completo}</div>
                    <div class="student-ru" style="font-size:1rem;margin:8px 0">RU: {ru_ver}</div>
                    <img class="qr-image" src="data:image/png;base64,{base64.b64encode(qr_buffer.getvalue()).decode()}" width="180" style="margin:12px 0">
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button("📥 QR", data=qr_buffer.getvalue(), file_name=f"{ru_ver}_qr.png", mime="image/png", use_container_width=True)
                with col_btn2:
                    tarjeta_img = crear_tarjeta_estudiante(ed)
                    st.download_button("📇 Tarjeta", data=tarjeta_img, file_name=f"tarjeta_{ru_ver}.png", mime="image/png", use_container_width=True)
            else:
                st.warning("⚠️ RU no encontrado")
        
        st.markdown("---")
        st.markdown('<h3>✏️ Gestionar</h3>', unsafe_allow_html=True)
        
        estudiantes_display = estudiantes.copy()
        estudiantes_display["nombre_completo"] = estudiantes_display["ru"].astype(str) + " - " + estudiantes_display["nombres"] + " " + estudiantes_display["apellido_paterno"]
        opciones = estudiantes_display["nombre_completo"].tolist()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            seleccion = st.selectbox("Estudiante", opciones, key="select_est", label_visibility="collapsed")
            ru_seleccionado = seleccion.split(" - ")[0] if seleccion else None
        
        if ru_seleccionado:
            estudiante_data = estudiantes[estudiantes["ru"] == ru_seleccionado].iloc[0]
            
            with st.form(key="form_editar"):
                c1, c2 = st.columns(2)
                with c1:
                    nuevo_ru = st.text_input("RU", value=estudiante_data["ru"], key="edit_ru")
                    nuevos_nombres = st.text_input("Nombres", value=estudiante_data["nombres"], key="edit_nom")
                with c2:
                    nuevo_paterno = st.text_input("Paterno", value=estudiante_data["apellido_paterno"], key="edit_pat")
                    nuevo_materno = st.text_input("Materno", value=estudiante_data["apellido_materno"], key="edit_mat")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
                with col_btn2:
                    submit_eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
            
            if submit_actualizar:
                if not nuevo_ru or not nuevo_ru.isdigit():
                    st.error("❌ RU inválido")
                else:
                    try:
                        if nuevo_ru != ru_seleccionado:
                            existe = supabase.table("estudiantes").select("ru").eq("ru", nuevo_ru).execute()
                            if existe.data:
                                st.error("❌ RU ya existe")
                                st.stop()
                        supabase.table("estudiantes").update({
                            "ru": nuevo_ru, "nombres": nuevos_nombres,
                            "apellido_paterno": nuevo_paterno, "apellido_materno": nuevo_materno
                        }).eq("ru", ru_seleccionado).execute()
                        if nuevo_ru != ru_seleccionado:
                            supabase.table("asistencia").update({"ru": nuevo_ru}).eq("ru", ru_seleccionado).execute()
                        st.success("✅ Actualizado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            if submit_eliminar:
                st.session_state.confirmar_eliminar = ru_seleccionado
            
            if st.session_state.confirmar_eliminar:
                st.markdown(f"""
                <div class="modal-overlay">
                    <div class="modal-title">{icon('warning')} Confirmar eliminación</div>
                    <p>¿Eliminar estudiante RU: {st.session_state.confirmar_eliminar}?</p>
                    <p class="text-muted" style="font-size:0.9rem">Se eliminarán también sus registros de asistencia.</p>
                </div>
                """, unsafe_allow_html=True)
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("✅ Sí, eliminar", use_container_width=True, key="confirm_elim"):
                        try:
                            supabase.table("asistencia").delete().eq("ru", st.session_state.confirmar_eliminar).execute()
                            supabase.table("estudiantes").delete().eq("ru", st.session_state.confirmar_eliminar).execute()
                            st.success("✅ Eliminado")
                            st.session_state.confirmar_eliminar = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                with col_c2:
                    if st.button("❌ Cancelar", use_container_width=True, key="cancel_elim", type="secondary"):
                        st.session_state.confirmar_eliminar = None
                        st.rerun()
        
        st.markdown("---")
        archivo_descarga = "registro_estudiantes_temp.xlsx"
        estudiantes.to_excel(archivo_descarga, index=False)
        with open(archivo_descarga, "rb") as file:
            st.download_button("📥 Exportar Excel", data=file, file_name="estudiantes.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# 📸 ESCANEAR QR
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<h2>Escanear código QR</h2>', unsafe_allow_html=True)
    st.markdown('<p class="text-muted">Apunta la cámara al código QR del estudiante</p>', unsafe_allow_html=True)
    
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
                            "ru": ru, "nombres": nombres, "apellido_paterno": paterno,
                            "apellido_materno": materno, "fecha": fecha.isoformat(),
                            "hora": hora, "estado": "Presente"
                        }).execute()
                        st.session_state.ultimo_registro = {"ru": ru, "nombres": nombres, "hora": hora, "fecha": fecha}
                        st.success(f"✅ {nombres} {paterno} - Registrado {hora}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning(f"⚠️ Ya registrado hoy a las {registro_existente['hora']}")
            else:
                st.error("❌ Estudiante no encontrado")
        else:
            st.warning("⚠️ No se detectó código QR")

# ------------------------------------------------------------
# ✍️ REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        st.markdown(f"""
        <div class="card elevated text-center" style="max-width:400px;margin:20px auto">
            <div style="font-size:2rem;margin-bottom:12px">{icon('lock')}</div>
            <h3 style="margin:0 0 8px">Acceso restringido</h3>
            <p class="text-muted" style="margin:0 0 16px">Ingrese contraseña para continuar</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(key="password_form"):
            password = st.text_input("", type="password", placeholder="Contraseña", label_visibility="collapsed", key="pwd_input")
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
        st.markdown('<h2>Registro manual</h2>', unsafe_allow_html=True)
        estudiantes = leer_estudiantes()
        
        if len(estudiantes) > 0:
            estudiantes["nombre_completo"] = estudiantes["ru"].astype(str) + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            opciones = estudiantes["nombre_completo"].tolist()
            
            seleccionado = st.selectbox("👤 Seleccionar estudiante", opciones, key="select_manual", label_visibility="collapsed")
            
            if seleccionado:
                ru_sel = seleccionado.split(" - ")[0]
                ed = estudiantes[estudiantes["ru"].astype(str) == ru_sel].iloc[0]
                
                st.markdown(f"""
                <div class="card compact">
                    <strong>{ed['nombres']} {ed['apellido_paterno']}</strong><br>
                    <span class="text-muted">RU: {ed['ru']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"], key="estado_manual")
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, reg_exist = verificar_registro_duplicado(ru_sel, fecha)
                
                if tiene_registro:
                    st.warning(f"⚠️ Ya registrado hoy {reg_exist['hora']} ({reg_exist['estado']})")
                    st.button("✅ Registrar", disabled=True, use_container_width=True)
                else:
                    if st.button("✅ Registrar asistencia", use_container_width=True, key="btn_manual_reg"):
                        try:
                            supabase.table("asistencia").insert({
                                "ru": ru_sel, "nombres": ed["nombres"],
                                "apellido_paterno": ed["apellido_paterno"], "apellido_materno": ed["apellido_materno"],
                                "fecha": fecha.isoformat(), "hora": hora, "estado": estado
                            }).execute()
                            st.success(f"✅ Registrado {hora}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ No hay estudiantes registrados")

# ------------------------------------------------------------
# 📊 VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<h2>Panel de asistencia</h2>', unsafe_allow_html=True)
    
    estudiantes_total = leer_estudiantes()
    total_est = len(estudiantes_total)
    asistencia_df = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    registrados_hoy = asistencia_df[asistencia_df["fecha"] == hoy]["ru"].nunique()
    faltantes = total_est - registrados_hoy
    pct_reg = (registrados_hoy / total_est * 100) if total_est > 0 else 0
    pct_falt = (faltantes / total_est * 100) if total_est > 0 else 0
    
    # Dashboard cards estilo sistema
    st.markdown(f"""
    <div class="dashboard-grid">
        <div class="stat-card">
            <div class="stat-label">Total</div>
            <div class="stat-value">{total_est}</div>
            <div class="stat-bar"><div class="stat-fill blue" style="width:100%"></div></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Registrados</div>
            <div class="stat-value text-success">{registrados_hoy}</div>
            <div class="stat-bar"><div class="stat-fill green" style="width:{pct_reg}%"></div></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Faltantes</div>
            <div class="stat-value text-warning">{faltantes}</div>
            <div class="stat-bar"><div class="stat-fill orange" style="width:{pct_falt}%"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(asistencia_df) > 0:
        asistencia_mostrar = asistencia_df.copy()
        asistencia_mostrar['fecha'] = asistencia_mostrar['fecha'].astype(str)
        asistencia_mostrar['hora'] = asistencia_mostrar['hora'].astype(str)
        st.dataframe(asistencia_mostrar.drop(columns=['id']), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Verificación de duplicados
        st.markdown('<h3>🔍 Integridad</h3>', unsafe_allow_html=True)
        duplicados = asistencia_df.groupby(['ru', 'fecha']).size().reset_index(name='count')
        duplicados = duplicados[duplicados['count'] > 1]
        if len(duplicados) > 0:
            st.warning(f"⚠️ {len(duplicados)} registros duplicados detectados")
            if st.button("🧹 Limpiar duplicados", use_container_width=True, key="btn_limp_dup"):
                try:
                    ids_ok = asistencia_df.groupby(['ru', 'fecha'])['id'].first().tolist()
                    supabase.table("asistencia").delete().not_.in_("id", ids_ok).execute()
                    st.success("✅ Duplicados eliminados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.success("✅ Sin duplicados")
        
        # Editar estado
        st.markdown("---")
        st.markdown('<h3>✏️ Editar estado</h3>', unsafe_allow_html=True)
        if len(asistencia_df) > 0:
            asistencia_df["desc"] = (asistencia_df["ru"].astype(str) + " - " + 
                                   asistencia_df["nombres"] + " " + asistencia_df["apellido_paterno"] + 
                                   f" ({asistencia_df['fecha']} {asistencia_df['hora']})")
            opciones = asistencia_df["desc"].tolist()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                sel = st.selectbox("Registro", opciones, key="sel_edit_asist", label_visibility="collapsed")
                idx = asistencia_df[asistencia_df["desc"] == sel].index[0]
                id_reg = asistencia_df.loc[idx, "id"]
                estado_act = asistencia_df.loc[idx, "estado"]
            with col2:
                nuevo_estado = st.selectbox("Nuevo estado", ["Presente","Tarde","Permiso","Ausente"], 
                                           index=["Presente","Tarde","Permiso","Ausente"].index(estado_act), key="nuevo_estado_sel")
            
            if st.button("🔄 Actualizar", use_container_width=True, key="btn_upd_estado"):
                try:
                    supabase.table("asistencia").update({"estado": nuevo_estado}).eq("id", id_reg).execute()
                    st.success("✅ Actualizado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Exportar día
        st.markdown("---")
        hoy_str = str(hoy)
        asistencia_hoy = asistencia_df[asistencia_df["fecha"].astype(str) == hoy_str].copy()
        if len(asistencia_hoy) > 0:
            asistencia_hoy['fecha'] = pd.to_datetime(asistencia_hoy['fecha']).dt.strftime('%d-%m-%Y')
            nombre_archivo = f"asistencia_{hoy.strftime('%d-%m-%Y')}.xlsx"
            asistencia_hoy.to_excel(nombre_archivo, index=False)
            with open(nombre_archivo, "rb") as file:
                st.download_button("📥 Descargar hoy", data=file, file_name=nombre_archivo, use_container_width=True)
    else:
        st.info("📭 Sin registros")

# ------------------------------------------------------------
# 📅 ASISTENCIA POR FECHA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📅 Asistencia por fecha":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None
    
    st.markdown('<h2>Consulta por fecha</h2>', unsafe_allow_html=True)
    
    fecha_sel = st.date_input("📆 Fecha", value=datetime.now(ZONA_HORARIA).date(), key="fecha_consulta_new", label_visibility="collapsed")
    
    asistencia_df = leer_asistencia()
    
    if len(asistencia_df) > 0:
        asistencia_df['fecha_date'] = pd.to_datetime(asistencia_df['fecha']).dt.date
        asistentes_fecha = asistencia_df[asistencia_df['fecha_date'] == fecha_sel].copy()
        
        if len(asistentes_fecha) > 0:
            st.markdown(f"### 📌 {fecha_sel.strftime('%d/%m/%Y')}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("👥 Asistentes", len(asistentes_fecha))
            with col2:
                conteo = asistentes_fecha['estado'].value_counts().to_dict()
                st.metric("📊 Estados", ", ".join([f"{k}: {v}" for k, v in conteo.items()]))
            
            tabla = asistentes_fecha.drop(columns=['id', 'fecha_date'], errors='ignore').sort_values('hora')
            st.dataframe(tabla, use_container_width=True, hide_index=True)
            
            # Exportar
            tabla_exp = tabla.copy()
            tabla_exp['fecha'] = pd.to_datetime(tabla_exp['fecha']).dt.strftime('%d-%m-%Y')
            archivo = f"asistencia_{fecha_sel.strftime('%Y%m%d')}.xlsx"
            tabla_exp.to_excel(archivo, index=False)
            with open(archivo, "rb") as f:
                st.download_button("📥 Exportar", data=f, file_name=archivo, use_container_width=True)
        else:
            st.info(f"📭 Sin registros para {fecha_sel.strftime('%d/%m/%Y')}")
        
        # Exportar semana
        st.markdown("---")
        st.markdown('<h3>📆 Exportar semana</h3>', unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_ini = st.date_input("Inicio", value=datetime.now(ZONA_HORARIA).date(), key="sem_ini", label_visibility="collapsed")
        with col_f2:
            dias = 6 - fecha_ini.weekday()
            fecha_fin = fecha_ini + pd.Timedelta(days=dias)
            st.write(f"**Hasta:** {fecha_fin.strftime('%d/%m/%Y')}")
        
        if st.button("📊 Generar Excel semanal", use_container_width=True, key="btn_sem_exp"):
            asistencia_df = leer_asistencia()
            asistencia_df['fecha_date'] = pd.to_datetime(asistencia_df['fecha']).dt.date
            semana_df = asistencia_df[(asistencia_df['fecha_date'] >= fecha_ini) & (asistencia_df['fecha_date'] <= fecha_fin)]
            
            if len(semana_df) > 0:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for fecha, grupo in semana_df.groupby('fecha_date'):
                        nombre_hoja = fecha.strftime('%a_%d%m')[:31]
                        grupo_limpio = grupo.drop(columns=['id', 'fecha_date'], errors='ignore')
                        grupo_limpio['fecha'] = pd.to_datetime(grupo_limpio['fecha']).dt.strftime('%d-%m-%Y')
                        grupo_limpio = grupo_limpio.sort_values('hora')
                        grupo_limpio.to_excel(writer, sheet_name=nombre_hoja, index=False)
                output.seek(0)
                st.download_button(
                    label="📥 Descargar semana",
                    data=output,
                    file_name=f"asistencia_semana_{fecha_ini.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Sin registros en el rango")
    else:
        st.info("📭 Sin registros en el sistema")

# ------------------------------------------------------------
# FUNCIÓN CREAR TARJETA (Sin cambios en lógica)
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
