import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import sqlite3
import hashlib
import streamlit.components.v1 as components

# Importar estilos CSS desde styles.py
try:
    from styles import CSS_STYLES
except:
    CSS_STYLES = """
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .dashboard-compact {
        display: flex;
        gap: 20px;
        margin: 20px 0;
    }
    .dashboard-card {
        flex: 1;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        color: white;
    }
    .green-card { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .blue-card { background: linear-gradient(135deg, #1e3c72, #2a5298); }
    .orange-card { background: linear-gradient(135deg, #f12711, #f5af19); }
    .dashboard-card .title { font-size: 16px; opacity: 0.9; }
    .dashboard-card .value { font-size: 36px; font-weight: bold; margin: 10px 0; }
    .dashboard-card .percentage { font-size: 14px; opacity: 0.8; }
    .progress-bar-bg { background: rgba(255,255,255,0.3); border-radius: 10px; margin-top: 10px; overflow: hidden; }
    .progress-bar-fill { background: white; height: 8px; border-radius: 10px; transition: width 0.3s; }
    </style>
    """

# ------------------------------------------------------------
# CONFIGURACIÓN DE BASE DE DATOS SQLITE LOCAL
# ------------------------------------------------------------
DB_PATH = "sistema_asistencia.db"

def init_database():
    """Inicializa la base de datos SQLite con las tablas necesarias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            ru TEXT PRIMARY KEY,
            nombres TEXT NOT NULL,
            apellido_paterno TEXT NOT NULL,
            apellido_materno TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de asistencia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ru TEXT NOT NULL,
            nombres TEXT NOT NULL,
            apellido_paterno TEXT NOT NULL,
            apellido_materno TEXT NOT NULL,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            estado TEXT DEFAULT 'Presente',
            FOREIGN KEY (ru) REFERENCES estudiantes (ru)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al inicio
init_database()

# ------------------------------------------------------------
# FUNCIONES DE ACCESO A BASE DE DATOS
# ------------------------------------------------------------
def leer_estudiantes():
    """Lee todos los estudiantes de la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT ru, nombres, apellido_paterno, apellido_materno FROM estudiantes ORDER BY ru"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al leer estudiantes: {e}")
        return pd.DataFrame(columns=["ru", "nombres", "apellido_paterno", "apellido_materno"])

def guardar_estudiante(ru, nombres, apellido_paterno, apellido_materno):
    """Guarda un nuevo estudiante en la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO estudiantes (ru, nombres, apellido_paterno, apellido_materno)
            VALUES (?, ?, ?, ?)
        ''', (ru, nombres, apellido_paterno, apellido_materno))
        conn.commit()
        conn.close()
        return True, "Estudiante guardado exitosamente"
    except sqlite3.IntegrityError:
        return False, "El RU ya existe"
    except Exception as e:
        return False, f"Error: {str(e)}"

def actualizar_estudiante(ru_original, nuevo_ru, nombres, apellido_paterno, apellido_materno):
    """Actualiza los datos de un estudiante"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if ru_original != nuevo_ru:
            # Verificar si el nuevo RU ya existe
            cursor.execute("SELECT ru FROM estudiantes WHERE ru = ?", (nuevo_ru,))
            if cursor.fetchone():
                conn.close()
                return False, "El nuevo RU ya existe"
            
            # Actualizar el RU en ambas tablas
            cursor.execute('''
                UPDATE estudiantes 
                SET ru = ?, nombres = ?, apellido_paterno = ?, apellido_materno = ?
                WHERE ru = ?
            ''', (nuevo_ru, nombres, apellido_paterno, apellido_materno, ru_original))
            
            cursor.execute('''
                UPDATE asistencia 
                SET ru = ?, nombres = ?, apellido_paterno = ?, apellido_materno = ?
                WHERE ru = ?
            ''', (nuevo_ru, nombres, apellido_paterno, apellido_materno, ru_original))
        else:
            cursor.execute('''
                UPDATE estudiantes 
                SET nombres = ?, apellido_paterno = ?, apellido_materno = ?
                WHERE ru = ?
            ''', (nombres, apellido_paterno, apellido_materno, ru_original))
        
        conn.commit()
        conn.close()
        return True, "Estudiante actualizado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_estudiante(ru):
    """Elimina un estudiante y todos sus registros de asistencia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM asistencia WHERE ru = ?", (ru,))
        cursor.execute("DELETE FROM estudiantes WHERE ru = ?", (ru,))
        conn.commit()
        conn.close()
        return True, "Estudiante y sus registros eliminados"
    except Exception as e:
        return False, f"Error: {str(e)}"

def leer_asistencia():
    """Lee todos los registros de asistencia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT id, ru, nombres, apellido_paterno, apellido_materno, fecha, hora, estado FROM asistencia ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
        return df
    except Exception as e:
        st.error(f"Error al leer asistencia: {e}")
        return pd.DataFrame(columns=["id", "ru", "nombres", "apellido_paterno", "apellido_materno", "fecha", "hora", "estado"])

