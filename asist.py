import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
from io import BytesIO
import cv2
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import time

# CONFIGURACION
st.set_page_config(
    page_title="Asistencia QR",
    page_icon="📷",
    layout="wide"
)

# ESTILO
st.markdown("""
<style>
.stApp {
background-color:#0f172a;
color:white;
}

h1,h2,h3{
color:#38bdf8;
}

.stButton>button{
background-color:#2563eb;
color:white;
border-radius:10px;
height:45px;
font-size:16px;
}

.stTextInput>div>div>input{
background-color:#1e293b;
color:white;
}

.stSelectbox>div>div{
background-color:#1e293b;
}

</style>
""", unsafe_allow_html=True)


archivo_estudiantes = "estudiantes.xlsx"
archivo_asistencia = "asistencia.xlsx"

st.title("📷 Sistema de Asistencia QR")

menu = st.sidebar.selectbox("Menú",
[
"👨‍🎓 Registrar estudiante",
"📋 Lista estudiantes",
"📷 Escanear QR (Celular)",
"✍️ Registrar asistencia manual",
"📊 Ver asistencia"
])


# CREAR ARCHIVOS
if not os.path.exists(archivo_estudiantes):
    pd.DataFrame(columns=["RU","Nombre","Apellido","QR"]).to_excel(archivo_estudiantes,index=False)

if not os.path.exists(archivo_asistencia):
    pd.DataFrame(columns=["RU","Nombre","Apellido","Fecha","Hora","Estado","Actividad"]).to_excel(archivo_asistencia,index=False)


# REGISTRAR ESTUDIANTE
if menu == "👨‍🎓 Registrar estudiante":

    st.subheader("Registrar estudiante")

    ru = st.text_input("RU")
    nombre = st.text_input("Nombre")
    apellido = st.text_input("Apellido")

    if st.button("Guardar estudiante"):

        df = pd.read_excel(archivo_estudiantes)

        if ru in df["RU"].astype(str).values:

            st.error("RU ya existe")

        else:

            if not os.path.exists("qr"):
                os.mkdir("qr")

            ruta_qr = f"qr/{ru}.png"

            qr = qrcode.make(ru)
            qr.save(ruta_qr)

            nuevo = pd.DataFrame([[ru, nombre, apellido, ruta_qr]],
            columns=["RU","Nombre","Apellido","QR"])

            df = pd.concat([df, nuevo], ignore_index=True)

            df.to_excel(archivo_estudiantes, index=False)

            st.success("Estudiante registrado")

            st.image(ruta_qr, width=200)

            with open(ruta_qr, "rb") as f:
                st.download_button(
                "⬇ Descargar QR",
                f,
                file_name=f"QR_{ru}.png"
                )


# LISTA ESTUDIANTES
elif menu == "📋 Lista estudiantes":

    df = pd.read_excel(archivo_estudiantes)

    st.dataframe(df, use_container_width=True)


# ESCANEAR QR CELULAR (CON CÁMARA)
elif menu == "📷 Escanear QR (Celular)":

    # Definimos el procesador de video dentro de este bloque (o podría ir fuera)
    class QRVideoProcessor(VideoProcessorBase):
        def __init__(self):
            self.qr_data = None
            self.last_detection_time = 0
            self.detection_cooldown = 3  # segundos para evitar múltiples registros del mismo QR

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(gray)

            if data and time.time() - self.last_detection_time > self.detection_cooldown:
                self.qr_data = data
                self.last_detection_time = time.time()
                # Dibujar rectángulo si se detecta el QR (opcional)
                if bbox is not None:
                    bbox = bbox.astype(int)
                    for i in range(len(bbox)):
                        cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), (0, 255, 0), 2)

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    st.subheader("Escanea el código QR con la cámara")
    actividad = st.text_input("Actividad (opcional)")

    # Iniciar stream de cámara
    ctx = webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=QRVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Si se detectó un QR, procesamos el registro
    if ctx.video_processor and ctx.video_processor.qr_data:
        ru = ctx.video_processor.qr_data.strip()

        estudiantes = pd.read_excel(archivo_estudiantes)
        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]

        if len(estudiante) > 0:
            nombre = estudiante.iloc[0]["Nombre"]
            apellido = estudiante.iloc[0]["Apellido"]

            fecha = datetime.now().date()
            hora = datetime.now().strftime("%H:%M:%S")

            asistencia = pd.read_excel(archivo_asistencia)
            ya = asistencia[
                (asistencia["RU"].astype(str) == ru) &
                (asistencia["Fecha"].astype(str) == str(fecha))
            ]

            if len(ya) == 0:
                nuevo = pd.DataFrame([[
                    ru, nombre, apellido, fecha, hora,
                    "Presente", actividad
                ]], columns=[
                    "RU", "Nombre", "Apellido",
                    "Fecha", "Hora", "Estado", "Actividad"
                ])

                asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                asistencia.to_excel(archivo_asistencia, index=False)

                st.success(f"✅ Asistencia registrada: {nombre} {apellido}")
                # Limpiar para que no se vuelva a registrar el mismo código hasta que pase el cooldown
                ctx.video_processor.qr_data = None
            else:
                st.warning("⚠️ Ya registró asistencia hoy")
                ctx.video_processor.qr_data = None
        else:
            st.error("❌ Estudiante no encontrado")
            ctx.video_processor.qr_data = None


# REGISTRO MANUAL
elif menu == "✍️ Registrar asistencia manual":

    estudiantes = pd.read_excel(archivo_estudiantes)

    estudiantes["nombre"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombre"]

    seleccionado = st.selectbox("Estudiante", estudiantes["nombre"])

    ru = seleccionado.split(" - ")[0]

    estado = st.selectbox("Estado", ["Presente", "Tarde", "Permiso", "Ausente"])

    actividad = st.text_input("Actividad")

    if st.button("Registrar"):

        est = estudiantes[estudiantes["RU"].astype(str) == ru]

        nombre = est.iloc[0]["Nombre"]
        apellido = est.iloc[0]["Apellido"]

        fecha = datetime.now().date()
        hora = datetime.now().strftime("%H:%M:%S")

        asistencia = pd.read_excel(archivo_asistencia)

        nuevo = pd.DataFrame([[
            ru, nombre, apellido, fecha, hora, estado, actividad
        ]], columns=[
            "RU", "Nombre", "Apellido",
            "Fecha", "Hora", "Estado", "Actividad"
        ])

        asistencia = pd.concat([asistencia, nuevo], ignore_index=True)

        asistencia.to_excel(archivo_asistencia, index=False)

        st.success("Registrado")


# VER ASISTENCIA
elif menu == "📊 Ver asistencia":

    asistencia = pd.read_excel(archivo_asistencia)

    st.dataframe(asistencia, use_container_width=True)

    fecha = st.date_input("Filtrar por fecha")

    if fecha:

        filtro = asistencia[
        asistencia["Fecha"].astype(str) == str(fecha)
        ]

        st.dataframe(filtro)

        # DESCARGAR EXCEL DEL DIA
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtro.to_excel(writer, index=False)

        st.download_button(
        "⬇ Descargar Excel del día",
        output.getvalue(),
        file_name=f"asistencia_{fecha}.xlsx"
        )

    st.subheader("Resumen")

    st.bar_chart(asistencia["Estado"].value_counts())
