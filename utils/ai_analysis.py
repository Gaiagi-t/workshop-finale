import anthropic
import config


# ── Helpers ───────────────────────────────────────────────────────────────────

def _steps_to_text(steps: list, is_tobe: bool = False) -> str:
    if not steps:
        return "(nessuno step inserito)"
    lines = []
    for s in steps:
        if is_tobe:
            lines.append(
                f"  Step {s.get('step','?')}: {s.get('attivita','—')} | "
                f"Chi: {s.get('chi','—')} | Strumenti/AI: {s.get('strumenti','—')} | "
                f"Tempo previsto: {s.get('tempo','—')} min | "
                f"Benefici: {s.get('benefici','—')} | Rischi: {s.get('rischi','—')}"
            )
        else:
            lines.append(
                f"  Step {s.get('step','?')}: {s.get('attivita','—')} | "
                f"Chi: {s.get('chi','—')} | Strumenti: {s.get('strumenti','—')} | "
                f"Tempo: {s.get('tempo','—')} min | Problemi: {s.get('problemi','—')}"
            )
    return "\n".join(lines)


def _profile_text(answers: dict) -> str:
    nome = answers.get("q0_nome", "N/D")
    ruolo = answers.get("q0_ruolo", "")
    org = answers.get("q0_org", "")
    processo = answers.get("q0_processo", "N/D")
    descrizione = answers.get("q0_descrizione", "")
    return (
        f"Nome/Ruolo: {nome}{' — ' + ruolo if ruolo else ''}\n"
        f"Organizzazione: {org or 'Non specificata'}\n"
        f"Processo: {processo}\n"
        f"Descrizione: {descrizione or 'Non specificata'}"
    )


def _time_stats(asis_steps: list, tobe_steps: list) -> str:
    try:
        asis_time = sum(int(s.get("tempo") or 0) for s in asis_steps)
        tobe_time = sum(int(s.get("tempo") or 0) for s in tobe_steps)
        delta = asis_time - tobe_time
        pct = round(delta / asis_time * 100, 1) if asis_time > 0 else 0
        return (
            f"Tempo totale AS-IS: {asis_time} min | "
            f"Tempo totale TO-BE: {tobe_time} min | "
            f"Risparmio atteso: {delta} min ({pct}%)"
        )
    except Exception:
        return ""


# ── Chat: initialize conversation ─────────────────────────────────────────────

def generate_chat_init(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    processo = answers.get("q0_processo", "il processo")

    prompt = f"""Sei un facilitatore esperto di trasformazione digitale con AI. \
Stai conducendo un workshop dove un partecipante ha appena mappato il processo \
"{processo}" in versione AS-IS e TO-BE.

PROFILO
{_profile_text(answers)}

MAPPA AS-IS
{_steps_to_text(asis_steps, is_tobe=False)}

MAPPA TO-BE
{_steps_to_text(tobe_steps, is_tobe=True)}

{_time_stats(asis_steps, tobe_steps)}

Il tuo compito: condurre una breve conversazione di approfondimento (4-6 domande totali, \
UNA ALLA VOLTA) per raccogliere informazioni che arricchiranno l'analisi finale. \
Focalizzati su aspetti che emergono dalle mappe ma che richiedono chiarimento: \
vincoli organizzativi, competenze disponibili, priorità di implementazione, \
aspettative di business, o rischi specifici non menzionati.

Inizia con UN messaggio di benvenuto caldo (2 righe max) che riconosce il lavoro fatto, \
poi fai SUBITO la prima domanda. Sii diretto e concreto. \
Non usare elenchi puntati nel tuo primo messaggio."""

    msg = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


# ── Chat: continue conversation ───────────────────────────────────────────────

def generate_chat_response(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    chat_history: list,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    processo = answers.get("q0_processo", "il processo")

    n_exchanges = sum(1 for m in chat_history if m["role"] == "user")

    if n_exchanges >= 5:
        closing_hint = (
            "Hai raccolto abbastanza informazioni. "
            "Concludi la conversazione con un breve riassunto (3-4 punti) "
            "delle informazioni chiave emerse e invita il partecipante a "
            "procedere con l'analisi finale con un messaggio entusiasta."
        )
    else:
        closing_hint = (
            f"Hai posto {n_exchanges} domanda/e finora. "
            "Fai UNA sola domanda di follow-up mirata, basata sulla risposta appena ricevuta. "
            "Massimo 3 righe."
        )

    system = f"""Sei un facilitatore esperto di trasformazione digitale con AI. \
Stai approfondendo il processo "{processo}" con questo partecipante.

PROFILO
{_profile_text(answers)}

MAPPA AS-IS
{_steps_to_text(asis_steps, is_tobe=False)}

MAPPA TO-BE
{_steps_to_text(tobe_steps, is_tobe=True)}

{_time_stats(asis_steps, tobe_steps)}

{closing_hint}
Rispondi sempre in italiano, tono professionale ma caldo."""

    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in chat_history
    ]

    msg = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=400,
        system=system,
        messages=messages,
    )
    return msg.content[0].text.strip()


