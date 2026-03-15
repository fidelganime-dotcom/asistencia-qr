import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ------------------------------------------------------------
# CONEXIÓN GOOGLE SHEETS
# ------------------------------------------------------------

scope = [
"https://spreadsheets.google.com/feeds",
"https://www.googleapis.com/auth/drive"
]

credenciales = ServiceAccountCredentials.from_json_keyfile_name(
"western-lambda-475101-e6-4e46b79cef5e.json",
scope
)

client = gspread.authorize(credenciales)

# Abrir hoja
sheet_estudiantes = client.open("asistencia_qr").worksheet("estudiantes")
sheet_asistencia = client.open("asistencia_qr").worksheet("asistencia")


def obtener_estudiantes():
    data = sheet_estudiantes.get_all_records()
    return pd.DataFrame(data)

def guardar_estudiante(data):
    sheet_estudiantes.append_row(data)

def obtener_asistencia():
    data = sheet_asistencia.get_all_records()
    return pd.DataFrame(data)

def guardar_asistencia(data):
    sheet_asistencia.append_row(data)


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
# CONFIGURACIÓN STREAMLIT
# ------------------------------------------------------------

st.set_page_config(
page_title="Sistema de Asistencia QR",
layout="wide"
)

st.title("📷 Sistema de Asistencia con QR")

menu = st.sidebar.selectbox(
"Menú",
[
"Registrar estudiante",
"Lista estudiantes",
"Escanear QR",
"Registrar asistencia manual",
"Ver asistencia"
]
)

# ------------------------------------------------------------
# REGISTRAR ESTUDIANTE
# ------------------------------------------------------------

if menu == "Registrar estudiante":

    st.subheader("Registrar nuevo estudiante")

    ru = st.text_input("RU")
    nombres = st.text_input("Nombres")
    paterno = st.text_input("Apellido paterno")
    materno = st.text_input("Apellido materno")

    if st.button("Guardar estudiante"):

        estudiantes = obtener_estudiantes()

        if ru in estudiantes["RU"].astype(str).values:
            st.error("Este RU ya existe")

        else:

            if not os.path.exists("qr"):
                os.mkdir("qr")

            ruta_qr = f"qr/{ru}.png"

            qr = qrcode.make(ru)
            qr.save(ruta_qr)

            guardar_estudiante([
                ru,
                nombres,
                paterno,
                materno,
                ruta_qr
            ])

            st.success("Estudiante registrado")

            st.image(ruta_qr, width=300)

# ------------------------------------------------------------
# LISTA ESTUDIANTES
# ------------------------------------------------------------

elif menu == "Lista estudiantes":

    st.subheader("Lista de estudiantes")

    estudiantes = obtener_estudiantes()

    st.dataframe(estudiantes)

    ru_ver = st.text_input("Ingresar RU para ver QR")

    if ru_ver != "":

        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru_ver]

        if len(estudiante) > 0:
            st.image(estudiante.iloc[0]["QR"], width=300)

        else:
            st.warning("RU no encontrado")

# ------------------------------------------------------------
# ESCANEAR QR
# ------------------------------------------------------------

elif menu == "Escanear QR":

    st.subheader("Escanear código QR")

    foto = st.camera_input("Escanear QR")

    if foto is not None:

        file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        detector = cv2.QRCodeDetector()

        data, bbox, _ = detector.detectAndDecode(frame)

        if data:

            ru = data

            estudiantes = obtener_estudiantes()

            estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]

            if len(estudiante) > 0:

                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha, hora = obtener_fecha_hora_exacta()

                asistencia = obtener_asistencia()

                ya = asistencia[
                (asistencia["RU"].astype(str) == ru) &
                (asistencia["Fecha"].astype(str) == str(fecha))
                ]

                if len(ya) == 0:

                    guardar_asistencia([
                        ru,
                        nombres,
                        paterno,
                        materno,
                        str(fecha),
                        hora,
                        "Presente"
                    ])

                    st.success(f"Asistencia registrada {nombres}")

                else:

                    st.warning("Ya registró asistencia hoy")

            else:

                st.error("Estudiante no encontrado")

        else:

            st.warning("No se detectó QR")

# ------------------------------------------------------------
# REGISTRO MANUAL
# ------------------------------------------------------------

elif menu == "Registrar asistencia manual":

    estudiantes = obtener_estudiantes()

    estudiantes["nombre"] = estudiantes["RU"].astype(str) + " - " + estudiantes["Nombres"]

    seleccionado = st.selectbox("Seleccionar estudiante", estudiantes["nombre"])

    ru = seleccionado.split(" - ")[0]

    estado = st.selectbox("Estado", ["Presente","Tarde","Permiso","Ausente"])

    if st.button("Registrar asistencia"):

        estudiante = estudiantes[estudiantes["RU"].astype(str) == ru]

        nombres = estudiante.iloc[0]["Nombres"]
        paterno = estudiante.iloc[0]["Apellido_paterno"]
        materno = estudiante.iloc[0]["Apellido_materno"]

        fecha, hora = obtener_fecha_hora_exacta()

        guardar_asistencia([
            ru,
            nombres,
            paterno,
            materno,
            str(fecha),
            hora,
            estado
        ])

        st.success("Asistencia registrada")


# ------------------------------------------------------------
# VER ASISTENCIA
# ------------------------------------------------------------

elif menu == "Ver asistencia":

    st.subheader("Registros de asistencia")

    asistencia = obtener_asistencia()

    st.dataframe(asistencia)
