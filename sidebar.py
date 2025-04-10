# sidebar.py
import os
import re
import json
from datetime import datetime
import streamlit as st
from xhtml2pdf import pisa
import emoji
import pytz
import tempfile
import uuid
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import certifi
from pymongo.server_api import ServerApi
import gridfs
import base64 # <--- Importar base64 para codificar imágenes

# --- Funciones existentes (sin cambios, excepto restauración) ---

def upload_to_mongodb(data):
    """Sube datos a MongoDB Atlas, usando ServerApi y tlsCAFile (sin ssl_context)."""
    # (Código original sin cambios)
    try:
        uri = st.secrets["mongodb"]["uri"]
        db_name = st.secrets["mongodb"]["db_name"]
        collection_name = st.secrets["mongodb"]["collection_name"] # Colección para auto-guardado

        server_api = ServerApi('1')
        client = MongoClient(
            uri,
            server_api=server_api,
            ssl=True,
            tlsCAFile=certifi.where()
        )
        client.admin.command('ping')
        db = client[db_name]
        collection = db[collection_name]
        collection.insert_one(data)
        client.close()
        return True
    except ConnectionFailure as e:
        st.error(f"Error de conexión con MongoDB (Auto-guardado): {e}")
        return False
    except TypeError as e:
        st.error(f"Error de configuración de MongoClient (Auto-guardado - TypeError): {e}")
        return False
    except Exception as e:
        st.error(f"Error general al operar con MongoDB (Auto-guardado): {e}")
        return False

# Configuración de la página (sin cambios)
PRIMARY_COLOR = "#4b83c0"
SECONDARY_COLOR = "#878889"
BACKGROUND_COLOR = "#ffffff"
ICOMEX_LOGO_PATH = "logos/ICOMEX_Logos sin fondo.png"
SOFIA_AVATAR_PATH = "logos/sofia_avatar.png"

# Función para cargar instrucciones (sin cambios)
def load_instructions(topic):
    INSTRUCTIONS_FILES = {
        "Oportunidades de Inversión": "instructions_inversiones.txt",
        "¡Quiero exportar!": "instructions_comercio_exterior.txt",
    }
    try:
        # Usar ruta absoluta relativa al script actual para mayor robustez
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, INSTRUCTIONS_FILES[topic])
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"No se encontró el archivo de instrucciones: {file_path}")
        return None
    except KeyError:
         st.error(f"Tema de instrucciones no válido: {topic}")
         return None
    except Exception as e:
        st.error(f"Error al leer instrucciones para {topic}: {e}")
        return None

# Limpia el mensaje para salida en PDF (sin cambios)
def clean_message(message_content):
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content)
    message_content = emoji.replace_emoji(message_content, replace="")
    message_content = message_content.replace("#", "")
    message_content = message_content.replace("\n", "<br>")
    return message_content

# Genera PDF a partir de HTML (sin cambios respecto a la versión anterior)
def generate_pdf(html_content, output_path):
    """Genera PDF a partir de HTML, especificando UTF-8."""
    try:
        with open(output_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file, encoding='UTF-8')
        if pisa_status.err:
            return False, f"Error de pisa ({pisa_status.err})"
        return True, None
    except FileNotFoundError:
        return False, f"Error: No se pudo crear/escribir el archivo PDF en '{output_path}'."
    except Exception as e:
        return False, f"Excepción al generar PDF: {e}"

# Botón para activar/desactivar la generación de audio (sin cambios)
def toggle_audio_button():
    if "audio_enabled" not in st.session_state:
        st.session_state.audio_enabled = False # Inicializar si no existe

    # button_text = "Activar / Desactivar Audio"
    # if st.button(button_text):
    #     st.session_state.audio_enabled = not st.session_state.audio_enabled

    # status = "activado" if st.session_state.get("audio_enabled", False) else "desactivado" # Usar .get con default
    # st.write(f"Audio **{status}**.")

