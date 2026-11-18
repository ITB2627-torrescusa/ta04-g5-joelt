import re
import json
import random
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# BANCO MASSIVA DE DADES PER A MÉS DE 5.000 COMBINACIONS ÚNIQUES
# ---------------------------------------------------------------------------
NOMS = ["Carlos", "Benjamin", "Joel", "Marc", "Laura", "Pau", "Adrià", "David", "Elena", "Marta", "Albert", "Sergi", "Arnau", "Guillem", "Pol", "Iván", "Dani", "Eric"]
COGNOMS = ["Artigas", "Jimenez", "Torrescusa", "García", "Martínez", "López", "Romero", "Navarro", "Vidal", "Serra", "Sánchez", "Pérez", "Gómez", "Fernández"]

DEPARTAMENTOS = [
    "Sistemas / IT", "Desarrollo de Software", "Recursos Humanos", "Contabilidad y Finanzas",
    "Marketing Digital", "Atención al Cliente", "Administración General", "Logística y Almacén",
    "Comercial / Ventas", "Calidad y Auditoría", "Ciberseguridad", "Mantenimiento Técnico"
]

EQUIPOS = [
    "Portátil Lenovo ThinkPad", "PC de Sobremesa HP Elite", "Servidor Rack Dell PowerEdge",
    "Impresora Multifunción HP", "Monitor LG 27 pulgadas", "Teléfono IP Yealink",
    "Router Cisco Principal", "Switch de Red Aruba", "Tablet Samsung Galaxy Tab", "SAI / UPS de Alimentación"
]

ESTADOS = [
    "Inoperativo totalmente", "Con fallos intermitentes", "Bloqueado por completo",
    "Encendido pero congelado", "Lento tras actualización", "Emitiendo ruidos metálicos",
    "Calentamiento excesivo", "Pantalla con parpadeos", "Sin respuesta al teclado/ratón"
]

PRIORIDADES = ["Baja", "Media", "Alta", "Crítica (Bloqueante)", "Urgente"]

CATEGORIAS = [
    "Hardware", "Software / Aplicaciones", "Red / Conectividad",
    "Permisos / Accesos", "Impresoras / Periféricos", "Sistemas Operativos", "Seguridad / Malware", "Otro"
]

INCIDENCIAS_BASE = [
    "La pantalla azul de la muerte (BSOD) aparece al abrir aplicaciones pesadas.",
    "El ordenador se apaga solo a los pocos minutos de encenderlo.",
    "No se conecta a la red Wi-Fi ni por cable Ethernet.",
    "La impresora se queda atascada y lanza hojas en blanco.",
    "Al reiniciar la máquina sale un mensaje de 'Operating System Not Found'.",
    "El ventilador suena a máxima velocidad constantemente sin carga de trabajo.",
    "No puedo acceder a la cuenta corporativa porque los credenciales han caducado.",
    "El teclado escribe caracteres extraños y las teclas se encasquillan.",
    "Tras una actualización del sistema, el equipo no detecta la segunda pantalla.",
    "El disco duro hace un chasquido constante y el sistema operativo no carga.",
    "El navegador web se bloquea al intentar abrir la intranet de la empresa.",
    "El ratón inalámbrico no responde incluso cambiando las pilas."
]

DETALLES_EXTRA = [
    "Ha ocurrido de forma repentina a primera hora.",
    "Afecta al trabajo diario del equipo entero.",
    "Necesitamos una solución antes de acabar la jornada.",
    "Sospechamos que puede ser un fallo eléctrico o de alimentación.",
    "El equipo ya dio problemas similares la semana pasada.",
    "Se requiere intervención presencial o remota urgente."
]

EXPLICACIONES_OTRO = [
    "Simplemente dejó de funcionar sin motivo aparente.",
    "Ha sido a raíz de un corte de luz en la planta.",
    "Es un fallo muy específico que no encaja en las opciones.",
    "Sospecho que se trata de un conflicto entre programas instalados.",
    "Afecta únicamente a las aplicaciones del departamento de ventas."
]

# Diccionari global per registrar les darreres respostes per a cada pregunta
HISTORIAL_PATRONES = {}

