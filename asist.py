import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2
import numpy as np

# CONFIGURACION
st.set_page_config(layout="wide")

# CSS PARA AGRANDAR CAMARA
st.markdown("""
<style>

div[data-testid="stCameraInput"] video{
width:100% !important;
height:75vh !important;
object-fit:cover;
}

div[data-testid="stCameraInput"]{
width:100% !important;
}

</style>
""", unsafe_allow_html=True)

# archivos
archivo_estudiantes="estudiantes.xlsx"
archivo_asistencia="asistencia.xlsx"

st.title("Sistema de Asistencia con QR")

menu=st.sidebar.selectbox("Menu",
[
"Registrar estudiante",
"Lista estudiantes",
"Escanear QR",
"Registrar asistencia manual",
"Ver asistencia"
])

# -------------------------
# CREAR ARCHIVOS
# -------------------------

if not os.path.exists(archivo_estudiantes):

    df=pd.DataFrame(columns=[
        "RU",
        "Nombres",
        "Apellido_paterno",
        "Apellido_materno",
        "QR"
    ])

    df.to_excel(archivo_estudiantes,index=False)


if not os.path.exists(archivo_asistencia):

    df=pd.DataFrame(columns=[
        "RU",
        "Nombres",
        "Apellido_paterno",
        "Apellido_materno",
        "Fecha",
        "Hora",
        "Estado"
    ])

    df.to_excel(archivo_asistencia,index=False)


# -------------------------
# REGISTRAR ESTUDIANTE
# -------------------------

if menu=="Registrar estudiante":

    st.subheader("Registrar nuevo estudiante")

    ru=st.text_input("RU")
    nombres=st.text_input("Nombres")
    paterno=st.text_input("Apellido paterno")
    materno=st.text_input("Apellido materno")

    if st.button("Guardar estudiante"):

        df=pd.read_excel(archivo_estudiantes)

        if ru in df["RU"].astype(str).values:

            st.error("Este RU ya existe")

        else:

            if not os.path.exists("qr"):
                os.mkdir("qr")

            ruta_qr=f"qr/{ru}.png"

            qr=qrcode.make(ru)
            qr.save(ruta_qr)

            nuevo=pd.DataFrame([[ru,nombres,paterno,materno,ruta_qr]],
            columns=["RU","Nombres","Apellido_paterno","Apellido_materno","QR"])

            df=pd.concat([df,nuevo],ignore_index=True)

            df.to_excel(archivo_estudiantes,index=False)

            st.success("Estudiante registrado")

            st.image(ruta_qr,width=350)

            with open(ruta_qr,"rb") as file:

                st.download_button(
                    label="Descargar QR",
                    data=file,
                    file_name=f"{ru}_qr.png",
                    mime="image/png"
                )


# -------------------------
# LISTA ESTUDIANTES
# -------------------------

elif menu=="Lista estudiantes":

    st.subheader("Lista de estudiantes")

    estudiantes=pd.read_excel(archivo_estudiantes)

    st.dataframe(estudiantes,use_container_width=True)

# EDITAR

    st.subheader("Editar estudiante")

    if len(estudiantes)>0:

        indice=st.number_input(
            "Indice del estudiante a editar",
            min_value=0,
            max_value=len(estudiantes)-1
        )

        ru=st.text_input("RU",value=str(estudiantes.loc[indice,"RU"]))
        nombres=st.text_input("Nombres",value=estudiantes.loc[indice,"Nombres"])
        paterno=st.text_input("Apellido paterno",value=estudiantes.loc[indice,"Apellido_paterno"])
        materno=st.text_input("Apellido materno",value=estudiantes.loc[indice,"Apellido_materno"])

        if st.button("Actualizar estudiante"):

            estudiantes.loc[indice,"RU"]=ru
            estudiantes.loc[indice,"Nombres"]=nombres
            estudiantes.loc[indice,"Apellido_paterno"]=paterno
            estudiantes.loc[indice,"Apellido_materno"]=materno

            estudiantes.to_excel(archivo_estudiantes,index=False)

            st.success("Estudiante actualizado")

# ELIMINAR

    st.subheader("Eliminar estudiante")

    if len(estudiantes)>0:

        eliminar=st.number_input(
            "Indice del estudiante a eliminar",
            min_value=0,
            max_value=len(estudiantes)-1,
            key="eliminar_est"
        )

        if st.button("Eliminar estudiante"):

            estudiantes=estudiantes.drop(eliminar)

            estudiantes.to_excel(archivo_estudiantes,index=False)

            st.success("Estudiante eliminado")

# DESCARGAR EXCEL

    st.subheader("Descargar registro de estudiantes")

    archivo_descarga="registro_estudiantes.xlsx"

    estudiantes.to_excel(archivo_descarga,index=False)

    with open(archivo_descarga,"rb") as file:

        st.download_button(
            "Descargar Excel estudiantes",
            data=file,
            file_name=archivo_descarga
        )

# VER QR

    ru_ver=st.text_input("Ver QR del estudiante (RU)")

    if ru_ver!="":

        estudiante=estudiantes[estudiantes["RU"].astype(str)==ru_ver]

        if len(estudiante)>0:

            ruta=estudiante.iloc[0]["QR"]

            st.image(ruta,width=350)

            with open(ruta,"rb") as file:

                st.download_button(
                    "Descargar QR",
                    data=file,
                    file_name=f"{ru_ver}_qr.png"
                )

        else:
            st.warning("RU no encontrado")


