import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Porra Mundial 2026", layout="wide")

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

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
    "M73": ("2A", "2B"), "M74": ("1E", "3_1"), "M75": ("1F", "2C"), "M76": ("1C", "2F"),
    "M77": ("1I", "3_2"), "M78": ("2E", "2I"), "M79": ("1A", "3_3"), "M80": ("1L", "3_4"),
    "M81": ("1D", "3_5"), "M82": ("1G", "3_6"), "M83": ("2K", "2L"), "M84": ("1H", "2J"),
    "M85": ("1B", "3_7"), "M86": ("1J", "2H"), "M87": ("1K", "3_8"), "M88": ("2D", "2G")
}
CRUCES_OCTAVOS  = {"M89": ("M74","M77"), "M90": ("M73","M75"), "M91": ("M76","M78"), "M92": ("M79","M80"), "M93": ("M83","M84"), "M94": ("M81","M82"), "M95": ("M85","M87"), "M96": ("M86","M88")}
CRUCES_CUARTOS  = {"M97": ("M89","M90"), "M98": ("M93","M94"), "M99": ("M91","M92"), "M100": ("M95","M96")}
CRUCES_SEMIS    = {"M101": ("M97","M98"), "M102": ("M99","M100")}
CRUCES_FINALES  = {"M103 (3º y 4º)": ("M101_L","M102_L"), "M104 (FINAL)": ("M101","M102")}

# --- GOOGLE SHEETS ---
@st.cache_resource
def get_gsheet_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = dict.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_resource
def get_spreadsheet():
    client = get_gsheet_client()
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

def get_sheet(name):
    ss = get_spreadsheet()
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        return ss.add_worksheet(title=name, rows=200, cols=20)

# ---- LECTURA ----
@st.cache_data(ttl=30)
def cargar_participantes():
    ws = get_sheet("participantes")
    rows = ws.get_all_values()
    result = {}
    for row in rows:
        if row and row[0]:
            result[row[0]] = [e for e in row[1:] if e]
    return result

@st.cache_data(ttl=30)
def cargar_resultados_grupos():
    ws = get_sheet("resultados_grupos")
    rows = ws.get_all_values()
    result = {}
    for row in rows:
        if len(row) >= 5 and row[0]:
            try:
                result[row[0]] = {
                    "equipo_A": row[1], "equipo_B": row[2],
                    "goles_A": int(row[3]), "goles_B": int(row[4])
                }
            except (ValueError, IndexError):
                pass
    return result

@st.cache_data(ttl=30)
def cargar_resultados_elim():
    ws = get_sheet("resultados_elim")
    rows = ws.get_all_values()
    result = {}
    for row in rows:
        if len(row) >= 7 and row[0]:
            try:
                result[row[0]] = {
                    "equipo_A": row[1], "equipo_B": row[2],
                    "goles_A": int(row[3]), "goles_B": int(row[4]),
                    "resolucion": row[5], "ganador": row[6],
                    "perdedor": row[7] if len(row) > 7 else ""
                }
            except (ValueError, IndexError):
                pass
    return result

@st.cache_data(ttl=30)
def cargar_pichichi():
    ws = get_sheet("pichichi")
    rows = ws.get_all_values()
    return rows[0][0] if rows and rows[0] else None

# ---- ESCRITURA ----
def guardar_participantes(participantes):
    ws = get_sheet("participantes")
    ws.clear()
    rows = [[nombre] + equipos for nombre, equipos in participantes.items()]
    if rows:
        ws.update(range_name="A1", values=rows)
    cargar_participantes.clear()

def guardar_resultado_grupo(key, eA, eB, gA, gB):
    ws = get_sheet("resultados_grupos")
    all_rows = ws.get_all_values()
    keys = [r[0] for r in all_rows]
    new_row = [key, eA, eB, str(gA), str(gB)]
    if key in keys:
        ws.update(range_name=f"A{keys.index(key)+1}", values=[new_row])
    else:
        ws.append_row(new_row)
    cargar_resultados_grupos.clear()

def borrar_resultado_grupo(key):
    ws = get_sheet("resultados_grupos")
    all_rows = ws.get_all_values()
    keys = [r[0] for r in all_rows]
    if key in keys:
        ws.delete_rows(keys.index(key) + 1)
    cargar_resultados_grupos.clear()

