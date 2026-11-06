# Dependency options

Need: Jingle signaling (XEP-0166/0167/0176/0320/0215/0353) plus a WebRTC media engine, usable from the Hermes gateway process (Python).

## Facts
- slixmpp (1.15.0 pinned by our plugin, 1.17.0 latest): XMPP core and JMI stanzas only. No Jingle core, RTP, ICE-UDP, DTLS, or external-service discovery plugins.
- aiortc 1.16.0 (Python >=3.11): ICE (aioice 0.13.0, TURN capable), DTLS-SRTP, Opus via av. Loopback verified on Python 3.14.9. Produces and consumes SDP, so Jingle is converted to SDP and back.
- aioxmpp 0.13.3 (2023): unmaintained, not evaluated further.
- GStreamer `webrtcbin` is installed on fw (`gst-inspect-1.0`) but needs native bindings, a heavy dependency for the gateway.

## Options
A. **New slixmpp add-ons plus aiortc glue, vendored in the plugin.** Write Jingle core, RTP/ICE-UDP/DTLS stanzas, XEP-0215, and a Jingle to SDP bridge as slixmpp plugins in the `jingle/` subpackage of the plugin fork. Nothing else to install; upstreamable to slixmpp later because `jingle/` imports neither aiortc nor Hermes. Cost: the most code, fully ours.
B. **Fork slixmpp and add the plugins inside it.** Same code as A but carried as a fork. Upstreamable; adds a fork to maintain and conflicts with the plugin's `slixmpp==1.15.0` pin.
C. **Borrow from prior art.** `xmpp-radio-tower` has a 742-line `jingle_webrtc.py` (Python, slixmpp, aiortc) that reports working calls with Conversations and five other clients. License not found, so reuse of code is unverified (U16); reading it as a reference is fine. `hermes-deltachat-platform` (MPL-2.0) is a ready-made Hermes call pipeline on aiortc; its media and conversation loop is the closest design reference.
D. **GStreamer webrtcbin.** Siproxylin got Conversations calls working this way after Go Pion failed. Strong interop, but native packaging, and the Hermes venv does not carry GI bindings.

## Recommendation for round 2 (to confirm after R3 and R4)
Take A as the shape, use C as reference and test oracle, keep D as the fallback if aiortc fails interop with Conversations (finding 13). Keep `jingle/` and `media/` independent of Hermes so they can be tested against Conversations with a tiny echo bot first. Delivery rule: the plugin fork is the only thing installed (OpenSpec `plugin-delivery`).

## Version pins to settle
slixmpp 1.15.0 vs 1.17.0, aiortc 1.16.0, av 19.0.2. Hermes installs plugin dependencies from `plugin.yaml` into its own venv; the VMs use Python 3.11 (U14).
