import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import pytz
import io
import base64
from PIL import Image
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
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# CSS BÁSICO
# ------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a2a 0%, #1a1a3a 100%);
    }
    .dashboard-compact {
        display: flex;
        gap: 20px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    .dashboard-card {
        flex: 1;
        background: linear-gradient(135deg, #1e1e3a, #2a2a4a);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(0,102,255,0.3);
    }
    .dashboard-card .title {
        font-size: 18px;
        color: #aaa;
        margin-bottom: 10px;
    }
    .dashboard-card .value {
        font-size: 48px;
        font-weight: bold;
        color: #00ffcc;
        margin-bottom: 10px;
    }
    .dashboard-card .percentage {
        font-size: 14px;
        color: #888;
    }
    .progress-bar-bg {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        height: 8px;
        margin-top: 15px;
        overflow: hidden;
    }
    .progress-bar-fill {
        background: #00ffcc;
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s;
    }
    .green-card .value { color: #00ff88; }
    .blue-card .value { color: #00ccff; }
    .orange-card .value { color: #ffaa00; }
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

# ------------------------------------------------------------
# TÍTULO
# ------------------------------------------------------------
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h1 style="color: #00ffcc;">🎓 INGENIERÍA DE SISTEMAS</h1>
    <p style="color: #aaa;">Sistema de Control de Asistencia por QR</p>
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
menu = st.radio("", opciones_menu, horizontal=True, label_visibility="collapsed")
st.session_state.menu_actual = menu

# ------------------------------------------------------------
# FUNCIÓN PARA REGISTRAR ASISTENCIA
# ------------------------------------------------------------
def registrar_asistencia_por_qr(ru_leido):
    # Buscar estudiante
    estudiantes = leer_estudiantes()
    estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_leido]
    
    if len(estudiante) == 0:
        return False, f"❌ Estudiante con RU {ru_leido} no encontrado"
    
    estudiante_data = estudiante.iloc[0]
    nombre_completo = f"{estudiante_data['nombres']} {estudiante_data['apellido_paterno']}"
    
    # Verificar duplicado
    fecha, hora = obtener_fecha_hora_exacta()
    tiene_registro, registro_existente = verificar_registro_duplicado(ru_leido, fecha)
    
    if tiene_registro:
        return False, f"⚠️ {nombre_completo} ya registró hoy a las {registro_existente['hora']}"
    
    # Registrar asistencia
    try:
        supabase.table("asistencia").insert({
            "ru": ru_leido,
            "nombres": estudiante_data["nombres"],
            "apellido_paterno": estudiante_data["apellido_paterno"],
            "apellido_materno": estudiante_data["apellido_materno"],
            "fecha": fecha.isoformat(),
            "hora": hora,
            "estado": "Presente"
        }).execute()
        return True, f"✅ {nombre_completo} registrado a las {hora}"
    except Exception as e:
        return False, f"❌ Error: {e}"

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    
    col1, col2 = st.columns(2)
    with col1:
        ru = st.text_input("🔢 RU (solo números)", placeholder="Ej: 2024001")
        nombres = st.text_input("👤 Nombres", placeholder="Ej: Juan Carlos")
    with col2:
        paterno = st.text_input("👨 Apellido paterno", placeholder="Ej: Pérez")
        materno = st.text_input("👩 Apellido materno", placeholder="Ej: Gómez")
    
    if st.button("💾 Guardar estudiante", use_container_width=True):
        if not ru or not ru.isdigit():
            st.error("❌ RU inválido - debe ser solo números")
        elif not nombres or not paterno:
            st.error("❌ Nombres y apellido paterno son obligatorios")
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
                    st.success(f"✅ Estudiante {nombres} {paterno} registrado")
                    
                    # Mostrar QR
                    qr_img = qrcode.make(ru)
                    buf = io.BytesIO()
                    qr_img.save(buf, format="PNG")
                    st.image(buf, width=300, caption=f"QR para {nombres} {paterno}")
                    
                    # Botón descargar
                    buf.seek(0)
                    st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru}_qr.png", mime="image/png")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de estudiantes")
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        st.dataframe(estudiantes, use_container_width=True)
        
        # Opción para descargar QR individual
        st.markdown("---")
        st.subheader("📱 Descargar QR individual")
        ru_buscar = st.text_input("Ingrese RU para generar su QR")
        if ru_buscar and st.button("Generar QR"):
            estudiante = estudiantes[estudiantes["ru"].astype(str) == ru_buscar]
            if len(estudiante) > 0:
                qr_img = qrcode.make(ru_buscar)
                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                st.image(buf, width=300)
                buf.seek(0)
                st.download_button("⬇️ Descargar QR", data=buf, file_name=f"{ru_buscar}_qr.png", mime="image/png")
            else:
                st.error("❌ RU no encontrado")
        
        # Eliminar estudiante
        st.markdown("---")
        st.subheader("🗑️ Eliminar estudiante")
        ru_eliminar = st.text_input("RU del estudiante a eliminar")
        if ru_eliminar and st.button("Eliminar estudiante"):
            try:
                supabase.table("asistencia").delete().eq("ru", ru_eliminar).execute()
                supabase.table("estudiantes").delete().eq("ru", ru_eliminar).execute()
                st.success("✅ Estudiante eliminado")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.info("📭 No hay estudiantes registrados")

# ------------------------------------------------------------
# ESCANEAR QR - VERSIÓN SIMPLE Y FUNCIONAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear código QR")
    st.markdown("Toma una foto del código QR usando tu cámara")
    
    # Usar camera_input de Streamlit (funciona en móvil)
    foto = st.camera_input("📷 Tomar foto del código QR", label_visibility="collapsed")
    
    if foto is not None:
        # Mostrar preview
        st.image(foto, width=300, caption="Foto tomada")
        
        # Procesar la imagen
        with st.spinner("🔍 Leyendo código QR..."):
            # Convertir a imagen PIL
            image = Image.open(foto)
            
            # Decodificar QR
            decoded_objects = decode(image)
            
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                st.success(f"📱 Código leído: {qr_data}")
                
                # Registrar asistencia
                success, mensaje = registrar_asistencia_por_qr(qr_data)
                if success:
                    st.balloons()
                    st.success(mensaje)
                else:
                    st.error(mensaje)
            else:
                st.error("❌ No se detectó ningún código QR en la imagen")
                st.info("💡 Asegúrate de que el código esté bien enfocado y sea visible")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        password = st.text_input("🔒 Contraseña", type="password")
        if st.button("Ingresar"):
            if password == "pocoyo123":
                st.session_state.manual_auth = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    else:
        st.subheader("✍️ Registrar asistencia manual")
        estudiantes = leer_estudiantes()
        
        if len(estudiantes) > 0:
            estudiantes["nombre_completo"] = estudiantes["nombres"] + " " + estudiantes["apellido_paterno"]
            seleccion = st.selectbox("Seleccionar estudiante", estudiantes["nombre_completo"].tolist())
            
            if seleccion:
                estudiante_data = estudiantes[estudiantes["nombre_completo"] == seleccion].iloc[0]
                ru = estudiante_data["ru"]
                estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                
                fecha, hora = obtener_fecha_hora_exacta()
                tiene_registro, _ = verificar_registro_duplicado(ru, fecha)
                
                if tiene_registro:
                    st.warning("⚠️ Este estudiante ya registró asistencia hoy")
                else:
                    if st.button("✅ Registrar asistencia", use_container_width=True):
                        try:
                            supabase.table("asistencia").insert({
                                "ru": ru,
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
            st.info("📭 No hay estudiantes")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de asistencia")
    
    estudiantes_total = leer_estudiantes()
    total_estudiantes = len(estudiantes_total)
    asistencia_df = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    registrados_hoy = len(asistencia_df[asistencia_df["fecha"] == hoy]) if not asistencia_df.empty else 0
    
    # Dashboard
    st.markdown(f"""
    <div class="dashboard-compact">
        <div class="dashboard-card blue-card">
            <div class="title">👨‍🎓 Total Estudiantes</div>
            <div class="value">{total_estudiantes}</div>
        </div>
        <div class="dashboard-card green-card">
            <div class="title">✅ Registrados Hoy</div>
            <div class="value">{registrados_hoy}</div>
        </div>
        <div class="dashboard-card orange-card">
            <div class="title">❌ Faltantes</div>
            <div class="value">{total_estudiantes - registrados_hoy}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabla de asistencia
    if len(asistencia_df) > 0:
        asistencia_mostrar = asistencia_df.copy()
        asistencia_mostrar['fecha'] = pd.to_datetime(asistencia_mostrar['fecha']).dt.strftime('%d/%m/%Y')
        st.dataframe(asistencia_mostrar.drop(columns=['id']), use_container_width=True)
        
        # Exportar
        if st.button("📥 Exportar a Excel"):
            archivo = f"asistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            asistencia_mostrar.to_excel(archivo, index=False)
            with open(archivo, "rb") as f:
                st.download_button("⬇️ Descargar Excel", data=f, file_name=archivo)
    else:
        st.info("📭 No hay registros de asistencia")
