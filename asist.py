import streamlit as st
import pandas as pd
import qrcode
from datetime import datetime
import os
from io import BytesIO

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


archivo_estudiantes="estudiantes.xlsx"
archivo_asistencia="asistencia.xlsx"

st.title("📷 Sistema de Asistencia QR")

menu=st.sidebar.selectbox("Menú",
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
if menu=="👨‍🎓 Registrar estudiante":

    st.subheader("Registrar estudiante")

    ru=st.text_input("RU")
    nombre=st.text_input("Nombre")
    apellido=st.text_input("Apellido")

    if st.button("Guardar estudiante"):

        df=pd.read_excel(archivo_estudiantes)

        if ru in df["RU"].astype(str).values:

            st.error("RU ya existe")

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

            with open(ruta_qr,"rb") as f:
                st.download_button(
                "⬇ Descargar QR",
                f,
                file_name=f"QR_{ru}.png"
                )


# LISTA ESTUDIANTES
elif menu=="📋 Lista estudiantes":

    df=pd.read_excel(archivo_estudiantes)

    st.dataframe(df,use_container_width=True)


# ESCANEAR QR CELULAR
elif menu=="📷 Escanear QR (Celular)":

    st.subheader("Escaneo QR con celular")

    actividad=st.text_input("Actividad (opcional)")

    qr_data=st.text_input("Escanear QR (pegar código)")

    if qr_data:

        ru=qr_data

        estudiantes=pd.read_excel(archivo_estudiantes)

        estudiante=estudiantes[estudiantes["RU"].astype(str)==ru]

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

                asistencia.to_excel(archivo_asistencia,index=False)

                st.success(f"Asistencia registrada: {nombre} {apellido}")

            else:

                st.warning("Ya registró asistencia hoy")

        else:

            st.error("Estudiante no encontrado")


# REGISTRO MANUAL
elif menu=="✍️ Registrar asistencia manual":

    estudiantes=pd.read_excel(archivo_estudiantes)

    estudiantes["nombre"]=estudiantes["RU"].astype(str)+" - "+estudiantes["Nombre"]

    seleccionado=st.selectbox("Estudiante",estudiantes["nombre"])

    ru=seleccionado.split(" - ")[0]

    estado=st.selectbox("Estado",["Presente","Tarde","Permiso","Ausente"])

    actividad=st.text_input("Actividad")

    if st.button("Registrar"):

        est=estudiantes[estudiantes["RU"].astype(str)==ru]

        nombre=est.iloc[0]["Nombre"]
        apellido=est.iloc[0]["Apellido"]

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

        st.success("Registrado")


# VER ASISTENCIA
elif menu=="📊 Ver asistencia":

    asistencia=pd.read_excel(archivo_asistencia)

    st.dataframe(asistencia,use_container_width=True)

    fecha=st.date_input("Filtrar por fecha")

    if fecha:

        filtro=asistencia[
        asistencia["Fecha"].astype(str)==str(fecha)
        ]

        st.dataframe(filtro)

        # DESCARGAR EXCEL DEL DIA
        output=BytesIO()

        with pd.ExcelWriter(output,engine='openpyxl') as writer:
            filtro.to_excel(writer,index=False)

        st.download_button(
        "⬇ Descargar Excel del día",
        output.getvalue(),
        file_name=f"asistencia_{fecha}.xlsx"
        )

    st.subheader("Resumen")

    st.bar_chart(asistencia["Estado"].value_counts())
