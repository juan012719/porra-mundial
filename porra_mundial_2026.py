import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Porra Mundial 2026 🌍", layout="wide", initial_sidebar_state="expanded")

# CSS personalizado
st.markdown("""
<style>
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
    .subtitulo {
        text-align: center;
        color: #888;
        font-size: 1em;
        margin-bottom: 30px;
    }
    .card {
        background: linear-gradient(135deg, #1e2530, #252d3a);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .medal-gold { color: #FFD700; font-size: 1.3em; }
    .medal-silver { color: #C0C0C0; font-size: 1.3em; }
    .medal-bronze { color: #CD7F32; font-size: 1.3em; }
    
    .partido-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 10px;
        margin: 3px 0;
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        font-size: 0.85em;
    }
    .resultado-badge {
        background: #FFD700;
        color: #000;
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .ganador-badge {
        background: linear-gradient(90deg, #FFD700, #FF6B35);
        color: #000;
        border-radius: 6px;
        padding: 3px 10px;
        font-weight: bold;
    }
    div[data-testid="stSidebarNav"] { display: none; }
    .stRadio > label { font-weight: 600; }
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

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=30)
def cargar_participantes():
    sb = get_supabase()
    rows = sb.table("participantes").select("*").execute().data
    return {r["nombre"]: r["equipos"].split(",") if r["equipos"] else [] for r in rows}

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

def guardar_participantes(participantes):
    sb = get_supabase()
    sb.table("participantes").delete().neq("nombre","").execute()
    rows = [{"nombre":n,"equipos":",".join(e)} for n,e in participantes.items()]
    if rows: sb.table("participantes").insert(rows).execute()
    cargar_participantes.clear()

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

if "admin" not in st.session_state:
    st.session_state.admin = False

participantes     = cargar_participantes()
resultados_grupos = cargar_resultados_grupos()
resultados_elim   = cargar_resultados_elim()
pichichi          = cargar_pichichi()

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
    puntos={eq:0 for eq in VALOR_EQUIPOS.keys()}
    for p in resultados_grupos.values():
        eA,eB=p['equipo_A'],p['equipo_B']; dif=p['goles_A']-p['goles_B']
        if dif>=3: puntos[eA]+=1; puntos[eB]-=1
        elif dif<=-3: puntos[eB]+=1; puntos[eA]-=1
        if dif>0: puntos[eA]+=3
        elif dif<0: puntos[eB]+=3
        else: puntos[eA]+=1; puntos[eB]+=1
    terceros_bono=[]
    for g in GRUPOS.keys():
        eqs=df_tabla[df_tabla['Grupo']==g].to_dict('records')
        if len(eqs)==4:
            puntos[eqs[0]['Equipo']]+=3; puntos[eqs[1]['Equipo']]+=2
            if eqs[3]['Pts']==0: puntos[eqs[3]['Equipo']]-=3
            else: puntos[eqs[3]['Equipo']]-=1
            terceros_bono.append(eqs[2])
    terceros_bono=sorted(terceros_bono,key=lambda x:(x['Pts'],x['Dif'],x['GF']),reverse=True)
    for i in range(min(8,len(terceros_bono))): puntos[terceros_bono[i]['Equipo']]+=1
    for m_id,p in resultados_elim.items():
        eA,eB,res,gan=p['equipo_A'],p['equipo_B'],p['resolucion'],p['ganador']
        dif=p['goles_A']-p['goles_B']
        if m_id=="M103 (3º y 4º)": puntos[gan]+=3; continue
        if dif>=3: puntos[eA]+=1; puntos[eB]-=1
        elif dif<=-3: puntos[eB]+=1; puntos[eA]-=1
        if res=="90 min":
            if dif>0: puntos[eA]+=4
            elif dif<0: puntos[eB]+=4
        elif res=="Prórroga":
            if dif>0: puntos[eA]+=3
            elif dif<0: puntos[eB]+=3
        elif res=="Penaltis":
            puntos[eA]+=1; puntos[eB]+=1; puntos[gan]+=1
        if m_id=="M104 (FINAL)":
            puntos[gan]+=10; puntos[eB if gan==eA else eA]+=6
    if pichichi: puntos[pichichi]+=2
    return puntos

df_tabla   = obtener_tabla_grupos()
pos_grupos = obtener_clasificados(df_tabla)

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="titulo-principal">⚽ Porra<br>Mundial 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">USA · CANADA · MEXICO</div>', unsafe_allow_html=True)
    st.divider()

    with st.expander("🔐 Acceso Admin"):
        if not st.session_state.admin:
            pwd = st.text_input("Contraseña", type="password", key="pwd_input")
            if st.button("Entrar", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin = True; st.rerun()
                else:
                    st.error("Contraseña incorrecta")
        else:
            st.success("✅ Admin activo")
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state.admin = False; st.rerun()

    st.divider()
    opciones_menu = ["📊 Clasificación General", "🏆 Tabla de Grupos", "⚽ Cuadro Eliminatorias"]
    if st.session_state.admin:
        opciones_menu += ["👥 Participantes", "🔧 Resultados Grupos", "⚔️ Resultados Eliminatorias", "🥇 Pichichi"]
    menu = st.radio("", opciones_menu, label_visibility="collapsed")

    st.divider()
    st.caption(f"🗃️ {len(resultados_grupos)}/72 partidos · {len(participantes)} jugadores")

# ══════════════════════════════════════════
# CLASIFICACIÓN GENERAL
# ══════════════════════════════════════════
if menu == "📊 Clasificación General":
    # CABECERA AÑADIDA
    st.image("TU_IMAGEN_AQUI.jpg", use_container_width=True)
    st.markdown('<div class="titulo-principal">📊 Clasificación General</div>', unsafe_allow_html=True)
    st.write("")
    if not participantes:
        st.warning("Aún no hay participantes registrados.")
    else:
        pts = calcular_puntos(df_tabla)
        clasif = sorted(
            [{"Jugador": a, "Puntos": sum(pts[eq] for eq in eqs), "Equipos": eqs} for a, eqs in participantes.items()],
            key=lambda x: x["Puntos"], reverse=True
        )
        medallas = ["🥇", "🥈", "🥉"]
        for i, row in enumerate(clasif):
            med = medallas[i] if i < 3 else f"#{i+1}"
            equipos_str = " ".join([f"{flag(e)}" for e in row["Equipos"]])
            nombres_str = ", ".join(row["Equipos"])
            # NOMBRE EN BLANCO APLICADO
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:1.5em">{med}</span>
                        <span style="font-size:1.3em; font-weight:700; margin-left:10px; color:white;">{row["Jugador"]}</span>
                        <br><small style="color:#888">{equipos_str} {nombres_str}</small>
                    </div>
                    <div style="font-size:2em; font-weight:900; color:#FFD700">{row["Puntos"]}<span style="font-size:0.4em; color:#888"> pts</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TABLA DE GRUPOS
# ══════════════════════════════════════════
elif menu == "🏆 Tabla de Grupos":
    st.markdown('<div class="titulo-principal">🏆 Tabla de Grupos</div>', unsafe_allow_html=True)
    st.write("")
    if not resultados_grupos:
        st.info("Aún no hay resultados en la fase de grupos.")
    
    mejores_3 = [pos_grupos.get(f"3_{i+1}") for i in range(8)]
    cols = st.columns(3)
    for idx, (grupo, _) in enumerate(GRUPOS.items()):
        with cols[idx % 3]:
            df_g = df_tabla[df_tabla['Grupo']==grupo][['Equipo','PJ','Pts','GF','GC','Dif']].reset_index(drop=True)
            df_g.index += 1
            df_g[''] = df_g['Equipo'].apply(flag)
            df_g = df_g[['','Equipo','PJ','Pts','GF','GC','Dif']]

            st.markdown(f"#### Grupo {grupo}")
            def hl(row):
                if row.name <= 2: return ['background-color:#1a472a;color:white']*len(row)
                if row.name == 3 and row['Equipo'] in mejores_3: return ['background-color:#2d4a1e;color:#90EE90']*len(row)
                return ['color:#888']*len(row)
            st.dataframe(df_g.style.apply(hl,axis=1), use_container_width=True, hide_index=False)

    if pos_grupos:
        st.write("")
        st.markdown("### Clasificados a Dieciseisavos")
        ca,cb,cc = st.columns(3)
        with ca:
            st.markdown("**🥇 Primeros de grupo**")
            for k,v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("1")):
                st.markdown(f"{flag(v)} **{v}** `{k}`")
        with cb:
            st.markdown("**🥈 Segundos de grupo**")
            for k,v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("2")):
                st.markdown(f"{flag(v)} **{v}** `{k}`")
        with cc:
            st.markdown("**🥉 Mejores terceros**")
            for k,v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("3")):
                st.markdown(f"{flag(v)} **{v}** `{k}`")

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
        fA = flag(eA) if eA in VALOR_EQUIPOS else "❓"
        fB = flag(eB) if eB in VALOR_EQUIPOS else "❓"
        if d:
            gan = d['ganador']
            st.markdown(f"""<div class="card" style="padding:12px">
                <div style="font-size:0.75em;color:#888;margin-bottom:4px">{m_id}</div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="{'font-weight:900;color:#FFD700' if gan==eA else 'color:#888'}">{fA} {eA}</span>
                    <span class="resultado-badge">{d['goles_A']} - {d['goles_B']}</span>
                    <span style="{'font-weight:900;color:#FFD700' if gan==eB else 'color:#888'}">{eB} {fB}</span>
                </div>
                <div style="text-align:center;margin-top:6px;font-size:0.8em;color:#888">{d['resolucion']} · 🏆 <b style="color:#FFD700">{gan}</b></div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="card" style="padding:12px;border:1px dashed #2d3748">
                <div style="font-size:0.75em;color:#888;margin-bottom:4px">{m_id}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;color:#555">
                    <span>{fA} {eA}</span>
                    <span style="color:#333">vs</span>
                    <span>{fB} {eB}</span>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("### 🔵 Dieciseisavos de Final")
    c16 = st.columns(4)
    for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items()):
        with c16[i%4]: mostrar_cruce(m_id, pos_grupos.get(c1,c1), pos_grupos.get(c2,c2))

    st.markdown("### 🟡 Octavos de Final")
    c8 = st.columns(4)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items()):
        with c8[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))

    st.markdown("### 🟠 Cuartos de Final")
    c4 = st.columns(4)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items()):
        with c4[i%4]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))

    st.markdown("### 🔴 Semifinales")
    c2 = st.columns(2)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items()):
        with c2[i]: mostrar_cruce(m_id, qu_gan(m1), qu_gan(m2))

    st.markdown("### 🏆 Finales")
    cf = st.columns(2)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items()):
        with cf[i]: mostrar_cruce(m_id, qu_gan(m1.replace("_L",""),perdedor="_L" in m1), qu_gan(m2.replace("_L",""),perdedor="_L" in m2))

