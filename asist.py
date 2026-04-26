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
            df["hora"] = pd.to_datetime(df["hora"], format="%H:%M:%S", errors="coerce").dt.strftime("%H:%M:%S")
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
        response = supabase.table("asistencia").select("*").eq("ru", str(ru)).eq("fecha", fecha.isoformat()).execute()
        if response.data:
            return True, response.data[0]
        return False, None
    except Exception as e:
        st.error(f"Error al verificar duplicado: {e}")
        return False, None

def registrar_asistencia_qr(ru_str):
    """
    Registra asistencia dado un RU como string.
    Retorna (tipo_mensaje, texto_mensaje)
    """
    estudiantes_df = leer_estudiantes()
    estudiante_fila = estudiantes_df[estudiantes_df["ru"].astype(str) == ru_str]

    if len(estudiante_fila) == 0:
        return "error", f"❌ RU '{ru_str}' no encontrado en la base de datos"

    nombres  = str(estudiante_fila.iloc[0]["nombres"])
    paterno  = str(estudiante_fila.iloc[0]["apellido_paterno"])
    materno  = str(estudiante_fila.iloc[0]["apellido_materno"])
    fecha, hora = obtener_fecha_hora_exacta()

    tiene_registro, registro_existente = verificar_registro_duplicado(ru_str, fecha)
    if tiene_registro:
        hora_reg = registro_existente.get("hora", "?")
        return "warning", f"⚠️ {nombres} {paterno} ya registró hoy a las {hora_reg}"

    try:
        supabase.table("asistencia").insert({
            "ru":               ru_str,
            "nombres":          nombres,
            "apellido_paterno": paterno,
            "apellido_materno": materno,
            "fecha":            fecha.isoformat(),
            "hora":             hora,
            "estado":           "Presente"
        }).execute()
        return "success", f"✅ Asistencia registrada: {nombres} {paterno} — {hora}"
    except Exception as e:
        return "error", f"❌ Error al guardar en Supabase: {str(e)}"

# ------------------------------------------------------------
# ESTILOS CSS
# ------------------------------------------------------------
CSS_STYLES = """
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #0a1a2f 100%);
        color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
    .subtitle-script { font-size: 1.2rem; color: #88aaff; font-style: italic; }
    .dashboard-compact { display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }
    .dashboard-card {
        flex: 1; background: rgba(20,30,55,0.7); backdrop-filter: blur(10px);
        border-radius: 20px; padding: 20px; text-align: center;
        border: 1px solid rgba(0,102,255,0.3); transition: transform 0.3s;
    }
    .dashboard-card:hover { transform: translateY(-5px); }
    .green-card  .title { color: #00ffaa; }
    .blue-card   .title { color: #0088ff; }
    .orange-card .title { color: #ffaa44; }
    .dashboard-card .value { font-size: 3rem; font-weight: bold; margin: 10px 0; }
    .progress-bar-bg  { background:#1e2a3a; border-radius:10px; height:10px; margin-top:15px; }
    .progress-bar-fill{ background:linear-gradient(90deg,#00ffcc,#0088ff); height:10px; border-radius:10px; }
    .student-search-card {
        background: rgba(20,30,55,0.6); border-radius:20px; padding:20px;
        text-align:center; margin:20px 0;
    }
    .student-name { font-size:1.8rem; font-weight:bold; color:#ffffff; }
    .student-ru   { font-size:1.2rem; color:#aaccff; }
    .stButton button {
        background: linear-gradient(135deg,#0066ff,#00aaff); border:none;
        border-radius:30px; padding:10px 25px; font-weight:bold; transition:all 0.3s;
    }
    .stButton button:hover { transform:scale(1.02); box-shadow:0 0 15px rgba(0,102,255,0.5); }
    .password-modal {
        background:rgba(20,30,55,0.8); backdrop-filter:blur(10px);
        border-radius:20px; padding:30px; text-align:center;
        border:1px solid #0066ff; max-width:400px; margin:0 auto;
    }
    .student-detail-card { background:rgba(20,30,55,0.5); border-radius:15px; padding:20px; margin:15px 0; }
</style>
"""