# ── Final analysis ────────────────────────────────────────────────────────────

def build_final_prompt(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    chat_history: list,
) -> str:
    conversation_summary = ""
    if chat_history:
        lines = []
        for m in chat_history:
            role = "AI" if m["role"] == "assistant" else "Partecipante"
            lines.append(f"{role}: {m['content']}")
        conversation_summary = (
            "\nINFORMAZIONI AGGIUNTIVE (dalla conversazione di approfondimento)\n"
            + "\n".join(lines)
        )

    return f"""Sei un esperto di trasformazione digitale con AI per aziende e organizzazioni. \
Genera un'analisi finale strutturata e concreta in italiano, basandoti su tutti i dati raccolti.

---
PROFILO PARTECIPANTE
{_profile_text(answers)}

MAPPA AS-IS
{_steps_to_text(asis_steps, is_tobe=False)}

MAPPA TO-BE
{_steps_to_text(tobe_steps, is_tobe=True)}

{_time_stats(asis_steps, tobe_steps)}
{conversation_summary}
---

Genera l'analisi strutturata esattamente in queste 5 sezioni:

## 📊 1. Integrazione AI per step: Sostituzione vs Augmentation

Crea questa tabella per ogni step TO-BE:

| Step # | Attività | Tipo integrazione | Come interviene l'AI | Beneficio concreto |
|--------|----------|-------------------|----------------------|--------------------|

Tipo integrazione: **Sostituzione** (task autonomo), **Augmentation** (AI affianca l'umano), **Umano** (nessuna AI).
Dopo la tabella: 2-3 righe di sintesi sull'impatto complessivo.

## 🌅 2. Scenario TO-BE: un giorno con l'AI

3-4 paragrafi vividi in seconda persona ("Con il nuovo processo..."). \
Confronta esplicitamente prima/dopo per i momenti chiave. Sii specifico al contesto.

## ⚠️ 3. Rischi e mitigazioni

| Rischio | Tipo | Probabilità | Impatto | Strategia di mitigazione |
|---------|------|-------------|---------|--------------------------|

Tipo: Tecnico, Organizzativo, Etico/Privacy, Operativo.
Paragrafo finale sul rischio prioritario.

## 📅 4. Roadmap di implementazione

- **Fase 1 — Settimane 1-2**: pilota interno
- **Fase 2 — Mese 1-2**: uso reale, feedback, revisione
- **Fase 3 — Trimestre 1**: consolidamento ed estensione

Per ogni fase: 3-4 azioni concrete + 1-2 KPI misurabili.

## 🤝 5. Domanda aperta per il team

Una domanda potente e specifica su confine umano-AI o implicazioni organizzative \
per questo specifico processo. Deve stimolare discussione nel team.

---
Stile: professionale ma accessibile, concreto, diretto. Ogni sezione immediatamente azionabile."""


