import xml.etree.ElementTree as ET
from collections import Counter
import os
import re
import json

# 🎨 Classe per als colors i formats ANSI
class Formato:
    TITULO = '\033[1;96m'      
    SUBTITULO = '\033[1;93m'   
    ETIQUETA = '\033[1;94m'    
    EXITO = '\033[1;92m'       
    VALOR = '\033[97m'         
    NUMERO = '\033[1;95m'      
    ERROR = '\033[1;91m'       
    BINARIO = '\033[1;90m'     
    GRAFICO = '\033[38;5;42m'  
    PUNTO = '\033[2;37m'       
    DIVISOR = '\033[1;90m'     
    RESET = '\033[0m'          
    LINEA = '\033[90m' + "─" * 78 + '\033[0m'

# 🛠️ Funció per alinear i generar el gràfic sense que es trenqui a la terminal
def generar_fila_grafica(etiqueta, cantidad, total, color_etiqueta, longitud_max_barra=15):
    texto = str(etiqueta)
    if len(texto) > 32:
        texto = texto[:29] + "..."
    
    longitud_texto = len(texto)
    puntos_relleno = "." * (35 - longitud_texto)
    texto_columna = f"{color_etiqueta}{texto}{Formato.RESET}{Formato.PUNTO}{puntos_relleno}{Formato.RESET}"
    
    num_alineado = f"{cantidad:>6}"
    
    porcentaje = (cantidad / total) * 100 if total > 0 else 0
    porc_texto = f"{porcentaje:>5.1f}%"
    porc_alineado = f"{porc_texto:>7}"
    
    longitud_barra = int((porcentaje / 100) * longitud_max_barra)
    barra = "█" * longitud_barra
    fondo = "░" * (longitud_max_barra - longitud_barra)
    grafico = f"{Formato.GRAFICO}{barra}{Formato.BINARIO}{fondo}{Formato.RESET}"
    
    divisor = f"{Formato.DIVISOR}│{Formato.RESET}"
    
    return f"  {color_etiqueta}▪{Formato.RESET} {texto_columna} {divisor} {Formato.NUMERO}{num_alineado}{Formato.RESET} {divisor} {Formato.VALOR}{porc_alineado}{Formato.RESET} {divisor} {grafico}"

# 🛠️ Funció per obtenir un identificador únic d'una incidència
def obtenir_id_unic(inc_dict):
    for clau, valor in inc_dict.items():
        # Busquem etiquetes o atributs que semblin IDs
        if clau.lower() in ['id', 'id_incidencia', 'idincidencia', '@id', '@id_incidencia']:
            return str(valor).strip()
    # Si no hi ha ID explícit, creem un hash (empremta) del contingut exacte
    return str(hash(frozenset(inc_dict.items())))