# ------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Asistencia con QR",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
defaults = {
    "menu_actual":                       "📝 Registrar estudiante",
    "ultimo_registro":                   None,
    "confirmar_eliminar":                None,
    "confirmar_eliminar_asistencia":     None,
    "confirmar_eliminar_todo_asistencia":False,
    "manual_auth":                       False,
    "selected_student_manual":           None,
    # ── QR scanner ──
    "qr_escaneado":                      "",   # RU recibido del iframe
    "qr_procesado":                      "",   # último RU ya procesado (evita doble procesado)
    "mensaje_escaneo":                   None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Desarrollado por Josué")
    st.markdown('<p style="color:#aaccff;">Base de datos en la nube con PostgreSQL</p>', unsafe_allow_html=True)

# ------------------------------------------------------------
# LOGO + TÍTULO
# ------------------------------------------------------------
logo_path = "assets/logo.png"
with st.container():
    col_logo, col_texto = st.columns([1, 8])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=80)
    with col_texto:
        st.markdown("""
        <div style="display:flex;flex-direction:column;justify-content:center;height:100%;">
            <h1 style="margin:0;line-height:1.2;">INGENIERÍA DE SISTEMAS</h1>
            <p class="subtitle-script" style="margin:0;">
                Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!
            </p>
        </div>""", unsafe_allow_html=True)

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
# HELPER: TARJETA EJECUTIVA
# ------------------------------------------------------------
def crear_tarjeta_estudiante(estudiante):
    ru             = str(estudiante["ru"])
    nombres        = estudiante["nombres"]
    paterno        = estudiante["apellido_paterno"]
    materno        = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    qr      = qrcode.make(ru, box_size=10, border=2)
    qr_size = 920
    qr      = qr.resize((qr_size, qr_size), Image.LANCZOS)

    card_size  = 1000
    background = Image.new('RGB', (card_size, card_size), color=(10, 20, 40))
    gradient   = Image.new('RGBA', (card_size, card_size), (0, 0, 0, 0))
    draw_grad  = ImageDraw.Draw(gradient)
    for y in range(card_size):
        blue_intensity = int(60 * (1 - y / card_size))
        draw_grad.rectangle([0, y, card_size, y+1], fill=(0, 0, blue_intensity, 180))
    background = Image.alpha_composite(background.convert('RGBA'), gradient).convert('RGB')
    draw = ImageDraw.Draw(background)

    font_bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    font_reg_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    title_font = ru_font = name_font = footer_font = None
    for p in font_bold_paths:
        if os.path.exists(p):
            title_font  = ImageFont.truetype(p, 88)
            ru_font     = ImageFont.truetype(p, 50)
            name_font   = ImageFont.truetype(p, 66)
            break
    for p in font_reg_paths:
        if os.path.exists(p):
            footer_font = ImageFont.truetype(p, 28)
            break
    if not title_font:
        title_font = ru_font = name_font = footer_font = ImageFont.load_default()

    draw.rectangle([0,0,card_size-1,card_size-1], outline=(0,102,255), width=8)

    bbox = draw.textbbox((0,0), nombre_completo, font=title_font)
    tx = (card_size - (bbox[2]-bbox[0])) // 2
    ty = 15
    draw.text((tx+3,ty+3), nombre_completo, fill=(0,0,0), font=title_font)
    draw.text((tx,ty),     nombre_completo, fill=(255,255,255), font=title_font)

    ru_text = f"RU: {ru}"
    bbox = draw.textbbox((0,0), ru_text, font=ru_font)
    rx = (card_size - (bbox[2]-bbox[0])) // 2
    ry = ty + 20
    draw.text((rx+2,ry+2), ru_text, fill=(0,0,0), font=ru_font)
    draw.text((rx,ry),     ru_text, fill=(255,255,200), font=ru_font)

    max_w = card_size - 60
    words, lines, current = nombre_completo.split(), [], ""
    for w in words:
        test = current + (" " + w if current else w)
        bb = draw.textbbox((0,0), test, font=name_font)
        if bb[2]-bb[0] <= max_w:
            current = test
        else:
            if current: lines.append(current)
            current = w
    if current: lines.append(current)
    if not lines: lines = [nombre_completo]

    spacing = 10
    sy = ry + 30
    for i, line in enumerate(lines):
        bb = draw.textbbox((0,0), line, font=name_font)
        lx = (card_size - (bb[2]-bb[0])) // 2
        ly = sy + i * spacing
        draw.text((lx+2,ly+2), line, fill=(0,0,0), font=name_font)
        draw.text((lx,ly),     line, fill=(255,255,255), font=name_font)

    qr_x = (card_size - qr_size) // 2
    qr_y = sy + len(lines)*spacing - 15
    background.paste(qr, (qr_x, qr_y))

    footer_text = "INGENIERÍA DE SISTEMAS\nUAP"
    fy = qr_y + qr_size + 30
    for i, line in enumerate(footer_text.split("\n")):
        bb = draw.textbbox((0,0), line, font=footer_font)
        fx = (card_size - (bb[2]-bb[0])) // 2
        fy2 = fy + i * 36
        draw.text((fx+2,fy2+2), line, fill=(0,0,0), font=footer_font)
        draw.text((fx,fy2),     line, fill=(220,220,255), font=footer_font)

    buf = io.BytesIO()
    background.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ============================================================