def guardar_resultado_elim(m_id, eA, eB, gA, gB, res, gan, perd):
    ws = get_sheet("resultados_elim")
    all_rows = ws.get_all_values()
    keys = [r[0] for r in all_rows]
    new_row = [m_id, eA, eB, str(gA), str(gB), res, gan, perd]
    if m_id in keys:
        ws.update(range_name=f"A{keys.index(m_id)+1}", values=[new_row])
    else:
        ws.append_row(new_row)
    cargar_resultados_elim.clear()

def borrar_resultado_elim(m_id):
    ws = get_sheet("resultados_elim")
    all_rows = ws.get_all_values()
    keys = [r[0] for r in all_rows]
    if m_id in keys:
        ws.delete_rows(keys.index(m_id) + 1)
    cargar_resultados_elim.clear()

def guardar_pichichi(eq):
    ws = get_sheet("pichichi")
    ws.clear()
    if eq:
        ws.update(range_name="A1", values=[[eq]])
    cargar_pichichi.clear()

# --- SESIÓN ---
if "admin" not in st.session_state:
    st.session_state.admin = False

# --- CARGA DE DATOS ---
participantes     = cargar_participantes()
resultados_grupos = cargar_resultados_grupos()
resultados_elim   = cargar_resultados_elim()
pichichi          = cargar_pichichi()

# --- CÁLCULO ---
def obtener_tabla_grupos():
    tabla = []
    for g, equipos in GRUPOS.items():
        for eq in equipos:
            pts = 0; gf = 0; gc = 0; pj = 0
            for p in resultados_grupos.values():
                if p['equipo_A'] == eq:
                    pj += 1; gf += p['goles_A']; gc += p['goles_B']
                    if p['goles_A'] > p['goles_B']: pts += 3
                    elif p['goles_A'] == p['goles_B']: pts += 1
                elif p['equipo_B'] == eq:
                    pj += 1; gf += p['goles_B']; gc += p['goles_A']
                    if p['goles_B'] > p['goles_A']: pts += 3
                    elif p['goles_B'] == p['goles_A']: pts += 1
            tabla.append({'Grupo': g, 'Equipo': eq, 'PJ': pj, 'Pts': pts, 'GF': gf, 'GC': gc, 'Dif': gf - gc})
    return pd.DataFrame(tabla).sort_values(
        by=['Grupo', 'Pts', 'Dif', 'GF'], ascending=[True, False, False, False]
    ).reset_index(drop=True)

def obtener_clasificados(df_tabla):
    posiciones = {}
    terceros = []
    for g in GRUPOS.keys():
        eqs = df_tabla[df_tabla['Grupo'] == g].to_dict('records')
        if len(eqs) == 4:
            posiciones[f"1{g}"] = eqs[0]['Equipo']
            posiciones[f"2{g}"] = eqs[1]['Equipo']
            terceros.append(eqs[2])
    terceros = sorted(terceros, key=lambda x: (x['Pts'], x['Dif'], x['GF']), reverse=True)
    for i in range(min(8, len(terceros))):
        posiciones[f"3_{i+1}"] = terceros[i]['Equipo']
    return posiciones

def calcular_puntos(df_tabla):
    puntos = {eq: 0 for eq in VALOR_EQUIPOS.keys()}
    for p in resultados_grupos.values():
        eA, eB = p['equipo_A'], p['equipo_B']
        dif = p['goles_A'] - p['goles_B']
        if dif >= 3: puntos[eA] += 1; puntos[eB] -= 1
        elif dif <= -3: puntos[eB] += 1; puntos[eA] -= 1
        if dif > 0: puntos[eA] += 3
        elif dif < 0: puntos[eB] += 3
        else: puntos[eA] += 1; puntos[eB] += 1

    terceros_bono = []
    for g in GRUPOS.keys():
        eqs = df_tabla[df_tabla['Grupo'] == g].to_dict('records')
        if len(eqs) == 4:
            puntos[eqs[0]['Equipo']] += 3
            puntos[eqs[1]['Equipo']] += 2
            if eqs[3]['Pts'] == 0: puntos[eqs[3]['Equipo']] -= 3
            else: puntos[eqs[3]['Equipo']] -= 1
            terceros_bono.append(eqs[2])
    terceros_bono = sorted(terceros_bono, key=lambda x: (x['Pts'], x['Dif'], x['GF']), reverse=True)
    for i in range(min(8, len(terceros_bono))):
        puntos[terceros_bono[i]['Equipo']] += 1

    for m_id, p in resultados_elim.items():
        eA, eB, res, gan = p['equipo_A'], p['equipo_B'], p['resolucion'], p['ganador']
        dif = p['goles_A'] - p['goles_B']
        if m_id == "M103 (3º y 4º)":
            puntos[gan] += 3; continue
        if dif >= 3: puntos[eA] += 1; puntos[eB] -= 1
        elif dif <= -3: puntos[eB] += 1; puntos[eA] -= 1
        if res == "90 min":
            if dif > 0: puntos[eA] += 4
            elif dif < 0: puntos[eB] += 4
        elif res == "Prórroga":
            if dif > 0: puntos[eA] += 3
            elif dif < 0: puntos[eB] += 3
        elif res == "Penaltis":
            puntos[eA] += 1; puntos[eB] += 1; puntos[gan] += 1
        if m_id == "M104 (FINAL)":
            puntos[gan] += 10
            puntos[eB if gan == eA else eA] += 6
    if pichichi:
        puntos[pichichi] += 2
    return puntos

