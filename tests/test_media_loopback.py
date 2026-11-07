"""Whole answer path without XMPP: an aiortc caller sends a tone through our Jingle/SDP bridge
and CallMedia echoes it back. Conversations-style: the caller's candidates are trickled."""

import asyncio
import fractions
import time
from dataclasses import replace
from typing import cast
from xml.etree import ElementTree as ET

import av
import numpy as np
from aiortc import RTCConfiguration, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamTrack

from xmpp_calls.jingle import wire
from xmpp_calls.jingle.model import Content, Jingle
from xmpp_calls.jingle.sdp import answer_to_content, candidate_from_sdp, offer_to_sdp
from xmpp_calls.media import CallMedia

TONE_HZ = 440


class Tone(MediaStreamTrack):
    kind = "audio"

    def __init__(self) -> None:
        super().__init__()
        self.start = time.time()
        self.n = 0

    async def recv(self) -> av.AudioFrame:
        await asyncio.sleep(max(0, self.start + self.n * 0.02 - time.time()))
        t = (np.arange(960) + self.n * 960) / 48000
        pcm = (np.sin(2 * np.pi * TONE_HZ * t) * 12000).astype(np.int16)
        frame = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate, frame.pts, frame.time_base = (
            48000,
            self.n * 960,
            fractions.Fraction(1, 48000),
        )
        self.n += 1
        return frame


def over_the_wire(jingle: Jingle) -> Jingle:
    return wire.parse(ET.fromstring(ET.tostring(wire.build(jingle))))


async def test_tone_is_echoed_with_trickled_candidates() -> None:
    caller = RTCPeerConnection(RTCConfiguration(iceServers=[]))
    caller.addTrack(Tone())
    heard: list[np.ndarray] = []
    readers: list[asyncio.Future[None]] = []

    @caller.on("track")
    def on_track(track: MediaStreamTrack) -> None:
        async def read() -> None:
            while True:
                frame = await track.recv()
                heard.append(
                    cast(av.AudioFrame, frame).to_ndarray().reshape(-1, 2)[:, 0]
                )  # stereo interleaved -> left

        readers.append(asyncio.ensure_future(read()))

    await caller.setLocalDescription(await caller.createOffer())
    sdp = caller.localDescription.sdp
    mid = "0"
    content = answer_to_content(sdp, Content("initiator", mid))  # offer SDP has the same shape
    trickled = content.transport.candidates  # type: ignore[union-attr]
    assert trickled, "aiortc offer should carry candidates"
    bare = replace(content, transport=replace(content.transport, candidates=()))  # type: ignore[type-var]
    offer = over_the_wire(Jingle("session-initiate", "s1", contents=(bare,), group=(mid,)))

    media = CallMedia([])
    accepted = over_the_wire(
        Jingle("session-accept", "s1", contents=(await media.answer(offer),), group=(mid,))
    )
    await caller.setRemoteDescription(RTCSessionDescription(offer_to_sdp(accepted), "answer"))
    for candidate in trickled:
        update = replace(bare, transport=replace(bare.transport, candidates=(candidate,)))  # type: ignore[type-var]
        sent_update = over_the_wire(Jingle("transport-info", "s1", contents=(update,)))
        await media.add_candidate(sent_update.contents[0].transport.candidates[0])  # type: ignore[union-attr]

    await asyncio.wait_for(media.connected.wait(), 15)
    await asyncio.sleep(3)
    received, sent = await media.packets()
    await media.close()
    await caller.close()

    assert received > 50
    assert sent > 50
    x = np.concatenate(heard).astype(float)[-9600:]
    peak = np.argmax(np.abs(np.fft.rfft(x * np.hanning(len(x))))) * 48000 / len(x)
    assert abs(peak - TONE_HZ) < 20, peak


def test_candidate_helper_used() -> None:
    assert candidate_from_sdp("1 1 udp 1 1.2.3.4 5 typ host").port == 5
