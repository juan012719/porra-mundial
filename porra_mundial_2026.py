import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Porra Mundial 2026 🌍", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizado
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { display: none !important; }
    
    .stApp, .stMarkdown, p, label { color: #f0f2f6 !important; }
    .main { background-color: #0e1117; }
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%); }
    
    [data-testid="block-container"] { max-width: 650px; margin: 0 auto; padding-top: 2rem; }
    
    /* Botones blindados: Fondo dorado, letra negra siempre */
    button[kind="secondary"], button[kind="primary"], div.stButton > button {
        background-color: #FFD700 !important; border: 2px solid #B8860B !important; border-radius: 8px !important; margin-top: -5px; margin-bottom: 15px;
    }
    button[kind="secondary"] p, button[kind="primary"] p, div.stButton > button p {
        color: #000000 !important; font-weight: 900 !important; font-size: 1.1em !important;
    }
    button:hover { background-color: #FFA500 !important; }
    
    .titulo-principal { text-align: center; font-size: 2.5em; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF6B35, #FFD700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 20px 0 5px 0; letter-spacing: 2px; }
    .titulo-landing { text-align: center; font-size: clamp(2.5em, 8vw, 4.5em); font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF6B35, #FFD700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 10px 0 10px 0; letter-spacing: 2px; }
    .subtitulo { text-align: center; color: #aaa !important; font-size: clamp(0.9em, 3vw, 1.2em); margin-bottom: 30px; letter-spacing: 5px; }
    
    .card { background: linear-gradient(135deg, #1e2530, #252d3a); border: 1px solid #2d3748; border-radius: 12px; padding: 20px; margin: 10px 0 5px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .mini-card { background-color: #1e2530; border: 1px solid #333; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    .resultado-badge { background: #FFD700; color: #000 !important; border-radius: 6px; padding: 2px 8px; font-weight: bold; font-size: 0.9em; }
    
    .centrado-absoluto { max-width: 500px; margin: 15vh auto 0 auto; padding: 15px; }
</style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

BANDERAS = {
    "ESPAÑA": "🇪🇸", "FRANCIA": "🇫🇷", "INGLATERRA": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "BRASIL": "🇧🇷", "ARGENTINA": "🇦🇷",
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

def flag(eq): return BANDERAS.get(eq, "🏳️")

VALOR_EQUIPOS = {
    "ESPAÑA":29,"FRANCIA":27,"INGLATERRA":26,"BRASIL":24,"ARGENTINA":24,"PORTUGAL":20,"ALEMANIA":20,"PAÍSES BAJOS":19,"NORUEGA":18,"BÉLGICA":17,
    "COLOMBIA":17,"JAPÓN":15,"USA":14,"MARRUECOS":14,"URUGUAY":14,"SUIZA":13,"MÉXICO":13,"CROACIA":13,"TURQUÍA":11,"ECUADOR":10,
    "SENEGAL":10,"SUECIA":9,"CANADÁ":9,"AUSTRIA":9,"PARAGUAY":8,"ESCOCIA":8,"BOSNIA HERZEG.":8,"COSTA MARFIL":7,"EGIPTO":7,"CHEQUIA":7,
    "GHANA":6,"ARGELIA":6,"COREA DEL SUR":5,"TÚNEZ":5,"AUSTRALIA":5,"IRÁN":4,"CONGO":3,"SUDÁFRICA":3,"CATAR":3,"ARABIA SAUDÍ":2,
    "PANAMÁ":2,"NUEVA ZELANDA":2,"IRAK":2,"CABO VERDE":2,"CURACAO":2,"UZBEQUISTÁN":2,"JORDANIA":1,"HAITÍ":0
}

GRUPOS = {
    "A":["MÉXICO","SUDÁFRICA","COREA DEL SUR","CHEQUIA"],"B":["CANADÁ","BOSNIA HERZEG.","CATAR","SUIZA"],"C":["BRASIL","MARRUECOS","HAITÍ","ESCOCIA"],"D":["USA","PARAGUAY","AUSTRALIA","TURQUÍA"],
    "E":["ALEMANIA","CURACAO","COSTA MARFIL","ECUADOR"],"F":["PAÍSES BAJOS","JAPÓN","SUECIA","TÚNEZ"],"G":["BÉLGICA","EGIPTO","IRÁN","NUEVA ZELANDA"],"H":["ESPAÑA","CABO VERDE","ARABIA SAUDÍ","URUGUAY"],
    "I":["FRANCIA","SENEGAL","IRAK","NORUEGA"],"J":["ARGENTINA","ARGELIA","AUSTRIA","JORDANIA"],"K":["PORTUGAL","CONGO","UZBEQUISTÁN","COLOMBIA"],"L":["INGLATERRA","CROACIA","GHANA","PANAMÁ"]
}

EMPAREJAMIENTOS_16VOS = {"M73":("2A","2B"),"M74":("1E","3_1"),"M75":("1F","2C"),"M76":("1C","2F"),"M77":("1I","3_2"),"M78":("2E","2I"),"M79":("1A","3_3"),"M80":("1L","3_4"),"M81":("1D","3_5"),"M82":("1G","3_6"),"M83":("2K","2L"),"M84":("1H","2J"),"M85":("1B","3_7"),"M86":("1J","2H"),"M87":("1K","3_8"),"M88":("2D","2G")}
CRUCES_OCTAVOS = {"M89":("M74","M77"),"M90":("M73","M75"),"M91":("M76","M78"),"M92":("M79","M80"),"M93":("M83","M84"),"M94":("M81","M82"),"M95":("M85","M87"),"M96":("M86","M88")}
CRUCES_CUARTOS = {"M97":("M89","M90"),"M98":("M93","M94"),"M99":("M91","M92"),"M100":("M95","M96")}
CRUCES_SEMIS = {"M101":("M97","M98"),"M102":("M99","M100")}
CRUCES_FINALES = {"M103 (3º y 4º)":("M101_L","M102_L"),"M104 (FINAL)":("M101","M102")}
DIAS_INICIO = {"A":11,"B":12,"C":13,"D":13,"E":14,"F":14,"G":15,"H":15,"I":16,"J":16,"K":17,"L":17}

def obtener_fecha_grupo(eA, eB, grupo):
    if eA=="ESPAÑA" and eB=="CABO VERDE": return "15 Jun - 18:00"
    if eA=="ESPAÑA" and eB=="ARABIA SAUDÍ": return "21 Jun - 18:00"
    if eA=="ESPAÑA" and eB=="URUGUAY": return "25 Jun - 22:00"
    eqs = GRUPOS[grupo]; base = DIAS_INICIO.get(grupo, 11)
    if (eA, eB) == (eqs[0], eqs[1]): dia=base; hora="21:00"
    elif (eA, eB) == (eqs[2], eqs[3]): dia=base+1; hora="18:00"
    elif (eA, eB) == (eqs[0], eqs[2]): dia=base+5; hora="21:00"
    elif (eA, eB) == (eqs[1], eqs[3]): dia=base+6; hora="18:00"
    elif (eA, eB) == (eqs[0], eqs[3]): dia=base+9; hora="22:00"
    else: dia=base+9; hora="18:00"
    mes = "Jul" if dia > 30 else "Jun"
    return f"{dia-30 if dia>30 else dia} {mes} - {hora}"

FECHAS_ELIM = {"M73":"28 Jun - 18:00","M74":"28 Jun - 22:00","M75":"29 Jun - 18:00","M76":"29 Jun - 22:00","M77":"30 Jun - 18:00","M78":"30 Jun - 22:00","M79":"1 Jul - 18:00","M80":"1 Jul - 22:00","M81":"2 Jul - 18:00","M82":"2 Jul - 22:00","M83":"3 Jul - 18:00","M84":"3 Jul - 22:00","M85":"4 Jul - 18:00","M86":"4 Jul - 22:00","M87":"5 Jul - 18:00","M88":"5 Jul - 22:00","M89":"6 Jul - 18:00","M90":"6 Jul - 22:00","M91":"7 Jul - 18:00","M92":"7 Jul - 22:00","M93":"8 Jul - 18:00","M94":"8 Jul - 22:00","M95":"9 Jul - 18:00","M96":"9 Jul - 22:00","M97":"11 Jul - 18:00","M98":"11 Jul - 22:00","M99":"12 Jul - 18:00","M100":"12 Jul - 22:00","M101":"14 Jul - 21:00","M102":"15 Jul - 21:00","M103 (3º y 4º)":"18 Jul - 21:00","M104 (FINAL)":"19 Jul - 21:00"}

@st.cache_resource
def get_supabase(): return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=30)
def cargar_participantes(liga):
    if not liga: return {}
    sb = get_supabase(); rows = sb.table("participantes").select("*").eq("liga", liga).execute().data
    return {r["nombre"]: r["equipos"].split(",") if r["equipos"] else [] for r in rows}

@st.cache_data(ttl=30)
def cargar_ajustes_puntos(liga):
    if not liga: return {}
    try: return {r["nombre"]: r["puntos_extra"] for r in get_supabase().table("ajustes_puntos").select("*").eq("liga", liga).execute().data}
    except: return {}

def guardar_participantes(liga, part_dict):
    if not liga: return
    sb = get_supabase(); sb.table("participantes").delete().eq("liga", liga).execute()
    rows = [{"liga": liga, "nombre": n, "equipos": ",".join(e)} for n, e in part_dict.items()]
    if rows: sb.table("participantes").insert(rows).execute()
    cargar_participantes.clear()

def guardar_ajuste_puntos(liga, nombre, pts):
    if not liga: return
    try: get_supabase().table("ajustes_puntos").upsert({"liga": liga, "nombre": nombre, "puntos_extra": pts}).execute(); cargar_ajustes_puntos.clear()
    except: pass

@st.cache_data(ttl=30)
def cargar_resultados_grupos(): return {r["key"]: {"equipo_A":r["equipo_a"],"equipo_B":r["equipo_b"],"goles_A":r["goles_a"],"goles_B":r["goles_b"]} for r in get_supabase().table("resultados_grupos").select("*").execute().data}

@st.cache_data(ttl=30)
def cargar_resultados_elim(): return {r["key"]: {"equipo_A":r["equipo_a"],"equipo_B":r["equipo_b"],"goles_A":r["goles_a"],"goles_B":r["goles_b"],"resolucion":r["resolucion"],"ganador":r["ganador"],"perdedor":r["perdedor"]} for r in get_supabase().table("resultados_elim").select("*").execute().data}

@st.cache_data(ttl=30)
def cargar_pichichi():
    rows = get_supabase().table("pichichi").select("*").execute().data
    return rows[0]["equipo"] if rows else None

@st.cache_data(ttl=30)
def cargar_pichichis_reales():
    try: return get_supabase().table("pichichis_reales").select("*").order("goles", desc=True).execute().data
    except: return []

def guardar_resultado_grupo(k, eA, eB, gA, gB): get_supabase().table("resultados_grupos").upsert({"key":k,"equipo_a":eA,"equipo_b":eB,"goles_a":gA,"goles_b":gB}).execute(); cargar_resultados_grupos.clear()
def borrar_resultado_grupo(k): get_supabase().table("resultados_grupos").delete().eq("key",k).execute(); cargar_resultados_grupos.clear()
def guardar_resultado_elim(m_id, eA, eB, gA, gB, res, gan, perd): get_supabase().table("resultados_elim").upsert({"key":m_id,"equipo_a":eA,"equipo_b":eB,"goles_a":gA,"goles_b":gB,"resolucion":res,"ganador":gan,"perdedor":perd}).execute(); cargar_resultados_elim.clear()
def borrar_resultado_elim(m_id): get_supabase().table("resultados_elim").delete().eq("key",m_id).execute(); cargar_resultados_elim.clear()
def guardar_pichichi(eq): sb = get_supabase(); sb.table("pichichi").delete().neq("id",0).execute(); sb.table("pichichi").insert({"equipo":eq}).execute() if eq else None; cargar_pichichi.clear()
def guardar_goleador_real(jug, eq, gol, pen):
    try: get_supabase().table("pichichis_reales").upsert({"jugador": jug.title(), "equipo": eq, "goles": gol, "goles_penalti": pen}).execute(); cargar_pichichis_reales.clear()
    except: pass
def borrar_goleador_real(jug):
    try: get_supabase().table("pichichis_reales").delete().eq("jugador", jug).execute(); cargar_pichichis_reales.clear()
    except: pass


# ══════════════════════════════════════════
# CONTROL DE ESTADO (LOGIN Y NAVEGACIÓN)
# ══════════════════════════════════════════
if "liga_actual" not in st.session_state: st.session_state.liga_actual = ""
if "admin" not in st.session_state: st.session_state.admin = False
if "menu_seleccionado" not in st.session_state: st.session_state.menu_seleccionado = "📊 Clasificación General"
if "jugador_detalle" not in st.session_state: st.session_state.jugador_detalle = None

if not st.session_state.liga_actual:
    st.markdown("""
    <div class="centrado-absoluto">
        <div class="titulo-landing">⚽ Porra Mundial 2026</div>
        <div class="subtitulo">USA · CANADA · MEXICO</div>
        <div class="card" style="text-align: center; padding: 40px; margin-top: 30px;">
            <h2 style="color:white; margin-top:0;">🏆 Accede a tu Porra</h2>
            <p style="color: #aaa; margin-bottom: 20px;">Introduce el código secreto para entrar a tu liga privada.</p>
    """, unsafe_allow_html=True)
    
    codigo = st.text_input("Código", placeholder="Ejemplo: CUADRILLA...", label_visibility="collapsed").strip().upper()
    st.write("")
    if st.button("🚀 ENTRAR A MI LIGA", use_container_width=True):
        if codigo:
            if st.session_state.admin: st.session_state.liga_actual = codigo; st.rerun()
            else:
                try:
                    check = get_supabase().table("participantes").select("nombre").eq("liga", codigo).limit(1).execute()
                    if check.data and len(check.data) > 0: st.session_state.liga_actual = codigo; st.rerun()
                    else: st.error(f"❌ La liga '{codigo}' no existe. Comprueba el código.")
                except: st.error("Hubo un problema. Inténtalo de nuevo.")
        else: st.error("Escribe un código.")
            
    st.markdown("</div></div><br><br><br>", unsafe_allow_html=True)
    
    if not st.session_state.admin:
        with st.expander("⚙️ Acceso Administrador"):
            pwd = st.text_input("Contraseña Admin", type="password")
            if st.button("Entrar Admin"):
                if pwd == ADMIN_PASSWORD: st.session_state.admin = True; st.rerun()
                else: st.error("Clave incorrecta")
    else:
        if st.button("🔴 Cerrar sesión Administrador"): st.session_state.admin = False; st.rerun()
    st.stop()


# ══════════════════════════════════════════
# CÁLCULOS GLOBALES (DENTRO DE LA LIGA)
# ══════════════════════════════════════════
liga_actual = st.session_state.liga_actual
participantes = cargar_participantes(liga_actual)
ajustes_manuales = cargar_ajustes_puntos(liga_actual)
resultados_grupos = cargar_resultados_grupos()
resultados_elim = cargar_resultados_elim()
pichichi = cargar_pichichi()
goleadores_reales = cargar_pichichis_reales()

def obtener_tabla_grupos():
    tabla = []
    for g, eqs in GRUPOS.items():
        for eq in eqs:
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

df_tabla = obtener_tabla_grupos()

def obtener_clasificados(df):
    pos={}; ter=[]
    for g in GRUPOS.keys():
        eqs=df[df['Grupo']==g].to_dict('records')
        if len(eqs)==4: pos[f"1{g}"]=eqs[0]['Equipo']; pos[f"2{g}"]=eqs[1]['Equipo']; ter.append(eqs[2])
    ter=sorted(ter,key=lambda x:(x['Pts'],x['Dif'],x['GF']),reverse=True)
    for i in range(min(8,len(ter))): pos[f"3_{i+1}"]=ter[i]['Equipo']
    return pos

pos_grupos = obtener_clasificados(df_tabla)

def calcular_puntos(df):
    pt={e:0 for e in VALOR_EQUIPOS.keys()}
    det={e:{"Gr(Partidos)":0,"Gr(Goles)":0,"Gr(Bono)":0,"Eliminatorias":0,"Pichichi":0} for e in VALOR_EQUIPOS.keys()}
    for p in resultados_grupos.values():
        eA,eB=p['equipo_A'],p['equipo_B']; dif=p['goles_A']-p['goles_B']
        if dif>=3: det[eA]["Gr(Goles)"]+=1; det[eB]["Gr(Goles)"]-=1
        elif dif<=-3: det[eB]["Gr(Goles)"]+=1; det[eA]["Gr(Goles)"]-=1
        if dif>0: det[eA]["Gr(Partidos)"]+=3
        elif dif<0: det[eB]["Gr(Partidos)"]+=3
        else: det[eA]["Gr(Partidos)"]+=1; det[eB]["Gr(Partidos)"]+=1
    ter_b=[]
    for g in GRUPOS.keys():
        part = [p for p in resultados_grupos.values() if p['equipo_A'] in GRUPOS[g]]
        eqs = df[df['Grupo']==g].to_dict('records')
        if len(part)==6 and len(eqs)==4:
            det[eqs[0]['Equipo']]["Gr(Bono)"]+=3; det[eqs[1]['Equipo']]["Gr(Bono)"]+=2; det[eqs[3]['Equipo']]["Gr(Bono)"]-=1
            ter_b.append(eqs[2])
    ter_b=sorted(ter_b,key=lambda x:(x['Pts'],x['Dif'],x['GF']),reverse=True)
    for i in range(min(8,len(ter_b))): det[ter_b[i]['Equipo']]["Gr(Bono)"]+=1
    
    for m_id,p in resultados_elim.items():
        eA,eB,res,gan=p['equipo_A'],p['equipo_B'],p['resolucion'],p['ganador']
        dif=p['goles_A']-p['goles_B']
        if m_id=="M103 (3º y 4º)": det[gan]["Eliminatorias"]+=3; continue
        if dif>=3: det[eA]["Eliminatorias"]+=1; det[eB]["Eliminatorias"]-=1
        elif dif<=-3: det[eB]["Eliminatorias"]+=1; det[eA]["Eliminatorias"]-=1
        if res=="90 min":
            if dif>0: det[eA]["Eliminatorias"]+=4
            elif dif<0: det[eB]["Eliminatorias"]+=4
        elif res=="Prórroga":
            if dif>0: det[eA]["Eliminatorias"]+=3
            elif dif<0: det[eB]["Eliminatorias"]+=3
        elif res=="Penaltis":
            det[eA]["Eliminatorias"]+=1; det[eB]["Eliminatorias"]+=1; det[gan]["Eliminatorias"]+=1
        if m_id=="M104 (FINAL)": det[gan]["Eliminatorias"]+=10; det[eB if gan==eA else eA]["Eliminatorias"]+=6
            
    if pichichi: det[pichichi]["Pichichi"]+=2
    for eq in VALOR_EQUIPOS.keys(): pt[eq] = sum(det[eq].values())
    return pt, det

pts_globales, detalles_globales = calcular_puntos(df_tabla)

lista_clasif = []
for a, eqs in participantes.items():
    lista_clasif.append({"Jugador": a, "Puntos": sum(pts_globales[eq] for eq in eqs) + ajustes_manuales.get(a, 0), "Equipos": eqs, "Extra": ajustes_manuales.get(a, 0)})
clasificacion_ordenada = sorted(lista_clasif, key=lambda x: x["Puntos"], reverse=True)


# ══════════════════════════════════════════
# MENÚ SUPERIOR (CON TELETRANSPORTE)
# ══════════════════════════════════════════
col_title, col_btn = st.columns([3, 1])
with col_title: st.markdown(f"<h3 style='color:#FFD700; margin:0; padding-top:5px;'>🏆 Liga: {liga_actual}</h3>", unsafe_allow_html=True)
with col_btn:
    if st.button("🚪 Salir", use_container_width=True): 
        st.session_state.liga_actual = ""
        st.session_state.menu_seleccionado = "📊 Clasificación General"
        st.rerun()

st.write("")
opciones_menu = ["📊 Clasificación General", "👤 Detalle por Jugador", "🔥 Tabla de Goleadores", "🏆 Tabla de Grupos", "📅 Resultados Partidos", "⚽ Cuadro Eliminatorias"]
if st.session_state.admin: opciones_menu += ["--- ZONA ADMIN ---", "👥 Participantes", "🔧 Resultados Grupos", "⚔️ Resultados Elim.", "🥇 Pichichi Equipo", "🎯 Pichichis Jugadores", "➕ Ajuste Puntos"]

# Recuperamos el menú donde nos habíamos quedado
try: idx_menu = opciones_menu.index(st.session_state.menu_seleccionado)
except ValueError: idx_menu = 0

menu = st.selectbox("👉 Elige qué quieres ver:", opciones_menu, index=idx_menu)

# Si el usuario cambia el menú manualmente, actualizamos el estado
if menu != st.session_state.menu_seleccionado:
    st.session_state.menu_seleccionado = menu
    st.rerun()

if menu == "--- ZONA ADMIN ---": st.info("👆 Selecciona una herramienta de admin arriba."); st.stop()


# ══════════════════════════════════════════
# VISTAS PÚBLICAS
# ══════════════════════════════════════════
if menu == "📊 Clasificación General":
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b4/Lionel-Messi-Argentina-2022.jpg", use_container_width=True)
    st.markdown('<div class="titulo-principal">📊 Clasificación General</div>', unsafe_allow_html=True)
    if not participantes: st.warning("Aún no hay participantes en esta liga.")
    else:
        for i, row in enumerate(clasificacion_ordenada):
            med = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            eq_str = " ".join([f"{flag(e)}" for e in row["Equipos"]])
            ext_bdg = f'<span style="font-size:0.5em; background:rgba(255,255,255,0.2); padding:2px 5px; border-radius:4px; margin-left:10px;">Ajuste: {row["Extra"]} pts</span>' if row["Extra"]!=0 else ""
            
            # Tarjeta de jugador
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><span style="font-size:1.5em">{med}</span><span style="font-size:1.3em; font-weight:700; margin-left:10px; color:white;">{row["Jugador"]}</span>{ext_bdg}<br><small style="color:#aaa;">{eq_str}</small></div>
                    <div style="font-size:2em; font-weight:900; color:#FFD700">{row["Puntos"]}<span style="font-size:0.4em; color:#aaa;"> pts</span></div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            # Botón de teletransporte debajo de la tarjeta
            if st.button(f"🔍 Ver detalle de {row['Jugador']}", key=f"ver_{row['Jugador']}", use_container_width=True):
                st.session_state.menu_seleccionado = "👤 Detalle por Jugador"
                st.session_state.jugador_detalle = row["Jugador"]
                st.rerun()

elif menu == "👤 Detalle por Jugador":
    st.markdown('<div class="titulo-principal">👤 Detalle por Jugador</div>', unsafe_allow_html=True)
    if not participantes: st.warning("Aún no hay participantes.")
    else:
        nombres = [r["Jugador"] for r in clasificacion_ordenada]
        
        # Teletransporte: seleccionamos por defecto al amigo elegido en la pestaña anterior
        idx_jug = nombres.index(st.session_state.jugador_detalle) if st.session_state.jugador_detalle in nombres else 0
        jug_sel = st.selectbox("Selecciona un amigo:", nombres, index=idx_jug)
        
        # Si cambia el selector, actualizamos para la próxima
        if jug_sel != st.session_state.jugador_detalle:
            st.session_state.jugador_detalle = jug_sel
            
        row = next(item for item in clasificacion_ordenada if item["Jugador"] == jug_sel)
        
        st.markdown(f"<h3 style='color: white;'>🛡️ Selecciones ({row['Puntos']} pts)</h3>", unsafe_allow_html=True)
        for eq in row["Equipos"]:
            det = detalles_globales[eq]
            desglose = []
            if det['Gr(Partidos)'] != 0: desglose.append(f"Grupos: {det['Gr(Partidos)']}")
            if det['Gr(Goles)'] != 0: desglose.append(f"Goleadas: {det['Gr(Goles)']}")
            if det['Gr(Bono)'] != 0: desglose.append(f"Bono: {det['Gr(Bono)']}")
            if det['Eliminatorias'] != 0: desglose.append(f"Elim: {det['Eliminatorias']}")
            if det['Pichichi'] != 0: desglose.append(f"Pichichi: {det['Pichichi']}")
            str_desglose = " · ".join(desglose) if desglose else "Aún sin puntos"
            st.markdown(f"""
            <div class="mini-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div><span style="font-size:1.1em; color:white;">{flag(eq)} <b>{eq}</b></span><br><span style="font-size:0.8em; color:#aaa;">{str_desglose}</span></div>
                <div style="background-color:#FFD700; color:#000; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:1.2em;">{pts_globales[eq]}</div>
            </div>""", unsafe_allow_html=True)
            
        st.markdown("<h3 style='color: white; margin-top:20px;'>📅 Sus Partidos</h3>", unsafe_allow_html=True)
        html_partidos = ""
        for g, equipos in GRUPOS.items():
            for eA, eB in [(equipos[0],equipos[1]), (equipos[2],equipos[3]), (equipos[0],equipos[2]), (equipos[1],equipos[3]), (equipos[0],equipos[3]), (equipos[1],equipos[2])]:
                if eA in row["Equipos"] or eB in row["Equipos"]:
                    fecha = obtener_fecha_grupo(eA, eB, g); k = f"{eA}_{eB}"
                    cA, bA = ("#FFD700", "bold") if eA in row["Equipos"] else ("#aaa", "normal")
                    cB, bB = ("#FFD700", "bold") if eB in row["Equipos"] else ("#aaa", "normal")
                    if k in resultados_grupos:
                        p = resultados_grupos[k]
                        html_partidos += f"""<div class="mini-card"><div style="text-align:center; font-size:0.65em; color:#aaa; margin-bottom:6px;">🕒 {fecha} - Gr. {g}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:{cA}; font-weight:{bA}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> <span style="background:#252d3a; border: 1px solid #444; padding:3px 10px; border-radius:6px; color:white; font-weight:bold;">{p['goles_A']} - {p['goles_B']}</span> <span style="color:{cB}; font-weight:{bB}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span></div></div>"""
                    else:
                        html_partidos += f"""<div class="mini-card"><div style="text-align:center; font-size:0.65em; color:#aaa; margin-bottom:6px;">🕒 {fecha} - Gr. {g}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:{cA}; font-weight:{bA}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> <span style="color:#aaa; font-weight:bold;">vs</span> <span style="color:{cB}; font-weight:{bB}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span></div></div>"""
        
        for m_id, p in resultados_elim.items():
            eA, eB = p['equipo_A'], p['equipo_B']
            if eA in row["Equipos"] or eB in row["Equipos"]:
                fecha = FECHAS_ELIM.get(m_id, "")
                cA, bA = ("#FFD700", "bold") if eA in row["Equipos"] else ("#aaa", "normal")
                cB, bB = ("#FFD700", "bold") if eB in row["Equipos"] else ("#aaa", "normal")
                rex = f"<br><span style='font-size:0.7em; color:#aaa; font-weight:normal;'>{p['resolucion']}</span>" if p['resolucion'] != "90 min" else ""
                html_partidos += f"""<div class="mini-card"><div style="text-align:center; font-size:0.65em; color:#aaa; margin-bottom:6px;">🕒 {fecha} - {m_id}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:{cA}; font-weight:{bA}; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span> <span style="background:#252d3a; border: 1px solid #444; padding:3px 10px; border-radius:6px; color:white; font-weight:bold; text-align:center; line-height:1.2;">{p['goles_A']} - {p['goles_B']}{rex}</span> <span style="color:{cB}; font-weight:{bB}; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span></div></div>"""
        
        if html_partidos == "": st.caption("No hay partidos de estas selecciones.")
        else: st.markdown(html_partidos, unsafe_allow_html=True)

elif menu == "🔥 Tabla de Goleadores":
    st.markdown('<div class="titulo-principal">🔥 Top Pichichis</div>', unsafe_allow_html=True)
    if not goleadores_reales: st.info("Aún no se han registrado goles en el torneo.")
    else:
        for i, j in enumerate(goleadores_reales):
            med = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            pen = f"<br><span style='font-size:0.5em; color:#FF8C00; font-weight:normal;'>({j.get('goles_penalti', 0)} de penalti)</span>" if j.get('goles_penalti', 0) > 0 else ""
            st.markdown(f"""<div class="card" style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-left: 5px solid #FFD700;"><div style="font-size:1.4em; color:#ffffff; font-weight:bold;">{med} {j['jugador']} <span style="color:#cccccc; font-size:0.7em; margin-left:10px; font-weight:normal;">{flag(j['equipo'])} {j['equipo']}</span></div><div style="font-size:1.6em; font-weight:900; color:#FFD700; text-align:right; line-height:1.1;">{j['goles']} ⚽{pen}</div></div>""", unsafe_allow_html=True)

elif menu == "🏆 Tabla de Grupos":
    st.markdown('<div class="titulo-principal">🏆 Tabla de Grupos</div>', unsafe_allow_html=True)
    mejores_3 = [pos_grupos.get(f"3_{i+1}") for i in range(8)]
    cols = st.columns(3)
    for idx, (grupo, _) in enumerate(GRUPOS.items()):
        with cols[idx % 3]:
            df_g = df_tabla[df_tabla['Grupo']==grupo][['Equipo','PJ','Pts','GF','GC','Dif']].reset_index(drop=True); df_g.index += 1; df_g[''] = df_g['Equipo'].apply(flag)
            st.markdown(f"<h4 style='color: #FFD700; margin-bottom: 10px;'>Grupo {grupo}</h4>", unsafe_allow_html=True)
            def hl(row): return ['background-color:#1a472a;color:white']*len(row) if row.name<=2 else (['background-color:#2d4a1e;color:#90EE90']*len(row) if row.name==3 and row['Equipo'] in mejores_3 else ['color:#bbb']*len(row))
            st.dataframe(df_g[['','Equipo','PJ','Pts','GF','GC','Dif']].style.apply(hl,axis=1), use_container_width=True, hide_index=False)

elif menu == "📅 Resultados Partidos":
    st.markdown('<div class="titulo-principal">📅 Partidos</div>', unsafe_allow_html=True)
    st.markdown("<h3 style='color: white;'>Fase de Grupos</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3); col_idx = 0
    for g, equipos in GRUPOS.items():
        with [c1, c2, c3][col_idx % 3]:
            st.markdown(f"<h4 style='color: #FFD700;'>Grupo {g}</h4>", unsafe_allow_html=True)
            html_p = ""
            for eA, eB in [(equipos[0],equipos[1]), (equipos[2],equipos[3]), (equipos[0],equipos[2]), (equipos[1],equipos[3]), (equipos[0],equipos[3]), (equipos[1],equipos[2])]:
                k = f"{eA}_{eB}"; f = obtener_fecha_grupo(eA, eB, g)
                if k in resultados_grupos: html_p += f'<div style="border-bottom:1px solid #2d3748; padding:6px 0;"><div style="font-size:0.65em; color:#aaa; text-align:center;">🕒 {f}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:white; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span><span style="background:#FFD700; color:#000; padding:2px 8px; border-radius:4px; font-weight:bold;">{resultados_grupos[k]["goles_A"]}-{resultados_grupos[k]["goles_B"]}</span><span style="color:white; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span></div></div>'
                else: html_p += f'<div style="border-bottom:1px solid #2d3748; padding:6px 0;"><div style="font-size:0.65em; color:#aaa; text-align:center;">🕒 {f}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:#aaa; width:40%; text-align:right; font-size:0.9em;">{flag(eA)} {eA}</span><span style="color:#777;">vs</span><span style="color:#aaa; width:40%; text-align:left; font-size:0.9em;">{eB} {flag(eB)}</span></div></div>'
            st.markdown(f'<div class="card" style="padding:10px;">{html_p}</div>', unsafe_allow_html=True); col_idx += 1

    st.markdown("<h3 style='color: white;'>Eliminatorias</h3>", unsafe_allow_html=True)
    if resultados_elim:
        ce1, ce2 = st.columns(2)
        for i, (m_id, r) in enumerate(resultados_elim.items()):
            with [ce1, ce2][i % 2]:
                st.markdown(f"""<div class="card" style="padding:15px; margin-bottom:10px;"><div style="display:flex; justify-content:space-between; font-size:0.8em; color:#aaa; margin-bottom:5px;"><span>{m_id} · {r['resolucion']}</span><span>🕒 {FECHAS_ELIM.get(m_id,"")}</span></div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-weight:{'bold' if r['ganador']==r['equipo_A'] else 'normal'}; color:{'#FFD700' if r['ganador']==r['equipo_A'] else 'white'};">{flag(r['equipo_A'])} {r['equipo_A']}</span><span style="background:#FFD700; color:#000; padding:4px 10px; border-radius:6px; font-weight:bold;">{r['goles_A']} - {r['goles_B']}</span><span style="font-weight:{'bold' if r['ganador']==r['equipo_B'] else 'normal'}; color:{'#FFD700' if r['ganador']==r['equipo_B'] else 'white'};">{r['equipo_B']} {flag(r['equipo_B'])}</span></div></div>""", unsafe_allow_html=True)

elif menu == "⚽ Cuadro Eliminatorias":
    st.markdown('<div class="titulo-principal">⚽ Cuadro de Eliminatorias</div>', unsafe_allow_html=True)
    def qu_gan(m_id, perdedor=False): return resultados_elim[m_id]['perdedor' if perdedor else 'ganador'] if m_id in resultados_elim else f"❓"
    def mostrar_cruce(m_id, eA, eB):
        d = resultados_elim.get(m_id); fA, fB = (flag(eA) if eA in VALOR_EQUIPOS else "❓"), (flag(eB) if eB in VALOR_EQUIPOS else "❓")
        if d: st.markdown(f"""<div class="card" style="padding:12px"><div style="display:flex; justify-content:space-between; font-size:0.75em;color:#aaa;margin-bottom:4px"><span>{m_id}</span> <span>🕒 {FECHAS_ELIM.get(m_id, "")}</span></div><div style="display:flex;justify-content:space-between;align-items:center"><span style="{'font-weight:900;color:#FFD700' if d['ganador']==eA else 'color:#aaa'}">{fA} {eA}</span><span class="resultado-badge">{d['goles_A']}-{d['goles_B']}</span><span style="{'font-weight:900;color:#FFD700' if d['ganador']==eB else 'color:#aaa'}">{eB} {fB}</span></div><div style="text-align:center;margin-top:6px;font-size:0.8em;color:#aaa">{d['resolucion']} · 🏆 <b style="color:#FFD700">{d['ganador']}</b></div></div>""", unsafe_allow_html=True)
        else: st.markdown(f"""<div class="card" style="padding:12px;border:1px dashed #2d3748"><div style="display:flex; justify-content:space-between; font-size:0.75em;color:#aaa;margin-bottom:4px"><span>{m_id}</span> <span>🕒 {FECHAS_ELIM.get(m_id, "")}</span></div><div style="display:flex;justify-content:space-between;align-items:center;color:#888"><span>{fA} {eA}</span><span style="color:#555">vs</span><span>{fB} {eB}</span></div></div>""", unsafe_allow_html=True)

    c16 = st.columns(4); st.markdown("<h3 style='color:#add8e6;'>🔵 1/16 Final</h3>", unsafe_allow_html=True)
    for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items()):
        with c16[i%4]: mostrar_cruce(m_id, pos_grupos.get(c1,c1), pos_grupos.get(c2,c2))
    c8 = st.columns(4); st.markdown("<h3 style='color:#FFD700;'>🟡 Octavos</h3>", unsafe_allow_html=True)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items()):
        with c8[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    c4 = st.columns(4); st.markdown("<h3 style='color:#FFA500;'>🟠 Cuartos</h3>", unsafe_allow_html=True)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items()):
        with c4[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    c2 = st.columns(2); st.markdown("<h3 style='color:#FF6347;'>🔴 Semifinales</h3>", unsafe_allow_html=True)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items()):
        with c2[i]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))
    cf = st.columns(2); st.markdown("<h3 style='color:#FFD700;'>🏆 Finales</h3>", unsafe_allow_html=True)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items()):
        with cf[i]: mostrar_cruce(m_id, qu_gan(m1.replace("_L",""),perdedor="_L" in m1), qu_gan(m2.replace("_L",""),perdedor="_L" in m2))


# ══════════════════════════════════════════
# ZONA ADMIN
# ══════════════════════════════════════════
elif menu == "👥 Participantes":
    st.markdown('<div class="titulo-principal">👥 Participantes</div>', unsafe_allow_html=True)
    nombre = st.text_input("Nombre")
    equipos_sel = st.multiselect("Selecciones (máx 30 pts)", list(VALOR_EQUIPOS.keys()), format_func=lambda x: f"{flag(x)} {x} ({VALOR_EQUIPOS[x]} pts)")
    coste = sum(VALOR_EQUIPOS[e] for e in equipos_sel)
    st.markdown(f"Coste: <b style='color:{'#90EE90' if coste <= 30 else '#FF6347'}'>{coste} / 30 pts</b>", unsafe_allow_html=True)
    if st.button("✅ Añadir / Actualizar Jugador", use_container_width=True):
        if not nombre: st.error("Falta nombre.")
        elif coste > 30: st.error("Demasiados puntos.")
        else: participantes[nombre] = equipos_sel; guardar_participantes(liga_actual, participantes); st.success("Guardado"); st.rerun()
    if participantes:
        st.divider()
        for nom, eqs in participantes.items():
            c1,c2 = st.columns([5,1])
            c1.markdown(f"**{nom}** ({sum(VALOR_EQUIPOS[e] for e in eqs)} pts) {' '.join([flag(e) for e in eqs])}")
            if c2.button("🗑️", key=f"del_{nom}"): del participantes[nom]; guardar_participantes(liga_actual, participantes); st.rerun()

elif menu == "🔧 Resultados Grupos":
    cols = st.columns(3)
    for idx,(g,eq) in enumerate(GRUPOS.items()):
        with cols[idx%3]:
            st.markdown(f"<h4 style='color: #FFD700;'>Grupo {g}</h4>", unsafe_allow_html=True)
            for eA,eB in [(eq[0],eq[1]),(eq[2],eq[3]),(eq[0],eq[2]),(eq[1],eq[3]),(eq[0],eq[3]),(eq[1],eq[2])]:
                key = f"{eA}_{eB}"; rg = resultados_grupos.get(key,{})
                c1,c2,c3,c4 = st.columns([3,1,1,3])
                c1.markdown(f"{flag(eA)} {eA}"); gA = c2.text_input("",key=f"i_A_{key}",value=rg.get("goles_A",""),label_visibility="collapsed")
                gB = c3.text_input("",key=f"i_B_{key}",value=rg.get("goles_B",""),label_visibility="collapsed"); c4.markdown(f"{eB} {flag(eB)}")
                if gA.isdigit() and gB.isdigit() and (not rg or rg.get("goles_A")!=int(gA) or rg.get("goles_B")!=int(gB)): guardar_resultado_grupo(key,eA,eB,int(gA),int(gB))
                elif rg.get("goles_A","")!="" and gA=="" and gB=="": borrar_resultado_grupo(key)

elif menu == "⚔️ Resultados Elim.":
    def renderizar(m_id, eA, eB, col):
        with col:
            st.markdown(f"**{m_id}**")
            if eA not in VALOR_EQUIPOS or eB not in VALOR_EQUIPOS: return
            re = resultados_elim.get(m_id,{})
            c1,c2 = st.columns(2)
            gA = c1.text_input(f"{flag(eA)} {eA}",key=f"ga_{m_id}",value=re.get("goles_A",""))
            gB = c2.text_input(f"{flag(eB)} {eB}",key=f"gb_{m_id}",value=re.get("goles_B",""))
            res = st.selectbox("Decisión",["90 min","Prórroga","Penaltis"],index=["90 min","Prórroga","Penaltis"].index(re.get("resolucion","90 min")),key=f"res_{m_id}")
            gan_pen = st.selectbox("Ganó penaltis:",[eA,eB],index=[eA,eB].index(re.get("ganador",eA)) if re.get("ganador",eA) in [eA,eB] else 0,key=f"pen_{m_id}") if res=="Penaltis" else None
            if gA.isdigit() and gB.isdigit():
                gA_i,gB_i = int(gA),int(gB)
                if gA_i>gB_i: gan,perd=eA,eB
                elif gB_i>gA_i: gan,perd=eB,eA
                else: 
                    if res!="Penaltis": return
                    gan, perd = gan_pen, eB if gan_pen==eA else eA
                if not re or re.get("goles_A")!=gA_i or re.get("goles_B")!=gB_i or re.get("resolucion")!=res or re.get("ganador")!=gan: guardar_resultado_elim(m_id,eA,eB,gA_i,gB_i,res,gan,perd)
            elif re.get("goles_A","")!="" and gA=="" and gB=="": borrar_resultado_elim(m_id)
            
    c16=st.columns(4); [renderizar(m_id,pos_grupos.get(c1,c1),pos_grupos.get(c2,c2),c16[i%4]) for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items())]
    c8=st.columns(4); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c8[i%4]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items())]
    c4=st.columns(4); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c4[i%4]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items())]
    c2=st.columns(2); [renderizar(m_id,qu_gan(m1),qu_gan(m2),c2[i]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items())]
    cf=st.columns(2); [renderizar(m_id,qu_gan(m1.replace("_L",""),perdedor="_L" in m1),qu_gan(m2.replace("_L",""),perdedor="_L" in m2),cf[i]) for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items())]

