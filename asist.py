import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2

# archivos
archivo_estudiantes="estudiantes.xlsx"
archivo_asistencia="asistencia.xlsx"
archivo_extension="extension.xlsx"

st.title("Sistema de Asistencia con QR")

menu=st.sidebar.selectbox("Menu",
[
"Registrar estudiante",
"Lista estudiantes",
"Escanear QR",
"Registrar asistencia manual",
"Ver asistencia",
"Extension universitaria"
])

# crear archivos si no existen
if not os.path.exists(archivo_estudiantes):
    df=pd.DataFrame(columns=["RU","Nombre","Apellido","QR"])
    df.to_excel(archivo_estudiantes,index=False)

if not os.path.exists(archivo_asistencia):
    df=pd.DataFrame(columns=[
    "RU","Nombre","Apellido","Fecha","Hora","Estado","Actividad"
    ])
    df.to_excel(archivo_asistencia,index=False)

if not os.path.exists(archivo_extension):
    df=pd.DataFrame(columns=[
    "RU","Nombre","Apellido",
    "Actividad","Fecha",
    "Hora_inicio","Hora_fin"
    ])
    df.to_excel(archivo_extension,index=False)


# -----------------------------
# REGISTRAR ESTUDIANTE
# -----------------------------
if menu=="Registrar estudiante":

    st.subheader("Nuevo estudiante")

    ru=st.text_input("RU")
    nombre=st.text_input("Nombre")
    apellido=st.text_input("Apellido")

    if st.button("Guardar"):

        df=pd.read_excel(archivo_estudiantes)

        if ru in df["RU"].astype(str).values:
            st.error("Este RU ya existe")

        else:

            if not os.path.exists("qr"):
                os.mkdir("qr")

            ruta_qr=f"qr/{ru}.png"

            qr=qrcode.make(ru)
            qr.save(ruta_qr)

            nuevo=pd.DataFrame([[ru,nombre,apellido,ruta_qr]],
            columns=["RU","Nombre","Apellido","QR"])

            df=pd.concat([df,nuevo],ignore_index=True)

            df.to_excel(archivo_estudiantes,index=False)

            st.success("Estudiante registrado")
            st.image(ruta_qr,width=200)


# -----------------------------
# LISTA ESTUDIANTES
# -----------------------------
elif menu=="Lista estudiantes":

    st.subheader("Lista de estudiantes")

    df=pd.read_excel(archivo_estudiantes)

    st.dataframe(df)

    ru_ver=st.text_input("Ver QR del estudiante (RU)")

    if ru_ver!="":

        estudiante=df[df["RU"].astype(str)==ru_ver]

        if len(estudiante)>0:
            st.image(estudiante.iloc[0]["QR"],width=200)
        else:
            st.warning("RU no encontrado")


# -----------------------------
# ESCANEAR QR
# -----------------------------
elif menu=="Escanear QR":

    st.subheader("Escaneo automático de QR")

    actividad=st.text_input("Actividad (opcional)")

    if st.button("Activar cámara"):

        detector = cv2.QRCodeDetector()
        cap=cv2.VideoCapture(0)

        st.info("Mostrando cámara. Escanea el QR")

        frame_placeholder = st.empty()

        while True:

            ret,frame=cap.read()

            if not ret:
                st.error("No se pudo abrir la cámara")
                break

            data,bbox,_ = detector.detectAndDecode(frame)

            frame_placeholder.image(frame,channels="BGR")

            if data:

                ru=data

                estudiantes=pd.read_excel(archivo_estudiantes)

                estudiante=estudiantes[
                estudiantes["RU"].astype(str)==ru
                ]

                if len(estudiante)>0:

                    nombre=estudiante.iloc[0]["Nombre"]
                    apellido=estudiante.iloc[0]["Apellido"]

                    fecha=datetime.now().date()
                    hora=datetime.now().strftime("%H:%M:%S")

                    asistencia=pd.read_excel(archivo_asistencia)

                    ya=asistencia[
                    (asistencia["RU"].astype(str)==ru) &
                    (asistencia["Fecha"].astype(str)==str(fecha))
                    ]

                    if len(ya)==0:

                        nuevo=pd.DataFrame([[ 
                        ru,nombre,apellido,fecha,hora,
                        "Presente",actividad
                        ]],

                        columns=[
                        "RU","Nombre","Apellido",
                        "Fecha","Hora","Estado","Actividad"
                        ])

                        asistencia=pd.concat([asistencia,nuevo],ignore_index=True)

                        asistencia.to_excel(
                        archivo_asistencia,index=False)

                        st.success(
                        f"Asistencia registrada: {nombre} {apellido}"
                        )

                    else:
                        st.warning("Ya registró asistencia hoy")

                else:
                    st.error("Estudiante no encontrado")

                cap.release()
                break

        cap.release()
        cv2.destroyAllWindows()


