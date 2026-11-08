"""The call loop: caller audio -> endpointing -> STT -> agent -> sentence TTS -> playback,
with barge-in. Providers are injected, so the loop is testable without audio models."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Protocol

import numpy as np
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack

from .audio import Downsampler, Endpointer, PlaybackTrack, SpeechHeld, Utterance
from .speech import sentences, split_hangup

OOPS = "Sorry, something went wrong. Please say that again."


class Speech(Protocol):
    async def transcribe(self, pcm: np.ndarray) -> str: ...
    async def synthesize(self, text: str) -> np.ndarray: ...


class Turn:
    """What was said in the current reply and how much of it has been queued as audio."""

    def __init__(self, parts: list[str], start: int) -> None:
        self.parts, self.start = parts, start
        self.samples: list[int] = []  # audio length per synthesized part, in order

    def heard_fraction(self, played: int) -> float:
        remaining, heard = played - self.start, 0.0
        for text, length in zip(self.parts, self.samples, strict=False):
            heard += len(text) * min(1.0, max(0.0, remaining / max(length, 1)))
            remaining -= length
        return heard / max(sum(len(p) for p in self.parts), 1)


class Conversation:
    def __init__(
        self,
        speech: Speech,
        respond: Callable[[str], Awaitable[str]],
        on_hangup: Callable[[], Awaitable[None]],
    ) -> None:
        self.speech, self.respond, self.on_hangup = speech, respond, on_hangup
        self.playback = PlaybackTrack()
        self._task: asyncio.Task[None] | None = None  # the running turn
        self._listener: asyncio.Task[None] | None = None
        self._turn: Turn | None = None
        self._note = ""

    def attach(self, incoming: MediaStreamTrack) -> MediaStreamTrack:
        """CallMedia hook: start listening to the caller, return the track we speak on."""
        self._listener = asyncio.create_task(self._listen(incoming))
        return self.playback

    async def say(self, text: str) -> None:
        """Speak without a turn (greeting, outgoing-call opening)."""
        await self._speak(Turn(sentences(text), self.playback.played))

    def stop(self) -> None:
        for task in (self._listener, self._task):
            if task:
                task.cancel()

    async def _listen(self, track: MediaStreamTrack) -> None:
        down, endpointer = Downsampler(), Endpointer()
        try:
            while True:
                for event in endpointer.feed(down.feed(await track.recv())):  # type: ignore[arg-type]
                    if isinstance(event, SpeechHeld):
                        self._barge_in()
                    elif isinstance(event, Utterance):
                        self._start_turn(event.pcm)
        except MediaStreamError:
            return

    def _barge_in(self) -> None:
        """Caller spoke over us: stop audio, drop pending synthesis, remember what was heard."""
        if not (self.playback.busy or (self._task and not self._task.done())):
            return
        if self._turn and self.playback.busy:
            percent = round(self._turn.heard_fraction(self.playback.played) * 10) * 10
            self._note = (
                f"[The caller interrupted; they heard about {percent}% of your last reply.] "
            )
        self.playback.flush()
        if self._task:
            self._task.cancel()

    def _start_turn(self, pcm: np.ndarray) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = asyncio.create_task(self._run_turn(pcm))

    async def _run_turn(self, pcm: np.ndarray) -> None:
        try:
            text = await self.speech.transcribe(pcm)
            if not text:
                return
            logging.info("caller: %s", text)
            reply, hangup = split_hangup(await self.respond(self._note + text))
            self._note = ""
            logging.info("agent: %s", reply)
            await self._speak(Turn(sentences(reply), self.playback.played))
            await self.playback.wait_idle()
            if hangup:
                await self.on_hangup()
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("turn failed")
            await self._apologize()

    async def _speak(self, turn: Turn) -> None:
        self._turn = turn
        for part in turn.parts:
            audio = await self.speech.synthesize(part)
            turn.samples.append(len(audio))
            self.playback.play(audio)

    async def _apologize(self) -> None:
        try:
            self.playback.play(await self.speech.synthesize(OOPS))
        except Exception:
            logging.exception("TTS also failed; staying silent")
