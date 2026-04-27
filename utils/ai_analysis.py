import anthropic
import pandas as pd
import config


def _df_to_text(df: pd.DataFrame) -> str:
    if df.empty:
        return "(tabella vuota)"
    rows = []
    rows.append(" | ".join(str(c) for c in df.columns))
    rows.append("|".join("---" for _ in df.columns))
    for _, row in df.iterrows():
        values = []
        for v in row.values:
            s = str(v)
            if s in ("0", "", "nan", "None", "<NA>"):
                s = "—"
            values.append(s)
        rows.append(" | ".join(values))
    return "\n".join(rows)


def build_prompt(answers: dict, asis_df: pd.DataFrame, tobe_df: pd.DataFrame) -> str:
    nome = answers.get("q0_nome", "N/D")
    ruolo = answers.get("q0_ruolo", "")
    org = answers.get("q0_org", "")
    processo = answers.get("q0_processo", "N/D")
    descrizione = answers.get("q0_descrizione", "")

    asis_time = int(asis_df["Tempo (min)"].fillna(0).sum())
    tobe_time = int(tobe_df["Tempo previsto (min)"].fillna(0).sum())
    delta = asis_time - tobe_time
    pct = round(delta / asis_time * 100, 1) if asis_time > 0 else 0

    asis_filled = asis_df[asis_df["Attività"].fillna("").astype(str).str.strip() != ""]
    tobe_filled = tobe_df[tobe_df["Attività futura"].fillna("").astype(str).str.strip() != ""]

    asis_text = _df_to_text(asis_filled)
    tobe_text = _df_to_text(tobe_filled)

    nome_ruolo = nome + (" — " + ruolo if ruolo else "")

    return f"""Sei un esperto di trasformazione digitale con AI per aziende e organizzazioni. \
Un partecipante al workshop "AI nei Processi Aziendali" ha appena mappato il proprio processo \
AS-IS e immaginato lo scenario TO-BE con l'integrazione dell'AI. \
Analizza entrambe le mappe e genera un'analisi strutturata e concreta in italiano.

---
PROFILO PARTECIPANTE
Nome / Ruolo: {nome_ruolo}
Organizzazione: {org if org else 'Non specificata'}
Processo analizzato: {processo}
Descrizione: {descrizione if descrizione else 'Non specificata'}

MAPPA AS-IS (processo attuale)
{asis_text}
Tempo totale AS-IS: {asis_time} minuti

MAPPA TO-BE (scenario futuro con AI)
{tobe_text}
Tempo totale TO-BE: {tobe_time} minuti
Risparmio atteso: {delta} minuti ({pct}%)
---

Genera l'analisi strutturata esattamente in queste 5 sezioni, con i titoli indicati:

## 📊 1. Integrazione AI per step: Sostituzione vs Augmentation

Per ogni step del processo TO-BE, crea questa tabella:

| Step # | Attività | Tipo integrazione | Come interviene l'AI | Beneficio concreto |
|--------|----------|-------------------|----------------------|--------------------|

Dove "Tipo integrazione" è uno tra:
- **Sostituzione**: l'AI esegue il task autonomamente (attività ripetitive, standardizzate)
- **Augmentation**: l'AI affianca l'umano (analisi complesse, decisioni, creatività)
- **Umano**: nessuna AI, rimane responsabilità esclusivamente umana

Dopo la tabella, aggiungi 2-3 righe di sintesi: quanti step vengono sostituiti, augmentati, \
rimangono umani, e qual è l'impatto complessivo sul carico di lavoro.

## 🌅 2. Scenario TO-BE: un giorno con l'AI

Racconta in 3-4 paragrafi vividi e concreti come cambia la giornata lavorativa del partecipante \
con questo processo AI-integrato attivo. Usa la seconda persona ("Con il nuovo processo..."). \
Sii specifico al contesto, non generico. Descrivi momenti concreti: come inizia il lavoro, \
come vengono gestiti gli input, quali output si producono, quanto tempo si risparmia. \
Confronta esplicitamente prima e dopo per i momenti chiave.

## ⚠️ 3. Rischi e mitigazioni

Identifica i 3-5 rischi principali in questa tabella:

| Rischio | Tipo | Probabilità | Impatto | Strategia di mitigazione |
|---------|------|-------------|---------|--------------------------|

Dove "Tipo" è uno tra: Tecnico, Organizzativo, Etico/Privacy, Operativo.

Poi aggiungi un breve paragrafo su quale rischio monitorare con priorità e perché.

## 📅 4. Roadmap di implementazione

Piano pratico in 3 fasi:
- **Fase 1 — Settimane 1-2**: pilota interno, test con casi reali
- **Fase 2 — Mese 1-2**: primo ciclo di uso reale, raccolta feedback e revisione
- **Fase 3 — Trimestre 1**: consolidamento ed eventuale estensione al team

Per ogni fase: 3-4 azioni concrete + 1-2 KPI misurabili.

## 🤝 5. Domanda aperta per il team

Concludi con una singola domanda aperta, potente e specifica per questo processo, \
che il partecipante dovrebbe portare alla prossima riunione del suo team. \
La domanda deve toccare il confine umano-AI o un'implicazione organizzativa rilevante \
per questo specifico contesto.

---
Stile: professionale ma accessibile, concreto, diretto. Evita il gergo tecnico eccessivo. \
Ogni sezione deve essere immediatamente utile e azionabile."""


def generate_tobe_analysis(
    answers: dict,
    asis_df: pd.DataFrame,
    tobe_df: pd.DataFrame,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(answers, asis_df, tobe_df)

    message = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