def procesar_estadisticas_avanzadas():
    nombre_archivo = 'incidencies.xml'
    nombre_json = 'incidencies.json'
    
    try:
        ruta_script = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(ruta_script, nombre_archivo)
        ruta_json = os.path.join(ruta_script, nombre_json)
    except NameError:
        ruta_archivo = nombre_archivo
        ruta_json = nombre_json

    print(f"\n{Formato.TITULO}📊 ANÀLISI AVANÇADA DE DADES: {nombre_archivo}{Formato.RESET}")
    print(Formato.LINEA)

    if not os.path.exists(ruta_archivo):
        print(f"{Formato.ERROR}❌ Error: No es troba el fitxer '{nombre_archivo}'.{Formato.RESET}")
        return

    try:
        arbol = ET.parse(ruta_archivo)
        raiz = arbol.getroot()
        total_registros = len(raiz)
        
        if total_registros == 0:
            print(f"{Formato.ERROR}⚠️ El fitxer XML està buit.{Formato.RESET}\n")
            return

        incidencias_correctas = 0
        incidencias_eliminadas = 0
        incidencias_binarias = 0
        estadisticas_generales = {}
        incidencies_per_a_json = []

        # 🔍 Analitzar cada incidència
        for elemento in raiz:
            es_correcta = False
            es_eliminada = False
            tiene_binario = False
            textos_incidencia = []
            
            # Diccionari per desar les dades d'aquesta incidència en concret
            dades_incidencia = {}

            # Extreure Atributs
            for clau, val in elemento.attrib.items():
                text_net = val.strip()
                dades_incidencia[f"@{clau}"] = text_net
                textos_incidencia.append(text_net.lower())

            # Extreure Etiquetes i Valors
            for dato in elemento:
                valor = dato.text.strip() if dato.text else ""
                if valor:
                    dades_incidencia[dato.tag] = valor
                    textos_incidencia.append(valor.lower())
                    textos_incidencia.append(dato.tag.lower())

                    if len(valor) < 50:
                        if dato.tag not in estadisticas_generales:
                            estadisticas_generales[dato.tag] = []
                        estadisticas_generales[dato.tag].append(valor)
            
            # Afegir a la llista d'exportació
            if dades_incidencia:
                incidencies_per_a_json.append(dades_incidencia)

            texto_unido = " ".join(textos_incidencia)

            if any(p in texto_unido for p in ['eliminada', 'eliminado', 'borrada', 'borrado', 'deleted', 'baja']):
                es_eliminada = True
            elif any(p in texto_unido for p in ['correcta', 'correcto', 'ok', 'resuelta', 'valida', 'válida']):
                es_correcta = True

            for texto_original in [dato.text.strip() for dato in elemento if dato.text]:
                texto_sin_espacios = texto_original.replace(" ", "").replace("\n", "")
                if re.fullmatch(r'[01]{8,}', texto_sin_espacios) or 'binario' in texto_unido:
                    tiene_binario = True
                    break

            if es_eliminada: incidencias_eliminadas += 1
            if es_correcta: incidencias_correctas += 1
            if tiene_binario: incidencias_binarias += 1

        # 📈 SECCIÓ 1: RESUM D'ESTATS
        print(f"{Formato.TITULO}🎯 RESUM D'ESTATS{Formato.RESET}")
        
        texto_total = "Total d'incidències al fitxer"
        p_relleno = "." * (35 - len(texto_total))
        texto_tot_columna = f"{Formato.ETIQUETA}{texto_total}{Formato.RESET}{Formato.PUNTO}{p_relleno}{Formato.RESET}"
        divisor = f"{Formato.DIVISOR}│{Formato.RESET}"
        
        print(f"  {Formato.ETIQUETA}▪{Formato.RESET} {texto_tot_columna} {divisor} {Formato.NUMERO}{total_registros:>6}{Formato.RESET} {divisor} {Formato.VALOR}{'100.0%':>7}{Formato.RESET} {divisor}")
        print(generar_fila_grafica("Incidències Correctes", incidencias_correctas, total_registros, Formato.EXITO))
        print(generar_fila_grafica("Incidències Eliminades", incidencias_eliminadas, total_registros, Formato.ERROR))
        print(generar_fila_grafica("Codificades en Binari", incidencias_binarias, total_registros, Formato.BINARIO))
        print(Formato.LINEA)

        # 📈 SECCIÓ 2: ESTADÍSTIQUES GENERALS
        for etiqueta, valores in estadisticas_generales.items():
            contador = Counter(valores)
            
            if 0 < len(contador) <= 30 or len(contador) < (total_registros * 0.6):
                print(f"{Formato.SUBTITULO}📌 Desglossament per '{etiqueta.upper()}':{Formato.RESET}")
                for valor, cantidad in contador.most_common(10):
                    print(generar_fila_grafica(valor, cantidad, total_registros, Formato.ETIQUETA))
                if len(contador) > 10:
                    print(f"  {Formato.VALOR}... (+{len(contador) - 10} variants omeses){Formato.RESET}")
                print(Formato.LINEA)

        # 💾 SECCIÓ 3: GESTIÓ DEL FITXER JSON
        print(f"\n{Formato.TITULO}💾 EXPORTACIÓ DE DADES{Formato.RESET}")
        
        if not os.path.exists(ruta_json):
            # Crear per primer cop
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(incidencies_per_a_json, f, ensure_ascii=False, indent=4)
            print(f"  {Formato.EXITO}✔️ No s'ha trobat cap fitxer previ. S'ha creat '{nombre_json}' amb {len(incidencies_per_a_json)} incidències.{Formato.RESET}\n")
        
        else:
            # Ja existeix, cal preguntar
            print(f"  {Formato.SUBTITULO}⚠️ El fitxer '{nombre_json}' ja existeix.{Formato.RESET}")
            print(f"  Què vols fer?")
            print(f"  {Formato.ETIQUETA}[ 1 ]{Formato.RESET} Sobreescriure'l {Formato.PUNTO}(Esborra el contingut anterior i escriu tot de nou){Formato.RESET}")
            print(f"  {Formato.ETIQUETA}[ 2 ]{Formato.RESET} Afegir noves incidències {Formato.PUNTO}(Conserva les existents, evitant duplicats per ID){Formato.RESET}")
            print(f"  {Formato.ERROR}[ 3 ]{Formato.RESET} Cancel·lar i no desar res.")
            
            opcio = input(f"\n  Introdueix 1, 2 o 3: ").strip()
            
            if opcio == '1':
                with open(ruta_json, 'w', encoding='utf-8') as f:
                    json.dump(incidencies_per_a_json, f, ensure_ascii=False, indent=4)
                print(f"  {Formato.EXITO}✔️ Fitxer sobreescrit amb èxit. S'han desat {len(incidencies_per_a_json)} incidències.{Formato.RESET}\n")
            
            elif opcio == '2':
                try:
                    with open(ruta_json, 'r', encoding='utf-8') as f:
                        dades_existents = json.load(f)
                        if not isinstance(dades_existents, list):
                            dades_existents = []
                except (json.JSONDecodeError, FileNotFoundError):
                    dades_existents = []

                # Mapejar els IDs que ja hi ha al JSON
                ids_existents = set()
                for d in dades_existents:
                    ids_existents.add(obtenir_id_unic(d))

                afegides = 0
                for nova_inc in incidencies_per_a_json:
                    id_nou = obtenir_id_unic(nova_inc)
                    if id_nou not in ids_existents:
                        dades_existents.append(nova_inc)
                        ids_existents.add(id_nou)
                        afegides += 1

                with open(ruta_json, 'w', encoding='utf-8') as f:
                    json.dump(dades_existents, f, ensure_ascii=False, indent=4)
                print(f"  {Formato.EXITO}✔️ Procés completat. S'han afegit {afegides} incidències noves que no hi eren (S'han omès {len(incidencies_per_a_json) - afegides} duplicats).{Formato.RESET}\n")
            
            else:
                print(f"  {Formato.ERROR}❌ Operació cancel·lada. No s'ha modificat el fitxer JSON.{Formato.RESET}\n")

    except ET.ParseError:
        print(f"{Formato.ERROR}❌ Error: El fitxer XML està corrupte o no té un format vàlid.{Formato.RESET}")
    except Exception as e:
        print(f"{Formato.ERROR}❌ Error inesperat: {e}{Formato.RESET}")

if __name__ == "__main__":
    procesar_estadisticas_avanzadas()