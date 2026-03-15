# ESCANEAR QR CELULAR (CON CÁMARA + RESPALDO MANUAL)
elif menu == "📷 Escanear QR (Celular)":

    # Clase procesadora de video (definida dentro para evitar conflictos)
    class QRVideoProcessor(VideoProcessorBase):
        def __init__(self):
            self.qr_data = None
            self.last_detection_time = 0
            self.detection_cooldown = 5  # segundos

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(gray)

            if data and time.time() - self.last_detection_time > self.detection_cooldown:
                self.qr_data = data.strip()
                self.last_detection_time = time.time()
                # Dibujar rectángulo si hay bbox
                if bbox is not None:
                    bbox = bbox.astype(int)
                    for i in range(len(bbox)):
                        cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1)%len(bbox)][0]), (0,255,0), 3)
                # También podemos poner un texto en el frame
                cv2.putText(img, "QR Detectado!", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            return av.VideoFrame.from_ndarray(img, format="bgr24")

    st.subheader("📸 Escanea el código QR con la cámara")
    st.info("Apunta la cámara al código QR. Cuando se detecte, se registrará automáticamente.")

    actividad = st.text_input("Actividad (opcional)", key="actividad_qr")

    # Iniciar stream de cámara
    ctx = webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=QRVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # --- Mostrar estado de la cámara ---
    if ctx.state.playing:
        st.success("✅ Cámara activa")
    else:
        st.warning("⏳ Iniciando cámara...")

    # --- Procesar QR detectado ---
    if ctx.video_processor and ctx.video_processor.qr_data:
        ru_detectado = ctx.video_processor.qr_data
        st.info(f"📌 Código detectado: {ru_detectado}")

        # Limpiar el dato (eliminar espacios y caracteres extraños)
        ru_limpio = ru_detectado.strip()

        # Cargar estudiantes
        estudiantes = pd.read_excel(archivo_estudiantes)
        estudiantes['RU_str'] = estudiantes['RU'].astype(str).str.strip()

        # Buscar coincidencia exacta
        match = estudiantes[estudiantes['RU_str'] == ru_limpio]

        if not match.empty:
            estudiante = match.iloc[0]
            nombre = estudiante['Nombre']
            apellido = estudiante['Apellido']

            fecha = datetime.now().date()
            hora = datetime.now().strftime("%H:%M:%S")

            asistencia = pd.read_excel(archivo_asistencia)
            ya_registrado = asistencia[
                (asistencia['RU'].astype(str).str.strip() == ru_limpio) &
                (asistencia['Fecha'].astype(str) == str(fecha))
            ]

            if ya_registrado.empty:
                nuevo_registro = pd.DataFrame([[
                    ru_limpio, nombre, apellido, fecha, hora,
                    "Presente", actividad
                ]], columns=["RU","Nombre","Apellido","Fecha","Hora","Estado","Actividad"])

                asistencia = pd.concat([asistencia, nuevo_registro], ignore_index=True)
                asistencia.to_excel(archivo_asistencia, index=False)

                st.success(f"✅ **{nombre} {apellido}** ha sido marcado como **Presente** a las {hora}")
                # Limpiar el dato para evitar doble registro
                ctx.video_processor.qr_data = None
                # Forzar recarga para limpiar mensajes
                time.sleep(1)
                st.rerun()
            else:
                st.warning("⚠️ Este estudiante ya registró asistencia hoy.")
                ctx.video_processor.qr_data = None
        else:
            st.error(f"❌ No se encontró ningún estudiante con RU: {ru_limpio}")
            ctx.video_processor.qr_data = None

    # --- Línea separadora ---
    st.markdown("---")
    st.subheader("⌨️ O ingresa el código manualmente")

    with st.form("manual_qr_form"):
        codigo_manual = st.text_input("Pega el código QR aquí")
        submitted = st.form_submit_button("Registrar asistencia manual")

        if submitted and codigo_manual:
            ru_manual = codigo_manual.strip()
            estudiantes = pd.read_excel(archivo_estudiantes)
            estudiantes['RU_str'] = estudiantes['RU'].astype(str).str.strip()
            match = estudiantes[estudiantes['RU_str'] == ru_manual]

            if not match.empty:
                estudiante = match.iloc[0]
                nombre = estudiante['Nombre']
                apellido = estudiante['Apellido']
                fecha = datetime.now().date()
                hora = datetime.now().strftime("%H:%M:%S")
                asistencia = pd.read_excel(archivo_asistencia)
                ya = asistencia[
                    (asistencia['RU'].astype(str).str.strip() == ru_manual) &
                    (asistencia['Fecha'].astype(str) == str(fecha))
                ]
                if ya.empty:
                    nuevo = pd.DataFrame([[
                        ru_manual, nombre, apellido, fecha, hora, "Presente", actividad
                    ]], columns=["RU","Nombre","Apellido","Fecha","Hora","Estado","Actividad"])
                    asistencia = pd.concat([asistencia, nuevo], ignore_index=True)
                    asistencia.to_excel(archivo_asistencia, index=False)
                    st.success(f"✅ Asistencia registrada para {nombre} {apellido}")
                else:
                    st.warning("⚠️ Ya registró hoy")
            else:
                st.error("❌ RU no encontrado")
