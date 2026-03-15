import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import cv2
import numpy as np
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# ----------------------------------------
# ZONA HORARIA
# ----------------------------------------
ZONA_HORARIA = pytz.timezone('America/La_Paz')

def obtener_fecha_hora():
    ahora = datetime.now(ZONA_HORARIA)
    return ahora.date(), ahora.strftime("%H:%M:%S")

# ----------------------------------------
# CONEXION GOOGLE SHEETS
# ----------------------------------------
scope = [
'https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive'
]

credenciales = ServiceAccountCredentials.from_json_keyfile_name(
"credenciales.json", scope
)

cliente = gspread.authorize(credenciales)

SHEET_ID = "TU_ID_DE_GOOGLE_SHEET"

sheet = cliente.open_by_key(SHEET_ID)

hoja_estudiantes = sheet.worksheet("estudiantes")
hoja_asistencia = sheet.worksheet("asistencia")

# ----------------------------------------
# FUNCIONES
# ----------------------------------------
def cargar_estudiantes():
    datos = hoja_estudiantes.get_all_records()
    return pd.DataFrame(datos)

def cargar_asistencia():
    datos = hoja_asistencia.get_all_records()
    return pd.DataFrame(datos)

def guardar_estudiante(fila):
    hoja_estudiantes.append_row(fila)

def guardar_asistencia(fila):
    hoja_asistencia.append_row(fila)

# ----------------------------------------
# STREAMLIT
# ----------------------------------------
st.title("📷 Sistema de Asistencia con QR")

menu = st.sidebar.selectbox("Menú",[
"Registrar estudiante",
"Lista estudiantes",
"Escanear QR",
"Registrar asistencia manual",
"Ver asistencia"
])

# ----------------------------------------
# REGISTRAR ESTUDIANTE
# ----------------------------------------
if menu == "Registrar estudiante":

    ru = st.text_input("RU")
    nombres = st.text_input("Nombres")
    paterno = st.text_input("Apellido paterno")
    materno = st.text_input("Apellido materno")

    if st.button("Guardar"):

        estudiantes = cargar_estudiantes()

        if ru in estudiantes["RU"].astype(str).values:
            st.error("RU ya existe")
        else:

            if not os.path.exists("qr"):
                os.mkdir("qr")

            ruta_qr = f"qr/{ru}.png"

            qr = qrcode.make(ru)
            qr.save(ruta_qr)

            guardar_estudiante([
            ru,nombres,paterno,materno,ruta_qr
            ])

            st.success("Estudiante registrado")

            st.image(ruta_qr,width=300)

# ----------------------------------------
# LISTA ESTUDIANTES
# ----------------------------------------
elif menu == "Lista estudiantes":

    estudiantes = cargar_estudiantes()

    st.dataframe(estudiantes)

    archivo = "estudiantes.xlsx"
    estudiantes.to_excel(archivo,index=False)

    with open(archivo,"rb") as f:
        st.download_button(
        "Descargar Excel",
        f,
        file_name="estudiantes.xlsx"
        )

# ----------------------------------------
# ESCANEAR QR
# ----------------------------------------
elif menu == "Escanear QR":

    foto = st.camera_input("Escanear QR")

    if foto:

        file_bytes = np.asarray(bytearray(foto.read()),dtype=np.uint8)

        frame = cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)

        detector = cv2.QRCodeDetector()

        data,bbox,_ = detector.detectAndDecode(frame)

        if data:

            ru = data

            estudiantes = cargar_estudiantes()

            estudiante = estudiantes[
            estudiantes["RU"].astype(str)==ru
            ]

            if len(estudiante)>0:

                nombres = estudiante.iloc[0]["Nombres"]
                paterno = estudiante.iloc[0]["Apellido_paterno"]
                materno = estudiante.iloc[0]["Apellido_materno"]

                fecha,hora = obtener_fecha_hora()

                asistencia = cargar_asistencia()

                ya = asistencia[
                (asistencia["RU"].astype(str)==ru)
                &
                (asistencia["Fecha"].astype(str)==str(fecha))
                ]

                if len(ya)==0:

                    guardar_asistencia([
                    ru,
                    nombres,
                    paterno,
                    materno,
                    str(fecha),
                    hora,
                    "Presente"
                    ])

                    st.success(f"Asistencia registrada {hora}")

                else:
                    st.warning("Ya registró hoy")

        else:
            st.warning("QR no detectado")

# ----------------------------------------
# REGISTRO MANUAL
# ----------------------------------------
elif menu == "Registrar asistencia manual":

    estudiantes = cargar_estudiantes()

    estudiantes["nombre"]=(
    estudiantes["RU"].astype(str)+" - "+
    estudiantes["Nombres"]
    )

    sel = st.selectbox("Estudiante",estudiantes["nombre"])

    ru = sel.split(" - ")[0]

    estado = st.selectbox("Estado",[
    "Presente","Tarde","Permiso","Ausente"
    ])

    if st.button("Registrar"):

        estudiante = estudiantes[
        estudiantes["RU"].astype(str)==ru
        ]

        nombres = estudiante.iloc[0]["Nombres"]
        paterno = estudiante.iloc[0]["Apellido_paterno"]
        materno = estudiante.iloc[0]["Apellido_materno"]

        fecha,hora = obtener_fecha_hora()

        guardar_asistencia([
        ru,
        nombres,
        paterno,
        materno,
        str(fecha),
        hora,
        estado
        ])

        st.success("Registrado")

# ----------------------------------------
# VER ASISTENCIA
# ----------------------------------------
elif menu == "Ver asistencia":

    asistencia = cargar_asistencia()

    st.dataframe(asistencia)

    archivo = "asistencia.xlsx"

    asistencia.to_excel(archivo,index=False)

    with open(archivo,"rb") as f:
        st.download_button(
        "Descargar Excel",
        f,
        file_name="asistencia.xlsx"
        )
