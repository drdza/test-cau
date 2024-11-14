import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv
import re

# Cargar las credenciales y configuración
env = os.getenv('GCP_ENV', 'local')
if env == 'local':
    load_dotenv()

credentials_dict = {
    "type": os.getenv("GCP_TYPE"),
    "project_id": os.getenv("GCP_PROJECT_ID"),
    "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GCP_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GCP_CLIENT_EMAIL"),
    "client_id": os.getenv("GCP_CLIENT_ID"),
    "auth_uri": os.getenv("GCP_AUTH_URI"),
    "token_uri": os.getenv("GCP_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("GCP_CLIENT_CERT_URL")
}

# Guardar credenciales temporalmente para la autenticación
with open("temp_credentials.json", "w") as f:
    json.dump(credentials_dict, f)

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

try:
    credentials = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
    client = gspread.authorize(credentials)
    st.write("✅ Conexión exitosa con Google Sheets.")
except Exception as e:
    st.error(f"Error en la autenticación con Google Sheets: {e}")
    st.stop()

# Eliminar archivo de credenciales temporal para seguridad
os.remove("temp_credentials.json")

# Intentar abrir la hoja de Google
try:
    sheet_name = os.getenv("GCP_GOOGLE_SHEET_NAME")
    sheet = client.open(sheet_name).sheet1
    st.write("✅ Hoja de Google abierta correctamente.")
except Exception as e:
    st.error(f"Error al abrir la hoja de Google: {e}")
    st.stop()

# Cargar preguntas desde archivo JSON
try:
    with open("preguntas.json", "r") as file:
        survey_data = json.load(file)
except FileNotFoundError:
    st.error("No se encontró el archivo questions.json")
    st.stop()

# Validar usuario (email único)
def validate_user(email):
    try:
        records = sheet.get_all_records()
        return not any(record["Email"] == email for record in records)
    except Exception as e:
        st.error(f"Error al validar el usuario: {e}")
        return False

# Contar preguntas en el JSON
total_questions = sum(len(section["questions"]) for section in survey_data["sections"])

# Asegurar inicialización de session state
if "form_submitted" not in st.session_state:
    st.session_state["form_submitted"] = False
if "row" not in st.session_state:
    st.session_state["row"] = []
if "responses" not in st.session_state:
    st.session_state["responses"] = {}

# Interfaz de la encuesta
st.title("CAU & Soporte Survey")
st.write("Please enter your information and complete each section of the survey.")

# Entrada de usuario
name = st.text_input("Nombre", value=st.session_state.get("name", ""))
email = st.text_input("Correo Electrónico", value=st.session_state.get("email", ""))

# Guardar en `session_state`
if name:
    st.session_state["name"] = name
if email:
    st.session_state["email"] = email

# Verificación de correo y visualización de preguntas
if st.button("🔓 Acceder") and name and email:
    if validate_user(email):
        st.success("👍 Gracias por apoyarnos, te pedimos que respondas todas las preguntas.")
        
        # Mostrar cada sección y pregunta sin `st.form`
        for section in survey_data["sections"]:
            st.subheader(section["title"])
            for question in section["questions"]:
                question_number = re.match(r"(\d+)", question).group(1)
                key = f"Pregunta {question_number}"
                st.session_state["responses"][key] = st.text_area(question, key=key)

        # Generar fila de datos y mostrar para revisión
        st.session_state["row"] = [st.session_state["name"], st.session_state["email"]] + \
                                  [st.session_state["responses"].get(f"Pregunta {i+1}", "") for i in range(total_questions)]
        
        st.write("Datos a insertar:", st.session_state["row"])

# Botón para confirmar el envío
if st.button("Enviar Encuesta") and st.session_state["row"]:
    try:
        sheet.append_row(st.session_state["row"])
        st.success("🎉 Encuesta enviada con éxito. ¡Gracias!")
        st.session_state["form_submitted"] = True
    except Exception as e:
        st.error(f"Error al insertar datos en Google Sheets: {e}")

# Mensaje de confirmación si la encuesta ya fue enviada
if st.session_state["form_submitted"]:
    st.info("Gracias por enviar la encuesta. No puedes enviar otra respuesta.")
