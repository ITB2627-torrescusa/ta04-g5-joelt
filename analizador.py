import xml.etree.ElementTree as ET
from collections import Counter
import os
import re

# 🎨 Clase para los colores y formatos ANSI
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
    RESET = '\033[0m'          
    LINEA = '\033[90m' + "-" * 85 + '\033[0m'

# 🛠️ Función mágica para alinear todo a la misma altura y generar el gráfico
def generar_fila_grafica(etiqueta, cantidad, total, color_etiqueta, longitud_max_barra=25):
    # 1. Columna de texto: Fija a 35 caracteres exactos
    texto = str(etiqueta)
    if len(texto) > 32:
        texto = texto[:29] + "..."  # Trunca si es muy largo
    texto_alineado = texto.ljust(35) # Rellena con espacios hasta 35
    
    # 2. Columna de números: Fija a 6 caracteres (alineado a la derecha)
    num_alineado = f"{cantidad:>6}"
    
    # 3. Columna de porcentajes: Fija a 9 caracteres
    porcentaje = (cantidad / total) * 100 if total > 0 else 0
    porc_texto = f"({porcentaje:>5.1f}%)"
    porc_alineado = f"{porc_texto:>9}"
    
    # 4. Columna de gráfico
    longitud_barra = int((porcentaje / 100) * longitud_max_barra)
    barra = "█" * longitud_barra
    fondo = "░" * (longitud_max_barra - longitud_barra)
    grafico = f"{Formato.GRAFICO}{barra}{Formato.BINARIO}{fondo}{Formato.RESET}"
    
    # Ensamblar línea con colores independientes para no romper el espaciado
    return f"  {color_etiqueta}▪ {texto_alineado}{Formato.RESET} {Formato.NUMERO}{num_alineado}{Formato.RESET} {Formato.VALOR}{porc_alineado}{Formato.RESET}  {grafico}"


def procesar_estadisticas_avanzadas():
    nombre_archivo = 'incidencies.xml'
    
    try:
        ruta_script = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(ruta_script, nombre_archivo)
    except NameError:
        ruta_archivo = nombre_archivo

    print(f"\n{Formato.TITULO}📊 ANÁLISIS AVANZADO DE DATOS: {nombre_archivo}{Formato.RESET}")
    print(Formato.LINEA)

    if not os.path.exists(ruta_archivo):
        print(f"{Formato.ERROR}❌ Error: No se encuentra '{nombre_archivo}'.{Formato.RESET}")
        return

    try:
        arbol = ET.parse(ruta_archivo)
        raiz = arbol.getroot()
        total_registros = len(raiz)
        
        if total_registros == 0:
            print(f"{Formato.ERROR}⚠️ El archivo XML está vacío.{Formato.RESET}\n")
            return

        incidencias_correctas = 0
        incidencias_eliminadas = 0
        incidencias_binarias = 0
        estadisticas_generales = {}

        for elemento in raiz:
            es_correcta = False
            es_eliminada = False
            tiene_binario = False
            textos_incidencia = []

            for _, val in elemento.attrib.items():
                textos_incidencia.append(val.strip().lower())

            for dato in elemento:
                valor = dato.text.strip() if dato.text else ""
                if valor:
                    textos_incidencia.append(valor.lower())
                    textos_incidencia.append(dato.tag.lower())

                    if len(valor) < 50:
                        if dato.tag not in estadisticas_generales:
                            estadisticas_generales[dato.tag] = []
                        estadisticas_generales[dato.tag].append(valor)

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

        # 📈 SECCIÓN 1: RESUMEN DE ESTADOS (Ahora con gráficos alineados)
        print(f"{Formato.TITULO}🎯 RESUMEN DE ESTADOS{Formato.RESET}")
        
        # Línea de Total (Sin gráfico)
        texto_total = "Total de incidencias en el archivo".ljust(35)
        print(f"  {Formato.ETIQUETA}▪ {texto_total}{Formato.RESET} {Formato.NUMERO}{total_registros:>6}{Formato.RESET}")
        
        # Líneas de estadísticas principales
        print(generar_fila_grafica("Incidencias Correctas", incidencias_correctas, total_registros, Formato.EXITO))
        print(generar_fila_grafica("Incidencias Eliminadas", incidencias_eliminadas, total_registros, Formato.ERROR))
        print(generar_fila_grafica("Codificadas en Binario", incidencias_binarias, total_registros, Formato.BINARIO))
        print(Formato.LINEA)

        # 📈 SECCIÓN 2: ESTADÍSTICAS GENERALES (Misma alineación estricta)
        for etiqueta, valores in estadisticas_generales.items():
            contador = Counter(valores)
            
            if 0 < len(contador) <= 30 or len(contador) < (total_registros * 0.6):
                print(f"{Formato.SUBTITULO}📌 Desglose por '{etiqueta.upper()}':{Formato.RESET}")
                
                for valor, cantidad in contador.most_common(10):
                    # Usamos la misma función para garantizar alineación milimétrica
                    print(generar_fila_grafica(valor, cantidad, total_registros, Formato.ETIQUETA))
                
                if len(contador) > 10:
                    print(f"  {Formato.VALOR}... (+{len(contador) - 10} variantes omitidas){Formato.RESET}")
                
                print(Formato.LINEA)

    except ET.ParseError:
        print(f"{Formato.ERROR}❌ Error: El archivo XML está corrupto o mal formado.{Formato.RESET}")
    except Exception as e:
        print(f"{Formato.ERROR}❌ Error inesperado: {e}{Formato.RESET}")

if __name__ == "__main__":
    procesar_estadisticas_avanzadas()