# ══════════════════════════════════════════
# ADMIN - PARTICIPANTES
# ══════════════════════════════════════════
elif menu == "👥 Participantes":
    st.markdown('<div class="titulo-principal">👥 Gestión de Participantes</div>', unsafe_allow_html=True)
    st.write("")
    with st.form("form_amigos"):
        nombre = st.text_input("Nombre del participante")
        equipos_sel = st.multiselect("Selecciones (máx 30 pts)", list(VALOR_EQUIPOS.keys()),
                                      format_func=lambda x: f"{flag(x)} {x} ({VALOR_EQUIPOS[x]} pts)")
        coste = sum(VALOR_EQUIPOS[e] for e in equipos_sel)
        color = "green" if coste <= 30 else "red"
        st.markdown(f"Coste: <b style='color:{color}'>{coste} / 30 pts</b>", unsafe_allow_html=True)
        if st.form_submit_button("✅ Añadir / Actualizar", use_container_width=True):
            if not nombre: st.error("Falta el nombre.")
            elif coste > 30: st.error(f"Demasiados puntos ({coste}/30).")
            else:
                participantes[nombre] = equipos_sel
                guardar_participantes(participantes)
                st.success(f"✅ {nombre} guardado."); st.rerun()

    if participantes:
        st.divider()
        st.subheader("Participantes actuales")
        for nom, eqs in participantes.items():
            c1,c2 = st.columns([5,1])
            equipos_str = " ".join([flag(e) for e in eqs])
            c1.markdown(f"**{nom}** ({sum(VALOR_EQUIPOS[e] for e in eqs)} pts) {equipos_str}  \n*{', '.join(eqs)}*")