# SECCIÓN: REGISTRAR ESTUDIANTE
# ============================================================
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.session_state.manual_auth = False

    st.subheader("📝 Registrar nuevo estudiante")
    col1, col2 = st.columns(2)
    with col1:
        ru      = st.text_input("🔢 RU", placeholder="Solo números")
        nombres = st.text_input("👤 Nombres")
    with col2:
        paterno = st.text_input("👨 Apellido paterno")
        materno = st.text_input("👩 Apellido materno")

    _, col_btn, _ = st.columns([1,1,1])
    with col_btn:
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
                            "ru": ru, "nombres": nombres,
                            "apellido_paterno": paterno, "apellido_materno": materno
                        }).execute()
                        st.success("✅ Estudiante registrado exitosamente")

                        qr_img   = qrcode.make(ru)
                        qr_bytes = io.BytesIO()
                        qr_img.save(qr_bytes, format='PNG')
                        qr_bytes.seek(0)
                        _, ci, _ = st.columns([1,2,1])
                        with ci:
                            st.markdown(f'<div style="text-align:center;color:#fff;font-weight:bold;">{nombres.upper()} {paterno.upper()}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div style="text-align:center;color:#aaccff;">RU: {ru}</div>', unsafe_allow_html=True)
                            st.image(qr_bytes, width=300, caption="Código QR del estudiante")
                            buf2 = io.BytesIO()
                            qr_img.save(buf2, format="PNG"); buf2.seek(0)
                            st.download_button("⬇️ Descargar QR", data=buf2,
                                               file_name=f"{ru}_qr.png", mime="image/png",
                                               use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

# ============================================================
# SECCIÓN: LISTA ESTUDIANTES
# ============================================================
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.session_state.manual_auth = False

    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()

    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        st.markdown("---")

        # — Búsqueda —
        st.subheader("🔍 Buscar estudiante")
        c1, c2, _ = st.columns([3,1,3])
        with c1:
            ru_ver = st.text_input("Ingrese RU", placeholder="RU del estudiante", key="buscar_ru")
        with c2:
            buscar_click = st.button("🔍 Buscar", key="buscar_btn", use_container_width=True)

        if buscar_click and ru_ver:
            fila = estudiantes[estudiantes["ru"].astype(str) == ru_ver]
            if len(fila) > 0:
                ed = fila.iloc[0]
                nc = f"{ed['nombres']} {ed['apellido_paterno']}".strip().upper()
                qr_img2 = qrcode.make(ed["ru"])
                qbuf = io.BytesIO(); qr_img2.save(qbuf, format='PNG'); qbuf.seek(0)
                qb64 = base64.b64encode(qbuf.read()).decode()
                st.markdown(f"""
                <div class="student-search-card">
                    <div class="student-name">{nc}</div>
                    <div class="student-ru">RU: {ed['ru']}</div>
                    <img src="data:image/png;base64,{qb64}" width="280">
                </div>""", unsafe_allow_html=True)
                cb1, cb2, _ = st.columns([1,1,1])
                with cb1:
                    st.download_button("📥 Descargar QR",
                                       data=qbuf.getvalue(), file_name=f"{ed['ru']}_qr.png",
                                       mime="image/png", key="dl_qr_search", use_container_width=True)
                with cb2:
                    tarjeta = crear_tarjeta_estudiante(ed)
                    st.download_button("📇 Tarjeta Ejecutiva",
                                       data=tarjeta, file_name=f"tarjeta_{ed['ru']}.png",
                                       mime="image/png", key="dl_tarjeta_search", use_container_width=True)
            else:
                st.warning("⚠️ RU no encontrado")

        st.markdown("---")

        # — Editar / Eliminar —
        st.subheader("✏️ Gestionar estudiante")
        estudiantes["_display"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
        c1, _ = st.columns([1,2])
        with c1:
            sel = st.selectbox("Selecciona estudiante", estudiantes["_display"].tolist(), key="sel_est")
            ru_sel = sel.split(" - ")[0]
        ed_data = estudiantes[estudiantes["ru"] == ru_sel].iloc[0]

        with st.form("form_editar"):
            nru  = st.text_input("RU",              value=ed_data["ru"])
            nn   = st.text_input("Nombres",         value=ed_data["nombres"])
            np_  = st.text_input("Apellido paterno", value=ed_data["apellido_paterno"])
            nm   = st.text_input("Apellido materno", value=ed_data["apellido_materno"])
            cb1, cb2, _ = st.columns([1,1,2])
            with cb1: sub_act = st.form_submit_button("🔄 Actualizar", use_container_width=True)
            with cb2: sub_eli = st.form_submit_button("🗑️ Eliminar",   use_container_width=True)

        if sub_act:
            if not nru.isdigit():
                st.error("❌ RU debe ser numérico")
            else:
                try:
                    if nru != ru_sel:
                        ex = supabase.table("estudiantes").select("ru").eq("ru", nru).execute()
                        if ex.data: st.error("❌ Ese RU ya existe"); st.stop()
                    supabase.table("estudiantes").update({
                        "ru": nru, "nombres": nn, "apellido_paterno": np_, "apellido_materno": nm
                    }).eq("ru", ru_sel).execute()
                    if nru != ru_sel:
                        supabase.table("asistencia").update({"ru": nru}).eq("ru", ru_sel).execute()
                    st.success("✅ Actualizado"); st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if sub_eli:
            st.session_state.confirmar_eliminar = ru_sel

        if st.session_state.confirmar_eliminar:
            ruel  = st.session_state.confirmar_eliminar
            fila2 = estudiantes[estudiantes["ru"] == ruel].iloc[0]
            nomb  = f"{fila2['nombres']} {fila2['apellido_paterno']}"
            st.warning(f"⚠️ ¿Eliminar a **{nomb} (RU: {ruel})**? Se borrarán sus asistencias.")
            cc1, cc2, _ = st.columns([1,1,3])
            with cc1:
                if st.button("✅ Sí, eliminar", key="conf_eli", use_container_width=True):
                    supabase.table("asistencia").delete().eq("ru", ruel).execute()
                    supabase.table("estudiantes").delete().eq("ru", ruel).execute()
                    st.success("✅ Eliminado"); st.session_state.confirmar_eliminar = None; st.rerun()
            with cc2:
                if st.button("❌ Cancelar", key="canc_eli", use_container_width=True):
                    st.session_state.confirmar_eliminar = None; st.rerun()

        st.markdown("---")
        st.subheader("⬇️ Descargar Excel estudiantes")
        tmp = "estudiantes_tmp.xlsx"
        estudiantes.drop(columns=["_display"]).to_excel(tmp, index=False)
        with open(tmp, "rb") as f:
            st.download_button("📥 Descargar Excel", data=f, file_name="estudiantes.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay estudiantes registrados")

# ============================================================
# SECCIÓN: ESCANEAR QR  ← SOLUCIONADO
# ============================================================
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.session_state.manual_auth = False

    st.subheader("📸 Escanear QR — registro automático")

    # ── PASO 1: ¿Llega un RU nuevo desde el iframe vía query_params? ──
    # El iframe hace:  window.parent.postMessage({qr_ru: "12345"}, "*")
    # Y también setea ?qr_ru=12345 en la URL padre.
    # Streamlit recarga y aquí lo capturamos ANTES de limpiar.

    params       = st.query_params
    ru_from_url  = params.get("qr_ru", "")

    if ru_from_url and ru_from_url != st.session_state.qr_procesado:
        # Guardar en session_state para procesarlo
        st.session_state.qr_escaneado = ru_from_url
        # Limpiar URL inmediatamente para no reprocesar en el próximo rerun
        st.query_params.clear()
        # Procesar el registro
        tipo, texto = registrar_asistencia_qr(ru_from_url)
        st.session_state.mensaje_escaneo = {"tipo": tipo, "texto": texto}
        st.session_state.qr_procesado    = ru_from_url
        st.rerun()

    # ── PASO 2: Mostrar resultado del último escaneo ──
    if st.session_state.mensaje_escaneo:
        msg = st.session_state.mensaje_escaneo
        if   msg["tipo"] == "success": st.success(msg["texto"])
        elif msg["tipo"] == "warning": st.warning(msg["texto"])
        else:                          st.error(msg["texto"])

        col_btn, _ = st.columns([1,3])
        with col_btn:
            if st.button("📷 Escanear otro código", use_container_width=True):
                st.session_state.mensaje_escaneo = None
                st.session_state.qr_escaneado    = ""
                st.session_state.qr_procesado    = ""
                st.rerun()

    # ── PASO 3: Componente HTML del escáner ──
    # Usa postMessage Y también modifica la URL padre.
    # La modificación de URL es la que dispara el rerun de Streamlit.
    scanner_html = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: transparent;
      display: flex; flex-direction: column;
      align-items: center; padding: 10px; gap: 14px;
    }
    #reader {
      width: 100%; max-width: 480px;
      border-radius: 20px; overflow: hidden;
      box-shadow: 0 0 32px rgba(0,102,255,0.55);
    }
    #status {
      width: 100%; max-width: 480px;
      background: rgba(0,0,0,0.65); backdrop-filter: blur(8px);
      color: #bbd9ff; font-size: 15px; font-family: sans-serif;
      text-align: center; padding: 10px 18px; border-radius: 40px;
    }
    video { border-radius: 16px; }
  </style>
  <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
