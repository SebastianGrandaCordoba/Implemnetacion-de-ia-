import io
import unittest
import wave
from types import SimpleNamespace
from unittest import mock

from app import main
from app.config import get_settings
from app.domain.speech import MAX_SPEECH_CHARS, TTS_FALLBACK_MODEL, build_speech_prompt, clean_speech_text, pcm_to_wav
from app.gemini_service import GeminiGenerationError, synthesize_speech
from tests.api_support import FakeUseCase, client_with, close


def audio_client(failing: set[str]):
    calls: list[str] = []

    def generate_content(model, **kwargs):
        calls.append(model)
        if model in failing:
            raise RuntimeError("503 UNAVAILABLE")
        part = SimpleNamespace(inline_data=SimpleNamespace(data=b"\x00\x01" * 2400))
        return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])

    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)), calls


class SpeechDomainTests(unittest.TestCase):
    def test_text_is_read_the_way_people_speak(self) -> None:
        spoken = clean_speech_text("Promedio 3,4 → refuerzo • **ya**")
        self.assertIn("3 coma 4", spoken)
        self.assertFalse(any(symbol in spoken for symbol in "→•*"))
        long = "Frase corta. " * 300
        self.assertLessEqual(len(clean_speech_text(long)), MAX_SPEECH_CHARS)
        self.assertTrue(clean_speech_text(long).endswith("."))

    def test_prompt_asks_for_a_warm_neutral_latin_voice_and_keeps_the_text(self) -> None:
        prompt = build_speech_prompt("Hola, profe.")
        self.assertIn("español latinoamericano neutro", prompt)
        self.assertTrue(prompt.endswith("Hola, profe."))

    def test_wav_header_says_24_khz_mono_16_bit(self) -> None:
        with wave.open(io.BytesIO(pcm_to_wav(b"\x00\x00" * 24000))) as wav:
            shape = (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes())
        self.assertEqual(shape, (24000, 1, 2, 24000))


class SpeechModelTests(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "k"}, clear=True):
            self.settings = get_settings()

    def test_the_current_model_speaks_first(self) -> None:
        client, calls = audio_client(set())
        self.assertTrue(synthesize_speech(self.settings, "Hola", client).startswith(b"RIFF"))
        self.assertEqual(calls, [self.settings.gemini_tts_model])

    def test_the_older_model_takes_over_and_both_failing_is_an_error(self) -> None:
        client, calls = audio_client({self.settings.gemini_tts_model})
        synthesize_speech(self.settings, "Hola", client)
        self.assertEqual(calls, [self.settings.gemini_tts_model, TTS_FALLBACK_MODEL])
        broken, _ = audio_client({self.settings.gemini_tts_model, TTS_FALLBACK_MODEL})
        with self.assertRaises(GeminiGenerationError):
            synthesize_speech(self.settings, "Hola", broken)


class SpeakEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = client_with(FakeUseCase())
        self.calls: list[str] = []
        main._speech_cache.clear()

        def fake(text: str) -> bytes:
            self.calls.append(text)
            return pcm_to_wav(b"\x00\x00" * 10)

        main.app.dependency_overrides[main.get_speaker] = lambda: fake

    def tearDown(self) -> None:
        close(self.client)
        main._speech_cache.clear()

    def test_returns_wav_and_reuses_the_same_text(self) -> None:
        headers = {"X-AI-Service-Token": "test-token"}
        for _ in range(2):
            response = self.client.post("/speak", json={"text": "Hola, profe."}, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["content-type"], "audio/wav")
        self.assertEqual(len(self.calls), 1)

    def test_requires_the_backend_token(self) -> None:
        self.assertEqual(self.client.post("/speak", json={"text": "Hola"}).status_code, 401)
