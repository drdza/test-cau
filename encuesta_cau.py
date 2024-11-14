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
except Exception as e:
    st.error(f"Error en la autenticación con Google Sheets: {e}")
    st.stop()

# Eliminar archivo de credenciales temporal para seguridad
os.remove("temp_credentials.json")

# Intentar abrir la hoja de Google
try:
    sheet_name = os.getenv("GCP_GOOGLE_SHEET_NAME")
    sheet = client.open(sheet_name).sheet1
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

# Estado inicial para seguimiento de envío
if "form_submitted" not in st.session_state:
    st.session_state["form_submitted"] = False

# Interfaz de la encuesta
st.title("CAU & Soporte Survey")
st.write("Please enter your information and complete each section of the survey.")

# Entrada de usuario
name = st.text_input("Nombre")
email = st.text_input("Correo Electrónico")

# Verificación de correo
if st.button("🔓 Acceder"):
    if name and email:
        if validate_user(email):
            st.success("👍 Gracias por apoyarnos, te pedimos que respondas todas las preguntas.")
            with st.form("survey_form"):
                if "responses" not in st.session_state:
                    st.session_state["responses"] = {}

                # Mostrar cada sección y pregunta
                for section in survey_data["sections"]:
                    st.subheader(section["title"])
                    for question in section["questions"]:
                        question_number = re.match(r"(\d+)", question).group(1)
                        key = f"Pregunta {question_number}"
                        st.session_state["responses"][key] = st.text_area(question, key=key)

                # Botón para enviar el formulario
                submit_button = st.form_submit_button("Enviar Encuesta")

                # Procesar envío del formulario
                if submit_button and not st.session_state["form_submitted"]:
                    # Crear `row` y almacenar en `session_state`
                    st.session_state["row"] = [name, email] + [st.session_state["responses"].get(f"Pregunta {i+1}", "") for i in range(total_questions)]
                    
                    # Mostrar `row` para depuración
                    st.write("Datos a insertar:", st.session_state["row"])

                    # Confirmar envío
                    if st.button("Confirmar Envío"):
                        try:
                            sheet.append_row(st.session_state["row"])
                            st.success("🎉 Encuesta enviada con éxito. ¡Gracias!")
                            st.session_state["form_submitted"] = True
                        except Exception as e:
                            st.error(f"Error al insertar datos: {e}")
        else:
            st.success("Ya has completado la encuesta. 🙌 Gracias por tu participación.")
    else:
        st.warning("Por favor, completa ambos campos para validar tu correo.")

