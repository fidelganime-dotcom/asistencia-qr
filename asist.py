import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from supabase import create_client, Client
import pytz
import streamlit.components.v1 as components
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
# ZONA HORARIA
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
if "qr_ru_procesado" not in st.session_state:
    st.session_state.qr_ru_procesado = None          # Evita reprocesar el mismo QR
if "mensaje_escaneo" not in st.session_state:
    st.session_state.mensaje_escaneo = None

# ------------------------------------------------------------
# PARTÍCULAS, SIDEBAR, TÍTULO, MENÚ (igual que antes)
# ------------------------------------------------------------
# ... (todo el código de partículas, sidebar, título y menú se mantiene igual)
# Para no alargar, asumimos que ya está presente. 
# En el código final que entregaré, incluiré todo completo.

# ------------------------------------------------------------
# ESCANEAR QR — VERSIÓN CON MANEJO DE ESTADO ROBUSTO
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False
    st.session_state.selected_student_manual = None

    st.subheader("📸 Escanear QR (detección automática)")

    # ---- Procesar el QR detectado (si viene desde el componente JS) ----
    params = st.query_params
    ru_from_js = params.get("qr_ru", None)

    if ru_from_js and ru_from_js != st.session_state.get("qr_ru_procesado"):
        st.session_state.qr_ru_procesado = ru_from_js

        estudiantes_df = leer_estudiantes()
        estudiante_fila = estudiantes_df[estudiantes_df["ru"].astype(str) == ru_from_js]

        if len(estudiante_fila) > 0:
            nombres = estudiante_fila.iloc[0]["nombres"]
            paterno = estudiante_fila.iloc[0]["apellido_paterno"]
            materno = estudiante_fila.iloc[0]["apellido_materno"]
            fecha, hora = obtener_fecha_hora_exacta()
            tiene_registro, registro_existente = verificar_registro_duplicado(ru_from_js, fecha)

            if not tiene_registro:
                try:
                    # Insertar en Supabase
                    supabase.table("asistencia").insert({
                        "ru": ru_from_js,
                        "nombres": nombres,
                        "apellido_paterno": paterno,
                        "apellido_materno": materno,
                        "fecha": fecha.isoformat(),
                        "hora": hora,
                        "estado": "Presente"
                    }).execute()
                    st.session_state.mensaje_escaneo = {
                        "tipo": "success",
                        "texto": f"✅ Asistencia registrada: {nombres} {paterno} a las {hora}"
                    }
                except Exception as e:
                    st.session_state.mensaje_escaneo = {
                        "tipo": "error",
                        "texto": f"❌ Error al guardar: {str(e)}"
                    }
            else:
                st.session_state.mensaje_escaneo = {
                    "tipo": "warning",
                    "texto": f"⚠️ {nombres} {paterno} ya registró hoy a las {registro_existente['hora']}"
                }
        else:
            st.session_state.mensaje_escaneo = {
                "tipo": "error",
                "texto": f"❌ RU {ru_from_js} no encontrado en la base de datos"
            }

        # Limpiar el parámetro de la URL para que no se vuelva a procesar al recargar
        st.query_params.clear()
        # Forzar rerun para mostrar el mensaje inmediatamente
        st.rerun()

    # ---- Mostrar mensaje pendiente ----
    if st.session_state.mensaje_escaneo:
        mensaje = st.session_state.mensaje_escaneo
        if mensaje["tipo"] == "success":
            st.success(mensaje["texto"])
        elif mensaje["tipo"] == "warning":
            st.warning(mensaje["texto"])
        else:
            st.error(mensaje["texto"])
        # Botón para limpiar el mensaje y poder escanear otro QR
        if st.button("📷 Escanear otro código", use_container_width=True):
            st.session_state.mensaje_escaneo = None
            st.session_state.qr_ru_procesado = None
            st.rerun()

    # ---- Componente HTML con Html5Qrcode (escaneo continuo) ----
    scanner_html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 8px;
    gap: 12px;
  }
  #reader {
    width: 100%;
    max-width: 500px;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 0 28px rgba(0,102,255,0.5);
  }
  #status {
    width: 100%;
    max-width: 500px;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(8px);
    color: #bbd9ff;
    font-size: 14px;
    font-weight: 500;
    text-align: center;
    padding: 8px 16px;
    border-radius: 40px;
    margin-top: 8px;
  }
  video {
    border-radius: 16px;
  }
</style>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
</head>
<body>

<div id="reader"></div>
<div id="status">🔍 Iniciando cámara trasera...</div>

<script>
  let html5QrCode = null;
  let isScanning = true;
  let lastDetected = null;

  function onScanSuccess(decodedText, decodedResult) {
    if (!isScanning) return;
    if (lastDetected === decodedText) return;
    lastDetected = decodedText;

    // Detener el escáner para evitar múltiples disparos
    if (html5QrCode) {
      html5QrCode.stop().catch(e => console.warn(e));
      isScanning = false;
    }

    const statusDiv = document.getElementById('status');
    statusDiv.textContent = '✅ QR detectado: ' + decodedText + ' → procesando...';

    // Enviar el RU a Streamlit mediante query parameter
    const url = new URL(window.parent.location.href);
    url.searchParams.set('qr_ru', decodedText);
    window.parent.location.href = url.toString();
  }

  function onScanError(errorMessage) {
    // No mostrar errores comunes para no molestar
  }

  const config = {
    fps: 30,
    qrbox: { width: 250, height: 250 },
    aspectRatio: 1.0,
    rememberLastUsedCamera: true,
    supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
  };

  html5QrCode = new Html5Qrcode("reader");
  html5QrCode.start(
    { facingMode: "environment" },
    config,
    onScanSuccess,
    onScanError
  ).then(() => {
    document.getElementById('status').textContent = '✅ Cámara lista – escaneando códigos QR...';
  }).catch(err => {
    console.error(err);
    document.getElementById('status').textContent = '❌ No se pudo acceder a la cámara. Verifica permisos.';
  });

  window.addEventListener('beforeunload', () => {
    if (html5QrCode && html5QrCode.isScanning) {
      html5QrCode.stop().catch(e => console.warn(e));
    }
  });
</script>
</body>
</html>
"""
    components.html(scanner_html, height=550, scrolling=False)
