import sys
import os
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom
import re

def csv_a_xml(ruta_entrada):
    # Esto elimina cualquier ruta (ej: "C:/carpeta/incidencias.csv") y se queda solo con "incidencias.csv"
    nombre_archivo = os.path.basename(ruta_entrada)
    
    # Separamos el nombre de la extensión para crear el XML (ej: "incidencias" + ".xml")
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    archivo_salida = f"{nombre_sin_ext}.xml"

    root = ET.Element(nombre_sin_ext.capitalize()) # Usa el nombre del archivo como nodo principal

    try:
        with open(ruta_entrada, mode='r', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            
            for fila in lector:
                registro = ET.SubElement(root, "Registro")
                
                for columna, valor in fila.items():
                    if columna:
                        etiqueta = re.sub(r'\W|^(?=\d)', '_', columna.strip())
                    else:
                        etiqueta = "Columna_Sin_Nombre"
                    
                    hijo = ET.SubElement(registro, etiqueta)
                    hijo.text = str(valor).strip()

        xml_string = ET.tostring(root, encoding='utf-8')
        xml_formateado = xml.dom.minidom.parseString(xml_string).toprettyxml(indent="    ")

        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(xml_formateado)

        print(f"✅ Éxito: Se ha creado el archivo '{archivo_salida}' en esta carpeta.")

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_entrada}'.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")

# --- Ejecución ---
if __name__ == "__main__":
    # Comprueba si el usuario ha escrito el nombre del archivo en la terminal
    if len(sys.argv) < 2:
        print("⚠️ Uso correcto: python3 convertir.py incidencias.csv")
    else:
        # Pilla el archivo que le pases por consola
        csv_a_xml(sys.argv[1])