def registrar_asistencia(ru, nombres, apellido_paterno, apellido_materno, fecha, hora, estado="Presente"):
    """Registra asistencia de un estudiante"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si ya registró hoy
        cursor.execute('''
            SELECT id, hora, estado FROM asistencia 
            WHERE ru = ? AND fecha = ?
        ''', (ru, fecha.isoformat()))
        
        existe = cursor.fetchone()
        if existe:
            conn.close()
            return False, f"Ya registró hoy a las {existe[1]} (Estado: {existe[2]})"
        
        # Insertar nuevo registro
        cursor.execute('''
            INSERT INTO asistencia (ru, nombres, apellido_paterno, apellido_materno, fecha, hora, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ru, nombres, apellido_paterno, apellido_materno, fecha.isoformat(), hora, estado))
        
        conn.commit()
        conn.close()
        return True, "Asistencia registrada exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def actualizar_estado_asistencia(id_registro, nuevo_estado):
    """Actualiza el estado de un registro de asistencia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE asistencia SET estado = ? WHERE id = ?
        ''', (nuevo_estado, id_registro))
        conn.commit()
        conn.close()
        return True, "Estado actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_registro_asistencia(id_registro):
    """Elimina un registro de asistencia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM asistencia WHERE id = ?", (id_registro,))
        conn.commit()
        conn.close()
        return True, "Registro eliminado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_toda_asistencia():
    """Elimina todos los registros de asistencia"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM asistencia")
        conn.commit()
        conn.close()
        return True, "Todos los registros eliminados"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ------------------------------------------------------------
# FUNCIONES DE UTILIDAD
# ------------------------------------------------------------
def obtener_fecha_hora_exacta():
    ahora = datetime.now()
    fecha = ahora.date()
    hora = ahora.strftime("%H:%M:%S")
    return fecha, hora

def crear_tarjeta_estudiante(estudiante):
    """Crea una tarjeta ejecutiva con QR para el estudiante"""
    ru = str(estudiante["ru"])
    nombres = estudiante["nombres"]
    paterno = estudiante["apellido_paterno"]
    materno = estudiante["apellido_materno"]
    nombre_completo = f"{nombres} {paterno} {materno}".strip().upper()

    qr = qrcode.make(ru, box_size=10, border=2)
    qr_size = 920
    qr = qr.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    card_size = 1000
    background = Image.new('RGB', (card_size, card_size), color=(10, 20, 40))
    
    draw = ImageDraw.Draw(background)
    
    # Usar fuente por defecto (funciona siempre)
    try:
        font_title = ImageFont.truetype("arial.ttf", 88) if os.name == 'nt' else ImageFont.load_default()
        font_ru = ImageFont.truetype("arial.ttf", 50) if os.name == 'nt' else ImageFont.load_default()
        font_name = ImageFont.truetype("arial.ttf", 66) if os.name == 'nt' else ImageFont.load_default()
    except:
        font_title = ImageFont.load_default()
        font_ru = ImageFont.load_default()
        font_name = ImageFont.load_default()

    # Borde
    border_color = (0, 102, 255)
    border_width = 8
    draw.rectangle([0, 0, card_size-1, card_size-1], outline=border_color, width=border_width)

    # Título
    title_x = (card_size - len(nombre_completo) * 30) // 2
    draw.text((title_x, 15), nombre_completo, fill=(255,255,255), font=font_title)

    # RU
    ru_text = f"RU: {ru}"
    ru_x = (card_size - len(ru_text) * 20) // 2
    draw.text((ru_x, 120), ru_text, fill=(255,255,200), font=font_ru)

    # QR
    qr_x = (card_size - qr_size) // 2
    qr_y = 200
    background.paste(qr, (qr_x, qr_y))

    img_bytes = io.BytesIO()
    background.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Sistema de Asistencia con QR", layout="wide", initial_sidebar_state="expanded")

# Aplicar estilos CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ------------------------------------------------------------
# INICIALIZAR SESSION STATE
# ------------------------------------------------------------
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "📝 Registrar estudiante"
if "manual_auth" not in st.session_state:
    st.session_state.manual_auth = False
if "mensaje_qr" not in st.session_state:
    st.session_state.mensaje_qr = None
if "ultimo_qr_procesado" not in st.session_state:
    st.session_state.ultimo_qr_procesado = None

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📂 Sistema de Asistencia QR")
    st.markdown("### Desarrollado por Josué")
    st.markdown("---")
    st.markdown(f"**Base de datos:** SQLite Local")
    st.markdown(f"**Archivo:** `{DB_PATH}`")
    
    # Mostrar estadísticas rápidas
    estudiantes_count = len(leer_estudiantes())
    asistencia_count = len(leer_asistencia())
    st.markdown("---")
    st.metric("📚 Total Estudiantes", estudiantes_count)
    st.metric("📋 Total Asistencias", asistencia_count)

# ------------------------------------------------------------
# TÍTULO PRINCIPAL
# ------------------------------------------------------------
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>🎓 INGENIERÍA DE SISTEMAS</h1>
    <p style="font-size: 18px; color: #666;">Lógica, Programación e Inteligencia; ¡Sistemas Somos Excelencia!</p>
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

st.markdown("---")

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------
if st.session_state.menu_actual == "📝 Registrar estudiante":
    st.subheader("📝 Registrar nuevo estudiante")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ru = st.text_input("🔢 RU (Código Único)", placeholder="Ej: 20240001")
        nombres = st.text_input("👤 Nombres", placeholder="Ej: Juan Carlos")
    
    with col2:
        apellido_paterno = st.text_input("👨 Apellido Paterno", placeholder="Ej: Pérez")
        apellido_materno = st.text_input("👩 Apellido Materno", placeholder="Ej: González")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("💾 Guardar Estudiante", use_container_width=True, type="primary"):
            if not ru:
                st.error("❌ El RU es obligatorio")
            elif not ru.isdigit():
                st.error("❌ El RU debe contener solo números")
            elif not nombres:
                st.error("❌ Los nombres son obligatorios")
            elif not apellido_paterno:
                st.error("❌ El apellido paterno es obligatorio")
            else:
                exito, mensaje = guardar_estudiante(ru, nombres, apellido_paterno, apellido_materno)
                if exito:
                    st.success(f"✅ {mensaje}")
                    
                    # Mostrar QR generado
                    qr_img = qrcode.make(ru)
                    img_bytes = io.BytesIO()
                    qr_img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    st.markdown("---")
                    st.subheader("📱 Código QR del Estudiante")
                    col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                    with col_qr2:
                        st.image(img_bytes, width=300)
                        st.download_button(
                            label="⬇️ Descargar QR",
                            data=img_bytes.getvalue(),
                            file_name=f"{ru}_qr.png",
                            mime="image/png",
                            use_container_width=True
                        )
                else:
                    st.error(f"❌ {mensaje}")

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📋 Lista estudiantes":
    st.subheader("📋 Lista de Estudiantes")
    
    estudiantes = leer_estudiantes()
    
    if len(estudiantes) > 0:
        # Mostrar tabla
        st.dataframe(estudiantes, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("✏️ Gestionar Estudiante")
        
        # Selector de estudiante
        estudiantes['display'] = estudiantes['ru'] + " - " + estudiantes['nombres'] + " " + estudiantes['apellido_paterno']
        estudiante_seleccionado = st.selectbox("Seleccionar estudiante", estudiantes['display'].tolist())
        
        if estudiante_seleccionado:
            ru_seleccionado = estudiante_seleccionado.split(" - ")[0]
            estudiante_data = estudiantes[estudiantes['ru'] == ru_seleccionado].iloc[0]
            
            with st.form("form_editar_estudiante"):
                nuevo_ru = st.text_input("RU", value=estudiante_data['ru'])
                nuevos_nombres = st.text_input("Nombres", value=estudiante_data['nombres'])
                nuevo_paterno = st.text_input("Apellido Paterno", value=estudiante_data['apellido_paterno'])
                nuevo_materno = st.text_input("Apellido Materno", value=estudiante_data['apellido_materno'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
                with col2:
                    eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
            
            if actualizar:
                exito, mensaje = actualizar_estudiante(ru_seleccionado, nuevo_ru, nuevos_nombres, nuevo_paterno, nuevo_materno)
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")
            
            if eliminar:
                if st.button("⚠️ Confirmar eliminación", key="confirm_eliminar"):
                    exito, mensaje = eliminar_estudiante(ru_seleccionado)
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.rerun()
                    else:
                        st.error(f"❌ {mensaje}")
        
        st.markdown("---")
        st.subheader("⬇️ Exportar Datos")
        
        # Exportar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            estudiantes.to_excel(writer, index=False, sheet_name='Estudiantes')
        output.seek(0)
        
        st.download_button(
            label="📥 Descargar Excel con todos los estudiantes",
            data=output,
            file_name="estudiantes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("📭 No hay estudiantes registrados. Ve a 'Registrar estudiante' para agregar.")

# ------------------------------------------------------------
# ESCANEAR QR - VERSIÓN FUNCIONAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📸 Escanear QR":
    st.subheader("📸 Escanear Código QR")
    
    # Mostrar mensaje si existe
    if st.session_state.mensaje_qr:
        if "✅" in st.session_state.mensaje_qr:
            st.success(st.session_state.mensaje_qr)
        elif "⚠️" in st.session_state.mensaje_qr:
            st.warning(st.session_state.mensaje_qr)
        elif "❌" in st.session_state.mensaje_qr:
            st.error(st.session_state.mensaje_qr)
        
        if st.button("🔄 Limpiar y Escanear Otro", use_container_width=True):
            st.session_state.mensaje_qr = None
            st.session_state.ultimo_qr_procesado = None
            st.rerun()
        st.markdown("---")
    
    # Procesar QR detectado
    params = st.query_params
    qr_value = params.get("qr", None)
    
    if qr_value and qr_value != st.session_state.ultimo_qr_procesado:
        st.session_state.ultimo_qr_procesado = qr_value
        
        # Buscar estudiante
        estudiantes = leer_estudiantes()
        estudiante = estudiantes[estudiantes['ru'].astype(str) == qr_value]
        
        if len(estudiante) > 0:
            datos = estudiante.iloc[0]
            fecha, hora = obtener_fecha_hora_exacta()
            
            # Registrar asistencia
            exito, mensaje = registrar_asistencia(
                str(datos['ru']),
                datos['nombres'],
                datos['apellido_paterno'],
                datos['apellido_materno'],
                fecha,
                hora,
                "Presente"
            )
            
            if exito:
                st.session_state.mensaje_qr = f"✅ ¡ASISTENCIA REGISTRADA!\n\n👤 {datos['nombres']} {datos['apellido_paterno']}\n🕐 Hora: {hora}\n📅 Fecha: {fecha.strftime('%d/%m/%Y')}"
                st.balloons()
            else:
                st.session_state.mensaje_qr = f"⚠️ {mensaje}"
        else:
            st.session_state.mensaje_qr = f"❌ RU {qr_value} no encontrado en la base de datos"
        
        # Limpiar query params
        st.query_params.clear()
        st.rerun()
    
    # Componente del escáner
    scanner_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: 'Segoe UI', sans-serif;
            }
            .container {
                text-align: center;
                width: 100%;
                max-width: 500px;
            }
            #reader {
                width: 100%;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            .status {
                margin-top: 20px;
                padding: 12px;
                background: rgba(0,0,0,0.7);
                border-radius: 8px;
                color: #00ffcc;
                font-size: 14px;
                backdrop-filter: blur(10px);
            }
            .instruction {
                margin-top: 15px;
                color: #666;
                font-size: 12px;
            }
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
            let html5QrCode = null;
            let scanning = true;
            
            function onScanSuccess(decodedText, decodedResult) {
                if (!scanning) return;
                
                if (html5QrCode && html5QrCode.isScanning) {
                    html5QrCode.stop();
                    scanning = false;
                }
                
                document.getElementById('status').innerHTML = '✅ QR detectado: ' + decodedText + '<br>📝 Procesando...';
                
                const url = new URL(window.location.href);
                url.searchParams.set('qr', decodedText);
                window.location.href = url.toString();
            }
            
            function onScanError(errorMessage) {
                // Silenciar errores normales
            }
            
            const config = {
                fps: 20,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            };
            
            html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start(
                { facingMode: "environment" },
                config,
                onScanSuccess,
                onScanError
            ).then(() => {
                document.getElementById('status').innerHTML = '✅ Cámara lista - Escaneando...';
            }).catch(err => {
                document.getElementById('status').innerHTML = '❌ No se pudo acceder a la cámara';
            });
            
            window.addEventListener('beforeunload', function() {
                if (html5QrCode && html5QrCode.isScanning) {
                    html5QrCode.stop().catch(e => console.log(e));
                }
            });
        </script>
    </body>
    </html>
    """
    
    components.html(scanner_html, height=500)

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------
elif st.session_state.menu_actual == "✍️ Registrar asistencia manual":
    if not st.session_state.manual_auth:
        st.subheader("🔒 Acceso Restringido")
        password = st.text_input("Contraseña", type="password", placeholder="Ingrese la contraseña")
        
        if st.button("🔓 Ingresar", use_container_width=True):
            if password == "pocoyo123":
                st.session_state.manual_auth = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    else:
        st.subheader("✍️ Registrar Asistencia Manual")
        
        estudiantes = leer_estudiantes()
        
        if len(estudiantes) > 0:
            estudiantes['display'] = estudiantes['ru'] + " - " + estudiantes['nombres'] + " " + estudiantes['apellido_paterno']
            seleccion = st.selectbox("👤 Seleccionar Estudiante", estudiantes['display'].tolist())
            
            if seleccion:
                ru = seleccion.split(" - ")[0]
                estudiante = estudiantes[estudiantes['ru'] == ru].iloc[0]
                
                estado = st.selectbox("📌 Estado", ["Presente", "Tarde", "Permiso", "Ausente"])
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("✅ Registrar Asistencia", use_container_width=True, type="primary"):
                        fecha, hora = obtener_fecha_hora_exacta()
                        exito, mensaje = registrar_asistencia(
                            str(estudiante['ru']),
                            estudiante['nombres'],
                            estudiante['apellido_paterno'],
                            estudiante['apellido_materno'],
                            fecha,
                            hora,
                            estado
                        )
                        
                        if exito:
                            st.success(f"✅ {mensaje} a las {hora}")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
        else:
            st.warning("⚠️ No hay estudiantes registrados")

# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------
elif st.session_state.menu_actual == "📊 Ver asistencia":
    st.subheader("📊 Registros de Asistencia")
    
    # Estadísticas
    estudiantes = leer_estudiantes()
    asistencia = leer_asistencia()
    hoy = datetime.now().date()
    
    total_estudiantes = len(estudiantes)
    registrados_hoy = len(asistencia[asistencia['fecha'] == hoy]) if not asistencia.empty else 0
    faltantes = total_estudiantes - registrados_hoy
    
    # Dashboard
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Total Estudiantes", total_estudiantes, delta=None)
    with col2:
        porcentaje = (registrados_hoy / total_estudiantes * 100) if total_estudiantes > 0 else 0
        st.metric("✅ Registrados Hoy", registrados_hoy, delta=f"{porcentaje:.0f}%")
    with col3:
        st.metric("❌ Faltantes", faltantes, delta=None)
    
    st.markdown("---")
    
    # Mostrar tabla de asistencia
    if not asistencia.empty:
        asistencia_mostrar = asistencia.copy()
        asistencia_mostrar['fecha'] = pd.to_datetime(asistencia_mostrar['fecha']).dt.strftime('%d/%m/%Y')
        asistencia_mostrar = asistencia_mostrar.drop(columns=['id'])
        st.dataframe(asistencia_mostrar, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("⚙️ Gestionar Asistencia")
        
        # Editar estado
        if not asistencia.empty:
            asistencia['display'] = asistencia['ru'] + " - " + asistencia['nombres'] + " " + asistencia['apellido_paterno'] + " (" + asistencia['fecha'].astype(str) + ")"
            registro_seleccionado = st.selectbox("Seleccionar registro", asistencia['display'].tolist())
            
            if registro_seleccionado:
                idx = asistencia[asistencia['display'] == registro_seleccionado].index[0]
                id_registro = asistencia.loc[idx, 'id']
                estado_actual = asistencia.loc[idx, 'estado']
                
                nuevo_estado = st.selectbox("Nuevo estado", ["Presente", "Tarde", "Permiso", "Ausente"], 
                                           index=["Presente","Tarde","Permiso","Ausente"].index(estado_actual))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Actualizar Estado", use_container_width=True):
                        exito, mensaje = actualizar_estado_asistencia(id_registro, nuevo_estado)
                        if exito:
                            st.success(f"✅ {mensaje}")
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
                
                with col2:
                    if st.button("🗑️ Eliminar Registro", use_container_width=True):
                        exito, mensaje = eliminar_registro_asistencia(id_registro)
                        if exito:
                            st.success(f"✅ {mensaje}")
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
        
        st.markdown("---")
        
        # Eliminar todos
        if st.button("⚠️ Eliminar TODOS los registros de asistencia", use_container_width=True):
            if st.button("✅ Confirmar eliminación total", key="confirm_total"):
                exito, mensaje = eliminar_toda_asistencia()
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")
        
        st.markdown("---")
        st.subheader("⬇️ Exportar Asistencia")
        
        # Exportar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            asistencia_export = asistencia.copy()
            asistencia_export['fecha'] = pd.to_datetime(asistencia_export['fecha']).dt.strftime('%d/%m/%Y')
            asistencia_export.drop(columns=['id'], inplace=True)
            asistencia_export.to_excel(writer, index=False, sheet_name='Asistencia')
        output.seek(0)
        
        st.download_button(
            label="📥 Descargar Excel con todas las asistencias",
            data=output,
            file_name=f"asistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("📭 No hay registros de asistencia todavía")

# ------------------------------------------------------------
# PIE DE PÁGINA
# ------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 12px;'>"
    "Sistema de Asistencia con QR | Desarrollado con Python y Streamlit"
    "</div>",
    unsafe_allow_html=True
)
