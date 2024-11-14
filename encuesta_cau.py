import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv
import re

# Detecta si estamos en Streamlit Cloud o localmente
env = os.getenv('GCP_ENV', 'local')


if env == 'local':
  load_dotenv()
  
# Cargar las credenciales desde variables de entorno
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

# Guardar temporalmente las credenciales para autenticar
with open("temp_credentials.json", "w") as f:
    json.dump(credentials_dict, f)


# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
client = gspread.authorize(credentials)

# Eliminar el archivo temporal de credenciales para mayor seguridad
os.remove("temp_credentials.json")

sheet = client.open(os.getenv("GCP_GOOGLE_SHEET_NAME")).sheet1

# Load questions from JSON file
with open("preguntas.json", "r") as file:
    survey_data = json.load(file)

# User registration validation
def validate_user(email):
    records = sheet.get_all_records()
    return not any(record["Email"] == email for record in records)

# Contar la cantidad total de preguntas en el JSON
total_questions = sum(len(section["questions"]) for section in survey_data["sections"])

# App UI and survey
st.title("CAU & Soporte Survey")
st.write("Please enter your information and complete each section of the survey.")

# User input for identification
name = st.text_input("Nombre")
email = st.text_input("Correo Electrónico")

# Verificación de correo antes de mostrar el formulario
if st.button("🔓 Acceder"):
    if name and email:
        if validate_user(email):
            st.success("👍 Gracias por apoyarnos, te pedimos que respondas todas las preguntas.")          
            # Mostrar formulario solo si el correo es válido
            with st.form("survey_form"):
                if "responses" not in st.session_state:
                    st.session_state["responses"] = {}

                # Display each section and question in form
                for section in survey_data["sections"]:
                    st.subheader(section["title"])
                    for question in section["questions"]:
                       # Extraer número de pregunta usando regex
                        question_number = re.match(r"(\d+)", question).group(1)
                        key = f"Pregunta {question_number}"  # Crear clave en el formato "Pregunta N"
                        st.session_state["responses"][key] = st.text_area(question, key=key)

                # Form submission button
                submit_button = st.form_submit_button("Enviar Encuesta")
                if submit_button:
                    # Collect and save the responses to Google Sheets
                    row = [name, email] + [st.session_state["responses"].get(f"Pregunta {i+1}", "") for i in range(total_questions)]
                    
                    st.write(row)
                    sheet.append_row(row)
                    st.success("🎉 Encuesta enviada con éxito. ¡Gracias!")
                    st.session_state["responses"].clear()  # Clear responses after submission
        else:
             st.success("Ya has completado la encuesta. 🙌 Gracias por tu participación.")
    else:
        st.warning("Por favor, completa ambos campos para validar tu correo.")