df_tabla   = obtener_tabla_grupos()
pos_grupos = obtener_clasificados(df_tabla)

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
st.sidebar.title("Porra Mundial 2026 🌍")

with st.sidebar.expander("🔐 Admin"):
    if not st.session_state.admin:
        pwd = st.text_input("Contraseña", type="password", key="pwd_input")
        if st.button("Entrar"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
        st.success("✅ Modo admin activo")
        if st.button("Cerrar sesión"):
            st.session_state.admin = False
            st.rerun()

opciones_menu = ["📊 Clasificación General", "🏆 Clasificación de Grupos", "⚽ Cuadro Eliminatorias"]
if st.session_state.admin:
    opciones_menu += ["👥 Gestión de Participantes", "🔧 Fase de Grupos (Admin)", "⚔️ Eliminatorias (Admin)", "🥇 Pichichi (Admin)"]

menu = st.sidebar.radio("Navegación", opciones_menu)

# ══════════════════════════════════════════
# PÁGINAS PÚBLICAS
# ══════════════════════════════════════════
if menu == "📊 Clasificación General":
    st.header("📊 Clasificación General")
    if not participantes:
        st.warning("Aún no hay participantes registrados.")
    else:
        pts = calcular_puntos(df_tabla)
        clasif = [{"Jugador": a, "Puntos": sum(pts[eq] for eq in eqs), "Equipos": ", ".join(eqs)}
                  for a, eqs in participantes.items()]
        df = pd.DataFrame(clasif).sort_values("Puntos", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)

elif menu == "🏆 Clasificación de Grupos":
    st.header("🏆 Clasificación de Grupos")
    if not resultados_grupos:
        st.warning("Aún no hay resultados de la fase de grupos.")
    else:
        cols = st.columns(3)
        for idx, (grupo, _) in enumerate(GRUPOS.items()):
            with cols[idx % 3]:
                st.subheader(f"Grupo {grupo}")
                df_g = df_tabla[df_tabla['Grupo'] == grupo][['Equipo','PJ','Pts','GF','GC','Dif']].reset_index(drop=True)
                df_g.index += 1
                mejores_3 = [pos_grupos.get(f"3_{i+1}") for i in range(8)]
                def hl(row):
                    if row.name <= 2: return ['background-color:#1a472a;color:white']*len(row)
                    if row.name == 3 and row['Equipo'] in mejores_3: return ['background-color:#2d6a4f;color:white']*len(row)
                    return ['']*len(row)
                st.dataframe(df_g.style.apply(hl, axis=1), use_container_width=True)

        st.subheader("Clasificados a Dieciseisavos")
        ca, cb, cc = st.columns(3)
        with ca:
            st.markdown("**🥇 Primeros**")
            for k, v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("1")): st.write(f"{k}: {v}")
        with cb:
            st.markdown("**🥈 Segundos**")
            for k, v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("2")): st.write(f"{k}: {v}")
        with cc:
            st.markdown("**🥉 Mejores terceros**")
            for k, v in sorted((k,v) for k,v in pos_grupos.items() if k.startswith("3")): st.write(f"{k}: {v}")

