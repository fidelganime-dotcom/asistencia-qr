import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from supabase import create_client, Client
import streamlit.components.v1 as components
import time

# ------------------------------------------------------------
# CONFIGURACIÓN DE SUPABASE (TU BD)
# ------------------------------------------------------------
SUPABASE_URL = "https://rwmxhbojhbscrktswmhg.supabase.co"
SUPABASE_KEY = "sb_publishable_Ukse6FwyRq-Qg1FW8zDbLA_QqLmtUTm"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    st.sidebar.success("✅ Conexión a Supabase exitosa")
except Exception as e:
    st.error(f"❌ Error al conectar con Supabase: {e}")
    st.stop()

# ------------------------------------------------------------
# CONFIGURACIÓN DE ZONA HORARIA
# ------------------------------------------------------------
from pytz import timezone
ZONA_HORARIA = timezone('America/La_Paz')

def obtener_fecha_hora_exacta():
    ahora = datetime.now(ZONA_HORARIA)
    return ahora.date(), ahora.strftime("%H:%M:%S")

# ------------------------------------------------------------
# FUNCIONES CRUD CON SUPABASE
# ------------------------------------------------------------
def leer_estudiantes():
    try:
        response = supabase.table("estudiantes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame(columns=["ru", "nombres", "apellido_paterno", "apellido_materno"])
    except Exception as e:
        st.error(f"Error al leer estudiantes: {e}")
        return pd.DataFrame()

def registrar_asistencia(ru, nombres, paterno, materno, fecha, hora, estado="Presente"):
    """Registra asistencia en Supabase"""
    try:
        # Verificar si ya registró hoy
        response = supabase.table("asistencia").select("*").eq("ru", ru).eq("fecha", fecha.isoformat()).execute()
        
        if response.data:
            return False, f"Ya registró hoy a las {response.data[0]['hora']}"
        
        # Insertar nuevo registro
        data = {
            "ru": str(ru),
            "nombres": nombres,
            "apellido_paterno": paterno,
            "apellido_materno": materno,
            "fecha": fecha.isoformat(),
            "hora": hora,
            "estado": estado
        }
        
        result = supabase.table("asistencia").insert(data).execute()
        
        if result.data:
            return True, "Asistencia registrada exitosamente"
        return False, "Error al insertar"
    except Exception as e:
        return False, f"Error: {str(e)}"

def leer_asistencia():
    try:
        response = supabase.table("asistencia").select("*").order("id", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha']).dt.date
            return df
        return pd.DataFrame(columns=["id", "ru", "nombres", "apellido_paterno", "apellido_materno", "fecha", "hora", "estado"])
    except Exception as e:
        st.error(f"Error al leer asistencia: {e}")
        return pd.DataFrame()

def guardar_estudiante(ru, nombres, paterno, materno):
    try:
        supabase.table("estudiantes").insert({
            "ru": ru, "nombres": nombres, "apellido_paterno": paterno, "apellido_materno": materno
        }).execute()
        return True, "Estudiante registrado"
    except Exception as e:
        return False, str(e)

def eliminar_estudiante(ru):
    try:
        supabase.table("asistencia").delete().eq("ru", ru).execute()
        supabase.table("estudiantes").delete().eq("ru", ru).execute()
        return True, "Eliminado"
    except Exception as e:
        return False, str(e)

def actualizar_estudiante(ru_original, nuevo_ru, nombres, paterno, materno):
    try:
        if ru_original != nuevo_ru:
            supabase.table("asistencia").update({"ru": nuevo_ru}).eq("ru", ru_original).execute()
            supabase.table("estudiantes").delete().eq("ru", ru_original).execute()
            supabase.table("estudiantes").insert({
                "ru": nuevo_ru, "nombres": nombres, "apellido_paterno": paterno, "apellido_materno": materno
            }).execute()
        else:
            supabase.table("estudiantes").update({
                "nombres": nombres, "apellido_paterno": paterno, "apellido_materno": materno
            }).eq("ru", ru_original).execute()
        return True, "Actualizado"
    except Exception as e:
        return False, str(e)

def actualizar_estado_asistencia(id_registro, nuevo_estado):
    try:
        supabase.table("asistencia").update({"estado": nuevo_estado}).eq("id", id_registro).execute()
        return True, "Estado actualizado"
    except Exception as e:
        return False, str(e)

def eliminar_registro_asistencia(id_registro):
    try:
        supabase.table("asistencia").delete().eq("id", id_registro).execute()
        return True, "Registro eliminado"
    except Exception as e:
        return False, str(e)

def eliminar_toda_asistencia():
    try:
        supabase.table("asistencia").delete().neq("id", 0).execute()
        return True, "Todos los registros eliminados"
    except Exception as e:
        return False, str(e)

# ------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia QR", layout="wide")

# Estilos CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .dashboard-card {
        background: white; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;
    }
    .dashboard-card .value { font-size: 36px; font-weight: bold; color: #333; }
    .dashboard-card .label { color: #666; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if "manual_auth" not in st.session_state:
    st.session_state.manual_auth = False
if "mensaje_qr" not in st.session_state:
    st.session_state.mensaje_qr = None
if "ultimo_qr" not in st.session_state:
    st.session_state.ultimo_qr = None

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/qr-code.png", width=80)
    st.markdown("## 📱 Sistema QR")
    st.markdown("---")
    estudiantes_count = len(leer_estudiantes())
    st.metric("📚 Estudiantes", estudiantes_count)

# Título
st.title("🎓 INGENIERÍA DE SISTEMAS")
st.caption("Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!")

# Menú
menu = st.radio(
    "",
    ["📝 Registrar", "📋 Estudiantes", "📸 Escanear QR", "✍️ Manual", "📊 Asistencia"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ------------------------------------------------------------
# 1. REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if menu == "📝 Registrar":
    st.subheader("📝 Registrar Estudiante")
    
    col1, col2 = st.columns(2)
    with col1:
        ru = st.text_input("🔢 RU (solo números)")
        nombres = st.text_input("👤 Nombres")
    with col2:
        paterno = st.text_input("👨 Apellido Paterno")
        materno = st.text_input("👩 Apellido Materno")
    
    if st.button("💾 Guardar", type="primary", use_container_width=True):
        if not ru or not ru.isdigit():
            st.error("❌ RU válido requerido")
        elif not nombres or not paterno:
            st.error("❌ Nombres y apellido paterno requeridos")
        else:
            exito, msg = guardar_estudiante(ru, nombres, paterno, materno)
            if exito:
                st.success(f"✅ {msg}")
                # Mostrar QR
                qr = qrcode.make(ru)
                buf = io.BytesIO()
                qr.save(buf, format='PNG')
                buf.seek(0)
                
                col_qr1, col_qr2, col_qr3 = st.columns([1,2,1])
                with col_qr2:
                    st.image(buf, width=300)
                    st.download_button("⬇️ Descargar QR", buf, f"{ru}_qr.png", use_container_width=True)
            else:
                st.error(f"❌ {msg}")

# ------------------------------------------------------------
# 2. LISTA ESTUDIANTES
# ------------------------------------------------------------
elif menu == "📋 Estudiantes":
    st.subheader("📋 Lista de Estudiantes")
    
    df = leer_estudiantes()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("✏️ Gestionar")
        
        df['display'] = df['ru'] + " - " + df['nombres'] + " " + df['apellido_paterno']
        seleccion = st.selectbox("Seleccionar", df['display'].tolist())
        
        if seleccion:
            ru_sel = seleccion.split(" - ")[0]
            est = df[df['ru'] == ru_sel].iloc[0]
            
            with st.form("edit_form"):
                nuevo_ru = st.text_input("RU", value=est['ru'])
                nom = st.text_input("Nombres", value=est['nombres'])
                pat = st.text_input("Apellido Paterno", value=est['apellido_paterno'])
                mat = st.text_input("Apellido Materno", value=est['apellido_materno'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("🔄 Actualizar", use_container_width=True):
                        exito, msg = actualizar_estudiante(ru_sel, nuevo_ru, nom, pat, mat)
                        st.success(msg) if exito else st.error(msg)
                        if exito:
                            st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Eliminar", use_container_width=True):
                        exito, msg = eliminar_estudiante(ru_sel)
                        st.success(msg) if exito else st.error(msg)
                        if exito:
                            st.rerun()
    else:
        st.info("📭 No hay estudiantes")

# ------------------------------------------------------------
# 3. ESCANEAR QR - FUNCIONAL CON SUPABASE
# ------------------------------------------------------------
elif menu == "📸 Escanear QR":
    st.subheader("📸 Escanear Código QR")
    
    # Mostrar mensaje
    if st.session_state.mensaje_qr:
        if "✅" in st.session_state.mensaje_qr:
            st.success(st.session_state.mensaje_qr)
        elif "⚠️" in st.session_state.mensaje_qr:
            st.warning(st.session_state.mensaje_qr)
        else:
            st.error(st.session_state.mensaje_qr)
        
        if st.button("🔄 Escanear otro", use_container_width=True):
            st.session_state.mensaje_qr = None
            st.session_state.ultimo_qr = None
            st.rerun()
        st.divider()
    
    # Procesar QR detectado
    query_params = st.query_params
    qr_value = query_params.get("qr", None)
    
    if qr_value and qr_value != st.session_state.ultimo_qr:
        st.session_state.ultimo_qr = qr_value
        
        # Buscar estudiante
        estudiantes_df = leer_estudiantes()
        estudiante = estudiantes_df[estudiantes_df['ru'].astype(str) == qr_value]
        
        if not estudiante.empty:
            datos = estudiante.iloc[0]
            fecha, hora = obtener_fecha_hora_exacta()
            
            exito, mensaje = registrar_asistencia(
                str(datos['ru']),
                datos['nombres'],
                datos['apellido_paterno'],
                datos['apellido_materno'],
                fecha,
                hora
            )
            
            if exito:
                st.session_state.mensaje_qr = f"✅ ¡ASISTENCIA REGISTRADA!\n\n👤 {datos['nombres']} {datos['apellido_paterno']}\n🕐 {hora} | 📅 {fecha.strftime('%d/%m/%Y')}"
                st.balloons()
            else:
                st.session_state.mensaje_qr = f"⚠️ {mensaje}"
        else:
            st.session_state.mensaje_qr = f"❌ RU {qr_value} no encontrado"
        
        # Limpiar y recargar
        st.query_params.clear()
        st.rerun()
    
    # Escáner HTML
    scanner_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            body { background: transparent; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .container { text-align: center; width: 100%; max-width: 500px; }
            #reader { width: 100%; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
            .status { margin-top: 20px; padding: 12px; background: rgba(0,0,0,0.7); border-radius: 8px; color: #00ffcc; font-size: 14px; }
            .instruction { margin-top: 15px; color: #666; font-size: 12px; }
        </style>
        <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    </head>
    <body>
        <div class="container">
            <div id="reader"></div>
            <div class="status" id="status">🔍 Iniciando cámara...</div>
            <div class="instruction">📱 Coloca el código QR frente a la cámara</div>
        </div>
        <script>
            let scanner = null;
            let scanning = true;
            
            function onSuccess(text) {
                if (!scanning) return;
                if (scanner && scanner.isScanning) {
                    scanner.stop();
                    scanning = false;
                }
                document.getElementById('status').innerHTML = '✅ Detectado: ' + text + '<br>📝 Registrando...';
                const url = new URL(window.location.href);
                url.searchParams.set('qr', text);
                window.location.href = url.toString();
            }
            
            function onError(err) {}
            
            const config = { fps: 20, qrbox: { width: 250, height: 250 }, aspectRatio: 1.0 };
            
            scanner = new Html5Qrcode("reader");
            scanner.start({ facingMode: "environment" }, config, onSuccess, onError)
                .then(() => document.getElementById('status').innerHTML = '✅ Cámara lista - Escaneando...')
                .catch(() => document.getElementById('status').innerHTML = '❌ Error al acceder a la cámara');
            
            window.addEventListener('beforeunload', () => {
                if (scanner && scanner.isScanning) scanner.stop().catch(e => console.log(e));
            });
        </script>
    </body>
    </html>
    """
    
    components.html(scanner_html, height=500)

# ------------------------------------------------------------
# 4. REGISTRO MANUAL
# ------------------------------------------------------------
elif menu == "✍️ Manual":
    if not st.session_state.manual_auth:
        st.subheader("🔒 Acceso Restringido")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if pwd == "pocoyo123":
                st.session_state.manual_auth = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
        st.subheader("✍️ Registrar Asistencia Manual")
        
        df = leer_estudiantes()
        if not df.empty:
            df['display'] = df['ru'] + " - " + df['nombres'] + " " + df['apellido_paterno']
            seleccion = st.selectbox("Estudiante", df['display'].tolist())
            
            if seleccion:
                ru_sel = seleccion.split(" - ")[0]
                est = df[df['ru'] == ru_sel].iloc[0]
                estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                
                if st.button("✅ Registrar", type="primary"):
                    fecha, hora = obtener_fecha_hora_exacta()
                    exito, msg = registrar_asistencia(
                        str(est['ru']), est['nombres'], est['apellido_paterno'], 
                        est['apellido_materno'], fecha, hora, estado
                    )
                    if exito:
                        st.success(f"✅ {msg} a las {hora}")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        else:
            st.warning("No hay estudiantes")

# ------------------------------------------------------------
# 5. VER ASISTENCIA
# ------------------------------------------------------------
elif menu == "📊 Asistencia":
    st.subheader("📊 Registros de Asistencia")
    
    # Estadísticas
    estudiantes = leer_estudiantes()
    asistencia = leer_asistencia()
    hoy = datetime.now(ZONA_HORARIA).date()
    
    total_est = len(estudiantes)
    registrados = len(asistencia[asistencia['fecha'] == hoy]) if not asistencia.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📚 Total Estudiantes", total_est)
    col2.metric("✅ Registrados Hoy", registrados)
    col3.metric("❌ Faltantes", total_est - registrados)
    
    st.divider()
    
    if not asistencia.empty:
        # Mostrar tabla
        mostrar = asistencia.copy()
        mostrar['fecha'] = pd.to_datetime(mostrar['fecha']).dt.strftime('%d/%m/%Y')
        mostrar = mostrar.drop(columns=['id'])
        st.dataframe(mostrar, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("⚙️ Gestionar")
        
        # Editar estado
        asistencia['display'] = asistencia['ru'] + " - " + asistencia['nombres'] + " " + asistencia['apellido_paterno'] + " (" + asistencia['fecha'].astype(str) + ")"
        seleccion = st.selectbox("Seleccionar registro", asistencia['display'].tolist())
        
        if seleccion:
            idx = asistencia[asistencia['display'] == seleccion].index[0]
            id_reg = asistencia.loc[idx, 'id']
            estado_actual = asistencia.loc[idx, 'estado']
            
            nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"], 
                                       index=["Presente","Tarde","Permiso","Ausente"].index(estado_actual))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Actualizar", use_container_width=True):
                    exito, msg = actualizar_estado_asistencia(id_reg, nuevo_estado)
                    st.success(msg) if exito else st.error(msg)
                    if exito:
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Eliminar", use_container_width=True):
                    exito, msg = eliminar_registro_asistencia(id_reg)
                    st.success(msg) if exito else st.error(msg)
                    if exito:
                        st.rerun()
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚠️ Eliminar TODOS", use_container_width=True):
                exito, msg = eliminar_toda_asistencia()
                st.success(msg) if exito else st.error(msg)
                if exito:
                    st.rerun()
        
        with col2:
            # Exportar
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                export_df = asistencia.drop(columns=['id'])
                export_df['fecha'] = pd.to_datetime(export_df['fecha']).dt.strftime('%d/%m/%Y')
                export_df.to_excel(writer, index=False)
            output.seek(0)
            st.download_button("📥 Exportar Excel", output, f"asistencia_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
    else:
        st.info("📭 No hay registros de asistencia")
