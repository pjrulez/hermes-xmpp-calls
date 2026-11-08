"""The call loop with fake STT/TTS/agent and a scripted caller track."""

import asyncio
import fractions

import av
import numpy as np
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack

from xmpp_calls.audio import OUT_FRAME, OUT_RATE
from xmpp_calls.conversation import Conversation, Turn


def frame(pcm: np.ndarray, n: int) -> av.AudioFrame:
    f = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
    f.sample_rate, f.pts, f.time_base = OUT_RATE, n * OUT_FRAME, fractions.Fraction(1, OUT_RATE)
    return f


class Caller(MediaStreamTrack):
    """Plays a script of ("talk" | "quiet", ms) then ends the stream."""

    kind = "audio"

    def __init__(self, script: list[tuple[str, int]], stall: bool = False) -> None:
        super().__init__()
        self.stall = stall  # after the script, send nothing (a muted client) instead of ending
        self.frames = []
        for kind, ms in script:
            for _ in range(ms // 20):
                n = len(self.frames)
                t = np.arange(OUT_FRAME) + n * OUT_FRAME
                amp = 6000 if kind == "talk" else 10
                self.frames.append(frame((np.sin(t / 20) * amp).astype(np.int16), n))
        self.i = 0

    async def recv(self) -> av.AudioFrame:
        await asyncio.sleep(0)  # let the turn task run between frames
        if self.i >= len(self.frames):
            if self.stall:
                await asyncio.Event().wait()
            raise MediaStreamError
        self.i += 1
        return self.frames[self.i - 1]


class FakeSpeech:
    def __init__(self, transcript: str = "hello there") -> None:
        self.transcript, self.spoken = transcript, []

    async def transcribe(self, pcm: np.ndarray) -> str:
        return self.transcript

    async def synthesize(self, text: str) -> np.ndarray:
        self.spoken.append(text)
        return np.ones(OUT_RATE, np.int16)  # one second per sentence


async def settle(convo: Conversation) -> None:
    """Caller finished; give the turn time to queue audio. It then waits for playback to drain,
    which only happens when something calls playback.recv(), so do not await it to the end."""
    await convo._listener  # type: ignore[misc]
    if convo._task:
        await asyncio.wait({convo._task}, timeout=0.3)


async def test_turn_is_transcribed_answered_and_spoken() -> None:
    speech, replies = FakeSpeech(), []

    async def respond(text: str) -> str:
        replies.append(text)
        return "I am fine, thank you for asking. How are you doing today, my friend?"

    async def hangup() -> None: ...

    convo = Conversation(speech, respond, hangup)
    convo.attach(Caller([("quiet", 200), ("talk", 1000), ("quiet", 1000)]))
    await settle(convo)
    assert replies == ["hello there"]
    assert len(speech.spoken) == 2
    assert convo.playback.busy


async def test_empty_transcript_makes_no_turn() -> None:
    called = []

    async def respond(text: str) -> str:
        called.append(text)
        return "x"

    async def hangup() -> None: ...

    convo = Conversation(FakeSpeech(""), respond, hangup)
    convo.attach(Caller([("talk", 1000), ("quiet", 1000)]))
    await settle(convo)
    assert called == []


async def test_hangup_marker_is_not_spoken_and_ends_call() -> None:
    speech, ended = FakeSpeech(), []

    async def respond(text: str) -> str:
        return "Goodbye, talk to you later. [[hangup]]"

    async def hangup() -> None:
        ended.append(True)

    convo = Conversation(speech, respond, hangup)
    convo.attach(Caller([("talk", 1000), ("quiet", 1000)]))
    await settle(convo)
    convo.playback.flush()  # as if playback finished
    await asyncio.wait({convo._task}, timeout=1)  # type: ignore[arg-type]
    assert ended == [True]
    assert all("hangup" not in s for s in speech.spoken)


async def test_barge_in_flushes_audio_and_notes_heard_fraction() -> None:
    speech, seen = FakeSpeech(), []

    async def respond(text: str) -> str:
        seen.append(text)
        return "This is a rather long answer that goes on. And here is a second long sentence."

    async def hangup() -> None: ...

    convo = Conversation(speech, respond, hangup)
    convo.attach(Caller([("talk", 1000), ("quiet", 1000)]))
    await settle(convo)
    assert convo.playback.busy
    for _ in range(50):  # 1 s of 2 s played
        await convo.playback.recv()
    convo._barge_in()
    assert not convo.playback.busy
    assert "interrupted" in convo._note
    assert "50%" in convo._note


def test_heard_fraction_math() -> None:
    turn = Turn(["aaaa", "bbbb"], start=100)
    turn.samples = [1000, 1000]
    assert turn.heard_fraction(100) == 0
    assert turn.heard_fraction(600) == 0.25
    assert turn.heard_fraction(2100) == 1


async def test_muted_client_still_ends_the_utterance() -> None:
    """Dino sends no RTP while muted; silence must come from the clock."""
    replies = []

    async def respond(text: str) -> str:
        replies.append(text)
        return "Okay then, I heard you just fine."

    async def hangup() -> None: ...

    convo = Conversation(FakeSpeech(), respond, hangup)
    convo.attach(Caller([("talk", 1000)], stall=True))
    await asyncio.sleep(1.8)
    convo.stop()
    assert replies == ["hello there"]


async def test_slow_agent_gets_a_filler() -> None:
    speech = FakeSpeech()

    async def respond(text: str) -> str:
        await asyncio.sleep(0.15)
        return "The answer is long enough to be one sentence."

    async def hangup() -> None: ...

    convo = Conversation(speech, respond, hangup, filler_after=0.05)
    convo.attach(Caller([("talk", 1000), ("quiet", 1000)]))
    await settle(convo)
    assert speech.spoken[0] == "One moment."
    assert speech.spoken[1].startswith("The answer")
