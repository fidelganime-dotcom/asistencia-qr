import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import base64
from streamlit_option_menu import option_menu
import plotly.express as px
import time

# CONFIGURACION DE PAGINA
st.set_page_config(
    page_title="⚡ QR Asistencia Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILOS CSS PERSONALIZADOS - TEMA AZUL MARINO CON LINEAS ELECTRICAS
st.markdown("""
<style>
    /* Estilos globales */
    .stApp {
        background: linear-gradient(135deg, #0a1929 0%, #0f2744 50%, #1a3a5c 100%);
        color: #ffffff;
    }
    
    /* Animación de líneas eléctricas */
    @keyframes electricPulse {
        0% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.02); }
        100% { opacity: 0.3; transform: scale(1); }
    }
    
    @keyframes lightning {
        0% { clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }
        10% { clip-path: polygon(5% 0%, 95% 0%, 100% 100%, 0% 100%); }
        20% { clip-path: polygon(0% 0%, 100% 0%, 95% 100%, 5% 100%); }
        30% { clip-path: polygon(2% 0%, 98% 0%, 100% 100%, 0% 100%); }
        40% { clip-path: polygon(0% 0%, 100% 0%, 98% 100%, 2% 100%); }
        50% { clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }
        100% { clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }
    }
    
    /* Efecto de líneas eléctricas en el fondo */
    .electric-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        background: 
            repeating-linear-gradient(
                45deg,
                transparent,
                transparent 20px,
                rgba(0, 191, 255, 0.03) 20px,
                rgba(0, 191, 255, 0.03) 40px
            ),
            repeating-linear-gradient(
                -45deg,
                transparent,
                transparent 20px,
                rgba(100, 149, 237, 0.03) 20px,
                rgba(100, 149, 237, 0.03) 40px
            );
    }
    
    /* Cabeceras */
    h1, h2, h3 {
        color: #00ffff !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        border-bottom: 2px solid #00ffff;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Tarjetas con efecto neón */
    .electric-card {
        background: linear-gradient(145deg, #132f4c, #0a1f33);
        border: 1px solid #00ffff;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        animation: electricPulse 3s infinite;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .electric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
    }
    
    /* Botones con efecto eléctrico */
    .stButton > button {
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 20px #00ffff !important;
    }
    
    .stButton > button::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent
        );
        transform: rotate(45deg);
        animation: lightning 3s infinite;
    }
    
    /* Inputs con estilo futurista */
    .stTextInput > div > div > input {
        background: rgba(10, 25, 41, 0.8) !important;
        border: 2px solid #00b4db !important;
        border-radius: 10px !important;
        color: white !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00ffff !important;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.3) !important;
    }
    
    /* Selectbox personalizado */
    .stSelectbox > div > div {
        background: rgba(10, 25, 41, 0.8) !important;
        border: 2px solid #00b4db !important;
        border-radius: 10px !important;
        color: white !important;
    }
    
    /* DataFrames con estilo */
    .dataframe {
        background: rgba(10, 25, 41, 0.9) !important;
        border: 1px solid #00ffff !important;
        border-radius: 15px !important;
        padding: 10px !important;
    }
    
    .dataframe th {
        background: #00b4db !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    .dataframe td {
        color: white !important;
        border-bottom: 1px solid #00b4db !important;
    }
    
    /* Mensajes de éxito con animación */
    .stAlert {
        background: linear-gradient(45deg, #00b4db, #0083b0) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        animation: electricPulse 2s infinite !important;
    }
    
    /* Sidebar personalizado */
    .css-1d391kg {
        background: linear-gradient(180deg, #0a1929 0%, #0f2744 100%) !important;
        border-right: 2px solid #00ffff !important;
    }
    
    /* Cards para estadísticas */
    .stat-card {
        background: linear-gradient(145deg, #132f4c, #0a1f33);
        border: 1px solid #00ffff;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
    }
    
    .stat-number {
        font-size: 36px;
        font-weight: bold;
        color: #00ffff;
        text-shadow: 0 0 20px #00ffff;
    }
    
    .stat-label {
        font-size: 16px;
        color: #ffffff;
        margin-top: 10px;
    }
    
    /* Cámara con efecto neón */
    div[data-testid="stCameraInput"] {
        border: 3px solid #00ffff !important;
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.3) !important;
    }
    
    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        height: 75vh !important;
        object-fit: cover !important;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a1929;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00b4db;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00ffff;
    }
    
    /* Loader personalizado */
    .loader {
        border: 5px solid #132f4c;
        border-top: 5px solid #00ffff;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>

<div class="electric-bg"></div>
""", unsafe_allow_html=True)

# Fondo eléctrico animado
st.markdown('<div class="electric-bg"></div>', unsafe_allow_html=True)

# TITULO CON EFECTO
st.markdown("""
<div style="text-align: center; padding: 20px; animation: electricPulse 3s infinite;">
    <h1 style="font-size: 48px; margin-bottom: 0;">
        ⚡ SISTEMA DE ASISTENCIA QR ⚡
    </h1>
    <p style="color: #00ffff; font-size: 18px; letter-spacing: 2px;">
        TECNOLOGÍA DE PUNTA PARA CONTROL DE ASISTENCIA
    </p>
</div>
""", unsafe_allow_html=True)

# ARCHIVOS
archivo_estudiantes = "estudiantes.xlsx"
archivo_asistencia = "asistencia.xlsx"

# CREAR ARCHIVOS
if not os.path.exists(archivo_estudiantes):
    df = pd.DataFrame(columns=[
        "RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"
    ])
    df.to_excel(archivo_estudiantes, index=False)

if not os.path.exists(archivo_asistencia):
    df = pd.DataFrame(columns=[
        "RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"
    ])
    df.to_excel(archivo_asistencia, index=False)

# MENU LATERAL MODERNO
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: #00ffff; border: none;">⚡ MENÚ ⚡</h2>
    </div>
    """, unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=[
            "Registrar estudiante",
            "Lista estudiantes",
            "Escanear QR",
            "Registrar asistencia manual",
            "Ver asistencia",
            "Dashboard"
        ],
        icons=[
            'person-plus-fill',
            'people-fill',
            'camera-fill',
            'pencil-fill',
            'calendar-check-fill',
            'graph-up'
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#0a1929"},
            "icon": {"color": "#00ffff", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "--hover-color": "#132f4c",
                "color": "#ffffff"
            },
            "nav-link-selected": {
                "background-color": "#00b4db",
                "color": "white",
                "font-weight": "bold"
            },
        }
    )

# FUNCION PARA CARGAR DATOS CON CACHE
@st.cache_data
def cargar_estudiantes():
    return pd.read_excel(archivo_estudiantes)

@st.cache_data
def cargar_asistencia():
    return pd.read_excel(archivo_asistencia)

# FUNCION PARA MOSTRAR ESTADISTICAS
def mostrar_estadisticas():
    estudiantes = cargar_estudiantes()
    asistencia = cargar_asistencia()
    
    hoy = datetime.now().date()
    asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == str(hoy)]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(estudiantes)}</div>
            <div class="stat-label">Total Estudiantes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        presentes_hoy = len(asistencia_hoy[asistencia_hoy["Estado"] == "Presente"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{presentes_hoy}</div>
            <div class="stat-label">Presentes Hoy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tarde_hoy = len(asistencia_hoy[asistencia_hoy["Estado"] == "Tarde"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{tarde_hoy}</div>
            <div class="stat-label">Tarde Hoy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        ausentes_hoy = len(asistencia_hoy[asistencia_hoy["Estado"] == "Ausente"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{ausentes_hoy}</div>
            <div class="stat-label">Ausentes Hoy</div>
        </div>
        """, unsafe_allow_html=True)

