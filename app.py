import os
import json
from datetime import datetime

import pandas as pd
import streamlit as st

import config
from utils.ai_analysis import generate_tobe_analysis

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=config.WORKSHOP_TITLE,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<style>
[data-testid="stSidebar"] {{
    background-color: {config.COLORS['primary_dark']};
}}
[data-testid="stSidebar"] * {{
    color: white !important;
}}
[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.3);
    color: white !important;
}}
.main-header {{
    background: linear-gradient(135deg, {config.COLORS['primary_dark']} 0%,
                                        {config.COLORS['primary']} 100%);
    padding: 1.4rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    color: white;
}}
.phase-banner {{
    background-color: {config.COLORS['primary']};
    color: white !important;
    padding: 0.7rem 1.4rem;
    border-radius: 8px;
    margin-bottom: 1.4rem;
    font-size: 1.05rem;
    font-weight: 600;
}}
.info-card {{
    background: white;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}}
.hint-box {{
    background: #e8f4fd;
    border-radius: 6px;
    padding: 0.65rem 1rem;
    font-size: 0.88rem;
    color: {config.COLORS['text_muted']};
    margin-top: 0.4rem;
    margin-bottom: 1rem;
}}
h1, h2, h3 {{ color: {config.COLORS['primary_dark']}; }}
</style>
""",
    unsafe_allow_html=True,
)

# ── Default DataFrames ────────────────────────────────────────────────────────
def _default_asis() -> pd.DataFrame:
    return pd.DataFrame({
        "Step #": pd.array([1, 2, 3], dtype="Int64"),
        "Attività": ["", "", ""],
        "Chi la svolge?": ["", "", ""],
        "Strumenti usati": ["", "", ""],
        "Tempo (min)": pd.array([0, 0, 0], dtype="Int64"),
        "Problemi / criticità": ["", "", ""],
    })


def _default_tobe() -> pd.DataFrame:
    return pd.DataFrame({
        "Step #": pd.array([1, 2, 3], dtype="Int64"),
        "Attività futura": ["", "", ""],
        "Chi la svolge?": ["", "", ""],
        "Strumenti / Tecnologie": ["", "", ""],
        "Tempo previsto (min)": pd.array([0, 0, 0], dtype="Int64"),
        "Benefici attesi": ["", "", ""],
        "Rischi / ostacoli": ["", "", ""],
    })


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "current_phase": 0,
        "answers": {},
        "asis_df": _default_asis(),
        "tobe_df": _default_tobe(),
        "tobe_prepopulated": False,
        "analysis_result": None,
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()


def go_to(phase: int):
    st.session_state.current_phase = phase
    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:0.8rem 0 1rem 0;
                    border-bottom:1px solid rgba(255,255,255,0.2); margin-bottom:1rem;">
            <div style="font-size:2rem; font-weight:900; letter-spacing:1px;">iFAB</div>
            <div style="font-size:0.68rem; opacity:0.75; margin-top:0.2rem;
                        text-transform:uppercase; letter-spacing:0.5px;">
                International Foundation<br>Big Data &amp; AI for Human Development
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Workshop Finale")
    st.markdown(f"**{config.WORKSHOP_SUBTITLE}**")
    st.markdown("---")

    cur_phase = st.session_state.current_phase
    for pid, pcfg in config.PHASES.items():
        if pid < cur_phase:
            marker, style = "✅", "opacity:0.75;"
        elif pid == cur_phase:
            marker, style = "▶", "font-weight:700;"
        else:
            marker, style = "○", "opacity:0.45;"
        st.markdown(
            f"<div style='{style} padding:0.25rem 0; font-size:0.88rem;'>"
            f"{marker} {pcfg['icon']} {pcfg['name']} "
            f"<span style='opacity:0.65'>({pcfg['duration']})</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    with st.expander("⚙️ API Key"):
        key_input = st.text_input(
            "Anthropic API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-ant-...",
        )
        if key_input:
            st.session_state.api_key = key_input

    if st.session_state.analysis_result:
        st.markdown("---")
        a = st.session_state.answers
        export = {
            "timestamp": datetime.now().isoformat(),
            "profilo": {
                "nome": a.get("q0_nome", ""),
                "ruolo": a.get("q0_ruolo", ""),
                "organizzazione": a.get("q0_org", ""),
                "processo": a.get("q0_processo", ""),
                "descrizione": a.get("q0_descrizione", ""),
            },
            "asis": st.session_state.asis_df.to_dict(orient="records"),
            "tobe": st.session_state.tobe_df.to_dict(orient="records"),
            "analisi_tobe": st.session_state.analysis_result,
        }
        st.download_button(
            "📥 Esporta progetto (JSON)",
            data=json.dumps(export, ensure_ascii=False, indent=2),
            file_name=f"workshop_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "📄 Esporta analisi (MD)",
            data=st.session_state.analysis_result,
            file_name=f"analisi_tobe_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")
    if st.button("🔄 Ricomincia da capo", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
nome = st.session_state.answers.get("q0_nome", "")
processo = st.session_state.answers.get("q0_processo", "")
if nome and processo:
    sub = f"{nome} · {processo}"
elif nome:
    sub = f"Bentornato/a, {nome}!"
else:
    sub = "Workshop interattivo IFAB"

st.markdown(
    f"""
    <div class="main-header">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:0.8rem; opacity:0.8; margin-bottom:0.25rem;">
                    FONDAZIONE IFAB · {config.WORKSHOP_SUBTITLE}
                </div>
                <div style="font-size:1.45rem; font-weight:700; color:white;">
                    {config.WORKSHOP_TITLE}
                </div>
                <div style="font-size:0.88rem; opacity:0.85; margin-top:0.2rem;">{sub}</div>
            </div>
            <div style="font-size:2.8rem;">🔍</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Phase renderers
