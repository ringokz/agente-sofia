import os
import json
from datetime import datetime
import streamlit as st
from xhtml2pdf import pisa
import re
import emoji
import pytz
from google.cloud import storage
import tempfile
import uuid

# Configuración de la página
PRIMARY_COLOR = "#4b83c0"
SECONDARY_COLOR = "#878889"
BACKGROUND_COLOR = "#ffffff"  # White background
ICOMEX_LOGO_PATH = "logos/ICOMEX_Logos sin fondo.png"
SOFIA_AVATAR_PATH = "logos/sofia_avatar.png"

# Function to load instructions
def load_instructions(topic):
    INSTRUCTIONS_FILES = {
        "Oportunidades de Inversión": "instructions_inversiones.txt",
        "¡Quiero exportar!": "instructions_comercio_exterior.txt",
    }
    try:
        with open(INSTRUCTIONS_FILES[topic], "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"No se encontró el archivo de instrucciones para {topic}.")
        return None

# Clean message for PDF output
def clean_message(message_content):
    # Remove Markdown bold (**text** -> text)
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content)
    # Remove emojis
    message_content = emoji.replace_emoji(message_content, replace="")
    # Remove all "#" characters
    message_content = message_content.replace("#", "")
    # Replace line breaks with <br>
    message_content = message_content.replace("\n", "<br>")
    return message_content

# Generate PDF
def generate_pdf(html_content, output_path):
    with open(output_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            return False, pisa_status.err
    return True, None

# Botón para activar/desactivar la generación de audio
def toggle_audio_button():
    # Inicializar el estado si no existe
    if "audio_enabled" not in st.session_state:
        st.session_state.audio_enabled = False

    # Texto dinámico para el botón
    button_text = "Activar / Desactivar Audio"

    # Renderizar el botón
    if st.button(button_text):
        # Cambiar el estado al presionar el botón
        st.session_state.audio_enabled = not st.session_state.audio_enabled

    # Mostrar el estado actual
    status = "activado" if st.session_state.audio_enabled else "desactivado"
    st.write(f"Audio **{status}**.")

# Limpia un mensaje para asegurar que sea apto para texto a voz
def clean_message_for_audio(message_content):
    # Replace for pronunciation
    message_content = message_content.replace("$2.000.000.000","dos mil millones de pesos")
    message_content = message_content.replace("$300.000.000","trescientos millones de pesos")
    message_content = message_content.replace("$3.000.000.000","tres mil millones de pesos")
    message_content = message_content.replace("I-COMEX","ICÓMEX")
    message_content = message_content.replace("km","kilómetros")
    message_content = message_content.replace("1950", "mil novecientos cincuenta")
    message_content = message_content.replace("Pellegrini","Pelegrini")
    message_content = message_content.replace("2954575326", "dos nueve cinco cuatro, cincuenta y siete, cincuenta y tres, veintiseis.")
    message_content = message_content.replace("agencia@icomexlapampa.org","agencia, arroba, icomexlapampa, punto, org.")
    message_content = message_content.replace("08:00 a 15:00 hs","ocho a quince horas")
    message_content = message_content.replace("https://maps.app.goo.gl/RET62U9mK9JecpmT9","")
    # Remove Markdown bold (**text** -> text)
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content)
    # Remove emojis
    message_content = emoji.replace_emoji(message_content, replace="")
    # Remove all "#" characters
    message_content = message_content.replace("#", "")
    # Replace line breaks with spaces
    message_content = message_content.replace(":", "")
    return message_content

# Limpia un mensaje para asegurar que sea apto para texto a voz
def clean_message(message_content):
    # Remove Markdown bold (**text** -> text)
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content)
    # Remove emojis
    message_content = emoji.replace_emoji(message_content, replace="")
    # Remove all "#" characters
    message_content = message_content.replace("#", "")
    return message_content

# Save conversation form
# def save_conversation_form():
#     with st.sidebar.form("guardar_conversacion"):
#         st.write("Complete el formulario (se enviará esta conversación a su correo):")
#         name = st.text_input("Nombre")
#         last_name = st.text_input("Apellido")
#         email = st.text_input("Correo electrónico")
#         submitted = st.form_submit_button("Guardar y programar envío")

#         if submitted:
#             if name and last_name and email:
#                 # Filter messages
#                 filtered_messages = [
#                     msg for msg in st.session_state.messages if msg["role"] != "system"
#                 ]
#                 # Create data to save
#                 conversation_data = {
#                     "name": name,
#                     "last_name": last_name,
#                     "email": email,
#                     "topic": st.session_state.selected_topic,
#                     "messages": filtered_messages,
#                 }
#                 # Create folder if not exists
#                 folder = "./conversaciones/comercio_exterior" if st.session_state.selected_topic == "¡Quiero exportar!" else "./conversaciones/inversiones"
#                 os.makedirs(folder, exist_ok=True)

#                 # Create file name with date and time
#                 argentina_time = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires'))
#                 date_str = argentina_time.strftime("%Y%m%d%H%M")
#                 filename = f"{date_str}_{last_name.upper()}_{name.upper()}"
#                 json_filepath = os.path.join(folder, f"{filename}.json")
#                 pdf_filepath = os.path.join(folder, f"{filename}.pdf")