</head>
<body>
  <div id="reader"></div>
  <div id="status">🔍 Iniciando cámara trasera…</div>

  <script>
    let html5QrCode = null;
    let scanning    = true;
    let lastRU      = null;

    function onScanSuccess(decodedText) {
      // Ignorar si ya se envió este mismo RU o escáner detenido
      if (!scanning)            return;
      if (lastRU === decodedText) return;
      lastRU   = decodedText;
      scanning = false;

      // Detener cámara
      if (html5QrCode) {
        html5QrCode.stop().catch(function(e){ console.warn("stop:", e); });
      }

      document.getElementById('status').textContent =
        '✅ QR detectado: ' + decodedText + ' — enviando…';

      // ── Estrategia robusta: modificar la URL de la página PADRE ──
      // Esto provoca un rerun de Streamlit con ?qr_ru=<valor>
      try {
        var parentUrl = new URL(window.parent.location.href);
        parentUrl.searchParams.set('qr_ru', decodedText);
        window.parent.location.href = parentUrl.toString();
      } catch(err) {
        // Si por política de seguridad no podemos acceder al padre,
        // intentamos con postMessage (requiere listener en Streamlit — no disponible por defecto,
        // pero dejamos el intento para entornos con HTTPS mismo origen).
        window.parent.postMessage({ qr_ru: decodedText }, '*');
        document.getElementById('status').textContent =
          '⚠️ No se pudo redirigir automáticamente. RU: ' + decodedText;
      }
    }

    function onScanError(err) { /* ignorar errores de frame */ }

    var config = {
      fps: 30,
      qrbox: { width: 260, height: 260 },
      aspectRatio: 1.0,
      rememberLastUsedCamera: true
    };

    html5QrCode = new Html5Qrcode("reader");
    html5QrCode
      .start({ facingMode: "environment" }, config, onScanSuccess, onScanError)
      .then(function() {
        document.getElementById('status').textContent = '✅ Cámara lista — acerque el QR';
      })
      .catch(function(err) {
        // Intentar con cámara frontal si la trasera falla
        html5QrCode
          .start({ facingMode: "user" }, config, onScanSuccess, onScanError)
          .then(function() {
            document.getElementById('status').textContent = '✅ Cámara frontal lista — acerque el QR';
          })
          .catch(function(err2) {
            document.getElementById('status').textContent = '❌ Error cámara: ' + err2;
          });
      });

    window.addEventListener('beforeunload', function() {
      if (html5QrCode && html5QrCode.isScanning) {
        html5QrCode.stop().catch(function(e){});
      }
    });
  </script>
