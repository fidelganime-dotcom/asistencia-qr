"""
Sistema de Asistencia con QR — versión con st.camera_input + pyzbar
Sin iframes, sin redirecciones de URL, sin problemas de origen cruzado.
El escaneo ocurre 100% en Python: Streamlit captura la foto y pyzbar lee el QR.
"""

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

# pyzbar para leer QR desde imagen
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_OK = True
except ImportError:
    PYZBAR_OK = False

# ── Supabase ────────────────────────────────────────────────
SUPABASE_URL = "https://rwmxhbojhbscrktswmhg.supabase.co"
SUPABASE_KEY = "sb_publishable_Ukse6FwyRq-Qg1FW8zDbLA_QqLmtUTm"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

# ── Zona horaria ─────────────────────────────────────────────
TZ = pytz.timezone("America/La_Paz")

def ahora():
    n = datetime.now(TZ)
    return n.date(), n.strftime("%H:%M:%S")

# ── Helpers Supabase ─────────────────────────────────────────
@st.cache_data(ttl=10)
def leer_estudiantes():
    r = supabase.table("estudiantes").select("*").execute()
    if r.data:
        df = pd.DataFrame(r.data)[["ru","nombres","apellido_paterno","apellido_materno"]]
        return df
    return pd.DataFrame(columns=["ru","nombres","apellido_paterno","apellido_materno"])

@st.cache_data(ttl=5)
def leer_asistencia():
    r = supabase.table("asistencia").select("*").execute()
    if r.data:
        df = pd.DataFrame(r.data)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        cols = ["id","ru","nombres","apellido_paterno","apellido_materno","fecha","hora","estado"]
        return df[cols].sort_values("id").reset_index(drop=True)
    return pd.DataFrame(columns=["id","ru","nombres","apellido_paterno","apellido_materno","fecha","hora","estado"])

def duplicado(ru, fecha):
    r = supabase.table("asistencia").select("*").eq("ru", str(ru)).eq("fecha", fecha.isoformat()).execute()
    return (True, r.data[0]) if r.data else (False, None)

def registrar(ru_str):
    """Registra asistencia. Devuelve (tipo, mensaje)."""
    leer_estudiantes.clear()
    df = leer_estudiantes()
    fila = df[df["ru"].astype(str) == ru_str]
    if fila.empty:
        return "error", f"RU '{ru_str}' no encontrado en la base de datos"
    e = fila.iloc[0]
    fecha, hora = ahora()
    tiene, reg = duplicado(ru_str, fecha)
    if tiene:
        return "warning", f"{e['nombres']} {e['apellido_paterno']} ya registró hoy a las {reg['hora']}"
    try:
        supabase.table("asistencia").insert({
            "ru": ru_str,
            "nombres":          str(e["nombres"]),
            "apellido_paterno": str(e["apellido_paterno"]),
            "apellido_materno": str(e["apellido_materno"]),
            "fecha": fecha.isoformat(),
            "hora":  hora,
            "estado": "Presente"
        }).execute()
        leer_asistencia.clear()
        return "success", f"Asistencia registrada: {e['nombres']} {e['apellido_paterno']} a las {hora}"
    except Exception as ex:
        return "error", f"Error Supabase: {ex}"