#                 # Save JSON file
#                 with open(json_filepath, "w", encoding="utf-8") as f:
#                     json.dump(conversation_data, f, ensure_ascii=False, indent=4)

#                 # Create HTML content for PDF
#                 html_content = f"""
#                 <html>
#                 <head>
#                     <style>
#                         body {{
#                             font-family: Arial, sans-serif;
#                             line-height: 1.6;
#                             background-color: {BACKGROUND_COLOR};
#                             margin: 0;
#                             padding: 0;
#                             font-size: 120%;
#                         }}

#                         .logos-container {{
#                             width: 100%;
#                             text-align: center;
#                             margin: 20px 0;
#                         }}
#                         .logos-container table {{
#                             margin: 0 auto; /* Center the table horizontally */
#                             border-collapse: collapse;
#                         }}
#                         .logos-container img {{
#                             height: 60px; /* Fixed height */
#                             max-width: 150px; /* Restrict width to avoid stretching */
#                             margin: 0 10px; /* Spacing between logos */
#                             object-fit: contain; /* Maintain aspect ratio */
#                         }}
    
#                         .title-container h1 {{
#                             color: {PRIMARY_COLOR};
#                             font-size: 1.2rem; /* Tamaño de fuente más pequeño */
#                             margin-top: 20px;
#                             margin-bottom: 20px;
#                             font-weight: bold;
#                         }}
                       
#                         .title-container {{
#                             text-align: center;
#                             color: {PRIMARY_COLOR};
#                             font-size: 1.5rem;
#                             margin-top: 20px;
#                             margin-bottom: 20px;
#                             font-weight: bold;
#                         }}
#                         .content {{
#                             margin: 20px;
#                         }}
#                         .user {{
#                             color: {SECONDARY_COLOR};
#                             font-weight: bold;
#                         }}
#                         .assistant {{
#                             color: {PRIMARY_COLOR};
#                             font-weight: bold;
#                         }}
#                         .message {{
#                             margin-bottom: 1em;
#                         }}
#                     </style>
#                 </head>
#                 <body>
#                     <div class="logos-container">
#                         <table>
#                             <tr>
#                                 <td style="text-align: center; padding-left: 10px; padding-right: 10px;">
#                                     <img src="{SOFIA_AVATAR_PATH}" alt="SofIA Logo">
#                                     <img src="{ICOMEX_LOGO_PATH}" alt="ICOMEX Logo">
#                                 </td>
#                             </tr>
#                         </table>
#                     </div>
#                     <div class="title-container">
#                         <h1>{st.session_state.selected_topic}</h1>
#                         <h1>Conversación de {name.title()} con SofIA</h1>
#                     </div>
#                     <div class="content">
#                         <p><b>Nombre completo:</b> {name.title()} {last_name.title()}</p>
#                         <p><b>Correo:</b> {email}</p>
#                         <p><b>Fecha:</b> {argentina_time.strftime("%H:%M hs %d/%m/%Y")}</p>
#                         <h2>Mensajes</h2>
#                 """
#                 for msg in filtered_messages:
#                     role = name.title() if msg["role"] == "user" else "SofIA"
#                     color_class = "user" if msg["role"] == "user" else "assistant"
#                     html_content += f"<div class='message {color_class}'><b>{role}:</b> {clean_message(msg['content'])}</div>"

#                 html_content += "</div></body></html>"

#                 # Save PDF file
#                 success, error = generate_pdf(html_content, pdf_filepath)
#                 if success:
#                     st.success("El envío de esta conversación se ha programado correctamente.")
#                 else:
#                     st.error("La conversación no se ha guardado, por favor solicite ayuda al personal de I-COMEX.")

#                 st.session_state.show_form = False
#             else:
#                 st.error("Por favor complete todos los campos.")

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""

    try:
        # Load credentials from Streamlit secrets
        credentials = storage.Client.from_service_account_info(st.secrets["connections.gcs"])

        # Get the bucket and blob
        bucket = credentials.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # Upload the file
        blob.upload_from_filename(source_file_name)

    except Exception as e:
        st.error(f"Ha surgido un error en el guardado de la conversación: {e}")


