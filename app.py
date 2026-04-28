import os
import json
from datetime import datetime

import streamlit as st

import config
from utils.ai_analysis import (
    generate_chat_init,
    generate_chat_response,
    generate_final_analysis,
)
from utils.export import generate_html_report

# ── Page config ───────────────────────────────────────────────────────────────
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
[data-testid="stSidebar"] * {{ color: white !important; }}
.main-header {{
    background: linear-gradient(135deg, {config.COLORS['primary_dark']} 0%,
                                        {config.COLORS['primary']} 100%);
    padding: 1.3rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.4rem;
    color: white;
}}
.phase-banner {{
    background-color: {config.COLORS['primary']};
    color: white !important;
    padding: 0.65rem 1.3rem;
    border-radius: 8px;
    margin-bottom: 1.2rem;
    font-size: 1rem;
    font-weight: 600;
}}
.step-card {{
    background: white;
    border-left: 4px solid {config.COLORS['primary']};
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}}
.step-card .step-num {{
    font-weight: 700;
    color: {config.COLORS['primary']};
    font-size: 0.9rem;
}}
.step-card .step-title {{
    font-size: 1rem;
    font-weight: 600;
    margin: 2px 0;
}}
.step-card .step-meta {{
    font-size: 0.82rem;
    color: {config.COLORS['text_muted']};
}}
.hint-box {{
    background: #e8f4fd;
    border-radius: 6px;
    padding: 0.6rem 1rem;
    font-size: 0.87rem;
    color: {config.COLORS['text_muted']};
    margin-bottom: 1rem;
}}
.info-card {{
    background: white;
    border-radius: 10px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}}
h1, h2, h3 {{ color: {config.COLORS['primary_dark']}; }}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "current_phase": 0,
        "answers": {},
        "asis_steps": [],
        "tobe_steps": [],
        "chat_messages": [],
        "chat_initialized": False,
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


# ── Voice input helper ────────────────────────────────────────────────────────
def _apply_transcript(field_key: str):
    tkey = f"__transcript_{field_key}"
    if tkey in st.session_state:
        st.session_state[f"input_{field_key}"] = st.session_state.pop(tkey)


def voice_text_input(label: str, field_key: str, placeholder: str = "") -> str:
    _apply_transcript(field_key)
    col_t, col_m = st.columns([6, 1])
    with col_t:
        val = st.text_input(label, key=f"input_{field_key}", placeholder=placeholder)
    with col_m:
        st.write("")
        if st.button("🎤", key=f"micbtn_{field_key}", help="Registra con microfono"):
            st.session_state[f"__show_mic_{field_key}"] = True
    _render_mic(field_key)
    return val


def voice_text_area(label: str, field_key: str, placeholder: str = "", height: int = 110) -> str:
    _apply_transcript(field_key)
    col_t, col_m = st.columns([6, 1])
    with col_t:
        val = st.text_area(
            label, key=f"input_{field_key}", placeholder=placeholder, height=height
        )
    with col_m:
        st.write("")
        st.write("")
        if st.button("🎤", key=f"micbtn_{field_key}", help="Registra con microfono"):
            st.session_state[f"__show_mic_{field_key}"] = True
    _render_mic(field_key)
    return val