def generate_final_analysis(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    chat_history: list,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_final_prompt(answers, asis_steps, tobe_steps, chat_history)

    msg = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── TO-BE Tool Advisor ────────────────────────────────────────────────────────

_TRAINING_TOOLS = """
STRUMENTI AI TRATTATI NEL CORSO (da usare come riferimento primario nei suggerimenti):

ASSISTENTI GENERALI: ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google),
Microsoft Copilot, Perplexity — per generazione testi, analisi, sintesi, Q&A, ricerca.

AGENTI/GPT PERSONALIZZATI: ChatGPT Custom GPT, Claude Projects, Gemini Gems,
Copilot Studio — per creare assistenti specializzati con knowledge base aziendale.

CODING & SVILUPPO: GitHub Copilot, OpenAI Codex, Gemini 2.5, Qwen3 —
per generare, revisionare e automatizzare codice.

CREATIVITÀ — IMMAGINI & MOCKUP: DALL-E, Adobe Firefly, Canva AI, Recraft,
Bing Copilot, Image3 — per immagini, visual, mockup, asset grafici.

CREATIVITÀ — INFOGRAFICHE: Napkin.ai, Infografix, Piktochart —
per visualizzare dati, processi, report in modo visivo.

CREATIVITÀ — VIDEO & AVATAR: Runway, Lumen5, Lumalabs (video);
Heygen, Synthesia (avatar digitali) — per contenuti video professionali.

CREATIVITÀ — AUDIO & PRESENTAZIONI: ElevenLabs (voce/narrazione);
Loudly, Suno, Udio, Stable Audio (musica); SlidesAI, Tome, Gamma (presentazioni).

PROJECT MANAGEMENT: NotionAI, TrelloAI, Asana (Graph AI), ClickUp,
Monday.com, Wrike, Smartsheet AI — per pianificazione, task, Gantt, report.

AUTOMAZIONI: Zapier, Make/Integromat — per connettere app e automatizzare
workflow senza codice, con o senza LLM integrato.

DISTINZIONE FONDAMENTALE (insegnata nel corso):
• Automazioni: regole fisse predefinite, nessuna AI, esecuzione automatica
• Automazioni AI: regole + LLM, ancora vincolate a logica predefinita
• Agenti AI: autonomia decisionale, pianificano azioni in base agli obiettivi
• Sostituzione: AI esegue il task autonomamente (attività ripetitive/standardizzate)
• Augmentation: AI affianca e potenzia l'umano (analisi complessa, creatività, decisioni)
"""


def _advisor_system(answers: dict, asis_steps: list, tobe_steps: list) -> str:
    processo = answers.get("q0_processo", "il processo")
    org = answers.get("q0_org", "")
    nome = answers.get("q0_nome", "il partecipante")
    return (
        f"Sei un Tool Advisor esperto di strumenti AI per la trasformazione di processi "
        f"aziendali. Stai supportando {nome}{(' di ' + org) if org else ''} "
        f"nella mappatura TO-BE del processo \"{processo}\".\n\n"
        f"{_TRAINING_TOOLS}\n"
        f"MAPPA AS-IS\n{_steps_to_text(asis_steps, is_tobe=False)}\n\n"
        f"STEP TO-BE GIÀ DEFINITI\n"
        f"{_steps_to_text(tobe_steps, is_tobe=True) if tobe_steps else '(nessuno ancora)'}\n\n"
        "Rispondi in italiano. Sii concreto e diretto. "
        "Usa i nomi esatti dei tool del corso quando pertinenti. "
        "Massimo 5-6 righe per risposta."
    )


def generate_tobe_proactive_for_step(
    step_num: int,
    asis_step: dict,
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    api_key: str,
) -> str:
    """Generate a proactive suggestion for a specific AS-IS step."""
    client = anthropic.Anthropic(api_key=api_key)

    asis_desc = (
        f"Step {asis_step.get('step')}: {asis_step.get('attivita', '—')} | "
        f"Chi: {asis_step.get('chi', '—')} | "
        f"Strumenti attuali: {asis_step.get('strumenti') or 'non specificati'} | "
        f"Problemi: {asis_step.get('problemi') or 'non specificati'}"
    )

    prompt = (
        f"{_advisor_system(answers, asis_steps, tobe_steps)}\n\n"
        f"STEP ATTUALE DA TRASFORMARE:\n{asis_desc}\n\n"
        "Genera un messaggio PROATTIVO che:\n"
        "1. Analizza brevemente questo step specifico\n"
        "2. Suggerisce 2-3 strumenti AI concreti del corso più adatti\n"
        "3. Indica se è più indicata Sostituzione o Augmentation\n"
        "4. Termina con UNA domanda concreta per capire meglio il contesto\n"
        "Non iniziare con 'Ciao' o formule di cortesia. Vai dritto all'analisi."
    )

    msg = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=350,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def generate_tobe_assistant_response(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    chat_history: list,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    system = _advisor_system(answers, asis_steps, tobe_steps)
    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]

    msg = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=400,
        system=system,
        messages=messages,
    )
    return msg.content[0].text.strip()
