import base64
import anthropic
import config


def transcribe_audio(audio_file, api_key: str) -> str:
    """Transcribe audio using Claude's audio input capability."""
    client = anthropic.Anthropic(api_key=api_key)
    audio_data = base64.standard_b64encode(audio_file.getvalue()).decode("utf-8")

    message = client.messages.create(
        model=config.DEFAULT_MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Trascrivi esattamente questo audio in italiano. "
                            "Rispondi SOLO con la trascrizione letterale, nessun commento aggiuntivo."
                        ),
                    },
                    {
                        "type": "audio",
                        "source": {
                            "type": "base64",
                            "media_type": "audio/webm",
                            "data": audio_data,
                        },
                    },
                ],
            }
        ],
    )
    return message.content[0].text.strip()
