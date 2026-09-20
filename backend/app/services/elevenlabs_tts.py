import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.settings import settings


class ElevenLabsTTS:
    """Small dependency-free wrapper around the ElevenLabs text-to-speech API."""

    def synthesize(self, text: str) -> bytes:
        if not settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured")
        if not settings.elevenlabs_voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID is not configured")

        url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            f"{settings.elevenlabs_voice_id}?output_format={settings.elevenlabs_output_format}"
        )
        body = json.dumps(
            {
                "text": text,
                "model_id": settings.elevenlabs_model_id,
            }
        ).encode("utf-8")
        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
        )

        try:
            with urlopen(
                request, timeout=settings.elevenlabs_timeout_seconds
            ) as response:
                audio = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"ElevenLabs TTS request failed: {detail}") from exc
        except URLError as exc:
            raise RuntimeError("Could not reach ElevenLabs TTS service") from exc

        if not audio:
            raise RuntimeError("ElevenLabs returned empty audio")
        return audio


text_to_speech = ElevenLabsTTS()