def save_conversation_form():
    with st.sidebar.form("guardar_conversacion"):
        st.write("Complete el formulario (se enviará esta conversación a su correo):")
        name = st.text_input("Nombre")
        last_name = st.text_input("Apellido")
        email = st.text_input("Correo electrónico")
        submitted = st.form_submit_button("Guardar y programar envío")

        if submitted:
            if name and last_name and email:
                try:
                    # Get a valid temporary folder for the current OS
                    temp_base = tempfile.gettempdir()
                    folder = "conversaciones/comercio_exterior" if st.session_state.selected_topic == "¡Quiero exportar!" else "conversaciones/inversiones"
                    temp_folder = os.path.join(temp_base, folder)

                    # Ensure the temporary directory exists
                    os.makedirs(temp_folder, exist_ok=True)

                    # Filter messages
                    filtered_messages = [
                        msg for msg in st.session_state.messages if msg["role"] != "system"
                    ]

                    # Prepare data for JSON
                    conversation_data = {
                        "name": name,
                        "last_name": last_name,
                        "email": email,
                        "topic": st.session_state.selected_topic,
                        "messages": filtered_messages,
                    }

                    # Create a timestamped filename
                    argentina_time = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires'))
                    date_str = argentina_time.strftime("%Y%m%d%H%M")
                    filename_base = f"{date_str}_{last_name.upper()}_{name.upper()}"

                    # Local paths for JSON and PDF
                    json_path = os.path.join(temp_folder, f"{filename_base}.json")
                    pdf_path = os.path.join(temp_folder, f"{filename_base}.pdf")

                    # Save JSON locally
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(conversation_data, f, ensure_ascii=False, indent=4)

                    # Create HTML content for PDF with original format
                    html_content = f"""
                    <html>
                    <head>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                line-height: 1.6;
                                background-color: {BACKGROUND_COLOR};
                                margin: 0;
                                padding: 0;
                                font-size: 120%;
                            }}
                            .logos-container {{
                                width: 100%;
                                text-align: center;
                                margin: 20px 0;
                            }}
                            .logos-container table {{
                                margin: 0 auto;
                                border-collapse: collapse;
                            }}
                            .logos-container img {{
                                height: 60px;
                                max-width: 150px;
                                margin: 0 10px;
                                object-fit: contain;
                            }}
                            .title-container h1 {{
                                color: {PRIMARY_COLOR};
                                font-size: 1.2rem;
                                margin-top: 20px;
                                margin-bottom: 20px;
                                font-weight: bold;
                            }}
                            .title-container {{
                                text-align: center;
                                color: {PRIMARY_COLOR};
                                font-size: 1.5rem;
                                margin-top: 20px;
                                margin-bottom: 20px;
                                font-weight: bold;
                            }}
                            .content {{
                                margin: 20px;
                            }}
                            .user {{
                                color: {SECONDARY_COLOR};
                                font-weight: bold;
                            }}
                            .assistant {{
                                color: {PRIMARY_COLOR};
                                font-weight: bold;
                            }}
                            .message {{
                                margin-bottom: 1em;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="logos-container">
                            <table>
                                <tr>
                                    <td style="text-align: center; padding-left: 10px; padding-right: 10px;">
                                        <img src="{SOFIA_AVATAR_PATH}" alt="SofIA Logo">
                                        <img src="{ICOMEX_LOGO_PATH}" alt="ICOMEX Logo">
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <div class="title-container">
                            <h1>{st.session_state.selected_topic}</h1>
                            <h1>Conversación de {name.title()} con SofIA</h1>
                        </div>
                        <div class="content">
                            <p><b>Nombre completo:</b> {name.title()} {last_name.title()}</p>
                            <p><b>Correo:</b> {email}</p>
                            <p><b>Fecha:</b> {argentina_time.strftime("%H:%M hs %d/%m/%Y")}</p>
                            <h2>Mensajes</h2>
                    """
                    for msg in filtered_messages:
                        role = name.title() if msg["role"] == "user" else "SofIA"
                        color_class = "user" if msg["role"] == "user" else "assistant"
                        html_content += f"<div class='message {color_class}'><b>{role}:</b> {clean_message(msg['content'])}</div>"

                    html_content += "</div></body></html>"

                    # Save PDF locally
                    success, error = generate_pdf(html_content, pdf_path)

                    if success:
                        # Upload files to GCS
                        upload_to_gcs("sofia-asesora-virtual", json_path, f"{folder}/{filename_base}.json")
                        upload_to_gcs("sofia-asesora-virtual", pdf_path, f"{folder}/{filename_base}.pdf")
                        st.success("El envío de esta conversación se ha programado correctamente.")
                    else:
                        st.error("La conversación no se ha guardado. Por favor, intente nuevamente.")
                except Exception as e:
                    st.error(f"Se produjo un error: {e}")
            else:
                st.error("Por favor complete todos los campos.")

def auto_save_conversation():
    """Automatically save the current conversation to GCS in auto-saved folder."""
    try:
        # Filtrar mensajes
        filtered_messages = [
            msg for msg in st.session_state.messages if msg["role"] != "system"
        ]

        # Preparar datos para guardar en JSON
        conversation_data = {
            "topic": st.session_state.selected_topic,
            "messages": filtered_messages,
        }

        # Crear un nombre de archivo único
        session_id = st.session_state.get("session_id", str(uuid.uuid4()))  # Genera un nuevo UUID en caso de fallback
        gcs_file_name = f"auto-saved/conversation_{session_id}.json"

        # Guardar el archivo temporalmente
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(temp_file.name, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=4)

        # Subir a GCS
        upload_to_gcs(
            bucket_name="sofia-asesora-virtual",
            source_file_name=temp_file.name,
            destination_blob_name=f"conversaciones/{gcs_file_name}",
        )

        # Confirmación de guardado
        st.session_state.auto_saved = True

    except Exception as e:
        st.error(f"Error al guardar automáticamente la conversación: {e}")
