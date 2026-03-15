import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz
import shutil

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA
# ------------------------------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')  # Cambia según tu ubicación

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S.%f")[:-3]  # Con milisegundos
    return fecha, hora

# ------------------------------------------------------------
# FUNCIÓN PARA VERIFICAR REGISTRO DUPLICADO
# ------------------------------------------------------------
def verificar_registro_duplicado(ru, fecha):
    """
    Verifica si un estudiante ya tiene registro de asistencia en la fecha actual
    Retorna: (tiene_registro, registro_existente)
    """
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
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILOS CSS MEJORADOS - BOTONES ELEGANTES Y MENÚ HORIZONTAL
# ------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    :root {
        --bg-dark: #0a0c10;
        --bg-card: #15181f;
        --bg-sidebar: #111318;
        --text-primary: #ffffff;
        --text-secondary: #9ca3af;
        --accent: #8b5cf6;
        --accent-light: #a78bfa;
        --accent-dark: #7c3aed;
        --border: #2d3138;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --duplicate: #f97316;
        --info: #3b82f6;
        --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        --gradient-5: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
                    var(--bg-dark);
        color: var(--text-primary);
    }

    /* Título elegante */
    h1 {
        background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3rem !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);
    }

    /* MENÚ HORIZONTAL CON BOTONES ELEGANTES */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 12px;
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        padding: 18px 22px;
        border-radius: 100px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        margin-bottom: 30px;
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5),
                    0 0 0 1px rgba(139, 92, 246, 0.1) inset;
    }
    
    div.row-widget.stRadio > div label {
        color: var(--text-secondary) !important;
        font-size: 0.95rem;
        font-weight: 500;
        padding: 12px 28px;
        border-radius: 50px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        border: 1px solid transparent;
        background: rgba(255, 255, 255, 0.02);
        letter-spacing: 0.3px;
        position: relative;
        overflow: hidden;
        cursor: pointer;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
    /* Efecto de brillo en hover */
    div.row-widget.stRadio > div label::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
        z-index: 0;
        pointer-events: none;
    }
    
    div.row-widget.stRadio > div label:hover::before {
        width: 300px;
        height: 300px;
    }
    
    div.row-widget.stRadio > div label:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }

    /* Colores específicos para cada opción con gradientes elegantes */
    div.row-widget.stRadio > div label:nth-child(1) {
        background: linear-gradient(145deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
        border-color: #3b82f6;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
    }
    div.row-widget.stRadio > div label:nth-child(2) {
        background: linear-gradient(145deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
        border-color: #10b981;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
    }
    div.row-widget.stRadio > div label:nth-child(3) {
        background: linear-gradient(145deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
        border-color: #f59e0b;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.1);
    }
    div.row-widget.stRadio > div label:nth-child(4) {
        background: linear-gradient(145deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
        border-color: #ef4444;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.1);
    }
    div.row-widget.stRadio > div label:nth-child(5) {
        background: linear-gradient(145deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
        border-color: #8b5cf6;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.1);
    }

    /* Colores para la opción activa (checked) con gradientes más intensos */
    div.row-widget.stRadio > div label:nth-child(1) input:checked + div {
        background: linear-gradient(135deg, #3b82f6, #2563eb, #1d4ed8) !important;
        color: white !important;
        box-shadow: 0 15px 30px -8px #3b82f6 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    div.row-widget.stRadio > div label:nth-child(2) input:checked + div {
        background: linear-gradient(135deg, #10b981, #059669, #047857) !important;
        color: white !important;
        box-shadow: 0 15px 30px -8px #10b981 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    div.row-widget.stRadio > div label:nth-child(3) input:checked + div {
        background: linear-gradient(135deg, #f59e0b, #d97706, #b45309) !important;
        color: white !important;
        box-shadow: 0 15px 30px -8px #f59e0b !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    div.row-widget.stRadio > div label:nth-child(4) input:checked + div {
        background: linear-gradient(135deg, #ef4444, #dc2626, #b91c1c) !important;
        color: white !important;
        box-shadow: 0 15px 30px -8px #ef4444 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    div.row-widget.stRadio > div label:nth-child(5) input:checked + div {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed, #6d28d9) !important;
        color: white !important;
        box-shadow: 0 15px 30px -8px #8b5cf6 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Estilos para botones elegantes */
    .stButton button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 10px 20px -5px rgba(139, 92, 246, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton button:hover::before {
        left: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 20px 30px -8px rgba(139, 92, 246, 0.6);
        filter: brightness(1.1);
    }
    
    .stButton button:active {
        transform: translateY(0) scale(0.98);
    }
    
    /* Botón de búsqueda especial */
    .stButton button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.4);
    }
    
    /* Botón deshabilitado */
    .stButton button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
        background: linear-gradient(135deg, #4b5563, #374151);
    }

    /* Inputs elegantes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2), 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        transform: scale(1.01);
    }

    /* Tarjetas elegantes */
    .info-card {
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 1.8rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5);
        margin-bottom: 1.5rem;
    }
    
    .student-info {
        background: linear-gradient(145deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        border-left: 6px solid var(--accent);
        margin: 1.5rem 0;
        box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.3);
    }

    /* Tablas elegantes */
    .stDataFrame {
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5);
        overflow: hidden;
    }
    
    .stDataFrame table {
        color: var(--text-primary) !important;
        border-collapse: separate;
        border-spacing: 0 10px;
    }
    
    .stDataFrame th {
        background: linear-gradient(145deg, #2d3138, #262a32) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 15px !important;
        border-bottom: 2px solid var(--accent) !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        background: rgba(30, 33, 40, 0.6) !important;
        color: var(--text-secondary) !important;
        padding: 12px !important;
        border-bottom: 1px solid var(--border) !important;
        transition: all 0.3s ease;
    }
    
    .stDataFrame tr:hover td {
        background: rgba(139, 92, 246, 0.1) !important;
        color: var(--text-primary) !important;
    }

    /* Cámara elegante */
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 70vh !important;
        object-fit: cover;
        border-radius: 24px;
        border: 3px solid var(--accent);
        box-shadow: 0 25px 40px -15px rgba(139, 92, 246, 0.5);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stCameraInput"] video:hover {
        transform: scale(1.01);
        border-color: var(--accent-light);
    }

    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .stAlert {
        animation: fadeIn 0.4s ease-out;
        border-radius: 20px;
        border-left: 6px solid;
        background: rgba(21, 24, 31, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.2rem !important;
    }
    
    .stSuccess {
        border-left-color: var(--success) !important;
    }
    
    .stWarning {
        border-left-color: var(--warning) !important;
    }
    
    .stError {
        border-left-color: var(--error) !important;
    }
    
    .stInfo {
        border-left-color: var(--info) !important;
    }

    /* Sidebar elegante */
    .css-1d391kg, .css-163ttbj, [data-testid="stSidebar"] {
        background: rgba(17, 19, 24, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    .css-1d391kg h2, .css-163ttbj h2 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* File uploader elegante */
    .stFileUploader {
        background: rgba(21, 24, 31, 0.6);
        border-radius: 20px;
        border: 2px dashed var(--accent);
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: var(--accent-light);
        background: rgba(139, 92, 246, 0.05);
    }
    
    /* Progress bar elegante */
    .stProgress > div > div {
        background: linear-gradient(135deg, var(--accent), var(--accent-light));
        border-radius: 10px;
        height: 8px;
    }
    
    /* Tooltips personalizados */
    .stTooltip {
        background: var(--bg-card);
        border: 1px solid var(--accent);
        border-radius: 12px;
        color: var(--text-primary);
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--accent), var(--accent-light));
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--accent-light), var(--accent));
    }
    
    /* Cards de estadísticas */
    .metric-card {
        background: linear-gradient(145deg, rgba(21, 24, 31, 0.8), rgba(17, 19, 24, 0.9));
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: var(--accent);
        box-shadow: 0 20px 35px -10px rgba(139, 92, 246, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, var(--accent-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Dividers elegantes */
    hr {
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        height: 2px;
        border: none;
        margin: 2rem 0;
    }
    
    /* Expander elegante */
    .streamlit-expanderHeader {
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 1rem !important;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--accent);
        background: rgba(139, 92, 246, 0.1);
    }
    
    .streamlit-expanderContent {
        background: rgba(17, 19, 24, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 0 0 16px 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-top: none;
        padding: 1.5rem;
    }
    
    /* Checkbox elegante */
    .stCheckbox {
        color: var(--text-primary) !important;
    }
    
    .stCheckbox input[type="checkbox"] {
        accent-color: var(--accent);
        transform: scale(1.2);
    }
    
    /* Radio button elegante */
    .stRadio {
        color: var(--text-primary) !important;
    }
    
    .stRadio input[type="radio"] {
        accent-color: var(--accent);
        transform: scale(1.2);
    }
    
    /* Selectbox elegante */
    .stSelectbox label {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }
    
    /* Number input elegante */
    .stNumberInput input {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stNumberInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Date input elegante */
    .stDateInput input {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stDateInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Time input elegante */
    .stTimeInput input {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stTimeInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Text area elegante */
    .stTextArea textarea {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Caption elegante */
    .stCaption {
        color: var(--text-secondary) !important;
        font-size: 0.9rem;
        font-style: italic;
    }
    
    /* Code block elegante */
    .stCodeBlock {
        background: rgba(21, 24, 31, 0.8) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        padding: 1rem;
    }
    
    /* Markdown elegante */
    .stMarkdown {
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .stMarkdown a {
        color: var(--accent);
        text-decoration: none;
        transition: all 0.3s ease;
    }
    
    .stMarkdown a:hover {
        color: var(--accent-light);
        text-decoration: underline;
    }
    
    /* Balloon effect */
    .stBalloons {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    }
    
    /* Snow effect */
    .stSnow {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    }
    
    /* Confetti effect */
    .stConfetti {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    }
    
    /* Toast notifications */
    .stToast {
        background: rgba(21, 24, 31, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid var(--accent);
        color: var(--text-primary);
        padding: 1rem 1.5rem;
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5);
    }
    
    /* Spinner elegante */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
        border-left-color: var(--accent-light) !important;
        border-bottom-color: var(--accent) !important;
        border-right-color: var(--accent-light) !important;
    }
    
    /* Image container */
    .stImage {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    .stImage:hover {
        transform: scale(1.02);
        box-shadow: 0 25px 40px -10px rgba(139, 92, 246, 0.3);
    }
    
    /* Audio player */
    .stAudio {
        border-radius: 16px;
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    /* Video player */
    .stVideo {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.5);
        border: 2px solid var(--accent);
    }
    
    /* DataFrame toolbar */
    .stDataFrame-toolbar {
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    /* Pagination */
    .stDataFrame-pagination {
        background: rgba(21, 24, 31, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 0.5rem;
        margin-top: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    /* Sort indicator */
    .stDataFrame-sort {
        color: var(--accent) !important;
    }
    
    /* Filter indicator */
    .stDataFrame-filter {
        color: var(--accent) !important;
    }
    
    /* Column header */
    .stDataFrame-column-header {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    
    /* Row number */
    .stDataFrame-row-number {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    
    /* Empty state */
    .stDataFrame-empty {
        color: var(--text-secondary) !important;
        font-style: italic;
        padding: 2rem !important;
        text-align: center;
    }
    
    /* Loading state */
    .stDataFrame-loading {
        color: var(--text-secondary) !important;
        padding: 2rem !important;
        text-align: center;
    }
    
    /* Error state */
    .stDataFrame-error {
        color: var(--error) !important;
        padding: 2rem !important;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

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

# ------------------------------------------------------------
# TÍTULO Y MENÚ HORIZONTAL ELEGANTE
# ------------------------------------------------------------
st.title("📷 Sistema de Asistencia con QR")
st.markdown('<p style="color: #9ca3af; margin-top: -15px; margin-bottom: 30px; font-size: 1.1rem;">Gestión inteligente de asistencia mediante códigos QR</p>', unsafe_allow_html=True)

opciones_menu = [
    "📝 Registrar estudiante",
    "📋 Lista estudiantes",
    "📸 Escanear QR",
    "✍️ Registrar asistencia manual",
    "📊 Ver asistencia"
]

menu = st.radio(
    "",
    opciones_menu,
    horizontal=True,
    label_visibility="collapsed",
    key="menu_radio"
)

st.session_state.menu_actual = menu

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Cargar archivos Excel")
    st.markdown('<p style="color: #9ca3af; font-size: 0.9rem;">Sube tus propios archivos para trabajar con ellos</p>', unsafe_allow_html=True)

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
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def leer_estudiantes():
    if os.path.exists(st.session_state.ruta_estudiantes):
        return pd.read_excel(st.session_state.ruta_estudiantes)
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])

def guardar_estudiantes(df):
    df.to_excel(st.session_state.ruta_estudiantes, index=False)

def leer_asistencia():
    if os.path.exists(st.session_state.ruta_asistencia):
        return pd.read_excel(st.session_state.ruta_asistencia)
    else:
        return pd.DataFrame(columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])

def guardar_asistencia(df):
    df.to_excel(st.session_state.ruta_asistencia, index=False)

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

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("💾 Guardar estudiante", use_container_width=True):
                df = leer_estudiantes()
                if ru in df["RU"].astype(str).values:
                    st.error("❌ Este RU ya existe")
                else:
                    if not os.path.exists("qr"):
                        os.mkdir("qr")
                    ruta_qr = f"qr/{ru}.png"
                    qr = qrcode.make(ru)
                    qr.save(ruta_qr)

                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, ruta_qr]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
                    df = pd.concat([df, nuevo], ignore_index=True)
                    guardar_estudiantes(df)
                    st.success("✅ Estudiante registrado exitosamente")
                    
                    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
                    with col_img2:
                        st.image(ruta_qr, width=350, caption=f"QR de {nombres} {paterno}")
                        with open(ruta_qr, "rb") as file:
                            st.download_button("⬇️ Descargar QR", data=file, file_name=f"{ru}_qr.png", mime="image/png", use_container_width=True)

# ------------------------------------------------------------
# LISTA ESTUDIANTES - CON BOTÓN DE BÚSQUEDA MEJORADO
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Buscar estudiante")
        
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            ru_ver = st.text_input("Ingrese RU para buscar", placeholder="Ej: 2024001", key="buscar_ru")
        with col2:
            buscar_click = st.button("🔍 Buscar", key="buscar_btn", use_container_width=True)
        
        if buscar_click and ru_ver:
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
            if len(estudiante) > 0:
                with st.container():
                    st.markdown('<div class="student-info">', unsafe_allow_html=True)
                    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                    with col_info1:
                        st.markdown(f"**RU:** {estudiante.iloc[0]['RU']}")
                    with col_info2:
                        st.markdown(f"**Nombres:** {estudiante.iloc[0]['Nombres']}")
                    with col_info3:
                        st.markdown(f"**Ap. Paterno:** {estudiante.iloc[0]['Apellido_paterno']}")
                    with col_info4:
                        st.markdown(f"**Ap. Materno:** {estudiante.iloc[0]['Apellido_materno']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
                    with col_img2:
                        st.image(estudiante.iloc[0]["QR"], width=350, caption=f"QR de {estudiante.iloc[0]['Nombres']}")
            else:
                st.warning("⚠️ RU no encontrado en la base de datos")
        elif buscar_click and not ru_ver:
            st.warning("⚠️ Por favor ingrese un RU para buscar")

        st.markdown("---")
        st.subheader("🗑️ Eliminar estudiante")
        if len(estudiantes) > 0:
            col1, col2, col3 = st.columns([2, 1, 2])
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
    st.markdown('<p style="color: #9ca3af;">Toma una foto del código QR del estudiante para registrar su asistencia</p>', unsafe_allow_html=True)
    
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

                # VERIFICAR SI YA TIENE REGISTRO HOY
                tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)

                if not tiene_registro:
                    nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                          columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                    asistencia = leer_asistencia()
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    guardar_asistencia(asistencia)
                    
                    # Guardar en session state
                    st.session_state.ultimo_registro = {
                        "RU": ru,
                        "Nombres": nombres,
                        "Hora": hora,
                        "Fecha": fecha
                    }
                    
                    st.success(f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}")
                else:
                    st.warning(f"⚠️ {nombres} {paterno} ya registró asistencia hoy a las {registro_existente['Hora']}")
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
        
        # VERIFICAR SI YA TIENE REGISTRO HOY
        tiene_registro, registro_existente = verificar_registro_duplicado(ru, fecha)
        
        if tiene_registro:
            st.warning(f"⚠️ Este estudiante ya registró hoy a las {registro_existente['Hora']} (Estado: {registro_existente['Estado']})")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
            st.caption("Botón deshabilitado - Registro duplicado")
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
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
                    
                    # Guardar en session state
                    st.session_state.ultimo_registro = {
                        "RU": ru,
                        "Nombres": nombres,
                        "Hora": hora,
                        "Fecha": fecha
                    }
                    
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
        
        # Verificación de integridad
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
            col1, col2, col3 = st.columns([2, 2, 1])
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
            col1, col2, col3 = st.columns([2, 1, 2])
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