elif menu == "🥇 Pichichi Equipo":
    sel = st.selectbox("Selección Máxima Goleadora (Da puntos extra)", ["Ninguno aún..."] + list(VALOR_EQUIPOS.keys()), index=(["Ninguno aún..."] + list(VALOR_EQUIPOS.keys())).index(pichichi) if pichichi else 0)
    if st.button("💾 Guardar",use_container_width=True): guardar_pichichi(sel if sel!="Ninguno aún..." else None); st.success("Guardado")

elif menu == "🎯 Pichichis Jugadores":
    st.markdown('<div class="titulo-principal">🎯 Goles Reales</div>', unsafe_allow_html=True)
    jug_creados = sorted([j['jugador'] for j in goleadores_reales]); op_jug = ["✨ CREAR NUEVO JUGADOR ✨"] + jug_creados
    jug_sel = st.selectbox("1. Jugador", op_jug)
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    if jug_sel == "✨ CREAR NUEVO JUGADOR ✨":
        eq = c1.selectbox("Selección", list(VALOR_EQUIPOS.keys())); jug = c2.text_input("Nombre")
    else:
        jug = jug_sel; eq_ex = next((j['equipo'] for j in goleadores_reales if j['jugador'] == jug), list(VALOR_EQUIPOS.keys())[0])
        eq = c1.selectbox("Selección", list(VALOR_EQUIPOS.keys()), index=list(VALOR_EQUIPOS.keys()).index(eq_ex), disabled=True)
        c2.text_input("Nombre", value=jug, disabled=True)
    g_nuevos = c3.number_input("Goles a sumar", min_value=1, value=1); p_nuevos = c4.number_input("De penalti", min_value=0, value=0)
    if st.button("➕ Sumar Goles", use_container_width=True):
        if jug:
            exist = next((j for j in goleadores_reales if j['jugador'].lower() == jug.lower()), None)
            tot_g = exist['goles'] + g_nuevos if exist else g_nuevos
            tot_p = exist.get('goles_penalti', 0) + p_nuevos if exist else p_nuevos
            if tot_p > tot_g: st.error("Más penaltis que goles totales.")
            else: guardar_goleador_real(jug.title(), eq, tot_g, tot_p); st.rerun()
        else: st.error("Escribe un nombre.")
    if goleadores_reales:
        st.divider()
        for j in goleadores_reales:
            col1, col2 = st.columns([5,1])
            pen_tx = f" <span style='color:#FF8C00; font-size:0.85em;'>({j.get('goles_penalti', 0)} pen)</span>" if j.get('goles_penalti', 0) > 0 else ""
            col1.markdown(f"<div class='mini-card'><span style='color:white; font-weight:bold;'>{flag(j['equipo'])} {j['jugador']}</span> <span style='color:#FFD700; font-weight:bold; margin-left:10px;'>{j['goles']} goles</span>{pen_tx}</div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_gol_{j['jugador']}"): borrar_goleador_real(j['jugador']); st.rerun()

elif menu == "➕ Ajuste Puntos":
    st.markdown('<div class="titulo-principal">➕ Ajuste Manual</div>', unsafe_allow_html=True)
    p_sel = st.selectbox("Jugador:", list(participantes.keys()))
    if p_sel:
        nv = st.number_input("Puntos extra:", value=ajustes_manuales.get(p_sel, 0))
        if st.button("💾 Aplicar"): guardar_ajuste_puntos(liga_actual, p_sel, nv); st.rerun()
