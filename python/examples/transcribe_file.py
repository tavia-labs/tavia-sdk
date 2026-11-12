"""Transcribe an audio file.  Usage: TAVIA_API_KEY=... python transcribe_file.py call.wav"""

import asyncio
import os
import sys

from tavia import Tavia


async def main(path: str) -> None:
    async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
        result = await tavia.stt.transcribe(path, terms=["Tavia"])
        print(result["text"])


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "call.wav"))
