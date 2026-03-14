import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
import cv2

# CONFIGURACION APP (optimizado movil)
st.set_page_config(
    page_title="Asistencia QR",
    page_icon="📷",
    layout="wide"
)

# ESTILO OSCURO MODERNO
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

.stDataFrame{
background-color:#1e293b;
}

</style>
""", unsafe_allow_html=True)


# ARCHIVOS
archivo_estudiantes="estudiantes.xlsx"
archivo_asistencia="asistencia.xlsx"

st.title("📷 Sistema de Asistencia QR")


# MENU CON ICONOS
menu=st.sidebar.selectbox("Menú",
[
"👨‍🎓 Registrar estudiante",
"📋 Lista estudiantes",
"📷 Escanear QR",
"✍️ Registrar asistencia manual",
"📊 Ver asistencia"
])


# CREAR ARCHIVOS
if not os.path.exists(archivo_estudiantes):
    df=pd.DataFrame(columns=["RU","Nombre","Apellido","QR"])
    df.to_excel(archivo_estudiantes,index=False)

if not os.path.exists(archivo_asistencia):
    df=pd.DataFrame(columns=[
    "RU","Nombre","Apellido","Fecha","Hora","Estado","Actividad"
    ])
    df.to_excel(archivo_asistencia,index=False)


# -----------------------------
# REGISTRAR ESTUDIANTE
# -----------------------------
if menu=="👨‍🎓 Registrar estudiante":

    st.subheader("Registrar nuevo estudiante")

    ru=st.text_input("RU")
    nombre=st.text_input("Nombre")
    apellido=st.text_input("Apellidos")

    if st.button("Guardar estudiante"):

        df=pd.read_excel(archivo_estudiantes)

        if ru in df["RU"].astype(str).values:
            st.error("⚠️ Este RU ya existe")

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

            st.success("✅ Estudiante registrado")

            st.image(ruta_qr,width=220)

            # BOTON DESCARGAR QR
            with open(ruta_qr,"rb") as file:
                st.download_button(
                label="⬇ Descargar QR",
                data=file,
                file_name=f"QR_{ru}.png",
                mime="image/png"
                )


# -----------------------------
# LISTA ESTUDIANTES
# -----------------------------
elif menu=="📋 Lista estudiantes":

    st.subheader("Lista de estudiantes")

    df=pd.read_excel(archivo_estudiantes)

    st.dataframe(df,use_container_width=True)

    ru_ver=st.text_input("Ver QR por RU")

    if ru_ver!="":

        estudiante=df[df["RU"].astype(str)==ru_ver]

        if len(estudiante)>0:

            ruta=estudiante.iloc[0]["QR"]

            st.image(ruta,width=220)

            with open(ruta,"rb") as file:
                st.download_button(
                "⬇ Descargar QR",
                file,
                file_name=f"QR_{ru_ver}.png"
                )

        else:
            st.warning("RU no encontrado")


# -----------------------------
# ESCANEAR QR
# -----------------------------
elif menu=="📷 Escanear QR":

    st.subheader("Escanear código QR")

    actividad=st.text_input("Actividad (opcional)")

    if st.button("Activar cámara"):

        detector=cv2.QRCodeDetector()
        cap=cv2.VideoCapture(0)

        st.info("Escanea el QR del estudiante")

        frame_placeholder=st.empty()

        while True:

            ret,frame=cap.read()

            if not ret:
                st.error("No se pudo abrir la cámara")
                break

            data,bbox,_=detector.detectAndDecode(frame)

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
elif menu=="✍️ Registrar asistencia manual":

    st.subheader("Registro manual")

    estudiantes=pd.read_excel(archivo_estudiantes)

    if len(estudiantes)==0:
        st.warning("No hay estudiantes")

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
elif menu=="📊 Ver asistencia":

    st.subheader("Registros de asistencia")

    asistencia=pd.read_excel(archivo_asistencia)

    st.dataframe(asistencia,use_container_width=True)

    fecha=st.date_input("Filtrar por fecha")

    if fecha:

        filtro=asistencia[
        asistencia["Fecha"].astype(str)==str(fecha)
        ]

        st.write("Registros del día")

        st.dataframe(filtro,use_container_width=True)

    st.subheader("Resumen")

    st.bar_chart(asistencia["Estado"].value_counts())