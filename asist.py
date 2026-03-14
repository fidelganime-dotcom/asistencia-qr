elif menu == "📷 Escanear QR (Celular)":
    import cv2
    import av
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
    import threading
    import time

    class QRVideoProcessor(VideoProcessorBase):
        def __init__(self):
            self.qr_data = None
            self.last_detection_time = 0
            self.detection_cooldown = 3

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(gray)

            if data and time.time() - self.last_detection_time > self.detection_cooldown:
                self.qr_data = data
                self.last_detection_time = time.time()
                if bbox is not None:
                    bbox = bbox.astype(int)
                    for i in range(len(bbox)):
                        cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1)%len(bbox)][0]), (0,255,0), 2)

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    st.subheader("Escanea el código QR con la cámara")
    actividad = st.text_input("Actividad (opcional)")

    ctx = webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=QRVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

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
                ctx.video_processor.qr_data = None
            else:
                st.warning("⚠️ Ya registró asistencia hoy")
                ctx.video_processor.qr_data = None
        else:
            st.error("❌ Estudiante no encontrado")
            ctx.video_processor.qr_data = None