# ══════════════════════════════════════════════════════════════════════════════

def render_welcome():
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("## 👋 Benvenuto/a al workshop finale!")
        st.markdown(
            """
Questo workshop ti guida nella **mappatura e trasformazione di un processo aziendale**
con l'intelligenza artificiale, seguendo la metodologia AS-IS → TO-BE.

**Il percorso in 3 fasi:**
1. 🔍 **Mappatura AS-IS** — Come funziona oggi il processo? Chi fa cosa, con quali strumenti, in quanto tempo?
2. 🚀 **Mappatura TO-BE** — Come cambierebbe con l'AI? Quali step beneficiano di sostituzione o augmentation?
3. 🤖 **Confronto & AI** — Analisi comparativa, scenario narrativo, roadmap e analisi rischi generata dall'AI.

Alla fine avrai: una **mappa del tuo processo futuro**, un'**analisi dei rischi**
e una **roadmap concreta** di implementazione.
            """
        )

        st.markdown("---")
        st.markdown("### Parliamo di te e del tuo processo")

        nome_in = st.text_input(
            "Nome e cognome",
            value=st.session_state.answers.get("q0_nome", ""),
            placeholder="Es: Marco Rossi",
        )
        ruolo_in = st.text_input(
            "Ruolo / funzione",
            value=st.session_state.answers.get("q0_ruolo", ""),
            placeholder="Es: Responsabile Formazione",
        )
        org_in = st.text_input(
            "Organizzazione",
            value=st.session_state.answers.get("q0_org", ""),
            placeholder="Es: Oil & Steel SpA",
        )
        processo_in = st.text_input(
            "Processo da analizzare",
            value=st.session_state.answers.get("q0_processo", ""),
            placeholder="Es: Onboarding nuovi fornitori",
            help="Dai un nome breve e descrittivo al processo che vuoi analizzare",
        )
        descr_in = st.text_area(
            "Breve descrizione del processo",
            value=st.session_state.answers.get("q0_descrizione", ""),
            placeholder=(
                "Es: Il processo include la raccolta documenti, la verifica dei requisiti, "
                "la registrazione nel sistema e la formazione iniziale. "
                "Attualmente richiede 2-3 settimane e coinvolge 4 dipartimenti."
            ),
            height=110,
        )

        st.markdown("")
        if st.button("Inizia il workshop →", type="primary", use_container_width=True):
            if nome_in.strip() and processo_in.strip():
                st.session_state.answers.update({
                    "q0_nome": nome_in,
                    "q0_ruolo": ruolo_in,
                    "q0_org": org_in,
                    "q0_processo": processo_in,
                    "q0_descrizione": descr_in,
                })
                go_to(1)
            else:
                st.error("Inserisci almeno il nome e il processo da analizzare per continuare.")

    with col_side:
        st.markdown(
            f"""
            <div class="info-card">
                <div style="font-weight:600; margin-bottom:0.8rem; color:{config.COLORS['primary']};">
                    ⏱️ Struttura del workshop
                </div>
                <div style="font-size:0.88rem; line-height:2.2;">
                    👋 Introduzione · <strong>5'</strong><br>
                    🔍 Mappatura AS-IS · <strong>15'</strong><br>
                    🚀 Mappatura TO-BE · <strong>10'</strong><br>
                    🤖 Confronto &amp; AI · <strong>20'</strong>
                </div>
            </div>
            <div class="info-card" style="border-left: 4px solid {config.COLORS['accent']};">
                <div style="font-weight:600; margin-bottom:0.6rem;">💡 Come scegliere il processo</div>
                <div style="font-size:0.85rem; line-height:1.8;">
                    Scegli un processo che:<br>
                    • Si ripete regolarmente<br>
                    • Coinvolge più persone o step<br>
                    • Ha inefficienze note<br>
                    • Produce output standardizzabili<br>
                    • Non è critico al 100% (ideale per pilota)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_asis():
    pcfg = config.PHASES[1]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 1 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )

    processo = st.session_state.answers.get("q0_processo", "il processo")
    st.markdown(f"## 🔍 Come funziona oggi **{processo}**?")
    st.markdown(
        "Mappa il processo **AS-IS**: inserisci tutti gli step, chi li svolge, "
        "gli strumenti usati, il tempo e i problemi principali. "
        "Usa il pulsante **+** in basso per aggiungere righe."
    )

    st.markdown(
        f'<div class="hint-box">💡 <em>Suggerimento: parti dagli step principali '
        f'(3-8 è un buon numero). Anche stime approssimative del tempo sono utili.</em></div>',
        unsafe_allow_html=True,
    )

    edited_asis = st.data_editor(
        st.session_state.asis_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Step #": st.column_config.NumberColumn("Step #", min_value=1, step=1, width="small"),
            "Attività": st.column_config.TextColumn("Attività", width="large"),
            "Chi la svolge?": st.column_config.TextColumn("Chi la svolge?", width="medium"),
            "Strumenti usati": st.column_config.TextColumn("Strumenti usati", width="medium"),
            "Tempo (min)": st.column_config.NumberColumn("Tempo (min)", min_value=0, step=5, width="small"),
            "Problemi / criticità": st.column_config.TextColumn("Problemi / criticità", width="large"),
        },
        key="asis_editor",
    )
    st.session_state.asis_df = edited_asis

    total_time = int(edited_asis["Tempo (min)"].fillna(0).sum())
    if total_time > 0:
        st.markdown(
            f"**⏱️ Tempo totale AS-IS: {total_time} minuti** "
            f"({total_time // 60}h {total_time % 60}min)"
        )

    st.markdown("")
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Indietro", use_container_width=True):
            go_to(0)
    with col_next:
        n_filled = int(
            (edited_asis["Attività"].fillna("").astype(str).str.strip() != "").sum()
        )
        if st.button(
            "Vai alla Mappatura TO-BE →",
            type="primary",
            use_container_width=True,
            disabled=(n_filled == 0),
        ):
            _prepopulate_tobe_from_asis()
            go_to(2)
        if n_filled == 0:
            st.caption("⚠️ Inserisci almeno un'attività per continuare.")


def _prepopulate_tobe_from_asis():
    if st.session_state.tobe_prepopulated:
        return
    asis = st.session_state.asis_df
    mask = asis["Attività"].fillna("").astype(str).str.strip() != ""
    filled = asis[mask].reset_index(drop=True)
    if filled.empty:
        return
    n = len(filled)
    st.session_state.tobe_df = pd.DataFrame({
        "Step #": filled["Step #"].values,
        "Attività futura": filled["Attività"].values,
        "Chi la svolge?": filled["Chi la svolge?"].values,
        "Strumenti / Tecnologie": ["" for _ in range(n)],
        "Tempo previsto (min)": pd.array([0] * n, dtype="Int64"),
        "Benefici attesi": ["" for _ in range(n)],
        "Rischi / ostacoli": ["" for _ in range(n)],
    })
    st.session_state.tobe_prepopulated = True


def render_tobe_mapping():
    pcfg = config.PHASES[2]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 2 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )

    processo = st.session_state.answers.get("q0_processo", "il processo")
    st.markdown(f"## 🚀 Come cambierà **{processo}** con l'AI?")
    st.markdown(
        "Immagina il processo **TO-BE**: per ogni step, descrivi come cambierà l'attività, "
        "chi la svolgerà, quali tecnologie AI si userebbero e quali benefici si otterranno."
    )

    st.markdown(
        f'<div class="hint-box">💡 <em>Per ogni step chiediti: l\'AI <strong>sostituisce</strong> '
        f'l\'umano (task ripetitivi, standardizzati) oppure lo <strong>augmenta</strong> '
        f'(analisi, decisioni complesse)? Puoi anche eliminare step che diventano automatici.</em></div>',
        unsafe_allow_html=True,
    )

    col_tobe, col_ref = st.columns([3, 1])

    with col_ref:
        st.markdown("**📋 Riferimento AS-IS**")
        ref_df = st.session_state.asis_df[
            st.session_state.asis_df["Attività"].fillna("").astype(str).str.strip() != ""
        ][["Step #", "Attività", "Tempo (min)"]].copy()
        st.dataframe(ref_df, use_container_width=True, hide_index=True, height=320)
        asis_time = int(st.session_state.asis_df["Tempo (min)"].fillna(0).sum())
        if asis_time > 0:
            st.caption(f"AS-IS totale: **{asis_time} min**")

    with col_tobe:
        edited_tobe = st.data_editor(
            st.session_state.tobe_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Step #": st.column_config.NumberColumn("Step #", min_value=1, step=1, width="small"),
                "Attività futura": st.column_config.TextColumn("Attività futura", width="large"),
                "Chi la svolge?": st.column_config.TextColumn("Chi la svolge?", width="medium"),
                "Strumenti / Tecnologie": st.column_config.TextColumn("Strumenti AI / Tecnologie", width="medium"),
                "Tempo previsto (min)": st.column_config.NumberColumn("Tempo prev. (min)", min_value=0, step=5, width="small"),
                "Benefici attesi": st.column_config.TextColumn("Benefici attesi", width="medium"),
                "Rischi / ostacoli": st.column_config.TextColumn("Rischi / ostacoli", width="medium"),
            },
            key="tobe_editor",
        )
        st.session_state.tobe_df = edited_tobe

        tobe_time = int(edited_tobe["Tempo previsto (min)"].fillna(0).sum())
        if tobe_time > 0:
            delta = asis_time - tobe_time
            pct = int(delta / asis_time * 100) if asis_time > 0 else 0
            suffix = f" · risparmio **{delta} min ({pct}%)**" if delta > 0 else ""
            st.markdown(f"**⏱️ Tempo totale TO-BE: {tobe_time} minuti**{suffix}")

    st.markdown("")
    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button("← Indietro (AS-IS)", use_container_width=True):
            go_to(1)
    with col_next:
        n_filled = int(
            (edited_tobe["Attività futura"].fillna("").astype(str).str.strip() != "").sum()
        )
        if st.button(
            "Vai al Confronto & Analisi AI →",
            type="primary",
            use_container_width=True,
            disabled=(n_filled == 0),
        ):
            go_to(3)
        if n_filled == 0:
            st.caption("⚠️ Inserisci almeno un'attività TO-BE per continuare.")


def render_confronto():
    pcfg = config.PHASES[3]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 3 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )

    asis_df = st.session_state.asis_df
    tobe_df = st.session_state.tobe_df
    processo = st.session_state.answers.get("q0_processo", "il processo")

    st.markdown(f"## 🤖 Confronto AS-IS → TO-BE: **{processo}**")

    # ── Quick stats ──────────────────────────────────────────────────────────
    asis_time = int(asis_df["Tempo (min)"].fillna(0).sum())
    tobe_time = int(tobe_df["Tempo previsto (min)"].fillna(0).sum())
    delta = asis_time - tobe_time
    pct = int(delta / asis_time * 100) if asis_time > 0 else 0
    n_asis = int((asis_df["Attività"].fillna("").astype(str).str.strip() != "").sum())
    n_tobe = int((tobe_df["Attività futura"].fillna("").astype(str).str.strip() != "").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("⏱️ Tempo AS-IS", f"{asis_time} min")
    with c2:
        st.metric(
            "🚀 Tempo TO-BE",
            f"{tobe_time} min",
            delta=f"-{delta} min ({pct}%)" if delta > 0 else None,
            delta_color="inverse",
        )
    with c3:
        st.metric("📋 Step AS-IS", n_asis)
    with c4:
        st.metric("✨ Step TO-BE", n_tobe)

    st.markdown("---")

    # ── Tables comparison ────────────────────────────────────────────────────
    tab_asis, tab_tobe = st.tabs(["📋 Mappa AS-IS", "🚀 Mappa TO-BE"])
    with tab_asis:
        st.dataframe(
            asis_df[asis_df["Attività"].fillna("").astype(str).str.strip() != ""],
            use_container_width=True,
            hide_index=True,
        )
    with tab_tobe:
        st.dataframe(
            tobe_df[tobe_df["Attività futura"].fillna("").astype(str).str.strip() != ""],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # ── AI analysis ──────────────────────────────────────────────────────────
    if not st.session_state.analysis_result:
        _render_generate_analysis()
    else:
        _render_analysis_results()


def _render_generate_analysis():
    st.markdown("## 🤖 Genera l'analisi AI")
    st.markdown(
        """
Sulla base delle due mappe, l'AI genererà:

- 📊 **Sostituzione vs Augmentation** — classificazione step per step
- 🌅 **Scenario narrativo** — come cambierà la giornata lavorativa
- ⚠️ **Analisi dei rischi** — tecnici, organizzativi, etici, con mitigazioni
- 📅 **Roadmap** — piano pratico in 3 fasi con KPI
- 🤝 **Domanda aperta** — per portare la discussione al tuo team
        """
    )

    if not st.session_state.api_key:
        st.warning(
            "⚠️ Inserisci la tua **Anthropic API Key** nel pannello ⚙️ nella sidebar "
            "per generare l'analisi."
        )

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(
            "🤖 Genera Analisi AI",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.api_key,
        ):
            with st.spinner("L'AI sta analizzando AS-IS e TO-BE… ⏳"):
                try:
                    result = generate_tobe_analysis(
                        answers=st.session_state.answers,
                        asis_df=st.session_state.asis_df,
                        tobe_df=st.session_state.tobe_df,
                        api_key=st.session_state.api_key,
                    )
                    st.session_state.analysis_result = result
                    st.rerun()
                except Exception as exc:
                    st.error(f"Errore nella generazione: {exc}")
    with col2:
        if st.button("← Modifica TO-BE", use_container_width=True):
            go_to(2)


def _render_analysis_results():
    st.markdown("## 🎯 Analisi AI del tuo scenario TO-BE")
    st.markdown(st.session_state.analysis_result)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📄 Scarica analisi (MD)",
            data=st.session_state.analysis_result,
            file_name=f"analisi_tobe_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 Rigenera analisi", use_container_width=True):
            st.session_state.analysis_result = None
            st.rerun()
    with col3:
        if st.button("🏁 Concludi workshop", type="primary", use_container_width=True):
            st.balloons()
            st.success(
                "Workshop completato! Ottimo lavoro! 🎉  \n"
                "Hai la tua mappa TO-BE, l'analisi dei rischi e la roadmap: "
                "il prossimo passo è presentare i risultati al tuo team."
            )


# ══════════════════════════════════════════════════════════════════════════════
# Main router
# ══════════════════════════════════════════════════════════════════════════════
phase = st.session_state.current_phase

if phase == 0:
    render_welcome()
elif phase == 1:
    render_asis()
elif phase == 2:
    render_tobe_mapping()
elif phase == 3:
    render_confronto()