elif menu == "⚽ Cuadro Eliminatorias":
    st.header("⚽ Cuadro de Eliminatorias")

    def qu_gan(m_id, perdedor=False):
        if m_id in resultados_elim:
            return resultados_elim[m_id]['perdedor' if perdedor else 'ganador']
        return f"? ({m_id})"

    def mostrar(m_id, eA, eB):
        d = resultados_elim.get(m_id)
        if d:
            st.markdown(f"**{m_id}**: {eA} vs {eB} → `{d['goles_A']}-{d['goles_B']} ({d['resolucion']})` → 🏆 **{d['ganador']}**")
        else:
            st.markdown(f"**{m_id}**: {eA} vs {eB} — *pendiente*")

    st.subheader("Dieciseisavos")
    for m_id,(c1,c2) in EMPAREJAMIENTOS_16VOS.items(): mostrar(m_id, pos_grupos.get(c1,c1), pos_grupos.get(c2,c2))
    st.subheader("Octavos")
    for m_id,(m1,m2) in CRUCES_OCTAVOS.items(): mostrar(m_id, qu_gan(m1), qu_gan(m2))
    st.subheader("Cuartos")
    for m_id,(m1,m2) in CRUCES_CUARTOS.items(): mostrar(m_id, qu_gan(m1), qu_gan(m2))
    st.subheader("Semifinales")
    for m_id,(m1,m2) in CRUCES_SEMIS.items(): mostrar(m_id, qu_gan(m1), qu_gan(m2))
    st.subheader("Finales")
    for m_id,(m1,m2) in CRUCES_FINALES.items():
        mostrar(m_id, qu_gan(m1.replace("_L",""), perdedor="_L" in m1), qu_gan(m2.replace("_L",""), perdedor="_L" in m2))

# ══════════════════════════════════════════
# PÁGINAS ADMIN
# ══════════════════════════════════════════
elif menu == "👥 Gestión de Participantes":
    st.header("👥 Gestión de Participantes")
    with st.form("form_amigos"):
        nombre = st.text_input("Nombre")
        equipos_sel = st.multiselect("Selecciones (máx 30 pts)", list(VALOR_EQUIPOS.keys()))
        coste = sum(VALOR_EQUIPOS[e] for e in equipos_sel)
        st.write(f"Coste: **{coste} / 30**")
        if st.form_submit_button("Añadir / Actualizar"):
            if not nombre: st.error("Falta el nombre.")
            elif coste > 30: st.error(f"Demasiados puntos ({coste}/30).")
            else:
                participantes[nombre] = equipos_sel
                guardar_participantes(participantes)
                st.success(f"✅ {nombre} guardado."); st.rerun()
    if participantes:
        st.subheader("Participantes actuales")
        for nom, eqs in participantes.items():
            c1, c2 = st.columns([4,1])
            c1.write(f"**{nom}** ({sum(VALOR_EQUIPOS[e] for e in eqs)} pts): {', '.join(eqs)}")
            if c2.button("🗑️", key=f"del_{nom}"):
                del participantes[nom]
                guardar_participantes(participantes); st.rerun()

elif menu == "🔧 Fase de Grupos (Admin)":
    st.header("🔧 Resultados Fase de Grupos")
    st.info("Los cambios se guardan automáticamente en Google Sheets.")
    cols = st.columns(3)
    for idx, (grupo, eq) in enumerate(GRUPOS.items()):
        with cols[idx % 3]:
            st.subheader(f"Grupo {grupo}")
            cruces = [(eq[0],eq[1]),(eq[2],eq[3]),(eq[0],eq[2]),(eq[1],eq[3]),(eq[0],eq[3]),(eq[1],eq[2])]
            for eA, eB in cruces:
                key = f"{eA}_{eB}"
                g = resultados_grupos.get(key, {})
                val_A = str(g.get("goles_A","")) if g else ""
                val_B = str(g.get("goles_B","")) if g else ""
                c1,c2,c3,c4 = st.columns([3,1,1,3])
                c1.write(eA)
                gA = c2.text_input("", key=f"inp_A_{key}", value=val_A, label_visibility="collapsed")
                gB = c3.text_input("", key=f"inp_B_{key}", value=val_B, label_visibility="collapsed")
                c4.write(eB)
                if gA.isdigit() and gB.isdigit():
                    if not g or g.get("goles_A") != int(gA) or g.get("goles_B") != int(gB):
                        guardar_resultado_grupo(key, eA, eB, int(gA), int(gB))
                elif val_A != "" and gA == "" and gB == "":
                    borrar_resultado_grupo(key)
            st.divider()
    st.success(f"✅ {len(resultados_grupos)} / 72 partidos guardados")