# FUNCION PARA MOSTRAR GRAFICOS
def mostrar_graficos():
    asistencia = cargar_asistencia()
    
    if len(asistencia) > 0:
        # Gráfico de asistencia por fecha
        asistencia_por_fecha = asistencia.groupby(['Fecha', 'Estado']).size().reset_index(name='count')
        
        fig = px.bar(
            asistencia_por_fecha,
            x='Fecha',
            y='count',
            color='Estado',
            title='📊 Asistencia por Fecha',
            color_discrete_map={
                'Presente': '#00ff00',
                'Tarde': '#ffff00',
                'Permiso': '#00ffff',
                'Ausente': '#ff0000'
            }
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(10, 25, 41, 0.9)',
            paper_bgcolor='rgba(10, 25, 41, 0.9)',
            font_color='#ffffff',
            title_font_color='#00ffff',
            legend_title_font_color='#00ffff'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# CONTENIDO PRINCIPAL
if menu == "Registrar estudiante":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("📝 Registrar nuevo estudiante")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ru = st.text_input("🎓 RU", placeholder="Ingrese el RU del estudiante")
        nombres = st.text_input("👤 Nombres", placeholder="Ingrese los nombres")
    
    with col2:
        paterno = st.text_input("👨 Apellido paterno", placeholder="Ingrese apellido paterno")
        materno = st.text_input("👩 Apellido materno", placeholder="Ingrese apellido materno")
    
    if st.button("⚡ GUARDAR ESTUDIANTE", use_container_width=True):
        with st.spinner("Generando QR..."):
            df = pd.read_excel(archivo_estudiantes)
            
            if ru in df["RU"].astype(str).values:
                st.error("❌ Este RU ya existe en el sistema")
            else:
                if not os.path.exists("qr"):
                    os.mkdir("qr")
                
                ruta_qr = f"qr/{ru}.png"
                qr = qrcode.make(ru)
                qr.save(ruta_qr)
                
                nuevo = pd.DataFrame([[ru, nombres, paterno, materno, ruta_qr]],
                                    columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "QR"])
                
                df = pd.concat([df, nuevo], ignore_index=True)
                df.to_excel(archivo_estudiantes, index=False)
                
                st.success("✅ Estudiante registrado exitosamente!")
                
                col_qr1, col_qr2, col_qr3 = st.columns([1,2,1])
                with col_qr2:
                    st.image(ruta_qr, width=350)
                    
                    with open(ruta_qr, "rb") as file:
                        st.download_button(
                            label="📥 DESCARGAR QR",
                            data=file,
                            file_name=f"{ru}_qr.png",
                            mime="image/png",
                            use_container_width=True
                        )
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Lista estudiantes":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("📋 Lista de estudiantes")
    
    estudiantes = cargar_estudiantes()
    
    if len(estudiantes) > 0:
        # Mostrar estadísticas rápidas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total estudiantes", len(estudiantes))
        with col2:
            st.metric("Con QR generado", len(estudiantes[estudiantes["QR"].notna()]))
        with col3:
            st.metric("Sin QR", len(estudiantes[estudiantes["QR"].isna()]))
        
        # Mostrar tabla
        st.dataframe(estudiantes, use_container_width=True)
        
        # Pestañas para acciones
        tab1, tab2, tab3, tab4 = st.tabs(["✏️ Editar", "🗑️ Eliminar", "📥 Descargar", "🔍 Ver QR"])
        
        with tab1:
            st.subheader("Editar estudiante")
            indice = st.number_input(
                "Índice del estudiante",
                min_value=0,
                max_value=len(estudiantes)-1,
                key="edit_index"
            )
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    ru_edit = st.text_input("RU", value=str(estudiantes.loc[indice, "RU"]))
                    nombres_edit = st.text_input("Nombres", value=estudiantes.loc[indice, "Nombres"])
                with col2:
                    paterno_edit = st.text_input("Apellido paterno", value=estudiantes.loc[indice, "Apellido_paterno"])
                    materno_edit = st.text_input("Apellido materno", value=estudiantes.loc[indice, "Apellido_materno"])
                
                if st.form_submit_button("⚡ Actualizar estudiante"):
                    estudiantes.loc[indice, "RU"] = ru_edit
                    estudiantes.loc[indice, "Nombres"] = nombres_edit
                    estudiantes.loc[indice, "Apellido_paterno"] = paterno_edit
                    estudiantes.loc[indice, "Apellido_materno"] = materno_edit
                    estudiantes.to_excel(archivo_estudiantes, index=False)
                    st.success("✅ Estudiante actualizado!")
                    st.cache_data.clear()
        
        with tab2:
            st.subheader("Eliminar estudiante")
            eliminar = st.number_input(
                "Índice a eliminar",
                min_value=0,
                max_value=len(estudiantes)-1,
                key="delete_index"
            )
            
            if st.button("🗑️ Eliminar estudiante", type="primary"):
                if st.checkbox("Confirmar eliminación"):
                    # Eliminar archivo QR
                    try:
                        qr_path = estudiantes.loc[eliminar, "QR"]
                        if os.path.exists(qr_path):
                            os.remove(qr_path)
                    except:
                        pass
                    
                    estudiantes = estudiantes.drop(eliminar)
                    estudiantes.to_excel(archivo_estudiantes, index=False)
                    st.success("✅ Estudiante eliminado!")
                    st.cache_data.clear()
        
        with tab3:
            st.subheader("Descargar Excel")
            archivo_descarga = "registro_estudiantes.xlsx"
            estudiantes.to_excel(archivo_descarga, index=False)
            
            with open(archivo_descarga, "rb") as file:
                st.download_button(
                    "📥 Descargar Excel completo",
                    data=file,
                    file_name=archivo_descarga,
                    use_container_width=True
                )
        
        with tab4:
            st.subheader("Ver QR del estudiante")
            ru_ver = st.text_input("Ingrese RU del estudiante")
            
            if ru_ver:
                estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]
                if len(estudiante) > 0:
                    ruta = estudiante.iloc[0]["QR"]
                    if os.path.exists(ruta):
                        st.image(ruta, width=350)
                    else:
                        st.warning("⚠️ Archivo QR no encontrado")
                else:
                    st.error("❌ Estudiante no encontrado")
    else:
        st.info("ℹ️ No hay estudiantes registrados")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Escanear QR":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("📸 Escanear QR de asistencia")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        foto = st.camera_input("📷 Enfoque el código QR del estudiante")
    
    with col2:
        st.markdown("""
        <div style="background: rgba(0,180,219,0.1); padding: 20px; border-radius: 10px;">
            <h4 style="color: #00ffff;">📌 Instrucciones:</h4>
            <ul style="color: white;">
                <li>Enfoque bien el código QR</li>
                <li>Asegure buena iluminación</li>
                <li>Mantenga el QR estable</li>
                <li>Espere la confirmación</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    if foto is not None:
        with st.spinner("⚡ Procesando QR..."):
            file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(frame)
            
            if data:
                ru = data
                estudiantes = pd.read_excel(archivo_estudiantes)
                estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]
                
                if len(estudiante) > 0:
                    nombres = estudiante.iloc[0]["Nombres"]
                    paterno = estudiante.iloc[0]["Apellido_paterno"]
                    materno = estudiante.iloc[0]["Apellido_materno"]
                    
                    ahora = datetime.now()
                    fecha = ahora.date()
                    hora = ahora.strftime("%H:%M:%S")
                    
                    asistencia = pd.read_excel(archivo_asistencia)
                    ya = asistencia[
                        (asistencia["RU"].astype(str) == ru) &
                        (asistencia["Fecha"].astype(str) == str(fecha))
                    ]
                    
                    if len(ya) == 0:
                        nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, "Presente"]],
                                            columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
                        
                        asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                        asistencia.to_excel(archivo_asistencia, index=False)
                        
                        st.balloons()
                        st.success(f"""
                        ✅ **ASISTENCIA REGISTRADA EXITOSAMENTE!**
                        
                        **Estudiante:** {nombres} {paterno} {materno}
                        **RU:** {ru}
                        **Fecha:** {fecha}
                        **Hora:** {hora}
                        **Estado:** Presente
                        """)
                    else:
                        st.warning(f"⚠️ El estudiante {nombres} {paterno} ya registró asistencia hoy a las {ya.iloc[0]['Hora']}")
                else:
                    st.error("❌ Estudiante no encontrado en la base de datos")
            else:
                st.error("❌ No se detectó ningún código QR válido")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Registrar asistencia manual":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("✏️ Registro manual de asistencia")
    
    estudiantes = cargar_estudiantes()
    
    if len(estudiantes) > 0:
        estudiantes["nombre_completo"] = (
            estudiantes["RU"].astype(str) + " - " +
            estudiantes["Nombres"] + " " +
            estudiantes["Apellido_paterno"]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            seleccionado = st.selectbox(
                "👤 Seleccionar estudiante",
                estudiantes["nombre_completo"]
            )
            
            estado = st.selectbox(
                "📊 Estado",
                ["Presente", "Tarde", "Permiso", "Ausente"],
                help="Seleccione el estado de asistencia"
            )
        
        with col2:
            st.markdown("""
            <div style="background: rgba(0,180,219,0.1); padding: 20px; border-radius: 10px;">
                <h4 style="color: #00ffff;">📝 Leyenda:</h4>
                <ul style="color: white; list-style: none;">
                    <li>✅ Presente - Llegó a tiempo</li>
                    <li>⏰ Tarde - Llegó después de la hora</li>
                    <li>📋 Permiso - Con autorización</li>
                    <li>❌ Ausente - No asistió</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("⚡ REGISTRAR ASISTENCIA", use_container_width=True):
            ru = seleccionado.split(" - ")[0]
            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]
            
            nombres = estudiante.iloc[0]["Nombres"]
            paterno = estudiante.iloc[0]["Apellido_paterno"]
            materno = estudiante.iloc[0]["Apellido_materno"]
            
            ahora = datetime.now()
            fecha = ahora.date()
            hora = ahora.strftime("%H:%M:%S")
            
            asistencia = pd.read_excel(archivo_asistencia)
            
            nuevo = pd.DataFrame([[ru, nombres, paterno, materno, fecha, hora, estado]],
                                columns=["RU", "Nombres", "Apellido_paterno", "Apellido_materno", "Fecha", "Hora", "Estado"])
            
            asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
            asistencia.to_excel(archivo_asistencia, index=False)
            
            st.success(f"✅ Asistencia registrada: {nombres} {paterno} - {estado}")
    else:
        st.info("ℹ️ No hay estudiantes registrados")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Ver asistencia":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("📊 Registros de asistencia")
    
    asistencia = cargar_asistencia()
    
    if len(asistencia) > 0:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fecha_filter = st.date_input("📅 Filtrar por fecha", value=None)
        
        with col2:
            estado_filter = st.selectbox(
                "📊 Filtrar por estado",
                ["Todos", "Presente", "Tarde", "Permiso", "Ausente"]
            )
        
        with col3:
            busqueda = st.text_input("🔍 Buscar por RU o nombre", placeholder="Ingrese texto...")
        
        # Aplicar filtros
        datos_filtrados = asistencia.copy()
        
        if fecha_filter:
            datos_filtrados = datos_filtrados[datos_filtrados["Fecha"].astype(str) == str(fecha_filter)]
        
        if estado_filter != "Todos":
            datos_filtrados = datos_filtrados[datos_filtrados["Estado"] == estado_filter]
        
        if busqueda:
            datos_filtrados = datos_filtrados[
                datos_filtrados["RU"].astype(str).str.contains(busqueda, case=False) |
                datos_filtrados["Nombres"].str.contains(busqueda, case=False) |
                datos_filtrados["Apellido_paterno"].str.contains(busqueda, case=False)
            ]
        
        # Mostrar tabla
        st.dataframe(datos_filtrados, use_container_width=True)
        
        # Estadísticas
        st.subheader("📈 Resumen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total registros", len(datos_filtrados))
        with col2:
            st.metric("Presentes", len(datos_filtrados[datos_filtrados["Estado"] == "Presente"]))
        with col3:
            st.metric("Tarde", len(datos_filtrados[datos_filtrados["Estado"] == "Tarde"]))
        with col4:
            st.metric("Ausentes", len(datos_filtrados[datos_filtrados["Estado"] == "Ausente"]))
        
        # Acciones
        tab1, tab2, tab3 = st.tabs(["✏️ Editar estado", "🗑️ Eliminar registro", "📥 Descargar"])
        
        with tab1:
            if len(datos_filtrados) > 0:
                indice = st.number_input(
                    "Índice del registro",
                    min_value=0,
                    max_value=len(datos_filtrados)-1,
                    key="edit_asistencia"
                )
                
                nuevo_estado = st.selectbox(
                    "Nuevo estado",
                    ["Presente", "Tarde", "Permiso", "Ausente"],
                    key="estado_edit"
                )
                
                if st.button("⚡ Actualizar estado"):
                    idx_real = datos_filtrados.index[indice]
                    asistencia.loc[idx_real, "Estado"] = nuevo_estado
                    asistencia.to_excel(archivo_asistencia, index=False)
                    st.success("✅ Estado actualizado!")
                    st.cache_data.clear()
        
        with tab2:
            if len(datos_filtrados) > 0:
                eliminar = st.number_input(
                    "Índice a eliminar",
                    min_value=0,
                    max_value=len(datos_filtrados)-1,
                    key="delete_asistencia"
                )
                
                if st.button("🗑️ Eliminar registro"):
                    if st.checkbox("Confirmar eliminación"):
                        idx_real = datos_filtrados.index[eliminar]
                        asistencia = asistencia.drop(idx_real)
                        asistencia.to_excel(archivo_asistencia, index=False)
                        st.success("✅ Registro eliminado!")
                        st.cache_data.clear()
        
        with tab3:
            st.subheader("Descargar asistencia")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Descargar todos
                archivo_todos = "asistencia_completa.xlsx"
                asistencia.to_excel(archivo_todos, index=False)
                
                with open(archivo_todos, "rb") as file:
                    st.download_button(
                        "📥 Descargar todos los registros",
                        data=file,
                        file_name=archivo_todos,
                        use_container_width=True
                    )
            
            with col2:
                # Descargar día actual
                hoy = str(datetime.now().date())
                asistencia_hoy = asistencia[asistencia["Fecha"].astype(str) == hoy]
                
                if len(asistencia_hoy) > 0:
                    archivo_hoy = f"asistencia_{hoy}.xlsx"
                    asistencia_hoy.to_excel(archivo_hoy, index=False)
                    
                    with open(archivo_hoy, "rb") as file:
                        st.download_button(
                            "📥 Descargar asistencia del día",
                            data=file,
                            file_name=archivo_hoy,
                            use_container_width=True
                        )
    else:
        st.info("ℹ️ No hay registros de asistencia")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Dashboard":
    st.markdown('<div class="electric-card">', unsafe_allow_html=True)
    st.subheader("📊 Dashboard de Asistencia")
    
    # Estadísticas generales
    mostrar_estadisticas()
    
    # Gráficos
    mostrar_graficos()
    
    # Tabla de resumen
    asistencia = cargar_asistencia()
    
    if len(asistencia) > 0:
        st.subheader("📋 Últimos 10 registros")
        st.dataframe(asistencia.tail(10), use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div style="text-align: center; padding: 20px; margin-top: 50px;">
    <hr style="border-color: #00ffff;">
    <p style="color: #00ffff; font-size: 12px;">
        ⚡ Sistema de Asistencia QR v2.0 | Desarrollado con tecnología de punta ⚡
    </p>
</div>
""", unsafe_allow_html=True)
