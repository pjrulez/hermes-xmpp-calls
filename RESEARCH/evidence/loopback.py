"""Loopback: aiortc peer A sends a 440 Hz tone (Opus/DTLS-SRTP), peer B records it. No XMPP."""

import asyncio
import fractions
import time

import av
import numpy as np
from aiortc import MediaStreamTrack, RTCConfiguration, RTCPeerConnection


class Tone(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.t0 = None
        self.n = 0

    async def recv(self):
        if self.t0 is None:
            self.t0 = time.time()
        # pace at real time, 20 ms frames, 48 kHz mono s16
        await asyncio.sleep(max(0, self.t0 + self.n * 0.02 - time.time()))
        t = (np.arange(960) + self.n * 960) / 48000
        pcm = (np.sin(2 * np.pi * 440 * t) * 12000).astype(np.int16)
        f = av.AudioFrame.from_ndarray(pcm.reshape(1, -1), format="s16", layout="mono")
        f.sample_rate = 48000
        f.pts = self.n * 960
        f.time_base = fractions.Fraction(1, 48000)
        self.n += 1
        return f


async def main():
    a, b = (
        RTCPeerConnection(RTCConfiguration(iceServers=[])),
        RTCPeerConnection(RTCConfiguration(iceServers=[])),
    )
    a.addTrack(Tone())
    got = []
    tasks: list[asyncio.Future] = []

    @b.on("track")
    def on_track(track):
        async def rd():
            try:
                while True:
                    fr = await track.recv()
                    got.append(fr.to_ndarray().reshape(-1))
            except Exception:
                pass

        tasks.append(asyncio.ensure_future(rd()))

    await a.setLocalDescription(await a.createOffer())
    offer = a.localDescription
    await b.setRemoteDescription(offer)
    await b.setLocalDescription(await b.createAnswer())
    await a.setRemoteDescription(b.localDescription)
    await asyncio.sleep(4)
    print("states", a.connectionState, b.connectionState, "iceGathering", a.iceGatheringState)
    sdp = offer.sdp
    print(
        "offer has: opus",
        "opus/48000/2" in sdp,
        "| fingerprint",
        "a=fingerprint" in sdp,
        "| setup",
        [ln for ln in sdp.split("\r\n") if ln.startswith("a=setup")],
        "| ice-ufrag",
        "a=ice-ufrag" in sdp,
    )
    x = np.concatenate(got).astype(float) if got else np.zeros(1)
    print("frames", len(got), "samples", len(x))
    if len(x) > 4800:
        spec = np.abs(np.fft.rfft(x[-9600:] * np.hanning(9600)))
        print("peak Hz ~", round(float(np.argmax(spec) * 48000 / 9600)))
    await a.close()
    await b.close()


asyncio.run(main())