# ── Tarjeta ejecutiva ────────────────────────────────────────
def crear_tarjeta(est):
    ru  = str(est["ru"])
    nc  = f"{est['nombres']} {est['apellido_paterno']} {est['apellido_materno']}".strip().upper()
    qr  = qrcode.make(ru, box_size=10, border=2).resize((880, 880), Image.LANCZOS)
    sz  = 1000
    bg  = Image.new("RGB", (sz, sz), (10, 20, 40))
    ov  = Image.new("RGBA", (sz, sz), (0,0,0,0))
    dov = ImageDraw.Draw(ov)
    for y in range(sz):
        dov.rectangle([0,y,sz,y+1], fill=(0,0,int(60*(1-y/sz)),160))
    bg  = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    d   = ImageDraw.Draw(bg)
    bold_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    tf = rf = None
    for p in bold_fonts:
        if os.path.exists(p):
            tf = ImageFont.truetype(p, 72)
            rf = ImageFont.truetype(p, 44)
            break
    if not tf:
        tf = rf = ImageFont.load_default()
    d.rectangle([0,0,sz-1,sz-1], outline=(0,102,255), width=8)
    bb = d.textbbox((0,0), nc, font=tf)
    d.text(((sz-(bb[2]-bb[0]))//2+3, 18), nc, fill=(0,0,0), font=tf)
    d.text(((sz-(bb[2]-bb[0]))//2,   15), nc, fill=(255,255,255), font=tf)
    ru_t = f"RU: {ru}"
    bb2 = d.textbbox((0,0), ru_t, font=rf)
    d.text(((sz-(bb2[2]-bb2[0]))//2, 105), ru_t, fill=(255,255,200), font=rf)
    bg.paste(qr, ((sz-880)//2, 155))
    buf = io.BytesIO()
    bg.save(buf, "PNG")
    buf.seek(0)
    return buf

# ── Página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Asistencia QR — Sistemas",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: #070d1a;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(0,90,255,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(0,200,180,0.10) 0%, transparent 55%);
    color: #e8eeff;
}

section[data-testid="stSidebar"] { background: #0a1020; border-right: 1px solid #1a2540; }

h1,h2,h3,h4,h5,h6 {
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: .04em; color: #fff !important;
}

div[role="radiogroup"] {
    display: flex; gap: 6px; flex-wrap: wrap;
    background: #0c1628; border-radius: 14px; padding: 6px;
    border: 1px solid #1e3060;
}
div[role="radiogroup"] label {
    flex: 1; text-align: center;
    background: transparent; border-radius: 10px;
    padding: 8px 14px; cursor: pointer;
    font-family: 'Rajdhani', sans-serif; font-weight: 600; font-size: .95rem;
    color: #7a99cc; transition: all .2s; border: 1px solid transparent;
}
div[role="radiogroup"] label:hover { background: #152040; color: #a0c0ff; }

input, textarea, select {
    background: #0d1830 !important; color: #e8eeff !important;
    border: 1px solid #1e3060 !important; border-radius: 10px !important;
}
input:focus {
    border-color: #0055ff !important;
    box-shadow: 0 0 0 3px rgba(0,85,255,.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #0044cc, #0099dd) !important;
    color: #fff !important; border: none !important;
    border-radius: 12px !important; font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important; font-size: 1rem !important;
    padding: 10px 22px !important; transition: all .2s !important;
    letter-spacing: .04em !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0,80,255,.35) !important;
}
.stButton > button:disabled { opacity: .4 !important; transform: none !important; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #003399, #006699) !important;
    color: #fff !important; border: none !important; border-radius: 12px !important;
    font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;
}

.stDataFrame { border-radius: 14px; overflow: hidden; border: 1px solid #1a2e50; }

.card {
    background: linear-gradient(145deg, #0d1830, #0a1420);
    border: 1px solid #1a3060; border-radius: 18px; padding: 22px 26px; margin: 10px 0;
}
.stat-row { display: flex; gap: 16px; margin: 18px 0; flex-wrap: wrap; }
.stat {
    flex: 1; min-width: 140px; background: #0c1628; border: 1px solid #1a3060;
    border-radius: 16px; padding: 18px; text-align: center;
}
.stat .val {
    font-family: 'Rajdhani', sans-serif; font-size: 2.8rem;
    font-weight: 700; line-height: 1;
}
.stat .lbl { font-size: .8rem; color: #6688aa; margin-top: 6px; text-transform: uppercase; letter-spacing: .08em; }
.stat.green .val { color: #00e8a0; }
.stat.blue  .val { color: #2299ff; }
.stat.orange .val { color: #ffaa33; }
.pbar { background: #1a2a40; border-radius: 8px; height: 8px; margin-top: 10px; overflow: hidden; }
.pfill { height: 8px; border-radius: 8px; background: linear-gradient(90deg,#00e8a0,#0088ff); }

.app-header {
    display: flex; align-items: center; gap: 18px;
    padding: 18px 0 12px; border-bottom: 1px solid #1a2e50; margin-bottom: 18px;
}
.app-title { font-family: 'Rajdhani', sans-serif; font-size: 2rem; font-weight: 700; color: #fff; line-height: 1.1; }
.app-sub { font-size: .9rem; color: #6688aa; font-style: italic; margin-top: 2px; }

.scan-wrap {
    background: #0c1628; border: 2px dashed #1e4080;
    border-radius: 20px; padding: 28px; text-align: center; margin: 16px 0;
}
.scan-wrap p { color: #6688aa; margin: 10px 0 0; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
for k, v in {
    "manual_auth":      False,
    "conf_del_est":     None,
    "conf_del_asist":   None,
    "conf_del_todo":    False,
    "qr_result":        None,
    "last_photo_id":    None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <div class="app-title">INGENIERIA DE SISTEMAS</div>
    <div class="app-sub">Sistema de Asistencia con QR · Base de datos en la nube · UAP</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Menú ─────────────────────────────────────────────────────
MENU = [
    "Registrar estudiante",
    "Lista estudiantes",
    "Escanear QR",
    "Registro manual",
    "Ver asistencia"
]
menu = st.radio("", MENU, horizontal=True, label_visibility="collapsed")
st.markdown("<hr style='border-color:#1a2e50;margin:10px 0 20px'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 1. REGISTRAR ESTUDIANTE
# ════════════════════════════════════════════════════════════
if menu == "Registrar estudiante":
    st.markdown("### Nuevo estudiante")
    c1, c2 = st.columns(2)
    with c1:
        ru_in  = st.text_input("RU (solo numeros)", placeholder="Ej: 20210001")
        nom_in = st.text_input("Nombres", placeholder="Ej: Juan Carlos")
    with c2:
        pat_in = st.text_input("Apellido paterno", placeholder="Ej: Mamani")
        mat_in = st.text_input("Apellido materno", placeholder="Ej: Quispe")

    if st.button("Guardar estudiante", use_container_width=True):
        if not ru_in.strip():
            st.error("El RU no puede estar vacio")
        elif not ru_in.isdigit():
            st.error("El RU debe contener solo numeros")
        elif not nom_in.strip():
            st.error("Ingresa los nombres")
        else:
            ex = supabase.table("estudiantes").select("ru").eq("ru", ru_in).execute()
            if ex.data:
                st.error("Ese RU ya existe")
            else:
                supabase.table("estudiantes").insert({
                    "ru": ru_in, "nombres": nom_in,
                    "apellido_paterno": pat_in, "apellido_materno": mat_in
                }).execute()
                leer_estudiantes.clear()
                st.success(f"Estudiante {nom_in} {pat_in} registrado correctamente")
                qr_img = qrcode.make(ru_in)
                buf = io.BytesIO()
                qr_img.save(buf, "PNG")
                buf.seek(0)
                _, ci, _ = st.columns([1,2,1])
                with ci:
                    st.image(buf, caption=f"QR — RU: {ru_in}", width=280)
                    buf2 = io.BytesIO()
                    qr_img.save(buf2, "PNG")
                    buf2.seek(0)
                    st.download_button(
                        "Descargar QR", buf2,
                        f"{ru_in}_qr.png", "image/png",
                        use_container_width=True
                    )

# ════════════════════════════════════════════════════════════
# 2. LISTA ESTUDIANTES
# ════════════════════════════════════════════════════════════
elif menu == "Lista estudiantes":
    st.markdown("### Lista de estudiantes")
    df_est = leer_estudiantes()

    if df_est.empty:
        st.info("No hay estudiantes registrados aun")
    else:
        st.dataframe(df_est, use_container_width=True, hide_index=True)
        st.markdown(f"**Total:** {len(df_est)} estudiantes")
        st.markdown("---")

        st.markdown("#### Buscar por RU")
        c1, c2, _ = st.columns([2,1,2])
        with c1:
            ru_b = st.text_input(
                "RU", key="busq_ru",
                label_visibility="collapsed",
                placeholder="Ingresa el RU"
            )
        with c2:
            buscar = st.button("Buscar", key="btn_busq", use_container_width=True)

        if buscar and ru_b:
            fila = df_est[df_est["ru"].astype(str) == ru_b]
            if fila.empty:
                st.warning("RU no encontrado")
            else:
                e = fila.iloc[0]
                nc = f"{e['nombres']} {e['apellido_paterno']}".upper()
                qb = io.BytesIO()
                qrcode.make(e["ru"]).save(qb, "PNG")
                qb.seek(0)
                b64 = base64.b64encode(qb.read()).decode()
                st.markdown(f"""
                <div class="card" style="text-align:center">
                  <div style="font-family:Rajdhani,sans-serif;font-size:1.6rem;font-weight:700">{nc}</div>
                  <div style="color:#6688aa;margin:4px 0 14px">RU: {e['ru']}</div>
                  <img src="data:image/png;base64,{b64}" width="220">
                </div>""", unsafe_allow_html=True)
                ca, cb, _ = st.columns([1,1,2])
                with ca:
                    qb2 = io.BytesIO()
                    qrcode.make(e["ru"]).save(qb2, "PNG")
                    qb2.seek(0)
                    st.download_button("QR", qb2, f"{e['ru']}_qr.png", "image/png", use_container_width=True)
                with cb:
                    t = crear_tarjeta(e)
                    st.download_button("Tarjeta", t, f"tarjeta_{e['ru']}.png", "image/png", use_container_width=True)

        st.markdown("---")
        st.markdown("#### Editar o eliminar estudiante")
        df_est["_d"] = df_est["ru"] + " — " + df_est["nombres"] + " " + df_est["apellido_paterno"]
        sel = st.selectbox("Estudiante", df_est["_d"].tolist(), key="sel_ed_est")
        ru_sel = sel.split(" — ")[0]
        ed = df_est[df_est["ru"] == ru_sel].iloc[0]

        with st.form("form_edit_est"):
            nru = st.text_input("RU",               value=ed["ru"])
            nn  = st.text_input("Nombres",          value=ed["nombres"])
            np_ = st.text_input("Apellido paterno", value=ed["apellido_paterno"])
            nm  = st.text_input("Apellido materno", value=ed["apellido_materno"])
            fa, fb, _ = st.columns([1,1,2])
            with fa: sub_up  = st.form_submit_button("Actualizar", use_container_width=True)
            with fb: sub_del = st.form_submit_button("Eliminar",   use_container_width=True)

        if sub_up:
            if not nru.isdigit():
                st.error("RU debe ser numerico")
            else:
                if nru != ru_sel:
                    ex2 = supabase.table("estudiantes").select("ru").eq("ru", nru).execute()
                    if ex2.data:
                        st.error("Ese RU ya existe")
                        st.stop()
                supabase.table("estudiantes").update({
                    "ru": nru, "nombres": nn,
                    "apellido_paterno": np_, "apellido_materno": nm
                }).eq("ru", ru_sel).execute()
                if nru != ru_sel:
                    supabase.table("asistencia").update({"ru": nru}).eq("ru", ru_sel).execute()
                leer_estudiantes.clear()
                leer_asistencia.clear()
                st.success("Actualizado correctamente")
                st.rerun()

        if sub_del:
            st.session_state.conf_del_est = ru_sel

        if st.session_state.conf_del_est:
            rde  = st.session_state.conf_del_est
            fde  = df_est[df_est["ru"] == rde].iloc[0]
            st.warning(
                f"Eliminar a **{fde['nombres']} {fde['apellido_paterno']}** "
                f"(RU {rde}) y todas sus asistencias?"
            )
            ya, no, _ = st.columns([1,1,3])
            with ya:
                if st.button("Si, eliminar", key="conf_del_e", use_container_width=True):
                    supabase.table("asistencia").delete().eq("ru", rde).execute()
                    supabase.table("estudiantes").delete().eq("ru", rde).execute()
                    leer_estudiantes.clear()
                    leer_asistencia.clear()
                    st.session_state.conf_del_est = None
                    st.rerun()
            with no:
                if st.button("Cancelar", key="canc_del_e", use_container_width=True):
                    st.session_state.conf_del_est = None
                    st.rerun()

        st.markdown("---")
        tmp = "est_tmp.xlsx"
        df_est.drop(columns=["_d"]).to_excel(tmp, index=False)
        with open(tmp, "rb") as f:
            st.download_button("Exportar Excel", f, "estudiantes.xlsx", use_container_width=True)

# ════════════════════════════════════════════════════════════
# 3. ESCANEAR QR — con st.camera_input + pyzbar (100% Python, sin iframes)
# ════════════════════════════════════════════════════════════
elif menu == "Escanear QR":

    st.markdown("### Escanear codigo QR")

    if not PYZBAR_OK:
        st.error("""
**Falta la libreria pyzbar.**

Ejecuta en tu terminal:
```
pip install pyzbar
```

En Linux / Streamlit Cloud tambien necesitas:
```
sudo apt-get install libzbar0
```
O agrega `libzbar0` en tu archivo `packages.txt` (para Streamlit Cloud).

Luego reinicia la app.
        """)
        st.stop()

    # Resultado del ultimo escaneo
    if st.session_state.qr_result:
        r = st.session_state.qr_result
        if   r["tipo"] == "success": st.success(r["texto"])
        elif r["tipo"] == "warning": st.warning(r["texto"])
        else:                         st.error(r["texto"])

    st.markdown("""
    <div class="scan-wrap">
      <div style="font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:600;color:#a0c8ff;">
        Toma una foto del codigo QR del estudiante
      </div>
      <p>Usa el boton para abrir la camara. Cuando el QR este bien enfocado, toma la foto.<br>
         El registro se realizara automaticamente.</p>
    </div>
    """, unsafe_allow_html=True)

    foto = st.camera_input(
        label="Apunta la camara al codigo QR y toma la foto",
        key="cam_qr",
        help="Usa la camara trasera en movil para mejor resultado"
    )

    if foto is not None:
        foto_id = hash(foto.getvalue())
        if foto_id != st.session_state.last_photo_id:
            st.session_state.last_photo_id = foto_id

            img = Image.open(foto)
            decoded = pyzbar_decode(img)

            if not decoded:
                # Segundo intento: escala de grises con mayor contraste
                import numpy as np
                arr = np.array(img.convert("L")).astype(int)
                arr = np.clip((arr - 128) * 1.8 + 128, 0, 255).astype("uint8")
                decoded = pyzbar_decode(Image.fromarray(arr))

            if not decoded:
                # Tercer intento: redimensionar al doble
                img_big = img.resize((img.width*2, img.height*2), Image.LANCZOS)
                decoded = pyzbar_decode(img_big)

            if decoded:
                ru_detectado = decoded[0].data.decode("utf-8").strip()
                tipo, texto  = registrar(ru_detectado)
                st.session_state.qr_result = {"tipo": tipo, "texto": texto}
                st.rerun()
            else:
                st.session_state.qr_result = {
                    "tipo": "error",
                    "texto": (
                        "No se detecto ningun codigo QR en la foto. "
                        "Intenta con mejor iluminacion y el QR bien centrado y enfocado."
                    )
                }
                st.rerun()

    if st.session_state.qr_result:
        if st.button("Escanear otro QR", use_container_width=True):
            st.session_state.qr_result     = None
            st.session_state.last_photo_id  = None
            st.rerun()

    st.markdown("""
    <div style="margin-top:20px;padding:16px 20px;background:#0a1520;border-radius:14px;
                border:1px solid #1a2e50;font-size:.88rem;color:#6688aa;">
    <strong style="color:#a0c0e0">Consejos para mejor lectura:</strong><br>
    Buena iluminacion (evita sombras sobre el QR) ·
    Mantén el QR plano y sin doblar ·
    El QR debe ocupar al menos un tercio del encuadre ·
    Si falla, intenta con la camara trasera del movil
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 4. REGISTRO MANUAL
# ════════════════════════════════════════════════════════════
elif menu == "Registro manual":
    if not st.session_state.manual_auth:
        st.markdown("### Acceso restringido")
        _, cc, _ = st.columns([1,2,1])
        with cc:
            with st.form("pwd_form"):
                pwd = st.text_input("Contrasena", type="password", placeholder="Ingresa la contrasena")
                sub = st.form_submit_button("Ingresar", use_container_width=True)
        if sub:
            if pwd == "pocoyo123":
                st.session_state.manual_auth = True
                st.rerun()
            else:
                st.error("Contrasena incorrecta")
    else:
        st.markdown("### Registro manual de asistencia")
        df_est = leer_estudiantes()
        if df_est.empty:
            st.warning("No hay estudiantes registrados")
        else:
            df_est["_d"] = df_est["ru"] + " — " + df_est["nombres"] + " " + df_est["apellido_paterno"]
            sel_m = st.selectbox("Estudiante", df_est["_d"].tolist(), key="sel_manual")
            ru_m  = sel_m.split(" — ")[0]
            e_m   = df_est[df_est["ru"].astype(str) == ru_m].iloc[0]

            st.markdown(f"""
            <div class="card">
              <strong>{e_m['nombres']} {e_m['apellido_paterno']} {e_m['apellido_materno']}</strong>
              &nbsp;&nbsp;<span style="color:#6688aa;">RU: {e_m['ru']}</span>
            </div>""", unsafe_allow_html=True)

            estado_m        = st.selectbox("Estado", ["Presente","Tarde","Permiso","Ausente"])
            fecha_m, hora_m = ahora()
            tiene_m, reg_m  = duplicado(ru_m, fecha_m)

            if tiene_m:
                st.warning(f"Ya registro hoy a las {reg_m['hora']} — Estado: {reg_m['estado']}")
                st.button("Registrar asistencia", disabled=True, use_container_width=True)
            else:
                if st.button("Registrar asistencia", use_container_width=True):
                    supabase.table("asistencia").insert({
                        "ru":               ru_m,
                        "nombres":          str(e_m["nombres"]),
                        "apellido_paterno": str(e_m["apellido_paterno"]),
                        "apellido_materno": str(e_m["apellido_materno"]),
                        "fecha":            fecha_m.isoformat(),
                        "hora":             hora_m,
                        "estado":           estado_m
                    }).execute()
                    leer_asistencia.clear()
                    st.success(f"Asistencia registrada a las {hora_m}")
                    st.rerun()

        if st.button("Cerrar sesion admin", use_container_width=True):
            st.session_state.manual_auth = False
            st.rerun()

# ════════════════════════════════════════════════════════════
# 5. VER ASISTENCIA
# ════════════════════════════════════════════════════════════
elif menu == "Ver asistencia":
    st.markdown("### Registros de asistencia")

    df_as   = leer_asistencia()
    tot_est = len(leer_estudiantes())
    hoy     = datetime.now(TZ).date()
    reg_hoy = df_as[df_as["fecha"] == hoy]["ru"].nunique() if not df_as.empty else 0
    falt    = tot_est - reg_hoy
    pct_r   = reg_hoy / tot_est * 100 if tot_est > 0 else 0
    pct_f   = falt    / tot_est * 100 if tot_est > 0 else 0

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat green">
        <div class="val">{tot_est}</div>
        <div class="lbl">Total estudiantes</div>
      </div>
      <div class="stat blue">
        <div class="val">{reg_hoy}</div>
        <div class="lbl">Registrados hoy</div>
        <div class="pbar"><div class="pfill" style="width:{pct_r:.1f}%"></div></div>
        <div style="font-size:.75rem;color:#4488aa;margin-top:4px">{pct_r:.1f}%</div>
      </div>
      <div class="stat orange">
        <div class="val">{falt}</div>
        <div class="lbl">Faltantes hoy</div>
        <div class="pbar">
          <div class="pfill" style="width:{pct_f:.1f}%;background:linear-gradient(90deg,#ffaa33,#ff5555)">
          </div>
        </div>
        <div style="font-size:.75rem;color:#8866aa;margin-top:4px">{pct_f:.1f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Actualizar datos", use_container_width=True):
        leer_asistencia.clear()
        leer_estudiantes.clear()
        st.rerun()

    if df_as.empty:
        st.info("No hay registros de asistencia aun")
    else:
        mostrar = df_as.copy()
        mostrar["fecha"] = pd.to_datetime(mostrar["fecha"]).dt.strftime("%d-%m-%Y")
        st.dataframe(mostrar.drop(columns=["id"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Editar estado de un registro")
        df_as["_d"] = (
            df_as["ru"] + " — " +
            df_as["nombres"] + " " +
            df_as["apellido_paterno"] + " (" +
            df_as["fecha"].astype(str) + " " +
            df_as["hora"].astype(str) + ")"
        )
        opc = df_as["_d"].tolist()
        c1, c2 = st.columns([3,1])
        with c1:
            sel_as = st.selectbox("Registro", opc, key="sel_ed_as")
        idx_as = df_as[df_as["_d"] == sel_as].index[0]
        id_as  = df_as.loc[idx_as, "id"]
        est_as = df_as.loc[idx_as, "estado"]
        estados = ["Presente","Tarde","Permiso","Ausente"]
        with c2:
            nuevo_est = st.selectbox(
                "Estado", estados,
                index=estados.index(est_as) if est_as in estados else 0
            )
        if st.button("Actualizar estado", use_container_width=True):
            supabase.table("asistencia").update({"estado": nuevo_est}).eq("id", id_as).execute()
            leer_asistencia.clear()
            st.success("Estado actualizado")
            st.rerun()

        st.markdown("---")
        st.markdown("#### Eliminar registro individual")
        sel_del = st.selectbox("Registro a eliminar", opc, key="sel_del_as")
        idx_del = df_as[df_as["_d"] == sel_del].index[0]
        id_del  = df_as.loc[idx_del, "id"]
        if st.button("Eliminar este registro", use_container_width=True):
            st.session_state.conf_del_asist = id_del
        if st.session_state.conf_del_asist == id_del and id_del is not None:
            st.warning(f"Eliminar el registro: **{sel_del}**?")
            ya2, no2, _ = st.columns([1,1,3])
            with ya2:
                if st.button("Si, eliminar", key="conf_da", use_container_width=True):
                    supabase.table("asistencia").delete().eq("id", id_del).execute()
                    leer_asistencia.clear()
                    st.session_state.conf_del_asist = None
                    st.rerun()
            with no2:
                if st.button("No, cancelar", key="canc_da", use_container_width=True):
                    st.session_state.conf_del_asist = None
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Borrar TODA la asistencia")
        if st.button("Eliminar TODOS los registros", use_container_width=True):
            st.session_state.conf_del_todo = True
        if st.session_state.conf_del_todo:
            st.warning("Esta accion borrara TODOS los registros. No se puede deshacer.")
            ya3, no3, _ = st.columns([1,1,3])
            with ya3:
                if st.button("Si, borrar todo", key="conf_dt", use_container_width=True):
                    supabase.table("asistencia").delete().neq("id", 0).execute()
                    leer_asistencia.clear()
                    st.session_state.conf_del_todo = False
                    st.rerun()
            with no3:
                if st.button("Cancelar", key="canc_dt", use_container_width=True):
                    st.session_state.conf_del_todo = False
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Exportar asistencia del dia")
        as_hoy = df_as[df_as["fecha"] == hoy].drop(columns=["id","_d"], errors="ignore").copy()
        if not as_hoy.empty:
            as_hoy["fecha"] = pd.to_datetime(as_hoy["fecha"]).dt.strftime("%d-%m-%Y")
            fn = f"asistencia_{hoy.strftime('%d-%m-%Y')}.xlsx"
            as_hoy.to_excel(fn, index=False)
            with open(fn, "rb") as f:
                st.download_button("Descargar Excel del dia", f, fn, use_container_width=True)
        else:
            st.info("No hay registros para hoy")
