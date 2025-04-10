# download_pdf_script.py
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi
import gridfs
import certifi
# Para buscar por _id, necesitarías: from bson.objectid import ObjectId

# --- Configuración ---
# Reemplaza con tus valores reales o carga desde un archivo de configuración/secretos
MONGO_URI = "mongodb+srv://ringo:KDJs1yHWG8zUtblB@cluster0.xo1lsx7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" # Tu URI de conexión
DB_NAME = "asesora_sofia" # El nombre de tu base de datos
GRIDFS_PREFIX = "pdfs" # El prefijo usado para las colecciones GridFS

# --- Archivo a Descargar ---
# Nombre exacto del archivo PDF que quieres descargar (actualizado)
FILENAME_TO_DOWNLOAD = "202504092116_HARMELO_SASHA.pdf" # <--- ACTUALIZADO

# --- Nombre del Archivo Local ---
# Dónde guardar el archivo descargado (actualizado)
LOCAL_SAVE_PATH = f"./{FILENAME_TO_DOWNLOAD}" # Guarda en el mismo directorio que el script

# --- Script ---
client = None # Inicializar cliente
try:
    print("Conectando a MongoDB...")
    # Conectar usando la configuración segura
    server_api = ServerApi('1')
    client = MongoClient(
        MONGO_URI,
        server_api=server_api,
        ssl=True,
        tlsCAFile=certifi.where()
    )
    # Verificar conexión (opcional, pero bueno para diagnóstico)
    client.admin.command('ping')
    print("Conexión exitosa.")

    # Acceder a la base de datos y a GridFS
    db = client[DB_NAME]
    fs = gridfs.GridFS(db, collection=GRIDFS_PREFIX)

    # Buscar el archivo en GridFS por nombre
    # find_one devuelve None si no lo encuentra
    print(f"Buscando archivo: {FILENAME_TO_DOWNLOAD}...")
    grid_out = fs.find_one({"filename": FILENAME_TO_DOWNLOAD})

    # Si se encontró el archivo
    if grid_out:
        print(f"Archivo encontrado (ID: {grid_out._id}, Tamaño: {grid_out.length} bytes).")

        # Leer el contenido del archivo desde GridFS
        pdf_data = grid_out.read()

        # Guardar los datos leídos en un archivo local
        print(f"Guardando archivo en: {LOCAL_SAVE_PATH}...")
        with open(LOCAL_SAVE_PATH, "wb") as local_file: # 'wb' para escritura binaria
            local_file.write(pdf_data)
        print("¡Archivo descargado exitosamente!")

    else:
        # Si find_one devolvió None
        print(f"Error: No se encontró ningún archivo con el nombre '{FILENAME_TO_DOWNLOAD}' en GridFS (prefijo '{GRIDFS_PREFIX}').")
        print("Verifica el nombre del archivo y el prefijo GridFS.")
        # Podrías listar archivos disponibles para ayudar:
        # print("\nArchivos disponibles:")
        # for f in fs.find().limit(10): # Listar hasta 10 archivos
        #     print(f"- {f.filename} (ID: {f._id})")

# Manejo de errores de conexión u otros
except ConnectionFailure as e:
    print(f"Error de conexión con MongoDB: {e}")
except gridfs.errors.NoFile as e:
    # Este error ocurre si intentas usar fs.get() con un ID inválido,
    # pero find_one() devolviendo None es más común para búsquedas fallidas.
    print(f"Error de GridFS (NoFile): {e}")
except Exception as e:
    print(f"Se produjo un error inesperado: {e}")

# Asegurar que la conexión se cierre
finally:
    if client:
        client.close()
        print("Conexión a MongoDB cerrada.")