</body>
</html>
"""
    components.html(scanner_html, height=560, scrolling=False)

    # Instrucciones
    st.markdown("""
    <div style="text-align:center; color:#88aaff; font-size:0.9rem; margin-top:8px;">
        📱 Apunte la cámara al código QR del estudiante.<br>
        El registro se realizará de forma automática al detectarlo.
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECCIÓN: REGISTRO MANUAL
# ============================================================
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        st.markdown('<div class="password-modal"><h3>🔒 Acceso restringido</h3><p style="color:#aaccff;">Ingrese la contraseña</p></div>', unsafe_allow_html=True)
        with st.form("password_form"):
            pwd = st.text_input("Contraseña", type="password", placeholder="********")
            _, cb, _ = st.columns([1,2,1])
            with cb:
                sub_pwd = st.form_submit_button("🔓 Ingresar", use_container_width=True)
        if sub_pwd:
            if pwd == "pocoyo123":
                st.session_state.manual_auth = True; st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    else:
        st.subheader("✍️ Registrar asistencia manual")
        estudiantes = leer_estudiantes()
        if len(estudiantes) > 0:
            estudiantes["_display"] = estudiantes["ru"] + " - " + estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            sel_m = st.selectbox("👤 Seleccionar estudiante", estudiantes["_display"].tolist(), key="sel_manual")
            ru_m  = sel_m.split(" - ")[0]
            ed_m  = estudiantes[estudiantes["ru"].astype(str) == ru_m].iloc[0]

            st.markdown(f"""
            <div class="student-detail-card">
                <h4>📋 Datos del estudiante</h4>
                <p><strong>RU:</strong> {ed_m['ru']}</p>
                <p><strong>Nombres:</strong> {ed_m['nombres']}</p>
                <p><strong>Apellido Paterno:</strong> {ed_m['apellido_paterno']}</p>
                <p><strong>Apellido Materno:</strong> {ed_m['apellido_materno']}</p>
            </div>""", unsafe_allow_html=True)

            estado  = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
            fecha, hora = obtener_fecha_hora_exacta()
            tiene_reg, reg_ex = verificar_registro_duplicado(ru_m, fecha)

            if tiene_reg:
                st.warning(f"⚠️ Ya registró hoy a las {reg_ex['hora']} (Estado: {reg_ex['estado']})")
                _, cb, _ = st.columns([1,2,1])
                with cb: st.button("✅ Registrar asistencia", disabled=True, use_container_width=True)
            else:
                _, cb, _ = st.columns([1,2,1])
                with cb:
                    if st.button("✅ Registrar asistencia", use_container_width=True):
                        try:
                            supabase.table("asistencia").insert({
                                "ru":               ru_m,
                                "nombres":          ed_m["nombres"],
                                "apellido_paterno": ed_m["apellido_paterno"],
                                "apellido_materno": ed_m["apellido_materno"],
                                "fecha":            fecha.isoformat(),
                                "hora":             hora,
                                "estado":           estado
                            }).execute()
                            st.success(f"✅ Asistencia registrada a las {hora}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ No hay estudiantes registrados")

