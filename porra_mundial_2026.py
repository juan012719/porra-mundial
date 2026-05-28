import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Porra Mundial 2026 🌍", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizado
st.markdown("""
<style>
    /* Ocultar ABSOLUTAMENTE TODO el rastro de Streamlit para que parezca una app nativa */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { display: none !important; }
    
    .main { background-color: #0e1117; }
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%); }
    
    .titulo-principal {
        text-align: center;
        font-size: 2.5em;
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FF6B35, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px 0 5px 0;
        letter-spacing: 2px;
    }
    .titulo-landing {
        text-align: center;
        /* Hacemos el texto elástico: más pequeño en móvil y grande en PC */
        font-size: clamp(2.5em, 8vw, 4.5em);
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FF6B35, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 40px 0 10px 0;
        letter-spacing: 2px;
    }
    .subtitulo {
        text-align: center;
        color: #888;
        font-size: clamp(0.9em, 3vw, 1.2em);
        margin-bottom: 30px;
        letter-spacing: 5px;
    }
    .card {
        background: linear-gradient(135deg, #1e2530, #252d3a);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .mini-card {
        background-color: #1e2530;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .resultado-badge {
        background: #FFD700;
        color: #000;
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: bold;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

BANDERAS = {
    "ESPAÑA": "💩", "FRANCIA": "🇫🇷", "INGLATERRA": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "BRASIL": "🇧🇷", "ARGENTINA": "🇦🇷",
    "PORTUGAL": "🇵🇹", "ALEMANIA": "🇩🇪", "PAÍSES BAJOS": "🇳🇱", "NORUEGA": "🇳🇴", "BÉLGICA": "🇧🇪",
    "COLOMBIA": "🇨🇴", "JAPÓN": "🇯🇵", "USA": "🇺🇸", "MARRUECOS": "🇲🇦", "URUGUAY": "🇺🇾",
    "SUIZA": "🇨🇭", "MÉXICO": "🇲🇽", "CROACIA": "🇭🇷", "TURQUÍA": "🇹🇷", "ECUADOR": "🇪🇨",
    "SENEGAL": "🇸🇳", "SUECIA": "🇸🇪", "CANADÁ": "🇨🇦", "AUSTRIA": "🇦🇹", "PARAGUAY": "🇵🇾",
    "ESCOCIA": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "BOSNIA HERZEG.": "🇧🇦", "COSTA MARFIL": "🇨🇮", "EGIPTO": "🇪🇬", "CHEQUIA": "🇨🇿",
    "GHANA": "🇬🇭", "ARGELIA": "🇩🇿", "COREA DEL SUR": "🇰🇷", "TÚNEZ": "🇹🇳", "AUSTRALIA": "🇦🇺",
    "IRÁN": "🇮🇷", "CONGO": "🇨🇬", "SUDÁFRICA": "🇿🇦", "CATAR": "🇶🇦", "ARABIA SAUDÍ": "🇸🇦",
    "PANAMÁ": "🇵🇦", "NUEVA ZELANDA": "🇳🇿", "IRAK": "🇮🇶", "CABO VERDE": "🇨🇻", "CURACAO": "🇨🇼",
    "UZBEQUISTÁN": "🇺🇿", "JORDANIA": "🇯🇴", "HAITÍ": "🇭🇹"
}

def flag(eq):
    return BANDERAS.get(eq, "🏳️")

VALOR_EQUIPOS = {
    "ESPAÑA": 29, "FRANCIA": 27, "INGLATERRA": 26, "BRASIL": 24, "ARGENTINA": 24,
    "PORTUGAL": 20, "ALEMANIA": 20, "PAÍSES BAJOS": 19, "NORUEGA": 18, "BÉLGICA": 17,
    "COLOMBIA": 17, "JAPÓN": 15, "USA": 14, "MARRUECOS": 14, "URUGUAY": 14,
    "SUIZA": 13, "MÉXICO": 13, "CROACIA": 13, "TURQUÍA": 11, "ECUADOR": 10,
    "SENEGAL": 10, "SUECIA": 9, "CANADÁ": 9, "AUSTRIA": 9, "PARAGUAY": 8,
    "ESCOCIA": 8, "BOSNIA HERZEG.": 8, "COSTA MARFIL": 7, "EGIPTO": 7, "CHEQUIA": 7,
    "GHANA": 6, "ARGELIA": 6, "COREA DEL SUR": 5, "TÚNEZ": 5, "AUSTRALIA": 5,
    "IRÁN": 4, "CONGO": 3, "SUDÁFRICA": 3, "CATAR": 3, "ARABIA SAUDÍ": 2,
    "PANAMÁ": 2, "NUEVA ZELANDA": 2, "IRAK": 2, "CABO VERDE": 2, "CURACAO": 2,
    "UZBEQUISTÁN": 2, "JORDANIA": 1, "HAITÍ": 0
}

GRUPOS = {
    "A": ["MÉXICO", "SUDÁFRICA", "COREA DEL SUR", "CHEQUIA"],
    "B": ["CANADÁ", "BOSNIA HERZEG.", "CATAR", "SUIZA"],
    "C": ["BRASIL", "MARRUECOS", "HAITÍ", "ESCOCIA"],
    "D": ["USA", "PARAGUAY", "AUSTRALIA", "TURQUÍA"],
    "E": ["ALEMANIA", "CURACAO", "COSTA MARFIL", "ECUADOR"],
    "F": ["PAÍSES BAJOS", "JAPÓN", "SUECIA", "TÚNEZ"],
    "G": ["BÉLGICA", "EGIPTO", "IRÁN", "NUEVA ZELANDA"],
    "H": ["ESPAÑA", "CABO VERDE", "ARABIA SAUDÍ", "URUGUAY"],
    "I": ["FRANCIA", "SENEGAL", "IRAK", "NORUEGA"],
    "J": ["ARGENTINA", "ARGELIA", "AUSTRIA", "JORDANIA"],
    "K": ["PORTUGAL", "CONGO", "UZBEQUISTÁN", "COLOMBIA"],
    "L": ["INGLATERRA", "CROACIA", "GHANA", "PANAMÁ"]
}

EMPAREJAMIENTOS_16VOS = {
    "M73": ("2A","2B"), "M74": ("1E","3_1"), "M75": ("1F","2C"), "M76": ("1C","2F"),
    "M77": ("1I","3_2"), "M78": ("2E","2I"), "M79": ("1A","3_3"), "M80": ("1L","3_4"),
    "M81": ("1D","3_5"), "M82": ("1G","3_6"), "M83": ("2K","2L"), "M84": ("1H","2J"),
    "M85": ("1B","3_7"), "M86": ("1J","2H"), "M87": ("1K","3_8"), "M88": ("2D","2G")
}
CRUCES_OCTAVOS  = {"M89":("M74","M77"),"M90":("M73","M75"),"M91":("M76","M78"),"M92":("M79","M80"),"M93":("M83","M84"),"M94":("M81","M82"),"M95":("M85","M87"),"M96":("M86","M88")}
CRUCES_CUARTOS  = {"M97":("M89","M90"),"M98":("M93","M94"),"M99":("M91","M92"),"M100":("M95","M96")}
CRUCES_SEMIS    = {"M101":("M97","M98"),"M102":("M99","M100")}
CRUCES_FINALES  = {"M103 (3º y 4º)":("M101_L","M102_L"),"M104 (FINAL)":("M101","M102")}

DIAS_INICIO = {"A": 11, "B": 12, "C": 13, "D": 13, "E": 14, "F": 14, "G": 15, "H": 15, "I": 16, "J": 16, "K": 17, "L": 17}

def obtener_fecha_grupo(eA, eB, grupo):
    if eA == "ESPAÑA" and eB == "CABO VERDE": return "15 Jun - 18:00"
    if eA == "ESPAÑA" and eB == "ARABIA SAUDÍ": return "21 Jun - 18:00"
    if eA == "ESPAÑA" and eB == "URUGUAY": return "25 Jun - 22:00"
    eqs = GRUPOS[grupo]
    base = DIAS_INICIO.get(grupo, 11)
    if (eA, eB) == (eqs[0], eqs[1]): dia = base; hora = "21:00"
    elif (eA, eB) == (eqs[2], eqs[3]): dia = base + 1; hora = "18:00"
    elif (eA, eB) == (eqs[0], eqs[2]): dia = base + 5; hora = "21:00"
    elif (eA, eB) == (eqs[1], eqs[3]): dia = base + 6; hora = "18:00"
    elif (eA, eB) == (eqs[0], eqs[3]): dia = base + 9; hora = "22:00"
    else: dia = base + 9; hora = "18:00"
    mes = "Jul" if dia > 30 else "Jun"
    dia = dia - 30 if dia > 30 else dia
    return f"{dia} {mes} - {hora}"

FECHAS_ELIM = {
    "M73": "28 Jun - 18:00", "M74": "28 Jun - 22:00", "M75": "29 Jun - 18:00", "M76": "29 Jun - 22:00",
    "M77": "30 Jun - 18:00", "M78": "30 Jun - 22:00", "M79": "1 Jul - 18:00", "M80": "1 Jul - 22:00",
    "M81": "2 Jul - 18:00", "M82": "2 Jul - 22:00", "M83": "3 Jul - 18:00", "M84": "3 Jul - 22:00",
    "M85": "4 Jul - 18:00", "M86": "4 Jul - 22:00", "M87": "5 Jul - 18:00", "M88": "5 Jul - 22:00",
    "M89": "6 Jul - 18:00", "M90": "6 Jul - 22:00", "M91": "7 Jul - 18:00", "M92": "7 Jul - 22:00",
    "M93": "8 Jul - 18:00", "M94": "8 Jul - 22:00", "M95": "9 Jul - 18:00", "M96": "9 Jul - 22:00",
    "M97": "11 Jul - 18:00", "M98": "11 Jul - 22:00", "M99": "12 Jul - 18:00", "M100": "12 Jul - 22:00",
    "M101": "14 Jul - 21:00", "M102": "15 Jul - 21:00", "M103 (3º y 4º)": "18 Jul - 21:00", "M104 (FINAL)": "19 Jul - 21:00"
}

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- FUNCIONES DE BASE DE DATOS (MULTI-LIGA) ---
@st.cache_data(ttl=30)
def cargar_participantes(liga):
    if not liga: return {}
    sb = get_supabase()
    rows = sb.table("participantes").select("*").eq("liga", liga).execute().data
    return {r["nombre"]: r["equipos"].split(",") if r["equipos"] else [] for r in rows}

@st.cache_data(ttl=30)
def cargar_ajustes_puntos(liga):
    if not liga: return {}
    try:
        sb = get_supabase()
        rows = sb.table("ajustes_puntos").select("*").eq("liga", liga).execute().data
        return {r["nombre"]: r["puntos_extra"] for r in rows}
    except Exception: return {}

def guardar_participantes(liga, participantes_dict):
    if not liga: return
    sb = get_supabase()
    sb.table("participantes").delete().eq("liga", liga).execute()
    rows = [{"liga": liga, "nombre": n, "equipos": ",".join(e)} for n, e in participantes_dict.items()]
    if rows: sb.table("participantes").insert(rows).execute()
    cargar_participantes.clear()

def guardar_ajuste_puntos(liga, nombre, puntos_extra):
    if not liga: return
    try:
        sb = get_supabase()
        sb.table("ajustes_puntos").upsert({"liga": liga, "nombre": nombre, "puntos_extra": puntos_extra}).execute()
        cargar_ajustes_puntos.clear()
    except Exception: pass

# --- FUNCIONES GLOBALES (MUNDIAL) ---
@st.cache_data(ttl=30)
def cargar_resultados_grupos():
    sb = get_supabase()
    rows = sb.table("resultados_grupos").select("*").execute().data
    return {r["key"]: {"equipo_A":r["equipo_a"],"equipo_B":r["equipo_b"],"goles_A":r["goles_a"],"goles_B":r["goles_b"]} for r in rows}

@st.cache_data(ttl=30)
def cargar_resultados_elim():
    sb = get_supabase()
    rows = sb.table("resultados_elim").select("*").execute().data
    return {r["key"]: {"equipo_A":r["equipo_a"],"equipo_B":r["equipo_b"],"goles_A":r["goles_a"],"goles_B":r["goles_b"],"resolucion":r["resolucion"],"ganador":r["ganador"],"perdedor":r["perdedor"]} for r in rows}

@st.cache_data(ttl=30)
def cargar_pichichi():
    sb = get_supabase()
    rows = sb.table("pichichi").select("*").execute().data
    return rows[0]["equipo"] if rows else None

@st.cache_data(ttl=30)
def cargar_pichichis_reales():
    try:
        sb = get_supabase()
        return sb.table("pichichis_reales").select("*").order("goles", desc=True).execute().data
    except Exception: return []

def guardar_resultado_grupo(key, eA, eB, gA, gB):
    sb = get_supabase()
    sb.table("resultados_grupos").upsert({"key":key,"equipo_a":eA,"equipo_b":eB,"goles_a":gA,"goles_b":gB}).execute()
    cargar_resultados_grupos.clear()

def borrar_resultado_grupo(key):
    sb = get_supabase()
    sb.table("resultados_grupos").delete().eq("key",key).execute()
    cargar_resultados_grupos.clear()

def guardar_resultado_elim(m_id, eA, eB, gA, gB, res, gan, perd):
    sb = get_supabase()
    sb.table("resultados_elim").upsert({"key":m_id,"equipo_a":eA,"equipo_b":eB,"goles_a":gA,"goles_b":gB,"resolucion":res,"ganador":gan,"perdedor":perd}).execute()
    cargar_resultados_elim.clear()

def borrar_resultado_elim(m_id):
    sb = get_supabase()
    sb.table("resultados_elim").delete().eq("key",m_id).execute()
    cargar_resultados_elim.clear()

def guardar_pichichi(eq):
    sb = get_supabase()
    sb.table("pichichi").delete().neq("id",0).execute()
    if eq: sb.table("pichichi").insert({"equipo":eq}).execute()
    cargar_pichichi.clear()

def guardar_goleador_real(jugador, equipo, goles, goles_penalti=0):
    try:
        sb = get_supabase()
        sb.table("pichichis_reales").upsert({"jugador": jugador.title(), "equipo": equipo, "goles": goles, "goles_penalti": goles_penalti}).execute()
        cargar_pichichis_reales.clear()
    except Exception: pass

def borrar_goleador_real(jugador):
    try:
        sb = get_supabase()
        sb.table("pichichis_reales").delete().eq("jugador", jugador).execute()
        cargar_pichichis_reales.clear()
    except Exception: pass


# ══════════════════════════════════════════
# CONTROL DE ESTADO (LOGIN)
# ══════════════════════════════════════════
if "liga_actual" not in st.session_state:
    st.session_state.liga_actual = ""
if "admin" not in st.session_state:
    st.session_state.admin = False


# ══════════════════════════════════════════
# PANTALLA PRINCIPAL (LANDING PAGE)
# ══════════════════════════════════════════
if not st.session_state.liga_actual:
    st.markdown('<div class="titulo-landing">⚽ Porra Mundial 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">USA · CANADA · MEXICO</div>', unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 40px;">
            <h2>🏆 Accede a tu Porra</h2>
            <p style="color: #aaa; margin-bottom: 20px;">Introduce la palabra secreta de tu grupo de amigos o trabajo para entrar a tu liga privada.</p>
        """, unsafe_allow_html=True)
        
        codigo = st.text_input("", placeholder="Ejemplo: CUADRILLA, OFICINA, FAMILIA...").strip().upper()
        
        if st.button("🚀 ENTRAR A MI LIGA", use_container_width=True):
            if codigo:
                if st.session_state.admin:
                    # Si eres admin, pasas directamente aunque no exista (así la creas)
                    st.session_state.liga_actual = codigo
                    st.rerun()
                else:
                    # Comprobamos en la base de datos si la liga existe
                    try:
                        sb = get_supabase()
                        check = sb.table("participantes").select("nombre").eq("liga", codigo).limit(1).execute()
                        if check.data and len(check.data) > 0:
                            st.session_state.liga_actual = codigo
                            st.rerun()
                        else:
                            st.error(f"❌ La liga '{codigo}' no existe. Comprueba que esté bien escrito o pide al administrador que te añada.")
                    except Exception:
                        st.error("Hubo un problema al comprobar la liga. Inténtalo de nuevo.")
            else:
                st.error("Por favor, escribe un código para entrar.")
                
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    st.write("")
    
    # Login Admin escondido abajo del todo en la landing
    if not st.session_state.admin:
        with st.expander("⚙️ Acceso Administrador"):
            pwd = st.text_input("Contraseña Admin", type="password", key="pwd_land")
            if st.button("Entrar Admin"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin = True; st.rerun()
                else:
                    st.error("Clave incorrecta")
    else:
        if st.button("🔴 Cerrar sesión Administrador"):
            st.session_state.admin = False; st.rerun()
            
    st.stop()


# ══════════════════════════════════════════
# EL RESTO DE LA APP (DENTRO DE LA LIGA)
# ══════════════════════════════════════════
liga_actual = st.session_state.liga_actual

# CARGA DE DATOS
participantes     = cargar_participantes(liga_actual)
ajustes_manuales  = cargar_ajustes_puntos(liga_actual)
resultados_grupos = cargar_resultados_grupos()
resultados_elim   = cargar_resultados_elim()
pichichi          = cargar_pichichi()
goleadores_reales = cargar_pichichis_reales()

def obtener_tabla_grupos():
    tabla = []
    for g, equipos in GRUPOS.items():
        for eq in equipos:
            pts=0; gf=0; gc=0; pj=0
            for p in resultados_grupos.values():
                if p['equipo_A']==eq:
                    pj+=1; gf+=p['goles_A']; gc+=p['goles_B']
                    if p['goles_A']>p['goles_B']: pts+=3
                    elif p['goles_A']==p['goles_B']: pts+=1
                elif p['equipo_B']==eq:
                    pj+=1; gf+=p['goles_B']; gc+=p['goles_A']
                    if p['goles_B']>p['goles_A']: pts+=3
                    elif p['goles_B']==p['goles_A']: pts+=1
            tabla.append({'Grupo':g,'Equipo':eq,'PJ':pj,'Pts':pts,'GF':gf,'GC':gc,'Dif':gf-gc})
    return pd.DataFrame(tabla).sort_values(by=['Grupo','Pts','Dif','GF'],ascending=[True,False,False,False]).reset_index(drop=True)

def obtener_clasificados(df_tabla):
    posiciones={}; terceros=[]
    for g in GRUPOS.keys():
        eqs=df_tabla[df_tabla['Grupo']==g].to_dict('records')
        if len(eqs)==4:
            posiciones[f"1{g}"]=eqs[0]['Equipo']; posiciones[f"2{g}"]=eqs[1]['Equipo']
            terceros.append(eqs[2])
    terceros=sorted(terceros,key=lambda x:(x['Pts'],x['Dif'],x['GF']),reverse=True)
    for i in range(min(8,len(terceros))): posiciones[f"3_{i+1}"]=terceros[i]['Equipo']
    return posiciones

def calcular_puntos(df_tabla):
    puntos = {eq:0 for eq in VALOR_EQUIPOS.keys()}
    detalles = {eq: {"Gr(Partidos)":0, "Gr(Goles)":0, "Gr(Bono)":0, "Eliminatorias":0, "Pichichi":0} for eq in VALOR_EQUIPOS.keys()}
    
    for p in resultados_grupos.values():
        eA,eB=p['equipo_A'],p['equipo_B']; dif=p['goles_A']-p['goles_B']
        if dif>=3: detalles[eA]["Gr(Goles)"]+=1; detalles[eB]["Gr(Goles)"]-=1
        elif dif<=-3: detalles[eB]["Gr(Goles)"]+=1; detalles[eA]["Gr(Goles)"]-=1
        if dif>0: detalles[eA]["Gr(Partidos)"]+=3
        elif dif<0: detalles[eB]["Gr(Partidos)"]+=3
        else: detalles[eA]["Gr(Partidos)"]+=1; detalles[eB]["Gr(Partidos)"]+=1
        
    terceros_bono=[]
    for g in GRUPOS.keys():
        partidos = [p for p in resultados_grupos.values() if p['equipo_A'] in GRUPOS[g]]
        eqs=df_tabla[df_tabla['Grupo']==g].to_dict('records')
        
        if len(partidos) == 6 and len(eqs) == 4:
            detalles[eqs[0]['Equipo']]["Gr(Bono)"]+=3; detalles[eqs[1]['Equipo']]["Gr(Bono)"]+=2
            detalles[eqs[3]['Equipo']]["Gr(Bono)"]-=1
            terceros_bono.append(eqs[2])
            
    terceros_bono=sorted(terceros_bono,key=lambda x:(x['Pts'],x['Dif'],x['GF']),reverse=True)
    for i in range(min(8,len(terceros_bono))): detalles[terceros_bono[i]['Equipo']]["Gr(Bono)"]+=1
    
    for m_id,p in resultados_elim.items():
        eA,eB,res,gan=p['equipo_A'],p['equipo_B'],p['resolucion'],p['ganador']
        dif=p['goles_A']-p['goles_B']
        if m_id=="M103 (3º y 4º)": detalles[gan]["Eliminatorias"]+=3; continue
        if dif>=3: detalles[eA]["Eliminatorias"]+=1; detalles[eB]["Eliminatorias"]-=1
        elif dif<=-3: detalles[eB]["Eliminatorias"]+=1; detalles[eA]["Eliminatorias"]-=1
        if res=="90 min":
            if dif>0: detalles[eA]["Eliminatorias"]+=4
            elif dif<0: detalles[eB]["Eliminatorias"]+=4
        elif res=="Prórroga":
            if dif>0: detalles[eA]["Eliminatorias"]+=3
            elif dif<0: detalles[eB]["Eliminatorias"]+=3
        elif res=="Penaltis":
            detalles[eA]["Eliminatorias"]+=1; detalles[eB]["Eliminatorias"]+=1; detalles[gan]["Eliminatorias"]+=1
        if m_id=="M104 (FINAL)":
            detalles[gan]["Eliminatorias"]+=10; detalles[eB if gan==eA else eA]["Eliminatorias"]+=6
            
    if pichichi: detalles[pichichi]["Pichichi"]+=2
    for eq in VALOR_EQUIPOS.keys(): puntos[eq] = sum(detalles[eq].values())
    return puntos, detalles

df_tabla   = obtener_tabla_grupos()
pos_grupos = obtener_clasificados(df_tabla)


# ══════════════════════════════════════════
# CABECERA Y MENÚ SUPERIOR (NUEVO DISEÑO APP)
# ══════════════════════════════════════════
col_title, col_btn = st.columns([3, 1])
with col_title:
    st.markdown(f"<h3 style='color:#FFD700; margin:0; padding-top:5px;'>🏆 Liga: {liga_actual}</h3>", unsafe_allow_html=True)
with col_btn:
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.liga_actual = ""
        st.rerun()

st.write("") # Espacio

# Menú principal desplegable
opciones_menu = ["📊 Clasificación General", "🔥 Tabla de Goleadores", "🏆 Tabla de Grupos", "📅 Resultados Partidos", "⚽ Cuadro Eliminatorias"]

if st.session_state.admin:
    opciones_menu += [
        "--- ZONA ADMINISTRADOR ---",
        "👥 Participantes (Liga actual)", 
        "🔧 Resultados Grupos (Global)", 
        "⚔️ Resultados Elim. (Global)", 
        "🥇 Goles Equipo (Global)", 
        "🎯 Goles Jugadores (Global)", 
        "➕ Ajuste Puntos (Liga actual)"
    ]

menu = st.selectbox("👉 Elige qué quieres ver:", opciones_menu)

if menu == "--- ZONA ADMINISTRADOR ---":
    st.info("👆 Por favor, selecciona una herramienta de administrador en el menú desplegable.")
    st.stop()


# ══════════════════════════════════════════
# CLASIFICACIÓN GENERAL
# ══════════════════════════════════════════
if menu == "📊 Clasificación General":
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b4/Lionel-Messi-Argentina-2022.jpg", use_container_width=True)
    st.markdown('<div class="titulo-principal">📊 Clasificación General</div>', unsafe_allow_html=True)
    st.write("")
    
    if not participantes:
        st.warning(f"Aún no hay participantes registrados en la liga '{liga_actual}'. Si eres administrador, usa el menú para añadirlos.")
    else:
        st.caption(f"🏆 Mostrando resultados para la liga: **{liga_actual}**")
        pts, detalles = calcular_puntos(df_tabla)
        lista_clasif = []
        for a, eqs in participantes.items():
            base_puntos = sum(pts[eq] for eq in eqs)
            puntos_extra = ajustes_manuales.get(a, 0)
            lista_clasif.append({"Jugador": a, "Puntos": base_puntos + puntos_extra, "Equipos": eqs, "Extra": puntos_extra})
            
        clasif = sorted(lista_clasif, key=lambda x: x["Puntos"], reverse=True)
        medallas = ["🥇", "🥈", "🥉"]
        for i, row in enumerate(clasif):
            med = medallas[i] if i < 3 else f"#{i+1}"
            equipos_str = " ".join([f"{flag(e)}" for e in row["Equipos"]])
            nombres_str = ", ".join(row["Equipos"])
            extra_badge = f'<span style="font-size:0.5em; background:rgba(255,255,255,0.2); padding:2px 5px; border-radius:4px; margin-left:10px;">Ajuste: {row["Extra"]} pts</span>' if row["Extra"] != 0 else ""

            # Tarjeta principal del jugador
            st.markdown(f'<div class="card" style="margin-bottom: 10px;"><div style="display:flex; justify-content:space-between; align-items:center;"><div><span style="font-size:1.5em">{med}</span><span style="font-size:1.3em; font-weight:700; margin-left:10px; color:white;">{row["Jugador"]}</span>{extra_badge}<br><small style="color:#888">{equipos_str} {nombres_str}</small></div><div style="font-size:2em; font-weight:900; color:#FFD700">{row["Puntos"]}<span style="font-size:0.4em; color:#888"> pts</span></div></div></div>', unsafe_allow_html=True)
            
            # --- POPOVERS ESTILIZADOS ---
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1.popover("🔍 Ver Puntos", use_container_width=True):
                st.markdown(f"#### Desglose de Puntos")
                for eq in row["Equipos"]:
                    det = detalles[eq]
                    desglose = []
                    if det['Gr(Partidos)'] != 0: desglose.append(f"Grupos: {det['Gr(Partidos)']}")
                    if det['Gr(Goles)'] != 0: desglose.append(f"Goleadas: {det['Gr(Goles)']}")
                    if det['Gr(Bono)'] != 0: desglose.append(f"Bono: {det['Gr(Bono)']}")
                    if det['Eliminatorias'] != 0: desglose.append(f"Eliminatorias: {det['Eliminatorias']}")
                    if det['Pichichi'] != 0: desglose.append(f"Pichichi: {det['Pichichi']}")
                    str_desglose = " · ".join(desglose) if desglose else "Aún sin puntos"
                    
                    st.markdown(f"""
                    <div class="mini-card" style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:1.1em; color:white;">{flag(eq)} <b>{eq}</b></span><br>
                            <span style="font-size:0.75em; color:#aaa;">{str_desglose}</span>
                        </div>
                        <div style="background-color:#FFD700; color:#000; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:1.1em;">
                            {pts[eq]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_btn2.popover("⚽ Ver Partidos", use_container_width=True):
                st.markdown(f"#### Historial de Partidos")
                html_partidos = ""
                for g, equipos in GRUPOS.items():
                    cruces_g = [(equipos[0],equipos[1]), (equipos[2],equipos[3]), (equipos[0],equipos[2]), (equipos[1],equipos[3]), (equipos[0],equipos[3]), (equipos[1],equipos[2])]
                    for eA, eB in cruces_g:
                        if eA in row["Equipos"] or eB in row["Equipos"]:
                            fecha_str = obtener_fecha_grupo(eA, eB, g)
                            key = f"{eA}_{eB}"
                            col_A, bold_A = ("#FFD700", "bold") if eA in row["Equipos"] else ("#888", "normal")
                            col_B, bold_B = ("#FFD700", "bold") if eB in row["Equipos"] else ("#888", "normal")
                            
                            if key in resultados_grupos:
                                p = resultados_grupos[key]
                                html_partidos += f"""
                                <div class="mini-card">
                                    <div style="text-align:center; font-size:0.65em; color:#888; margin-bottom:6px;">🕒 {fecha_str} - Grupo {g}</div>
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="color:{col_A}; font-weight:{bold_A}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> 
                                        <span style="background:#252d3a; border: 1px solid #444; padding:3px 10px; border-radius:6px; color:white; font-weight:bold;">{p['goles_A']} - {p['goles_B']}</span> 
                                        <span style="color:{col_B}; font-weight:{bold_B}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span>
                                    </div>
                                </div>"""
                            else:
                                html_partidos += f"""
                                <div class="mini-card">
                                    <div style="text-align:center; font-size:0.65em; color:#888; margin-bottom:6px;">🕒 {fecha_str} - Grupo {g}</div>
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="color:{col_A}; font-weight:{bold_A}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> 
                                        <span style="color:#555; font-weight:bold;">vs</span> 
                                        <span style="color:{col_B}; font-weight:{bold_B}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span>
                                    </div>
                                </div>"""
                                
                for m_id, p in resultados_elim.items():
                    eA, eB = p['equipo_A'], p['equipo_B']
                    if eA in row["Equipos"] or eB in row["Equipos"]:
                        fecha_elim = FECHAS_ELIM.get(m_id, "")
                        col_A, bold_A = ("#FFD700", "bold") if eA in row["Equipos"] else ("#888", "normal")
                        col_B, bold_B = ("#FFD700", "bold") if eB in row["Equipos"] else ("#888", "normal")
                        res_extra = f"<br><span style='font-size:0.7em; color:#888; font-weight:normal;'>{p['resolucion']}</span>" if p['resolucion'] != "90 min" else ""
                        
                        html_partidos += f"""
                        <div class="mini-card">
                            <div style="text-align:center; font-size:0.65em; color:#888; margin-bottom:6px;">🕒 {fecha_elim} - {m_id}</div>
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="color:{col_A}; font-weight:{bold_A}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> 
                                <span style="background:#252d3a; border: 1px solid #444; padding:3px 10px; border-radius:6px; color:white; font-weight:bold; text-align:center; line-height:1.2;">{p['goles_A']} - {p['goles_B']}{res_extra}</span> 
                                <span style="color:{col_B}; font-weight:{bold_B}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span>
                            </div>
                        </div>"""
                
                if html_partidos == "": st.caption("Aún no tienen partidos.")
                else: st.markdown(html_partidos, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TOP GOLEADORES
# ══════════════════════════════════════════
elif menu == "🔥 Tabla de Goleadores":
    st.markdown('<div class="titulo-principal">🔥 Top Pichichis</div>', unsafe_allow_html=True)
    st.write("")
    if not goleadores_reales:
        st.info("Aún no se han registrado goles en el torneo.")
    else:
        for i, j in enumerate(goleadores_reales):
            med = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
            penaltis = j.get('goles_penalti', 0)
            texto_penalti = f"<br><span style='font-size:0.5em; color:#FF8C00; font-weight:normal;'>({penaltis} de penalti)</span>" if penaltis > 0 else ""
            
            st.markdown(f"""
            <div class="card" style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-left: 5px solid #FFD700;">
                <div style="font-size:1.4em; color:#ffffff; font-weight:bold;">
                    {med} {j['jugador']} 
                    <span style="color:#cccccc; font-size:0.7em; margin-left:10px; font-weight:normal;">
                        {flag(j['equipo'])} {j['equipo']}
                    </span>
                </div>
                <div style="font-size:1.6em; font-weight:900; color:#FFD700; min-width:80px; text-align:right; line-height:1.1;">
                    {j['goles']} ⚽{texto_penalti}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TABLA DE GRUPOS
# ══════════════════════════════════════════
elif menu == "🏆 Tabla de Grupos":
    st.markdown('<div class="titulo-principal">🏆 Tabla de Grupos</div>', unsafe_allow_html=True)
    st.write("")
    mejores_3 = [pos_grupos.get(f"3_{i+1}") for i in range(8)]
    cols = st.columns(3)
    for idx, (grupo, _) in enumerate(GRUPOS.items()):
        with cols[idx % 3]:
            df_g = df_tabla[df_tabla['Grupo']==grupo][['Equipo','PJ','Pts','GF','GC','Dif']].reset_index(drop=True)
            df_g.index += 1
            df_g[''] = df_g['Equipo'].apply(flag)
            st.markdown(f"#### Grupo {grupo}")
            def hl(row):
                if row.name <= 2: return ['background-color:#1a472a;color:white']*len(row)
                if row.name == 3 and row['Equipo'] in mejores_3: return ['background-color:#2d4a1e;color:#90EE90']*len(row)
                return ['color:#888']*len(row)
            st.dataframe(df_g[['','Equipo','PJ','Pts','GF','GC','Dif']].style.apply(hl,axis=1), use_container_width=True, hide_index=False)

# ══════════════════════════════════════════
# RESULTADOS PARTIDOS PÚBLICOS
# ══════════════════════════════════════════
elif menu == "📅 Resultados Partidos":
    st.markdown('<div class="titulo-principal">📅 Resultados de los Partidos</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("### Fase de Grupos")
    c1, c2, c3 = st.columns(3)
    col_idx = 0
    for g, equipos in GRUPOS.items():
        with [c1, c2, c3][col_idx % 3]:
            st.markdown(f"#### Grupo {g}")
            cruces = [(equipos[0],equipos[1]), (equipos[2],equipos[3]), (equipos[0],equipos[2]), (equipos[1],equipos[3]), (equipos[0],equipos[3]), (equipos[1],equipos[2])]
            html_partidos = ""
            for eA, eB in cruces:
                key = f"{eA}_{eB}"; fecha_str = obtener_fecha_grupo(eA, eB, g)
                if key in resultados_grupos:
                    r = resultados_grupos[key]
                    html_partidos += f'<div style="display:flex; flex-direction:column; border-bottom:1px solid #2d3748; padding: 6px 0;"><div style="font-size:0.65em; color:#888; text-align:center; margin-bottom:2px;">🕒 {fecha_str}</div><div style="display:grid; grid-template-columns: 1fr auto 1fr; gap:10px; align-items:center; font-size:0.9em;"><span style="color:white; text-align:right;">{flag(eA)} {eA}</span> <span style="background:#FFD700; color:#000; padding:2px 8px; border-radius:4px; font-weight:bold; text-align:center;">{r["goles_A"]} - {r["goles_B"]}</span> <span style="color:white; text-align:left;">{eB} {flag(eB)}</span></div></div>'
                else:
                    html_partidos += f'<div style="display:flex; flex-direction:column; border-bottom:1px solid #2d3748; padding: 6px 0;"><div style="font-size:0.65em; color:#888; text-align:center; margin-bottom:2px;">🕒 {fecha_str}</div><div style="display:grid; grid-template-columns: 1fr auto 1fr; gap:10px; align-items:center; font-size:0.9em;"><span style="text-align:right; color:#888;">{flag(eA)} {eA}</span> <span style="text-align:center; color:#555;">vs</span> <span style="text-align:left; color:#888;">{eB} {flag(eB)}</span></div></div>'
            st.markdown(f'<div class="card" style="padding:10px;">{html_partidos}</div>', unsafe_allow_html=True)
        col_idx += 1

    st.divider()
    st.markdown("### Eliminatorias")
    if resultados_elim:
        c1_elim, c2_elim = st.columns(2)
        for i, (m_id, r) in enumerate(resultados_elim.items()):
            eA, eB, ganador = r['equipo_A'], r['equipo_B'], r['ganador']
            with [c1_elim, c2_elim][i % 2]:
                st.markdown(f"""
                <div class="card" style="padding:15px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8em; color:#888; margin-bottom:5px;"><span>{m_id} · {r['resolucion']}</span><span>🕒 {FECHAS_ELIM.get(m_id, "")}</span></div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:{'bold' if ganador==eA else 'normal'}; color:{'#FFD700' if ganador==eA else 'white'};">{flag(eA)} {eA}</span>
                        <span style="background:#FFD700; color:#000; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:1.1em;">{r['goles_A']} - {r['goles_B']}</span>
                        <span style="font-weight:{'bold' if ganador==eB else 'normal'}; color:{'#FFD700' if ganador==eB else 'white'};">{eB} {flag(eB)}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# CUADRO ELIMINATORIAS
# ══════════════════════════════════════════
elif menu == "⚽ Cuadro Eliminatorias":
    st.markdown('<div class="titulo-principal">⚽ Cuadro de Eliminatorias</div>', unsafe_allow_html=True)
    st.write("")
    def qu_gan(m_id, perdedor=False):
        if m_id in resultados_elim: return resultados_elim[m_id]['perdedor' if perdedor else 'ganador']
        return f"❓"
    def mostrar_cruce(m_id, eA, eB):
        d = resultados_elim.get(m_id)
        fA, fB = (flag(eA) if eA in VALOR_EQUIPOS else "❓"), (flag(eB) if eB in VALOR_EQUIPOS else "❓")
        if d:
            gan = d['ganador']
            st.markdown(f"""<div class="card" style="padding:12px"><div style="display:flex; justify-content:space-between; font-size:0.75em;color:#888;margin-bottom:4px"><span>{m_id}</span> <span>🕒 {FECHAS_ELIM.get(m_id, "")}</span></div><div style="display:flex;justify-content:space-between;align-items:center"><span style="{'font-weight:900;color:#FFD700' if gan==eA else 'color:#888'}">{fA} {eA}</span><span class="resultado-badge">{d['goles_A']} - {d['goles_B']}</span><span style="{'font-weight:900;color:#FFD700' if gan==eB else 'color:#888'}">{eB} {fB}</span></div><div style="text-align:center;margin-top:6px;font-size:0.8em;color:#888">{d['resolucion']} · 🏆 <b style="color:#FFD700">{gan}</b></div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="card" style="padding:12px;border:1px dashed #2d3748"><div style="display:flex; justify-content:space-between; font-size:0.75em;color:#888;margin-bottom:4px"><span>{m_id}</span> <span>🕒 {FECHAS_ELIM.get(m_id, "")}</span></div><div style="display:flex;justify-content:space-between;align-items:center;color:#555"><span>{fA} {eA}</span><span style="color:#333">vs</span><span>{fB} {eB}</span></div></div>""", unsafe_allow_html=True)

    c16 = st.columns(4); st.markdown("### 🔵 Dieciseisavos de Final")
    for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items()):
        with c16[i%4]: mostrar_cruce(m_id, pos_grupos.get(c1,c1), pos_grupos.get(c2,c2))
    c8 = st.columns(4); st.markdown("### 🟡 Octavos de Final")
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items()):
        with c8[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    c4 = st.columns(4); st.markdown("### 🟠 Cuartos de Final")
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items()):
        with c4[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    c2 = st.columns(2); st.markdown("### 🔴 Semifinales")
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items()):
        with c2[i]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    cf = st.columns(2); st.markdown("### 🏆 Finales")
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items()):
        with cf[i]: mostrar_cruce(m_id, qu_gan(m1.replace("_L",""),perdedor="_L" in m1), qu_gan(m2.replace("_L",""),perdedor="_L" in m2))


# ══════════════════════════════════════════
# ZONA ADMIN: PARTICIPANTES
# ══════════════════════════════════════════
elif menu == "👥 Participantes (Liga actual)":
    st.markdown('<div class="titulo-principal">👥 Gestión de Participantes</div>', unsafe_allow_html=True)
    st.info(f"Estás añadiendo jugadores a la liga: **{liga_actual}**")
    
    # ATENCIÓN: Lo he sacado del "form" para que se actualicen los puntos en vivo al usar el móvil
    nombre = st.text_input("Nombre del participante")
    equipos_sel = st.multiselect("Selecciones (máx 30 pts)", list(VALOR_EQUIPOS.keys()), format_func=lambda x: f"{flag(x)} {x} ({VALOR_EQUIPOS[x]} pts)")
    coste = sum(VALOR_EQUIPOS[e] for e in equipos_sel)
    
    st.markdown(f"Coste: <b style='color:{'#90EE90' if coste <= 30 else '#FF6347'}'>{coste} / 30 pts</b>", unsafe_allow_html=True)
    
    if st.button("✅ Añadir / Actualizar", use_container_width=True):
        if not nombre: st.error("Falta el nombre.")
        elif coste > 30: st.error("Demasiados puntos.")
        else: 
            participantes[nombre] = equipos_sel
            guardar_participantes(liga_actual, participantes)
            st.success(f"✅ Guardado en {liga_actual}")
            st.rerun()
    
    if participantes:
        st.divider()
        st.markdown(f"### Jugadores en {liga_actual}")
        for nom, eqs in participantes.items():
            c1,c2 = st.columns([5,1])
            c1.markdown(f"**{nom}** ({sum(VALOR_EQUIPOS[e] for e in eqs)} pts) {' '.join([flag(e) for e in eqs])}")
            if c2.button("🗑️", key=f"del_{nom}"): 
                del participantes[nom]
                guardar_participantes(liga_actual, participantes)
                st.rerun()

# ══════════════════════════════════════════
# ZONA ADMIN: RESULTADOS GRUPOS
# ══════════════════════════════════════════
elif menu == "🔧 Resultados Grupos (Global)":
    st.info("🌐 IMPORTANTE: Lo que cambies aquí afectará a TODAS las ligas a la vez.")
    cols = st.columns(3)
    for idx,(grupo,eq) in enumerate(GRUPOS.items()):
        with cols[idx%3]:
            st.markdown(f"#### Grupo {grupo}")
            for eA,eB in [(eq[0],eq[1]),(eq[2],eq[3]),(eq[0],eq[2]),(eq[1],eq[3]),(eq[0],eq[3]),(eq[1],eq[2])]:
                key = f"{eA}_{eB}"
                g = resultados_grupos.get(key,{})
                c1,c2,c3,c4 = st.columns([3,1,1,3])
                c1.markdown(f"{flag(eA)} {eA}"); gA = c2.text_input("",key=f"i_A_{key}",value=g.get("goles_A",""),label_visibility="collapsed")
                gB = c3.text_input("",key=f"i_B_{key}",value=g.get("goles_B",""),label_visibility="collapsed"); c4.markdown(f"{eB} {flag(eB)}")
                if gA.isdigit() and gB.isdigit() and (not g or g.get("goles_A")!=int(gA) or g.get("goles_B")!=int(gB)):
                    guardar_resultado_grupo(key,eA,eB,int(gA),int(gB))
                elif g.get("goles_A","")!="" and gA=="" and gB=="": borrar_resultado_grupo(key)

# ══════════════════════════════════════════
# ZONA ADMIN: RESULTADOS ELIMINATORIAS
# ══════════════════════════════════════════
elif menu == "⚔️ Resultados Elim. (Global)":
    st.info("🌐 IMPORTANTE: Lo que cambies aquí afectará a TODAS las ligas a la vez.")
    def renderizar(m_id, eA, eB, col):
        with col:
            st.markdown(f"**{m_id}**")
            if eA not in VALOR_EQUIPOS or eB not in VALOR_EQUIPOS: return
            g = resultados_elim.get(m_id,{})
            c1,c2 = st.columns(2)
            gA = c1.text_input(f"{flag(eA)} {eA}",key=f"ga_{m_id}",value=g.get("goles_A",""))
            gB = c2.text_input(f"{flag(eB)} {eB}",key=f"gb_{m_id}",value=g.get("goles_B",""))
            res = st.selectbox("Decisión",["90 min","Prórroga","Penaltis"],index=["90 min","Prórroga","Penaltis"].index(g.get("resolucion","90 min")),key=f"res_{m_id}")
            gan_pen = st.selectbox("Ganó penaltis:",[eA,eB],index=[eA,eB].index(g.get("ganador",eA)) if g.get("ganador",eA) in [eA,eB] else 0,key=f"pen_{m_id}") if res=="Penaltis" else None
            if gA.isdigit() and gB.isdigit():
                gA_i,gB_i = int(gA),int(gB)
                if gA_i>gB_i: gan,perd=eA,eB
                elif gB_i>gA_i: gan,perd=eB,eA
                else: 
                    if res!="Penaltis": return
                    gan, perd = gan_pen, eB if gan_pen==eA else eA
                if not g or g.get("goles_A")!=gA_i or g.get("goles_B")!=gB_i or g.get("resolucion")!=res or g.get("ganador")!=gan:
                    guardar_resultado_elim(m_id,eA,eB,gA_i,gB_i,res,gan,perd)
            elif g.get("goles_A","")!="" and gA=="" and gB=="": borrar_resultado_elim(m_id)
            
    c16=st.columns(4); [renderizar(m_id,pos_grupos.get(c1,c1),pos_grupos.get(c2,c2),c16[i%4]) for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items())]
    c8=st.columns(4); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c8[i%4]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items())]
    c4=st.columns(4); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c4[i%4]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items())]
    c2=st.columns(2); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c2[i]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items())]
    cf=st.columns(2); [renderizar(m_id,qu_gan(m1.replace("_L",""),perdedor="_L" in m1),qu_gan(m2.replace("_L",""),perdedor="_L" in m2),cf[i]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items())]

# ══════════════════════════════════════════
# ZONA ADMIN: GOLES EQUIPOS Y JUGADORES
# ══════════════════════════════════════════
elif menu == "🥇 Goles Equipo (Global)":
    st.info("🌐 GLOBAL: La selección que elijas dará +2 pts a todos los que la tengan, en TODAS las ligas.")
    sel = st.selectbox("Selección Pichichi", ["Ninguno aún..."] + list(VALOR_EQUIPOS.keys()), index=(["Ninguno aún..."] + list(VALOR_EQUIPOS.keys())).index(pichichi) if pichichi else 0)
    if st.button("💾 Guardar",use_container_width=True): guardar_pichichi(sel if sel!="Ninguno aún..." else None); st.success("Guardado")

elif menu == "🎯 Goles Jugadores (Global)":
    st.markdown('<div class="titulo-principal">🎯 Añadir Goles (Pichichis)</div>', unsafe_allow_html=True)
    st.info("🌐 GLOBAL: Los goles que sumes aquí aparecerán en la lista pública de todas las ligas.")
    
    jugadores_creados = sorted([j['jugador'] for j in goleadores_reales])
    opciones_jugador = ["✨ CREAR NUEVO JUGADOR ✨"] + jugadores_creados
    
    jugador_sel = st.selectbox("1. Selecciona el jugador", opciones_jugador)
    
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    
    if jugador_sel == "✨ CREAR NUEVO JUGADOR ✨":
        equipo = c1.selectbox("Selección", list(VALOR_EQUIPOS.keys()))
        jugador = c2.text_input("Nombre (Ej: Morata)")
    else:
        jugador = jugador_sel
        equipo_existente = next((j['equipo'] for j in goleadores_reales if j['jugador'] == jugador), list(VALOR_EQUIPOS.keys())[0])
        idx_equipo = list(VALOR_EQUIPOS.keys()).index(equipo_existente) if equipo_existente in VALOR_EQUIPOS else 0
        equipo = c1.selectbox("Selección", list(VALOR_EQUIPOS.keys()), index=idx_equipo, disabled=True)
        c2.text_input("Nombre", value=jugador, disabled=True)
        
    goles_nuevos = c3.number_input("Goles a sumar", min_value=1, value=1)
    penaltis_nuevos = c4.number_input("De penalti (sumar)", min_value=0, value=0)
    
    if st.button("➕ Sumar Goles", use_container_width=True):
        if jugador:
            jugador_formateado = jugador.title()
            existente = next((j for j in goleadores_reales if j['jugador'].lower() == jugador.lower()), None)
            
            if existente:
                total_goles = existente['goles'] + goles_nuevos
                total_pen = existente.get('goles_penalti', 0) + penaltis_nuevos
            else:
                total_goles = goles_nuevos
                total_pen = penaltis_nuevos

            if total_pen > total_goles:
                st.error("Los goles de penalti totales no pueden ser mayores que los totales.")
            else:
                guardar_goleador_real(jugador_formateado, equipo, total_goles, total_pen)
                st.success(f"✅ ¡Sumados! {jugador_formateado} ({equipo}) tiene ahora {total_goles} goles en total.")
                st.rerun()
        else:
            st.error("Escribe un nombre.")
            
    if goleadores_reales:
        st.divider()
        st.markdown("### Jugadores registrados (Total Acumulado)")
        for j in goleadores_reales:
            col1, col2 = st.columns([5,1])
            pen_text = f" <span style='color:#FF8C00; font-size:0.85em;'>({j.get('goles_penalti', 0)} de penalti)</span>" if j.get('goles_penalti', 0) > 0 else ""
            col1.markdown(f"<div style='background:#1e2530; padding:10px; border-radius:8px; border:1px solid #4a5568;'><span style='color:white; font-weight:bold; font-size:1.1em;'>{flag(j['equipo'])} {j['jugador']}</span> <span style='color:#FFD700; font-weight:bold; margin-left:10px;'>{j['goles']} goles</span>{pen_text}</div>", unsafe_allow_html=True)
            if col2.button("🗑️ Borrar", key=f"del_gol_{j['jugador']}"):
                borrar_goleador_real(j['jugador'])
                st.rerun()

# ══════════════════════════════════════════
# ZONA ADMIN: AJUSTE PUNTOS
# ══════════════════════════════════════════
elif menu == "➕ Ajuste Puntos (Liga actual)":
    st.markdown('<div class="titulo-principal">➕ Ajuste Manual de Puntos</div>', unsafe_allow_html=True)
    if not participantes:
        st.warning(f"No hay participantes en la liga '{liga_actual}'.")
    else:
        st.info(f"Ajustando puntos para jugadores de la liga: **{liga_actual}**")
        participante_sel = st.selectbox("Jugador:", list(participantes.keys()))
        if participante_sel:
            nuevo_valor = st.number_input("Puntos extra:", value=ajustes_manuales.get(participante_sel, 0))
            if st.button("💾 Aplicar"): 
                guardar_ajuste_puntos(liga_actual, participante_sel, nuevo_valor)
                st.rerun()

# ══════════════════════════════════════════
# PIE DE PÁGINA (BOTÓN ADMIN INVISIBLE)
# ══════════════════════════════════════════
st.write("")
st.write("")
st.write("")
st.divider()

if not st.session_state.admin:
    with st.expander("⚙️ Acceso Administrador"):
        pwd = st.text_input("Contraseña Admin", type="password", key="pwd_app")
        if st.button("Entrar Admin", key="btn_admin"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin = True; st.rerun()
            else:
                st.error("Clave incorrecta")
else:
    if st.button("🔴 Cerrar sesión Administrador", use_container_width=True):
        st.session_state.admin = False; st.rerun()