elif menu == "⚔️ Eliminatorias (Admin)":
    st.header("⚔️ Cuadro de Eliminatorias (Admin)")

    def qu_gan(m_id, perdedor=False):
        if m_id in resultados_elim:
            return resultados_elim[m_id]['perdedor' if perdedor else 'ganador']
        return f"? ({m_id})"

    def renderizar(m_id, eA, eB, col):
        with col:
            st.markdown(f"**{m_id}**: {eA} vs {eB}")
            if eA not in VALOR_EQUIPOS or eB not in VALOR_EQUIPOS:
                st.caption("Esperando clasificados..."); return
            g = resultados_elim.get(m_id, {})
            val_gA = str(g.get("goles_A","")) if g else ""
            val_gB = str(g.get("goles_B","")) if g else ""
            val_res = g.get("resolucion","90 min") if g else "90 min"
            val_gan = g.get("ganador", eA) if g else eA
            c1,c2 = st.columns(2)
            gA = c1.text_input("Goles A", key=f"ga_{m_id}", value=val_gA, placeholder=eA[:3])
            gB = c2.text_input("Goles B", key=f"gb_{m_id}", value=val_gB, placeholder=eB[:3])
            ops = ["90 min","Prórroga","Penaltis"]
            res = st.selectbox("Decisión", ops, index=ops.index(val_res) if val_res in ops else 0, key=f"res_{m_id}")
            gan_pen = None
            if res == "Penaltis":
                idx_p = [eA,eB].index(val_gan) if val_gan in [eA,eB] else 0
                gan_pen = st.selectbox("Ganó penaltis:", [eA,eB], index=idx_p, key=f"pen_{m_id}")
            if gA.isdigit() and gB.isdigit():
                gA_i, gB_i = int(gA), int(gB)
                if gA_i > gB_i: gan,perd = eA,eB
                elif gB_i > gA_i: gan,perd = eB,eA
                else:
                    if res != "Penaltis": st.warning("Empate → selecciona Penaltis"); return
                    gan = gan_pen; perd = eB if gan == eA else eA
                if not g or g.get("goles_A")!=gA_i or g.get("goles_B")!=gB_i or g.get("resolucion")!=res or g.get("ganador")!=gan:
                    guardar_resultado_elim(m_id, eA, eB, gA_i, gB_i, res, gan, perd)
            elif val_gA != "" and gA == "" and gB == "":
                borrar_resultado_elim(m_id)

    st.subheader("Dieciseisavos"); c16=st.columns(4)
    for i,(m_id,(c1,c2)) in enumerate(EMPAREJAMIENTOS_16VOS.items()): renderizar(m_id, pos_grupos.get(c1,c1), pos_grupos.get(c2,c2), c16[i%4])
    st.subheader("Octavos"); c8=st.columns(4)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_OCTAVOS.items()): renderizar(m_id, qu_gan(m1), qu_gan(m2), c8[i%4])
    st.subheader("Cuartos"); c4=st.columns(4)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_CUARTOS.items()): renderizar(m_id, qu_gan(m1), qu_gan(m2), c4[i%4])
    st.subheader("Semifinales"); c2=st.columns(2)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_SEMIS.items()): renderizar(m_id, qu_gan(m1), qu_gan(m2), c2[i])
    st.subheader("Finales"); cf=st.columns(2)
    for i,(m_id,(m1,m2)) in enumerate(CRUCES_FINALES.items()):
        renderizar(m_id, qu_gan(m1.replace("_L",""),perdedor="_L" in m1), qu_gan(m2.replace("_L",""),perdedor="_L" in m2), cf[i])

elif menu == "🥇 Pichichi (Admin)":
    st.header("🥇 Premio Pichichi")
    ops = ["Ninguno aún..."] + list(VALOR_EQUIPOS.keys())
    idx = ops.index(pichichi) if pichichi in ops else 0
    sel = st.selectbox("Selección del Pichichi (+2 pts)", ops, index=idx)
    if st.button("Guardar"):
        guardar_pichichi(sel if sel != "Ninguno aún..." else None)
        st.success("¡Guardado!")