def _render_mic(field_key: str):
    if not st.session_state.get(f"__show_mic_{field_key}"):
        return
    api_key = st.session_state.api_key
    audio = st.audio_input("🎙️ Parla ora, poi clicca Stop", key=f"audio_{field_key}")
    col_ok, col_x = st.columns([2, 1])
    with col_x:
        if st.button("✕ Annulla", key=f"mic_cancel_{field_key}"):
            st.session_state[f"__show_mic_{field_key}"] = False
            st.rerun()
    if audio:
        with col_ok:
            if st.button("✓ Trascrivi", key=f"mic_ok_{field_key}", type="primary"):
                if not api_key:
                    st.warning("Inserisci la API Key nella sidebar per usare il microfono.")
                else:
                    with st.spinner("Trascrizione..."):
                        try:
                            from utils.voice import transcribe_audio
                            text = transcribe_audio(audio, api_key)
                            st.session_state[f"__transcript_{field_key}"] = text
                            st.session_state[f"__show_mic_{field_key}"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore trascrizione: {e}")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:0.8rem 0 1rem 0;
                    border-bottom:1px solid rgba(255,255,255,0.2); margin-bottom:1rem;">
            <div style="font-size:2rem; font-weight:900; letter-spacing:1px;">iFAB</div>
            <div style="font-size:0.65rem; opacity:0.75; margin-top:0.2rem;
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

    cur = st.session_state.current_phase
    for pid, pcfg in config.PHASES.items():
        if pid < cur:
            marker, style = "✅", "opacity:0.75;"
        elif pid == cur:
            marker, style = "▶", "font-weight:700;"
        else:
            marker, style = "○", "opacity:0.45;"
        st.markdown(
            f"<div style='{style} padding:0.2rem 0; font-size:0.87rem;'>"
            f"{marker} {pcfg['icon']} {pcfg['name']} "
            f"<span style='opacity:0.65'>({pcfg['duration']})</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # API key hidden in expander (not prominent)
    with st.expander("⚙️ Impostazioni"):
        key_in = st.text_input(
            "API Key (Anthropic)",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-ant-...",
        )
        if key_in:
            st.session_state.api_key = key_in

    if st.session_state.analysis_result:
        st.markdown("---")
        html = generate_html_report(
            answers=st.session_state.answers,
            asis_steps=st.session_state.asis_steps,
            tobe_steps=st.session_state.tobe_steps,
            analysis_text=st.session_state.analysis_result,
            conversation=st.session_state.chat_messages,
        )
        st.download_button(
            "📄 Scarica report (PDF via browser)",
            data=html,
            file_name=f"workshop_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True,
            help="Apri il file nel browser → Ctrl+P → Salva come PDF",
        )
        export_json = json.dumps(
            {
                "timestamp": datetime.now().isoformat(),
                "profilo": st.session_state.answers,
                "asis": st.session_state.asis_steps,
                "tobe": st.session_state.tobe_steps,
                "conversazione": st.session_state.chat_messages,
                "analisi": st.session_state.analysis_result,
            },
            ensure_ascii=False,
            indent=2,
        )
        st.download_button(
            "📥 Esporta dati (JSON)",
            data=export_json,
            file_name=f"workshop_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")
    if st.button("🔄 Ricomincia da capo", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
nome = st.session_state.answers.get("q0_nome", "")
processo = st.session_state.answers.get("q0_processo", "")
sub = f"{nome} · {processo}" if nome and processo else ("Bentornato/a!" if nome else "Workshop interattivo IFAB")

st.markdown(
    f"""
    <div class="main-header">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-size:0.78rem; opacity:0.8; margin-bottom:0.2rem;">
            FONDAZIONE IFAB · {config.WORKSHOP_SUBTITLE}
          </div>
          <div style="font-size:1.4rem; font-weight:700; color:white;">
            {config.WORKSHOP_TITLE}
          </div>
          <div style="font-size:0.87rem; opacity:0.85; margin-top:0.18rem;">{sub}</div>
        </div>
        <div style="font-size:2.6rem;">🔍</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Phase 0 — Welcome
# ══════════════════════════════════════════════════════════════════════════════

def render_welcome():
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown("## 👋 Benvenuto/a al workshop finale!")
        st.markdown(
            """
Questo workshop di **~2 ore** ti guida nella mappatura e trasformazione
di un processo aziendale con l'intelligenza artificiale.

**Il percorso:**
1. 🔍 **AS-IS** — Mappa il processo attuale, step per step
2. 🚀 **TO-BE** — Immagina il processo con l'AI integrata
3. 💬 **Approfondimento** — Un agente AI ti fa domande mirate per arricchire l'analisi
4. 🤖 **Analisi Finale** — Scenario narrativo, roadmap e analisi rischi

Puoi rispondere **scrivendo** o **parlando** (microfono) in ogni campo.
            """
        )
        st.markdown("---")
        st.markdown("### Parlaci di te e del tuo processo")

        nome_in = voice_text_input(
            "Nome e cognome *", "w_nome", "Es: Marco Rossi"
        )
        ruolo_in = voice_text_input(
            "Ruolo / funzione", "w_ruolo", "Es: Responsabile Formazione"
        )
        org_in = voice_text_input(
            "Organizzazione", "w_org", "Es: Oil & Steel SpA"
        )
        processo_in = voice_text_input(
            "Processo da analizzare *", "w_processo",
            "Es: Onboarding nuovi fornitori"
        )
        descr_in = voice_text_area(
            "Breve descrizione del processo", "w_descr",
            placeholder=(
                "Es: Il processo include raccolta documenti, verifica requisiti, "
                "registrazione nel sistema e formazione iniziale. "
                "Coinvolge 4 dipartimenti e dura 2-3 settimane."
            ),
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
                st.error("Compila almeno nome e processo per continuare.")

    with col_side:
        st.markdown(
            f"""
            <div class="info-card">
              <div style="font-weight:600; margin-bottom:0.8rem;
                          color:{config.COLORS['primary']};">⏱️ Struttura del workshop</div>
              <div style="font-size:0.87rem; line-height:2.1;">
                👋 Introduzione · <strong>10'</strong><br>
                🔍 Mappatura AS-IS · <strong>20'</strong><br>
                🚀 Mappatura TO-BE · <strong>15'</strong><br>
                💬 Approfondimento AI · <strong>20'</strong><br>
                🤖 Analisi Finale · <strong>20'</strong>
              </div>
            </div>
            <div class="info-card"
                 style="border-left: 4px solid {config.COLORS['accent']};">
              <div style="font-weight:600; margin-bottom:0.6rem;">
                💡 Come scegliere il processo
              </div>
              <div style="font-size:0.85rem; line-height:1.8;">
                Scegli un processo che:<br>
                • Si ripete regolarmente<br>
                • Coinvolge più persone o step<br>
                • Ha inefficienze note<br>
                • Produce output standardizzabili
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Shared: step form + step cards
# ══════════════════════════════════════════════════════════════════════════════

def _step_card(s: dict, is_tobe: bool = False):
    attivita = s.get("attivita", "—")
    chi = s.get("chi", "—")
    strumenti = s.get("strumenti", "")
    tempo = s.get("tempo", "")
    extra = s.get("benefici", "") if is_tobe else s.get("problemi", "")
    extra_label = "Benefici" if is_tobe else "Problemi"
    rischi = s.get("rischi", "") if is_tobe else ""

    meta_parts = [f"👤 {chi}"]
    if strumenti:
        meta_parts.append(f"🛠️ {strumenti}")
    if tempo:
        meta_parts.append(f"⏱️ {tempo} min")
    if extra:
        meta_parts.append(f"{'✅' if is_tobe else '⚠️'} {extra_label}: {extra}")
    if rischi:
        meta_parts.append(f"🔴 Rischi: {rischi}")

    st.markdown(
        f"""<div class="step-card">
          <div class="step-num">Step {s.get('step', '?')}</div>
          <div class="step-title">{attivita}</div>
          <div class="step-meta">{' &nbsp;|&nbsp; '.join(meta_parts)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _steps_table(steps: list, is_tobe: bool):
    import pandas as pd
    if not steps:
        st.info("Nessuno step inserito.")
        return
    if is_tobe:
        rows = [
            {
                "Step #": s.get("step"),
                "Attività futura": s.get("attivita"),
                "Chi la svolge": s.get("chi"),
                "Strumenti / AI": s.get("strumenti"),
                "Tempo prev. (min)": s.get("tempo"),
                "Benefici attesi": s.get("benefici"),
                "Rischi / ostacoli": s.get("rischi"),
            }
            for s in steps
        ]
    else:
        rows = [
            {
                "Step #": s.get("step"),
                "Attività": s.get("attivita"),
                "Chi la svolge": s.get("chi"),
                "Strumenti usati": s.get("strumenti"),
                "Tempo (min)": s.get("tempo"),
                "Problemi / criticità": s.get("problemi"),
            }
            for s in steps
        ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — AS-IS
# ══════════════════════════════════════════════════════════════════════════════

def render_asis():
    pcfg = config.PHASES[1]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 1 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )
    processo = st.session_state.answers.get("q0_processo", "il processo")
    st.markdown(f"## 🔍 Come funziona oggi **{processo}**?")

    steps = st.session_state.asis_steps
    n = len(steps)

    # ── Completed steps ───────────────────────────────────────────────────────
    if steps:
        st.markdown(f"**{n} step inserit{'o' if n == 1 else 'i'}:**")
        for s in steps:
            _step_card(s, is_tobe=False)
        st.markdown("")

    # ── Show summary table at end ─────────────────────────────────────────────
    if st.session_state.get("asis_done"):
        st.success(f"✅ Mappatura AS-IS completata — {n} step")
        _steps_table(steps, is_tobe=False)
        total = sum(int(s.get("tempo") or 0) for s in steps)
        if total:
            st.markdown(f"**⏱️ Tempo totale AS-IS: {total} minuti**")
        st.markdown("")
        col_back, col_next = st.columns([1, 2])
        with col_back:
            if st.button("← Modifica step", use_container_width=True):
                st.session_state.asis_done = False
                st.rerun()
        with col_next:
            if st.button("Vai alla Mappatura TO-BE →", type="primary", use_container_width=True):
                go_to(2)
        return

    # ── Step form ─────────────────────────────────────────────────────────────
    step_num = n + 1
    st.markdown(
        f'<div class="hint-box">💡 <em>Descrivi lo step {step_num} del processo. '
        f'Usa il 🎤 per dettare invece di scrivere.</em></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"#### ➕ Step {step_num}")

    prefix = f"asis_{step_num}"
    attivita = voice_text_area(
        "Descrivi questa attività *", f"{prefix}_att",
        placeholder="Es: Raccolta documenti richiesti al fornitore",
        height=90,
    )
    chi = voice_text_input(
        "Chi la svolge? *", f"{prefix}_chi",
        placeholder="Es: Ufficio Acquisti"
    )
    col1, col2 = st.columns(2)
    with col1:
        strumenti = voice_text_input(
            "Strumenti / sistemi usati", f"{prefix}_str",
            placeholder="Es: Email, SAP, Excel"
        )
    with col2:
        tempo_str = voice_text_input(
            "Tempo richiesto (minuti)", f"{prefix}_tempo",
            placeholder="Es: 45"
        )
    problemi = voice_text_area(
        "Problemi o inefficienze principali", f"{prefix}_prob",
        placeholder="Es: Documenti spesso incompleti, molte mail avanti-indietro",
        height=90,
    )

    def _get_tempo(s):
        try:
            return int(s.strip())
        except Exception:
            return None

    st.markdown("")
    col_add, col_done = st.columns([1, 1])

    with col_add:
        if st.button(f"+ Aggiungi Step {step_num}", use_container_width=True, type="primary"):
            if not attivita.strip() or not chi.strip():
                st.error("Attività e chi la svolge sono obbligatori.")
            else:
                step_data = {
                    "step": step_num,
                    "attivita": attivita.strip(),
                    "chi": chi.strip(),
                    "strumenti": strumenti.strip(),
                    "tempo": _get_tempo(tempo_str),
                    "problemi": problemi.strip(),
                }
                st.session_state.asis_steps.append(step_data)
                # Clear draft fields
                for suffix in ["att", "chi", "str", "tempo", "prob"]:
                    for prefix_key in [f"input_asis_{step_num}_{suffix}",
                                       f"__show_mic_asis_{step_num}_{suffix}"]:
                        st.session_state.pop(prefix_key, None)
                st.rerun()

    with col_done:
        if n > 0:
            if st.button("✓ Concludi AS-IS", use_container_width=True):
                st.session_state.asis_done = True
                st.rerun()
        else:
            st.caption("Aggiungi almeno uno step per concludere.")

    if n > 0:
        st.markdown("")
        if st.button("🗑️ Rimuovi ultimo step", use_container_width=True):
            st.session_state.asis_steps.pop()
            st.rerun()

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Indietro", use_container_width=True):
            go_to(0)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — TO-BE
# ══════════════════════════════════════════════════════════════════════════════

def render_tobe():
    pcfg = config.PHASES[2]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 2 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )
    processo = st.session_state.answers.get("q0_processo", "il processo")
    st.markdown(f"## 🚀 Come cambierà **{processo}** con l'AI?")

    steps = st.session_state.tobe_steps
    n = len(steps)

    # AS-IS reference panel
    with st.expander("📋 Riferimento AS-IS", expanded=False):
        _steps_table(st.session_state.asis_steps, is_tobe=False)

    if steps:
        st.markdown(f"**{n} step inserit{'o' if n == 1 else 'i'}:**")
        for s in steps:
            _step_card(s, is_tobe=True)
        st.markdown("")

    if st.session_state.get("tobe_done"):
        st.success(f"✅ Mappatura TO-BE completata — {n} step")
        _steps_table(steps, is_tobe=True)
        total_asis = sum(int(s.get("tempo") or 0) for s in st.session_state.asis_steps)
        total_tobe = sum(int(s.get("tempo") or 0) for s in steps)
        if total_tobe:
            delta = total_asis - total_tobe
            pct = int(delta / total_asis * 100) if total_asis else 0
            suffix = f" · risparmio **{delta} min ({pct}%)**" if delta > 0 else ""
            st.markdown(f"**⏱️ Tempo totale TO-BE: {total_tobe} minuti{suffix}**")
        st.markdown("")
        col_back, col_next = st.columns([1, 2])
        with col_back:
            if st.button("← Modifica step", use_container_width=True):
                st.session_state.tobe_done = False
                st.rerun()
        with col_next:
            if st.button("Vai all'Approfondimento AI →", type="primary", use_container_width=True):
                go_to(3)
        return

    step_num = n + 1
    st.markdown(
        f'<div class="hint-box">💡 <em>Per ogni step chiediti: l\'AI <strong>sostituisce</strong> '
        f'(task ripetitivi) o <strong>augmenta</strong> (analisi, decisioni)? '
        f'Usa il 🎤 per dettare.</em></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"#### ➕ Step {step_num}")

    prefix = f"tobe_{step_num}"
    attivita = voice_text_area(
        "Come diventa questa attività con l'AI? *", f"{prefix}_att",
        placeholder="Es: Il sistema AI pre-compila la checklist documenti e invia notifiche automatiche",
        height=90,
    )
    chi = voice_text_input(
        "Chi la svolge? *", f"{prefix}_chi",
        placeholder="Es: AI + Ufficio Acquisti (verifica finale)"
    )
    col1, col2 = st.columns(2)
    with col1:
        strumenti = voice_text_input(
            "Strumenti / Tecnologie AI", f"{prefix}_str",
            placeholder="Es: Copilot, RPA, LLM personalizzato"
        )
    with col2:
        tempo_str = voice_text_input(
            "Tempo previsto (minuti)", f"{prefix}_tempo",
            placeholder="Es: 10"
        )
    benefici = voice_text_area(
        "Benefici attesi", f"{prefix}_ben",
        placeholder="Es: -80% tempo raccolta, meno errori, notifiche automatiche",
        height=85,
    )
    rischi = voice_text_input(
        "Rischi / ostacoli", f"{prefix}_risk",
        placeholder="Es: Integrazione con SAP, resistenza al cambiamento"
    )

    def _get_tempo(s):
        try:
            return int(s.strip())
        except Exception:
            return None

    st.markdown("")
    col_add, col_done = st.columns([1, 1])

    with col_add:
        if st.button(f"+ Aggiungi Step {step_num}", use_container_width=True, type="primary"):
            if not attivita.strip() or not chi.strip():
                st.error("Attività e chi la svolge sono obbligatori.")
            else:
                st.session_state.tobe_steps.append({
                    "step": step_num,
                    "attivita": attivita.strip(),
                    "chi": chi.strip(),
                    "strumenti": strumenti.strip(),
                    "tempo": _get_tempo(tempo_str),
                    "benefici": benefici.strip(),
                    "rischi": rischi.strip(),
                })
                for suffix in ["att", "chi", "str", "tempo", "ben", "risk"]:
                    for pk in [f"input_tobe_{step_num}_{suffix}",
                                f"__show_mic_tobe_{step_num}_{suffix}"]:
                        st.session_state.pop(pk, None)
                st.rerun()

    with col_done:
        if n > 0:
            if st.button("✓ Concludi TO-BE", use_container_width=True):
                st.session_state.tobe_done = True
                st.rerun()
        else:
            st.caption("Aggiungi almeno uno step per concludere.")

    if n > 0:
        st.markdown("")
        if st.button("🗑️ Rimuovi ultimo step", use_container_width=True):
            st.session_state.tobe_steps.pop()
            st.rerun()

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Indietro (AS-IS)", use_container_width=True):
            go_to(1)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 3 — Conversational AI agent
# ══════════════════════════════════════════════════════════════════════════════

def render_chat():
    pcfg = config.PHASES[3]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 3 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("## 💬 Approfondimento con l'agente AI")
    st.markdown(
        "L'agente ha analizzato le tue mappe e ti farà alcune domande "
        "per arricchire l'analisi finale. Rispondi liberamente — anche con il microfono."
    )

    api_key = st.session_state.api_key
    if not api_key:
        st.warning("⚠️ Inserisci la API Key in **Impostazioni** nella sidebar per attivare l'agente.")
        if st.button("← Torna alla TO-BE", use_container_width=True):
            go_to(2)
        return

    # Initialize with AI's first message
    if not st.session_state.chat_initialized:
        with st.spinner("L'agente sta analizzando le tue mappe…"):
            try:
                first_msg = generate_chat_init(
                    answers=st.session_state.answers,
                    asis_steps=st.session_state.asis_steps,
                    tobe_steps=st.session_state.tobe_steps,
                    api_key=api_key,
                )
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": first_msg}
                ]
                st.session_state.chat_initialized = True
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")
                return

    # Render conversation history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Check if conversation is over (AI closed it)
    last = st.session_state.chat_messages[-1] if st.session_state.chat_messages else {}
    n_user = sum(1 for m in st.session_state.chat_messages if m["role"] == "user")
    show_proceed = n_user >= 3

    # Voice input for chat
    st.markdown("")
    col_voice, _ = st.columns([1, 3])
    with col_voice:
        if st.button("🎤 Rispondi con il microfono", use_container_width=True):
            st.session_state["__show_mic_chat"] = True

    if st.session_state.get("__show_mic_chat"):
        audio = st.audio_input("🎙️ Parla ora, poi Trascrivi", key="audio_chat")
        col_ok, col_x = st.columns([2, 1])
        with col_x:
            if st.button("✕ Annulla", key="mic_cancel_chat"):
                st.session_state["__show_mic_chat"] = False
                st.rerun()
        if audio:
            with col_ok:
                if st.button("✓ Trascrivi e invia", key="mic_ok_chat", type="primary"):
                    with st.spinner("Trascrizione…"):
                        try:
                            from utils.voice import transcribe_audio
                            text = transcribe_audio(audio, api_key)
                            st.session_state["__chat_voice_text"] = text
                            st.session_state["__show_mic_chat"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore trascrizione: {e}")

    # Handle voice-transcribed text as a pending user message
    pending_voice = st.session_state.pop("__chat_voice_text", None)
    if pending_voice:
        _send_chat_message(pending_voice, api_key)
        st.rerun()

    # Text chat input
    user_input = st.chat_input("Scrivi la tua risposta…")
    if user_input:
        _send_chat_message(user_input, api_key)
        st.rerun()

    # Proceed button
    if show_proceed:
        st.markdown("---")
        col_btn, _ = st.columns([2, 1])
        with col_btn:
            if st.button(
                "Procedi all'Analisi Finale →",
                type="primary",
                use_container_width=True,
            ):
                go_to(4)

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Torna alla TO-BE", use_container_width=True):
            go_to(2)


def _send_chat_message(text: str, api_key: str):
    st.session_state.chat_messages.append({"role": "user", "content": text})
    with st.spinner("L'agente risponde…"):
        try:
            reply = generate_chat_response(
                answers=st.session_state.answers,
                asis_steps=st.session_state.asis_steps,
                tobe_steps=st.session_state.tobe_steps,
                chat_history=st.session_state.chat_messages,
                api_key=api_key,
            )
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": f"⚠️ Errore: {e}"}
            )


# ══════════════════════════════════════════════════════════════════════════════
# Phase 4 — Final analysis
# ══════════════════════════════════════════════════════════════════════════════

def render_final():
    pcfg = config.PHASES[4]
    st.markdown(
        f'<div class="phase-banner">{pcfg["icon"]} Fase 4 — {pcfg["name"]} · {pcfg["duration"]}</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.analysis_result:
        _render_generate()
    else:
        _render_results()


def _render_generate():
    api_key = st.session_state.api_key
    st.markdown("## 🤖 Genera l'Analisi Finale")
    st.markdown(
        """
L'AI produrrà un'analisi completa basata su tutto ciò che hai inserito:

- 📊 **Sostituzione vs Augmentation** — per ogni step
- 🌅 **Scenario narrativo** — come cambierà la tua giornata
- ⚠️ **Analisi dei rischi** — con strategie di mitigazione
- 📅 **Roadmap** — piano concreto in 3 fasi
- 🤝 **Domanda aperta** — per il tuo team
        """
    )

    # Quick summary
    n_asis = len(st.session_state.asis_steps)
    n_tobe = len(st.session_state.tobe_steps)
    n_chat = sum(1 for m in st.session_state.chat_messages if m["role"] == "user")
    col1, col2, col3 = st.columns(3)
    col1.metric("Step AS-IS", n_asis)
    col2.metric("Step TO-BE", n_tobe)
    col3.metric("Scambi conversazione", n_chat)

    if not api_key:
        st.warning("⚠️ Inserisci la API Key in **Impostazioni** nella sidebar.")

    st.markdown("")
    col_gen, col_back = st.columns([2, 1])
    with col_gen:
        if st.button(
            "🤖 Genera Analisi Finale",
            type="primary",
            use_container_width=True,
            disabled=not api_key,
        ):
            with st.spinner("L'AI sta elaborando l'analisi completa… ⏳"):
                try:
                    result = generate_final_analysis(
                        answers=st.session_state.answers,
                        asis_steps=st.session_state.asis_steps,
                        tobe_steps=st.session_state.tobe_steps,
                        chat_history=st.session_state.chat_messages,
                        api_key=api_key,
                    )
                    st.session_state.analysis_result = result
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
    with col_back:
        if st.button("← Torna alla conversazione", use_container_width=True):
            go_to(3)


def _render_results():
    st.markdown("## 🎯 Analisi AI — Scenario TO-BE")
    st.markdown(st.session_state.analysis_result)

    st.markdown("---")

    # Generate HTML report for download
    html = generate_html_report(
        answers=st.session_state.answers,
        asis_steps=st.session_state.asis_steps,
        tobe_steps=st.session_state.tobe_steps,
        analysis_text=st.session_state.analysis_result,
        conversation=st.session_state.chat_messages,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📄 Scarica Report (apri → Ctrl+P → PDF)",
            data=html,
            file_name=f"workshop_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
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
                "Workshop completato! Ottimo lavoro! 🎉\n\n"
                "Scarica il report e aprilo nel browser → **Ctrl+P → Salva come PDF**."
            )


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════
phase = st.session_state.current_phase

if phase == 0:
    render_welcome()
elif phase == 1:
    render_asis()
elif phase == 2:
    render_tobe()
elif phase == 3:
    render_chat()
elif phase == 4:
    render_final()
