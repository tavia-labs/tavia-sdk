"""Render a sentence to a WAV file.  Usage: TAVIA_API_KEY=... python text_to_speech.py "Your table is ready." """

import asyncio
import os
import sys
from pathlib import Path

from tavia import Tavia


async def main(text: str) -> None:
    async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
        speech = await tavia.tts.render("elaine", text, "en")
        Path("speech.wav").write_bytes(speech.wav)
        print(f"wrote speech.wav ({speech.audio_s:.1f} s)")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "Your appointment is at ten tomorrow."))
