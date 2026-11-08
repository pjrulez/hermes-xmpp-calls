import numpy as np

from xmpp_calls.audio import STT_FRAME, Endpointer, SpeechHeld, Utterance

MS = STT_FRAME // 20  # samples per ms at 16 kHz


def tone(ms: int, amp: int = 5000) -> np.ndarray:
    return (np.sin(np.arange(ms * MS) / 7) * amp).astype(np.int16)


def quiet(ms: int) -> np.ndarray:
    return (np.random.default_rng(0).normal(0, 20, ms * MS)).astype(np.int16)


def run(*chunks: np.ndarray) -> list:
    endpointer = Endpointer()
    events = []
    for chunk in chunks:
        events += endpointer.feed(chunk)
    return events


def test_one_utterance_after_silence() -> None:
    events = run(quiet(400), tone(1000), quiet(900))
    assert [type(e) for e in events] == [SpeechHeld, Utterance]
    assert len(events[1].pcm) // MS == 1900  # 200 preroll + 1000 speech + 700 silence


def test_click_is_ignored() -> None:
    assert run(quiet(300), tone(60), quiet(1500)) == []


def test_two_sentences_make_two_utterances() -> None:
    events = run(tone(800), quiet(900), tone(800), quiet(900))
    assert [type(e) for e in events] == [SpeechHeld, Utterance, SpeechHeld, Utterance]


def test_max_length_cuts_monologue() -> None:
    endpointer = Endpointer(max_ms=2000)
    events = endpointer.feed(tone(5000))
    assert sum(isinstance(e, Utterance) for e in events) >= 2


def test_chunking_does_not_matter() -> None:
    signal = np.concatenate([quiet(400), tone(1000), quiet(900)])
    endpointer = Endpointer()
    events = []
    for i in range(0, len(signal), 97):  # odd chunk size
        events += endpointer.feed(signal[i : i + 97])
    assert [type(e) for e in events] == [SpeechHeld, Utterance]