# Limpia un mensaje para que sea apto para texto a voz (RESTAURADA)
def clean_message_for_audio(message_content):
    """Limpia el mensaje para mejorar la pronunciación del TTS."""
    # (Código original restaurado)
    message_content = message_content.replace("$2.000.000.000", "dos mil millones de pesos")
    message_content = message_content.replace("$300.000.000", "trescientos millones de pesos")
    message_content = message_content.replace("$3.000.000.000", "tres mil millones de pesos")
    message_content = message_content.replace("I-COMEX", "ICÓMEX")
    message_content = message_content.replace("km", "kilómetros")
    message_content = message_content.replace("1950", "mil novecientos cincuenta")
    message_content = message_content.replace("Pellegrini", "Pelegrini") # Corrección fonética
    message_content = message_content.replace("2954575326", "dos nueve cinco cuatro, cincuenta y siete, cincuenta y tres, veintiseis.")
    message_content = message_content.replace("agencia@icomexlapampa.org", "agencia, arroba, icomexlapampa, punto, org.")
    message_content = message_content.replace("08:00 a 15:00 hs", "ocho a quince horas")
    # Eliminar URLs que no aportan a la pronunciación
    message_content = message_content.replace("https://maps.app.goo.gl/RET62U9mK9JecpmT9", "")
    # Limpieza general similar a clean_message pero sin convertir \n a <br>
    message_content = re.sub(r"\*\*(.*?)\*\*", r"\1", message_content) # Quitar negritas
    message_content = emoji.replace_emoji(message_content, replace="") # Quitar emojis
    message_content = message_content.replace("#", "") # Quitar numerales
    message_content = message_content.replace(":", "") # Quitar dos puntos (pueden pausar TTS)
    # Reemplazar saltos de línea con espacio o punto para flujo de audio
    message_content = message_content.replace("\n", ". ")
    return message_content