# -------------------------
# ESCANEAR QR
# -------------------------

elif menu=="Escanear QR":

    st.subheader("Escanear QR")

    st.info("Apunta la cámara al QR del estudiante")

    foto=st.camera_input("Escanear QR")

    if foto is not None:

        file_bytes=np.asarray(bytearray(foto.read()),dtype=np.uint8)

        frame=cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)

        detector=cv2.QRCodeDetector()

        data,bbox,_=detector.detectAndDecode(frame)

        if data:

            ru=data

            estudiantes=pd.read_excel(archivo_estudiantes)

            estudiante=estudiantes[
                estudiantes["RU"].astype(str)==ru
            ]

            if len(estudiante)>0:

                nombres=estudiante.iloc[0]["Nombres"]
                paterno=estudiante.iloc[0]["Apellido_paterno"]
                materno=estudiante.iloc[0]["Apellido_materno"]

                fecha=datetime.now().date()
                hora=datetime.now().strftime("%H:%M:%S")

                asistencia=pd.read_excel(archivo_asistencia)

                ya=asistencia[
                    (asistencia["RU"].astype(str)==ru)
                    &
                    (asistencia["Fecha"].astype(str)==str(fecha))
                ]

                if len(ya)==0:

                    nuevo=pd.DataFrame([[ru,nombres,paterno,materno,fecha,hora,"Presente"]],
                    columns=["RU","Nombres","Apellido_paterno","Apellido_materno","Fecha","Hora","Estado"])

                    asistencia=pd.concat([asistencia,nuevo],ignore_index=True)

                    asistencia.to_excel(archivo_asistencia,index=False)

                    st.success(f"Asistencia registrada: {nombres} {paterno}")

                else:

                    st.warning("Ya registró asistencia hoy")

            else:

                st.error("Estudiante no encontrado")

        else:

            st.warning("No se detectó QR")


# -------------------------
# REGISTRO MANUAL
# -------------------------

elif menu=="Registrar asistencia manual":

    st.subheader("Registrar asistencia manual")

    estudiantes=pd.read_excel(archivo_estudiantes)

    if len(estudiantes)==0:

        st.warning("No hay estudiantes registrados")

    else:

        estudiantes["nombre_completo"]=(
        estudiantes["RU"].astype(str)+" - "+
        estudiantes["Nombres"]+" "+
        estudiantes["Apellido_paterno"]
        )

        seleccionado=st.selectbox(
            "Seleccionar estudiante",
            estudiantes["nombre_completo"]
        )

        ru=seleccionado.split(" - ")[0]

        estudiante=estudiantes[
            estudiantes["RU"].astype(str)==ru
        ]

        nombres=estudiante.iloc[0]["Nombres"]
        paterno=estudiante.iloc[0]["Apellido_paterno"]
        materno=estudiante.iloc[0]["Apellido_materno"]

        st.image(estudiante.iloc[0]["QR"],width=300)

        estado=st.selectbox(
            "Estado",
            ["Presente","Tarde","Permiso","Ausente"]
        )

        if st.button("Registrar asistencia"):

            fecha=datetime.now().date()
            hora=datetime.now().strftime("%H:%M:%S")

            asistencia=pd.read_excel(archivo_asistencia)

            nuevo=pd.DataFrame([[ru,nombres,paterno,materno,fecha,hora,estado]],
            columns=["RU","Nombres","Apellido_paterno","Apellido_materno","Fecha","Hora","Estado"])

            asistencia=pd.concat([asistencia,nuevo],ignore_index=True)

            asistencia.to_excel(archivo_asistencia,index=False)

            st.success("Asistencia registrada")


# -------------------------
# VER ASISTENCIA
# -------------------------

elif menu=="Ver asistencia":

    st.subheader("Registros de asistencia")

    asistencia=pd.read_excel(archivo_asistencia)

    st.dataframe(asistencia,use_container_width=True)

# EDITAR ESTADO

    st.subheader("Editar estado")

    if len(asistencia)>0:

        indice=st.number_input(
            "Indice del registro a editar",
            min_value=0,
            max_value=len(asistencia)-1
        )

        nuevo_estado=st.selectbox(
            "Nuevo estado",
            ["Presente","Tarde","Permiso","Ausente"]
        )

        if st.button("Actualizar estado"):

            asistencia.loc[indice,"Estado"]=nuevo_estado

            asistencia.to_excel(archivo_asistencia,index=False)

            st.success("Estado actualizado")


# ELIMINAR REGISTRO

    st.subheader("Eliminar registro")

    if len(asistencia)>0:

        eliminar=st.number_input(
            "Indice del registro a eliminar",
            min_value=0,
            max_value=len(asistencia)-1,
            key="eliminar"
        )

        if st.button("Eliminar registro"):

            asistencia=asistencia.drop(eliminar)

            asistencia.to_excel(archivo_asistencia,index=False)

            st.success("Registro eliminado")


# DESCARGAR EXCEL DEL DIA

    st.subheader("Descargar asistencia del día")

    hoy=str(datetime.now().date())

    asistencia_hoy=asistencia[
        asistencia["Fecha"].astype(str)==hoy
    ]

    archivo_descarga=f"asistencia_{hoy}.xlsx"

    asistencia_hoy.to_excel(archivo_descarga,index=False)

    with open(archivo_descarga,"rb") as file:

        st.download_button(
            "Descargar Excel del día",
            data=file,
            file_name=archivo_descarga
        )