# ============================================================
# SECCIÓN: VER ASISTENCIA
# ============================================================
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.session_state.manual_auth = False

    st.subheader("📊 Registros de asistencia")

    total_est    = len(leer_estudiantes())
    asistencia_df = leer_asistencia()
    hoy           = datetime.now(ZONA_HORARIA).date()
    reg_hoy       = asistencia_df[asistencia_df["fecha"] == hoy]["ru"].nunique() if len(asistencia_df) > 0 else 0
    faltantes     = total_est - reg_hoy
    pct_reg       = (reg_hoy  / total_est * 100) if total_est > 0 else 0
    pct_falt      = (faltantes/ total_est * 100) if total_est > 0 else 0

    st.markdown(f"""
    <div class="dashboard-compact">
        <div class="dashboard-card green-card">
            <div class="title">📋 Total estudiantes</div>
            <div class="value">{total_est}</div>
            <div class="percentage">100% total</div>
        </div>
        <div class="dashboard-card blue-card">
            <div class="title">✅ Ya registrados</div>
            <div class="value">{reg_hoy}</div>
            <div class="percentage">{pct_reg:.1f}% del total</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{pct_reg}%;"></div>
            </div>
        </div>
        <div class="dashboard-card orange-card">
            <div class="title">❌ Faltantes</div>
            <div class="value">{faltantes}</div>
            <div class="percentage">{pct_falt:.1f}% sin registrar</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{pct_falt}%;"></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if len(asistencia_df) > 0:
        mostrar = asistencia_df.copy()
        mostrar["fecha"] = pd.to_datetime(mostrar["fecha"]).dt.strftime("%d-%m-%Y")
        st.dataframe(mostrar.drop(columns=["id"]), use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 Verificación de integridad")
        dups = asistencia_df.groupby(["ru","fecha"]).size().reset_index(name="count")
        dups = dups[dups["count"] > 1]
        if len(dups) > 0:
            st.warning(f"⚠️ {len(dups)} casos duplicados encontrados")
            if st.button("🧹 Limpiar duplicados", use_container_width=True):
                ids_ok = asistencia_df.groupby(["ru","fecha"])["id"].first().tolist()
                supabase.table("asistencia").delete().not_.in_("id", ids_ok).execute()
                st.success("✅ Duplicados eliminados"); st.rerun()
        else:
            st.success("✅ Sin registros duplicados")

        st.markdown("---")
        st.subheader("✏️ Editar estado de registro")
        asistencia_df["_desc"] = (
            asistencia_df["ru"] + " - " +
            asistencia_df["nombres"] + " " +
            asistencia_df["apellido_paterno"] + " (" +
            asistencia_df["fecha"].astype(str) + " " +
            asistencia_df["hora"].astype(str) + ")"
        )
        opciones = asistencia_df["_desc"].tolist()
        c1, c2 = st.columns([2,1])
        with c1:
            sel_as = st.selectbox("Registro a editar", opciones, key="sel_asist")
            idx_as = asistencia_df[asistencia_df["_desc"] == sel_as].index[0]
            id_reg = asistencia_df.loc[idx_as, "id"]
            est_ac = asistencia_df.loc[idx_as, "estado"]
        with c2:
            estados = ["Presente","Tarde","Permiso","Ausente"]
            nuevo_est = st.selectbox("Nuevo estado", estados,
                                     index=estados.index(est_ac) if est_ac in estados else 0)
        if st.button("🔄 Actualizar estado", use_container_width=True):
            supabase.table("asistencia").update({"estado": nuevo_est}).eq("id", id_reg).execute()
            st.success("✅ Estado actualizado"); st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Eliminar registro individual")
        sel_eli = st.selectbox("Registro a eliminar", opciones, key="sel_eli_as")
        idx_eli = asistencia_df[asistencia_df["_desc"] == sel_eli].index[0]
        id_eli  = asistencia_df.loc[idx_eli, "id"]
        if st.button("🗑️ Eliminar este registro", use_container_width=True):
            st.session_state.confirmar_eliminar_asistencia = id_eli
        if st.session_state.confirmar_eliminar_asistencia == id_eli and id_eli is not None:
            st.warning(f"⚠️ ¿Eliminar **{sel_eli}**?")
            cc1, cc2, _ = st.columns([1,1,3])
            with cc1:
                if st.button("✅ Sí", key="conf_eli_as", use_container_width=True):
                    supabase.table("asistencia").delete().eq("id", id_eli).execute()
                    st.success("✅ Eliminado")
                    st.session_state.confirmar_eliminar_asistencia = None; st.rerun()
            with cc2:
                if st.button("❌ No", key="canc_eli_as", use_container_width=True):
                    st.session_state.confirmar_eliminar_asistencia = None; st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Eliminar TODA la asistencia")
        if st.button("⚠️ Eliminar TODOS los registros", use_container_width=True):
            st.session_state.confirmar_eliminar_todo_asistencia = True
        if st.session_state.confirmar_eliminar_todo_asistencia:
            st.warning("⚠️ ¡Esta acción borrará TODO! No se puede deshacer.")
            cc1, cc2, _ = st.columns([1,1,3])
            with cc1:
                if st.button("✅ Sí, borrar todo", key="conf_todo", use_container_width=True):
                    supabase.table("asistencia").delete().neq("id", 0).execute()
                    st.success("✅ Todos los registros eliminados")
                    st.session_state.confirmar_eliminar_todo_asistencia = False; st.rerun()
            with cc2:
                if st.button("❌ Cancelar", key="canc_todo", use_container_width=True):
                    st.session_state.confirmar_eliminar_todo_asistencia = False; st.rerun()

        st.markdown("---")
        st.subheader("⬇️ Descargar asistencia del día")
        as_hoy = asistencia_df[asistencia_df["fecha"] == hoy].copy()
        if "id" in as_hoy.columns: as_hoy = as_hoy.drop(columns=["id"])
        if "_desc" in as_hoy.columns: as_hoy = as_hoy.drop(columns=["_desc"])
        if len(as_hoy) > 0:
            as_hoy["fecha"] = pd.to_datetime(as_hoy["fecha"]).dt.strftime("%d-%m-%Y")
            fname = f"asistencia_{hoy.strftime('%d-%m-%Y')}.xlsx"
            as_hoy.to_excel(fname, index=False)
            with open(fname, "rb") as f:
                st.download_button("📥 Descargar Excel del día", data=f,
                                   file_name=fname, use_container_width=True)
        else:
            st.info("📭 Sin registros para hoy")
    else:
        st.info("📭 No hay registros de asistencia")
