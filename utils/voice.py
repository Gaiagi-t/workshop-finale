import openai


def transcribe_audio(audio_file, api_key: str) -> str:
    client = openai.OpenAI(api_key=api_key)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("recording.webm", audio_file.getvalue()),
        language="it",
    )
    return transcript.text.strip()