# --- Nueva Función Auxiliar para Base64 ---
def image_to_base64(image_path):
    """Lee una imagen y la convierte a una cadena Base64 para embeber en HTML."""
    try:
        # Construir ruta absoluta relativa al script actual
        script_dir = os.path.dirname(__file__)
        abs_image_path = os.path.join(script_dir, image_path)

        if not os.path.exists(abs_image_path):
             st.warning(f"Archivo de imagen no encontrado: {abs_image_path}")
             print(f"DEBUG: No se encontró la imagen en {abs_image_path}") # Log para consola
             return "" # Retornar cadena vacía si no existe

        # Leer archivo en modo binario, codificar y decodificar a string utf-8
        with open(abs_image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Error al convertir imagen a Base64 ({image_path}): {e}")
        print(f"DEBUG: Error Base64 para {image_path}: {e}") # Log para consola
        return "" # Retornar cadena vacía en caso de error

# --- Función save_conversation_form (MODIFICADA para usar Base64) ---
def save_conversation_form():
    """
    Muestra un formulario en la barra lateral para guardar la conversación como PDF en MongoDB.
    Usa Base64 para incrustar logos en el PDF.
    """
    with st.sidebar.form("guardar_conversacion_pdf_form"):
        st.write("Complete el formulario para enviar la conversación:")
        name = st.text_input("Nombre")
        last_name = st.text_input("Apellido")
        email = st.text_input("Correo electrónico")
        submitted = st.form_submit_button("Enviar conversación")

        if submitted:
            if name and last_name and email:
                client = None
                pdf_file_generated = False
                pdf_temp_path = None

                try:
                    # --- 1. Conexión a MongoDB (Sin cambios) ---
                    #st.info("Conectando a la base de datos...")
                    uri = st.secrets["mongodb"]["uri"]
                    db_name = st.secrets["mongodb"]["db_name"]
                    metadata_collection_name = st.secrets["mongodb"]["pdf_metadata_collection"]
                    gfs_prefix = st.secrets["mongodb"]["gridfs_prefix"]
                    server_api = ServerApi('1')
                    client = MongoClient(uri, server_api=server_api, ssl=True, tlsCAFile=certifi.where())
                    client.admin.command('ping')
                    db = client[db_name]
                    fs = gridfs.GridFS(db, collection=gfs_prefix)
                    #st.info("Conexión exitosa.")

                    # --- 2. Preparación de Datos y Nombres de Archivo (Sin cambios) ---
                    temp_base = tempfile.gettempdir()
                    session_id_part = st.session_state.get("session_id", str(uuid.uuid4()))
                    session_temp_folder = os.path.join(temp_base, f"conv_pdf_{session_id_part}")
                    os.makedirs(session_temp_folder, exist_ok=True)
                    filtered_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
                    current_timestamp = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires'))
                    metadata_to_save = {
                        "name": name, "last_name": last_name, "email": email,
                        "topic": st.session_state.selected_topic,
                        "session_id": st.session_state.get("session_id", "unknown_session"),
                        "timestamp": current_timestamp.isoformat(), "form_submitted": True,
                        "messages": filtered_messages, "pdf_gridfs_id": None
                    }
                    date_str = current_timestamp.strftime("%Y%m%d%H%M")
                    safe_last_name = re.sub(r'\W+', '', last_name.upper())
                    safe_name = re.sub(r'\W+', '', name.upper())
                    filename_base = f"{date_str}_{safe_last_name}_{safe_name}"
                    pdf_filename_for_storage = f"{filename_base}.pdf"
                    pdf_temp_path = os.path.join(session_temp_folder, pdf_filename_for_storage)

                    # --- 3. Generación de HTML para el PDF (Usando Base64 para logos) ---
                    #st.info("Preparando contenido del PDF...")
                    # Convertir logos a Base64 ANTES de generar el HTML
                    sofia_logo_b64 = image_to_base64(SOFIA_AVATAR_PATH)
                    icomex_logo_b64 = image_to_base64(ICOMEX_LOGO_PATH)

                    # Verificar si se obtuvieron las cadenas base64
                    if not sofia_logo_b64:
                        st.warning("No se pudo cargar el logo de SofIA para el PDF.")
                    if not icomex_logo_b64:
                        st.warning("No se pudo cargar el logo de ICOMEX para el PDF.")

                    html_parts = []
                    # **Inicio del HTML con CSS (CSS sin cambios respecto a la última versión)**
                    html_parts.append(f"""<!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            /* Estilos CSS (los mismos que la versión anterior, sin object-fit ni calc) */
                            @page {{ margin: 2cm; }}
                            body {{ font-family: Arial, sans-serif; line-height: 1.4; background-color: {BACKGROUND_COLOR}; margin: 0; padding: 0; font-size: 10pt; color: #333;}}
                            .logos-container {{ width: 100%; text-align: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;}}
                            .logos-container table {{ margin: 0 auto; border-collapse: collapse; }}
                            /* Estilo para imágenes (sin object-fit) */
                            .logos-container img {{ vertical-align: middle; height: 45px; max-width: 120px; margin: 0 8px; }}
                            .title-container {{ text-align: center; margin-bottom: 20px; }}
                            .title-container h1 {{ color: {PRIMARY_COLOR}; font-size: 14pt; margin: 5px 0; font-weight: bold; }}
                            .content {{ margin: 0; padding: 0; }}
                            .info p {{ margin: 2px 0; font-size: 9pt; }}
                            .messages h2 {{ font-size: 12pt; color: {PRIMARY_COLOR}; border-bottom: 1px solid #eee; padding-bottom: 3px; margin-top: 15px; margin-bottom: 10px;}}
                            .user b {{ color: {SECONDARY_COLOR}; }}
                            .assistant b {{ color: {PRIMARY_COLOR}; }}
                            .message {{ margin-bottom: 0.8em; padding-left: 5px; border-left: 2px solid #eee;}}
                            .message.user {{ border-left-color: {SECONDARY_COLOR}; }}
                            .message.assistant {{ border-left-color: {PRIMARY_COLOR}; }}
                            .message b {{ display: inline-block; width: 80px; font-weight: bold; vertical-align: top; padding-right: 5px;}}
                            /* Div del mensaje (sin calc) */
                            .message div {{ display: inline-block; width: auto; vertical-align: top; word-wrap: break-word; }}
                        </style>
                    </head>
                    <body>
                        <div class="logos-container">
                            <table>
                                <tr>
                                    <td style="text-align: center;">
                                        <img src="data:image/png;base64,{sofia_logo_b64}" alt="SofIA Logo">
                                        <img src="data:image/png;base64,{icomex_logo_b64}" alt="ICOMEX Logo">
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <div class="title-container">
                            <h1>{st.session_state.selected_topic}</h1>
                            <h1>Conversación de {name.title()} con SofIA</h1>
                        </div>
                        <div class="content">
                            <div class="info">
                                <p><b>Nombre:</b> {name.title()} {last_name.title()}</p>
                                <p><b>Correo:</b> {email}</p>
                                <p><b>Fecha:</b> {current_timestamp.strftime("%d/%m/%Y %H:%M")} hs</p>
                            </div>
                            <div class="messages">
                                <h2>Mensajes</h2>
                    """) # Fin cabecera

                    # **Bucle de Mensajes (sin cambios)**
                    for msg in filtered_messages:
                        role_display_name = name.title() if msg["role"] == "user" else "SofIA"
                        role_class = msg["role"]
                        cleaned_content = clean_message(msg['content'])
                        html_parts.append(f"<div class='message {role_class}'><b>{role_display_name}:</b> <div>{cleaned_content}</div></div>")

                    # **Cierre HTML (sin cambios)**
                    html_parts.append("</div></div></body></html>")
                    html_content = "\n".join(html_parts)

                    # --- 4. Generar el Archivo PDF (Sin cambios) ---
                    #st.info("Generando archivo PDF...")
                    pdf_success, pdf_error = generate_pdf(html_content, pdf_temp_path)

                    if not pdf_success:
                        st.error(f"Error crítico al generar el archivo PDF: {pdf_error}")
                        if pdf_temp_path and os.path.exists(pdf_temp_path):
                            try: os.remove(pdf_temp_path)
                            except Exception: pass
                        return
                    else:
                        pdf_file_generated = True
                        #st.info("Archivo PDF generado.")

                        # --- 5. Guardar el PDF en MongoDB GridFS (Sin cambios) ---
                        file_id = None
                        try:
                            #st.info("Subiendo PDF a la base de datos...")
                            with open(pdf_temp_path, "rb") as pdf_file_to_upload:
                                file_id = fs.put(
                                    pdf_file_to_upload, filename=pdf_filename_for_storage, contentType="application/pdf",
                                    email=email, topic=st.session_state.selected_topic,
                                    session_id=st.session_state.get("session_id", "unknown_session"),
                                    submitter_name=f"{name} {last_name}"
                                )
                            #st.info("Archivo PDF guardado en Base de Datos.")
                        except Exception as gfs_error:
                            st.error(f"Error al guardar el archivo PDF en MongoDB GridFS: {gfs_error}")
                            return

                        # --- 6. Guardar Metadatos (Sin cambios) ---
                        if file_id:
                            try:
                                #st.info("Guardando información del formulario...")
                                metadata_to_save["pdf_gridfs_id"] = file_id
                                metadata_collection = db[metadata_collection_name]
                                insert_result = metadata_collection.insert_one(metadata_to_save)
                                st.success(f"¡Conversación guardada exitosamente!")
                                st.session_state.show_form = False
                            except Exception as meta_error:
                                st.error(f"Error al guardar metadatos en MongoDB: {meta_error}")
                                try:
                                    fs.delete(file_id)
                                    st.warning("IMPORTANTE: Se revirtió la subida del PDF porque falló el guardado de metadatos.")
                                except Exception as delete_err:
                                    st.error(f"ERROR CRÍTICO: Falló el guardado de metadatos Y no se pudo eliminar el PDF de GridFS ({delete_err}). Por favor, contacte soporte.")
                        else:
                            st.warning("No se guardaron metadatos porque no se obtuvo un ID válido del archivo PDF en GridFS.")

                # --- Manejo de Errores Generales (Sin cambios) ---
                except ConnectionFailure as e:
                    st.error(f"Error de conexión con MongoDB: {e}")
                except Exception as e:
                    st.error(f"Se produjo un error inesperado durante el proceso de guardado: {e}")
                    # import traceback
                    # st.error(traceback.format_exc())

                # --- Bloque Finally (Sin cambios) ---
                finally:
                    if client:
                        client.close()
                    if pdf_file_generated and pdf_temp_path and os.path.exists(pdf_temp_path):
                        try:
                            os.remove(pdf_temp_path)
                        except Exception as clean_err:
                            st.warning(f"No se pudo eliminar el archivo PDF temporal ({pdf_temp_path}): {clean_err}")

            else: # Campos incompletos
                st.error("Por favor complete todos los campos del formulario.")

# --- Función de Auto-Guardado (sin cambios) ---
def auto_save_conversation():
    """Guarda automáticamente la conversación en MongoDB."""
    # (Código original sin cambios)
    if not st.session_state.get("messages") or not st.session_state.get("selected_topic"):
        return
    # if st.session_state.get("auto_saved", False): # Comentado para guardar siempre
    #    return

    try:
        filtered_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        # Modificado para verificar si hay mensajes de usuario o asistente específicamente
        if not any(msg["role"] in ["user", "assistant"] for msg in filtered_messages):
            return

        conversation_data = {
            "session_id": st.session_state.get("session_id", "unknown_session"),
            "topic": st.session_state.selected_topic,
            "messages": filtered_messages,
            "auto_saved": True,
            "timestamp": datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).isoformat()
        }
        success = upload_to_mongodb(conversation_data)
        # No es necesario marcar auto_saved en session_state si queremos que guarde siempre
        # if success:
        #    st.session_state.auto_saved = True
        # else:
        #    st.session_state.auto_saved = False
    except Exception as e:
        print(f"DEBUG: Error inesperado durante el guardado automático: {e}") # Log discreto
        # st.session_state.auto_saved = False # No marcar estado si queremos reintentar implícitamente

