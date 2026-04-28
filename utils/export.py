from datetime import datetime
import re
import markdown as md_lib


def _md_to_html(text: str) -> str:
    return md_lib.markdown(
        text,
        extensions=["tables", "nl2br", "fenced_code"],
    )


def generate_html_report(
    answers: dict,
    asis_steps: list,
    tobe_steps: list,
    analysis_text: str,
    conversation: list = None,
) -> str:
    nome = answers.get("q0_nome", "")
    ruolo = answers.get("q0_ruolo", "")
    org = answers.get("q0_org", "")
    processo = answers.get("q0_processo", "Processo analizzato")
    date_str = datetime.now().strftime("%d/%m/%Y")

    # Build AS-IS table rows
    asis_rows = ""
    for s in asis_steps:
        asis_rows += (
            f"<tr>"
            f"<td>{s.get('step', '')}</td>"
            f"<td>{s.get('attivita', '')}</td>"
            f"<td>{s.get('chi', '')}</td>"
            f"<td>{s.get('strumenti', '')}</td>"
            f"<td>{s.get('tempo', '')}</td>"
            f"<td>{s.get('problemi', '')}</td>"
            f"</tr>"
        )

    # Build TO-BE table rows
    tobe_rows = ""
    for s in tobe_steps:
        tobe_rows += (
            f"<tr>"
            f"<td>{s.get('step', '')}</td>"
            f"<td>{s.get('attivita', '')}</td>"
            f"<td>{s.get('chi', '')}</td>"
            f"<td>{s.get('strumenti', '')}</td>"
            f"<td>{s.get('tempo', '')}</td>"
            f"<td>{s.get('benefici', '')}</td>"
            f"<td>{s.get('rischi', '')}</td>"
            f"</tr>"
        )

    analysis_html = _md_to_html(analysis_text)

    conv_html = ""
    if conversation:
        msgs = ""
        for msg in conversation:
            role = "AI" if msg["role"] == "assistant" else "Partecipante"
            cls = "ai-msg" if msg["role"] == "assistant" else "user-msg"
            msgs += f'<div class="{cls}"><strong>{role}:</strong> {msg["content"]}</div>'
        conv_html = f"""
        <div class="section">
            <h2>💬 Approfondimento conversazionale</h2>
            <div class="conversation">{msgs}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analisi TO-BE — {processo}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    color: #1a2b3c;
    background: #fff;
    padding: 0;
  }}
  .cover {{
    background: linear-gradient(135deg, #0d2137 0%, #1b98e0 100%);
    color: white;
    padding: 60px 50px 40px;
    margin-bottom: 40px;
  }}
  .cover .label {{
    font-size: 9pt;
    opacity: 0.75;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
  }}
  .cover h1 {{ font-size: 26pt; font-weight: 700; margin-bottom: 8px; }}
  .cover h2 {{ font-size: 16pt; font-weight: 400; opacity: 0.9; margin-bottom: 24px; }}
  .cover .meta {{ font-size: 10pt; opacity: 0.8; line-height: 1.8; }}
  .content {{ padding: 0 50px 50px; }}
  .section {{ margin-bottom: 36px; page-break-inside: avoid; }}
  h2 {{
    font-size: 14pt;
    color: #0d2137;
    border-bottom: 2px solid #1b98e0;
    padding-bottom: 6px;
    margin-bottom: 16px;
    margin-top: 28px;
  }}
  h3 {{ font-size: 11pt; color: #1b98e0; margin: 14px 0 6px; }}
  p {{ margin-bottom: 10px; line-height: 1.6; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 20px;
    font-size: 9.5pt;
  }}
  th {{
    background: #0d2137;
    color: white;
    padding: 7px 10px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 6px 10px;
    border-bottom: 1px solid #dee2e6;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f4f8fc; }}
  ul, ol {{ margin: 8px 0 12px 20px; line-height: 1.7; }}
  li {{ margin-bottom: 4px; }}
  code {{
    background: #f4f8fc;
    border: 1px solid #dee2e6;
    border-radius: 3px;
    padding: 2px 5px;
    font-size: 9pt;
  }}
  pre {{
    background: #f4f8fc;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 14px;
    overflow-x: auto;
    font-size: 9pt;
    margin: 10px 0;
  }}
  blockquote {{
    border-left: 3px solid #1b98e0;
    padding-left: 12px;
    color: #6c757d;
    margin: 10px 0;
  }}
  .ai-msg {{
    background: #f4f8fc;
    border-left: 3px solid #1b98e0;
    padding: 8px 12px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
  }}
  .user-msg {{
    background: #fff;
    border: 1px solid #dee2e6;
    padding: 8px 12px;
    margin: 6px 0;
    border-radius: 6px;
  }}
  .conversation {{ margin: 12px 0; }}
  .print-btn {{
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #1b98e0;
    color: white;
    border: none;
    padding: 12px 22px;
    border-radius: 8px;
    font-size: 11pt;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    z-index: 999;
  }}
  .print-btn:hover {{ background: #0d2137; }}
  @media print {{
    .print-btn {{ display: none; }}
    body {{ padding: 0; }}
    .cover {{ padding: 40px 30px 30px; margin-bottom: 30px; }}
    .content {{ padding: 0 30px 30px; }}
    h2 {{ page-break-after: avoid; }}
  }}
</style>
</head>
<body>

<button class="print-btn" onclick="window.print()">🖨️ Salva come PDF</button>

<div class="cover">
  <div class="label">Fondazione IFAB · Workshop Finale</div>
  <h1>AI nei Processi Aziendali</h1>
  <h2>{processo}</h2>
  <div class="meta">
    Partecipante: <strong>{nome}{' — ' + ruolo if ruolo else ''}</strong><br>
    Organizzazione: <strong>{org if org else '—'}</strong><br>
    Data: {date_str}
  </div>
</div>

<div class="content">

  <div class="section">
    <h2>🔍 Mappa AS-IS — Processo attuale</h2>
    <table>
      <thead>
        <tr>
          <th>Step</th><th>Attività</th><th>Chi la svolge</th>
          <th>Strumenti</th><th>Tempo (min)</th><th>Problemi</th>
        </tr>
      </thead>
      <tbody>{asis_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>🚀 Mappa TO-BE — Scenario con AI</h2>
    <table>
      <thead>
        <tr>
          <th>Step</th><th>Attività futura</th><th>Chi la svolge</th>
          <th>Strumenti / AI</th><th>Tempo prev. (min)</th>
          <th>Benefici</th><th>Rischi</th>
        </tr>
      </thead>
      <tbody>{tobe_rows}</tbody>
    </table>
  </div>

  {conv_html}

  <div class="section">
    <h2>🤖 Analisi AI — Scenario TO-BE</h2>
    {analysis_html}
  </div>

</div>
</body>
</html>"""