# -----------------------------
# REGISTRO MANUAL
# -----------------------------
elif menu=="Registrar asistencia manual":

    st.subheader("Registro manual")

    estudiantes=pd.read_excel(archivo_estudiantes)

    if len(estudiantes)==0:

        st.warning("No hay estudiantes registrados")

    else:

        estudiantes["nombre_completo"]=(
        estudiantes["RU"].astype(str)+" - "+
        estudiantes["Nombre"]+" "+estudiantes["Apellido"]
        )

        seleccionado=st.selectbox(
        "Seleccionar estudiante",
        estudiantes["nombre_completo"]
        )

        ru=seleccionado.split(" - ")[0]

        estudiante=estudiantes[
        estudiantes["RU"].astype(str)==ru
        ]

        nombre=estudiante.iloc[0]["Nombre"]
        apellido=estudiante.iloc[0]["Apellido"]

        st.image(estudiante.iloc[0]["QR"],width=200)

        estado=st.selectbox("Estado",
        ["Presente","Tarde","Permiso","Ausente"])

        actividad=st.text_input("Actividad (opcional)")

        if st.button("Registrar asistencia"):

            fecha=datetime.now().date()
            hora=datetime.now().strftime("%H:%M:%S")

            asistencia=pd.read_excel(archivo_asistencia)

            nuevo=pd.DataFrame([[ 
            ru,nombre,apellido,fecha,hora,estado,actividad
            ]],

            columns=[
            "RU","Nombre","Apellido",
            "Fecha","Hora","Estado","Actividad"
            ])

            asistencia=pd.concat([asistencia,nuevo],ignore_index=True)

            asistencia.to_excel(archivo_asistencia,index=False)

            st.success("Asistencia registrada")


# -----------------------------
# VER ASISTENCIA
# -----------------------------
elif menu=="Ver asistencia":

    st.subheader("Registros de asistencia")

    asistencia=pd.read_excel(archivo_asistencia)

    st.dataframe(asistencia)

    st.subheader("Resumen")

    st.write(asistencia["Estado"].value_counts())


# -----------------------------
# EXTENSION UNIVERSITARIA
# -----------------------------
elif menu=="Extension universitaria":

    st.subheader("Registro de Actividades de Extension")

    estudiantes=pd.read_excel(archivo_estudiantes)

    estudiantes["nombre_completo"]=(
    estudiantes["RU"].astype(str)+" - "+
    estudiantes["Nombre"]+" "+estudiantes["Apellido"]
    )

    seleccionado=st.selectbox(
    "Seleccionar estudiante",
    estudiantes["nombre_completo"]
    )

    ru=seleccionado.split(" - ")[0]

    estudiante=estudiantes[
    estudiantes["RU"].astype(str)==ru
    ]

    nombre=estudiante.iloc[0]["Nombre"]
    apellido=estudiante.iloc[0]["Apellido"]

    actividad=st.text_input("Nombre de la actividad")

    hora_inicio=st.time_input("Hora inicio")
    hora_fin=st.time_input("Hora fin")

    if st.button("Registrar actividad"):

        fecha=datetime.now().date()

        extension=pd.read_excel(archivo_extension)

        nuevo=pd.DataFrame([[

        ru,
        nombre,
        apellido,
        actividad,
        fecha,
        hora_inicio,
        hora_fin

        ]],

        columns=[
        "RU","Nombre","Apellido",
        "Actividad","Fecha",
        "Hora_inicio","Hora_fin"
        ])

        extension=pd.concat([extension,nuevo],ignore_index=True)

        extension.to_excel(archivo_extension,index=False)

        st.success("Actividad registrada")