def generar_respuesta_infinita(titulo_pregunta):
    """
    Genera respostes úniques assegurant un rang de no-repetició de més de 700 enviaments.
    """
    titulo = titulo_pregunta.lower()

    if titulo_pregunta not in HISTORIAL_PATRONES:
        HISTORIAL_PATRONES[titulo_pregunta] = []

    usadas = HISTORIAL_PATRONES[titulo_pregunta]

    # Intentem fins a 1.000 vegades trobar una combinació que no s'hagi utilitzat recentment
    for _ in range(1000):
        if "correo" in titulo or "email" in titulo or "mail" in titulo:
            u = f"{random.choice(NOMS).lower()}.{random.choice(COGNOMS).lower()}{random.randint(1, 9999)}"
            dom = random.choice(["itb.cat", "empresa.com", "tech.org", "soporte.net"])
            val = f"{u}@{dom}"

        elif "nombre" in titulo or "nom" in titulo:
            val = f"{random.choice(NOMS)} {random.choice(COGNOMS)} {random.choice(COGNOMS)}"

        elif "departamento" in titulo or "departament" in titulo:
            val = random.choice(DEPARTAMENTOS)

        elif "equipament" in titulo or "dispositivo" in titulo or "equipo" in titulo:
            if "identificador" in titulo or "id" in titulo or "código" in titulo:
                val = f"DEV-ITB-{random.randint(10000, 99999)}"
            else:
                val = f"{random.choice(EQUIPOS)} (Sala {random.randint(1, 40)})"

        elif "estado" in titulo or "estat" in titulo:
            val = random.choice(ESTADOS)

        elif "prioridad" in titulo or "prioritat" in titulo or "nivel" in titulo:
            val = random.choice(PRIORIDADES)

        elif "categoria" in titulo or "categoría" in titulo:
            val = random.choice(CATEGORIAS)

        elif "otro" in titulo or "altre" in titulo or "marcado" in titulo or "explicailo" in titulo:
            val = f"{random.choice(EXPLICACIONES_OTRO)} (Ref: #{random.randint(100, 999)})"

        elif "explica" in titulo or "descripción" in titulo or "descripció" in titulo or "incidencia" in titulo:
            val = f"{random.choice(INCIDENCIAS_BASE)} {random.choice(DETALLES_EXTRA)}"

        else:
            val = f"Verificado por IT - Ticket #{random.randint(10000, 99999)}"

        # Assegurem que la resposta no estigui en les darreres 750 utilitzades per a aquesta pregunta
        if val not in usadas[-750:]:
            usadas.append(val)
            return val

    # Si exhaureix intents, afegeix un codi únic al final per mantenir la varietat absoluta
    val_final = f"{val} [{random.randint(100000, 999999)}]"
    usadas.append(val_final)
    return val_final

# ---------------------------------------------------------------------------
# MOTOR D'EXTRACCIÓ I ENVIAMENT
# ---------------------------------------------------------------------------
def obtener_estructura_formulario(url):
    if "/edit" in url:
        url = re.sub(r'/edit.*$', '/viewform', url)
    elif not url.endswith("/viewform"):
        url = url.rstrip("/") + "/viewform"

    print("\n[1/3] Extrayendo campos del formulario...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Error al cargar el formulario. Código HTTP: {res.status_code}")

    soup = BeautifulSoup(res.text, 'html.parser')

    script_target = None
    for s in soup.find_all('script'):
        if s.string and 'FB_PUBLIC_LOAD_DATA_' in s.string:
            script_target = s.string
            break

    if not script_target:
        raise Exception("No se encontraron los datos del formulario.")

    json_raw = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);', script_target, re.DOTALL).group(1)
    datos_form = json.loads(json_raw)

    preguntas_raw = datos_form[1][1]
    campos_detectados = []

    for item in preguntas_raw:
        if not item or len(item) < 5 or not item[4]:
            continue

        titulo = item[1]
        info_pregunta = item[4][0]
        entry_id = f"entry.{info_pregunta[0]}"

        opciones = []
        if len(info_pregunta) > 1 and info_pregunta[1]:
            opciones = [opt[0] for opt in info_pregunta[1] if opt and opt[0] is not None]

        campos_detectados.append({
            'id': entry_id,
            'titulo': titulo,
            'opciones': opciones
        })

    url_response = url.replace('/viewform', '/formResponse')
    return url_response, campos_detectados

def executar_bot_massiu():
    url_input = input("Introduce la URL del Google Form: ").strip()
    
    try:
        cantidad = int(input("¿Cuántas respuestas quieres enviar? (ej. 2000): "))
    except ValueError:
        print("Número no válido.")
        return

    try:
        url_response, campos = obtener_estructura_formulario(url_input)
    except Exception as e:
        print(f"Error analizando el formulario: {e}")
        return

    print(f"\n[2/3] Formulario listo con {len(campos)} preguntas.")
    print(f"[3/3] Generando {cantidad} respuestas únicas (Rango de no repetición > 700)...\n")

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0'
    }

    exitos = 0
    for i in range(cantidad):
        payload = {}
        print(f"--- Envío {i + 1}/{cantidad} ---")
        
        for c in campos:
            if c['opciones']:
                # Opcions de selecció del propi formulari
                valor = random.choice(c['opciones'])
            else:
                # Textos de resposta amb el filtre de 750 respostes sense repetir
                valor = generar_respuesta_infinita(c['titulo'])
            
            payload[c['id']] = valor
            print(f"  • {c['titulo']}: {valor}")

        res = requests.post(url_response, data=payload, headers=headers)

        if res.status_code == 200:
            exitos += 1
            print("  -> Registrada con éxito.\n")
        else:
            print(f"  -> Error HTTP {res.status_code}\n")

    print(f"Proceso masivo completado: {exitos}/{cantidad} respuestas enviadas.")

if __name__ == "__main__":
    executar_bot_massiu()
