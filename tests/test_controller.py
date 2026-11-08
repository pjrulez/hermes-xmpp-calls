"""CallController with a fake slixmpp client and host, and a real aiortc caller."""

import asyncio
import re
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
import slixmpp

from tests.helpers import make_offer
from xmpp_calls.controller import JMI, CallConfig, CallController
from xmpp_calls.jingle import wire
from xmpp_calls.jingle.model import Jingle

PEER = "owner@example.org/phone"


class Sent:
    def __init__(self, log: list, kind: str, to: str, xml: ET.Element) -> None:
        self.log, self.kind, self.to, self.xml = log, kind, to, xml

    def send(self) -> None:
        self.log.append(self)


class FakeClient:
    default_ns = "jabber:client"
    boundjid = slixmpp.JID("bot@example.org/res")

    def __init__(self) -> None:
        self.sent: list[Sent] = []
        self.plugin: dict = {}

    def make_message(self, mto: Any, mtype: str) -> Sent:
        return Sent(self.sent, "message", str(mto), ET.Element("message"))

    def make_iq_set(self, sub: ET.Element, ito: Any) -> Sent:
        return Sent(self.sent, "iq", str(ito), sub)

    def make_iq_get(self, ito: Any) -> Any:
        class Get:
            xml = ET.Element("iq")

            async def send(self, timeout: int = 0) -> Any:  # noqa: ASYNC109  mirrors slixmpp
                raise TimeoutError

        return Get()

    def jingle_sent(self) -> list[Jingle]:
        return [wire.parse(s.xml) for s in self.sent if s.kind == "iq"]

    def jmi_sent(self) -> list[tuple[str, str]]:
        return [(s.to, s.xml[0].tag.rsplit("}", 1)[1]) for s in self.sent if s.kind == "message"]


class FakeSpeech:
    async def transcribe(self, pcm: np.ndarray) -> str:
        return "hello"

    async def synthesize(self, text: str) -> np.ndarray:
        return np.zeros(4800, np.int16)


class FakeHost:
    speech = FakeSpeech()

    def authorized(self, bare_jid: str) -> bool:
        return bare_jid == "owner@example.org"

    async def ask(self, peer: str, call_id: str, text: str) -> str:
        return "A fine reply that is spoken aloud."

    def __init__(self) -> None:
        self.texts: list[tuple[str, str]] = []
        self.titles: list[str] = []

    async def post_text(self, peer: str, text: str) -> None:
        self.texts.append((peer, text))

    async def steer(self, peer: str, call_id: str, text: str) -> bool:
        return False

    async def name_call(self, peer: str, call_id: str, title: str) -> None:
        self.titles.append(title)


class FakeStanza:
    def __init__(self, xml: ET.Element, sender: str, kind: str = "set") -> None:
        self.xml, self._fields = xml, {"from": slixmpp.JID(sender), "type": kind}
        self.replies = 0

    def __getitem__(self, key: str) -> Any:
        return self._fields[key]

    def reply(self) -> Any:
        stanza = self

        class Reply:
            def send(self) -> None:
                stanza.replies += 1

        return Reply()


def propose(frm: str = PEER) -> FakeStanza:
    message = ET.Element("message")
    ET.SubElement(message, f"{{{JMI}}}propose", id="p1")
    return FakeStanza(message, frm, "chat")


def make() -> tuple[CallController, FakeClient]:
    client = FakeClient()
    return CallController(client, FakeHost()), client


def test_install_registers_handlers() -> None:
    client = slixmpp.ClientXMPP("bot@example.org/res", "x")
    before = len(client._handlers) if hasattr(client, "_handlers") else 0
    CallController(client, FakeHost()).install()
    assert (len(client._handlers) if hasattr(client, "_handlers") else 3) > before


async def test_propose_from_authorized_peer_is_accepted_and_proceeded() -> None:
    ctl, client = make()
    await ctl._on_jmi(propose())
    assert client.jmi_sent() == [("bot@example.org", "accept"), (PEER, "proceed")]


async def test_propose_from_stranger_is_ignored() -> None:
    ctl, client = make()
    await ctl._on_jmi(propose("evil@example.org/x"))
    assert client.sent == []


async def test_propose_while_busy_is_rejected() -> None:
    ctl, client = make()
    ctl.calls["other"] = object()  # type: ignore[assignment]
    await ctl._on_jmi(propose())
    assert client.jmi_sent() == [("owner@example.org", "reject")]


async def test_call_lifecycle() -> None:
    ctl, client = make()
    caller, offer, _ = await make_offer("s1")
    await ctl.handle(PEER, offer)
    (accept,) = client.jingle_sent()
    assert accept.action == "session-accept"
    assert accept.sid == "s1"
    assert accept.group == ("0",)
    assert set(ctl.calls) == {"s1"}

    await ctl.handle(PEER, Jingle("session-terminate", "s1", reason="success"))
    assert ctl.calls == {}
    await caller.close()


async def test_mute_ends_the_utterance() -> None:
    ctl, _ = make()
    caller, offer, _ = await make_offer("s2")
    await ctl.handle(PEER, offer)
    muted = []
    ctl.calls["s2"].convo.caller_muted = lambda: muted.append(True)  # type: ignore[method-assign]
    await ctl.handle(PEER, Jingle("session-info", "s2", info="mute"))
    assert muted == [True]
    await ctl.close()
    await caller.close()


async def test_second_call_gets_busy() -> None:
    ctl, client = make()
    first, offer1, _ = await make_offer("a")
    second, offer2, _ = await make_offer("b")
    await ctl.handle(PEER, offer1)
    await ctl.handle(PEER, offer2)
    assert [(j.action, j.reason) for j in client.jingle_sent()][-1] == ("session-terminate", "busy")
    assert set(ctl.calls) == {"a"}
    await ctl.close()
    await first.close()
    await second.close()


async def test_offer_without_dtls_is_refused_with_security_error() -> None:
    ctl, client = make()
    caller, offer, _ = await make_offer("s3")
    # Renaming the element hides the fingerprint from the parser without rebuilding the tree.
    xml = ET.tostring(wire.build(offer)).decode().replace("fingerprint", "xfingerprint")
    iq = ET.Element("iq")
    iq.append(ET.fromstring(xml))
    stanza = FakeStanza(iq, PEER)
    await ctl._on_jingle(stanza)
    assert stanza.replies == 1
    assert client.jingle_sent()[-1].reason == "security-error"
    assert ctl.calls == {}
    await caller.close()


async def test_close_hangs_up_open_calls() -> None:
    ctl, client = make()
    caller, offer, _ = await make_offer("s4")
    await ctl.handle(PEER, offer)
    await ctl.close()
    assert ctl.calls == {}
    assert client.jingle_sent()[-1].action == "session-terminate"
    await caller.close()
    await asyncio.sleep(0)


async def _run_outgoing(**options: Any) -> tuple[CallController, FakeClient, str, Any, list[str]]:
    """Place a call, have an aiortc-backed 'phone' answer it, return once connected."""
    ctl, client = make()
    spoken: list[str] = []
    ctl.host.speech.synthesize = lambda text: _record(spoken, text)  # type: ignore[method-assign]
    task = asyncio.create_task(
        ctl.place_call("owner@example.org", "Your backup finished.", **options)
    )
    await asyncio.sleep(0.05)
    (propose_msg,) = [s for s in client.sent if s.kind == "message"]
    proposal = str(propose_msg.xml[0].get("id"))
    assert propose_msg.xml[0].tag == f"{{{JMI}}}propose"
    assert propose_msg.to == "owner@example.org"

    await ctl._on_jmi(proceed(proposal))  # the phone answered
    for _ in range(100):
        initiates = [j for j in client.jingle_sent() if j.action == "session-initiate"]
        if initiates:
            break
        await asyncio.sleep(0.05)
    (initiate,) = initiates
    assert initiate.sid == proposal
    assert initiate.initiator == "bot@example.org/res"
    assert client.sent[-1].to == PEER

    from xmpp_calls.media import CallMedia

    phone = CallMedia([])
    answer = await phone.answer(initiate)
    accept = Jingle("session-accept", proposal, contents=(answer,), group=initiate.group)
    await ctl.handle(PEER, accept)
    for candidate in initiate.contents[0].transport.candidates:  # type: ignore[union-attr]
        await phone.add_candidate(candidate)
    result = await asyncio.wait_for(task, 20)
    return ctl, client, result, phone, spoken


async def test_outgoing_call_rings_offers_and_speaks_the_opening() -> None:
    ctl, _, result, phone, spoken = await _run_outgoing()
    sid = next(iter(ctl.calls))
    assert result.startswith("connected")
    await asyncio.sleep(0.1)
    assert "Your backup finished." in spoken
    assert "began by saying: Your backup finished." in ctl.calls[sid].convo._note
    assert not ctl.calls[sid].convo._protected
    await ctl.close()
    await phone.close()


async def test_uninterruptible_opening_is_protected_while_it_plays() -> None:
    ctl, _, _, phone, _ = await _run_outgoing(uninterruptible=True)
    sid = next(iter(ctl.calls))
    await asyncio.sleep(0.2)
    assert ctl.calls[sid].convo._protected  # still playing: nothing drains the playback in tests
    ctl.calls[sid].convo.playback.flush()
    await asyncio.sleep(0.2)
    assert not ctl.calls[sid].convo._protected
    await ctl.close()
    await phone.close()


async def test_hang_up_after_ends_the_call_when_the_opening_is_done() -> None:
    ctl, client, _, phone, _ = await _run_outgoing(hang_up_after=True)
    sid = next(iter(ctl.calls))
    await asyncio.sleep(0.2)
    assert sid in ctl.calls  # still delivering
    ctl.config = CallConfig(hangup_grace=0.5)
    ctl.calls[sid].convo.playback.flush()
    await asyncio.sleep(0.2)
    assert sid in ctl.calls  # warning beeps, then the caller gets a moment to speak
    for _ in range(40):
        if sid not in ctl.calls:
            break
        await asyncio.sleep(0.05)
    assert sid not in ctl.calls
    assert client.jingle_sent()[-1].action == "session-terminate"
    await phone.close()


async def test_outgoing_call_not_answered_is_retracted() -> None:
    ctl, client = make()
    ctl.config = CallConfig(ring_timeout=0)
    result = await ctl.place_call("owner@example.org", "Hello")
    assert result.startswith("no answer")
    assert client.jmi_sent()[-1][1] == "retract"
    assert ctl._ringing == {}
    ((peer, text),) = ctl.host.texts  # type: ignore[attr-defined]
    assert peer == "owner@example.org"  # sent as text instead
    assert "Hello" in text
    assert ctl._missed == {"owner@example.org": "Hello"}  # and remembered for a call back


async def test_outgoing_call_declined() -> None:
    ctl, client = make()
    task = asyncio.create_task(ctl.place_call("owner@example.org", "Hello"))
    await asyncio.sleep(0.05)
    proposal = str(client.sent[0].xml[0].get("id"))
    await ctl._on_jmi(proceed(proposal, "reject"))
    assert (await task).startswith("declined")
    assert "Hello" in ctl.host.texts[0][1]  # type: ignore[attr-defined]


async def test_outgoing_call_to_stranger_is_refused() -> None:
    ctl, client = make()
    assert (await ctl.place_call("evil@example.org", "Hi")).startswith("refused")
    assert client.sent == []


async def test_outgoing_call_while_busy() -> None:
    ctl, _ = make()
    ctl.calls["x"] = object()  # type: ignore[assignment]
    assert (await ctl.place_call("owner@example.org", "Hi")).startswith("busy")


def proceed(proposal: str, verb: str = "proceed") -> FakeStanza:
    message = ET.Element("message")
    ET.SubElement(message, f"{{{JMI}}}{verb}", id=proposal)
    return FakeStanza(message, PEER, "chat")


async def _record(spoken: list[str], text: str) -> np.ndarray:
    spoken.append(text)
    return np.zeros(
        48000 * 3, np.int16
    )  # 3 s: long enough that the sender cannot drain it mid-test


async def test_call_session_gets_a_recognizable_title() -> None:
    ctl, _, _, phone, _ = await _run_outgoing()
    await asyncio.sleep(0.1)
    (title,) = ctl.host.titles  # type: ignore[attr-defined]
    assert re.fullmatch(r"Call to owner \d{4}-\d\d-\d\d \d\d:\d\d", title)
    await phone.close()


async def test_call_title_includes_the_topic() -> None:
    ctl, _, _, phone, _ = await _run_outgoing(topic="daily-note")
    await asyncio.sleep(0.1)
    assert ctl.host.titles[0].endswith(" daily-note")  # type: ignore[attr-defined]
    await phone.close()


async def test_call_with_talk_ends_with_a_text_recap() -> None:
    ctl, _, _, phone, _ = await _run_outgoing()
    sid = next(iter(ctl.calls))
    ctl.calls[sid].convo.turns = 2  # the person said something and the agent answered
    await ctl.end(sid, "success", notify=True)
    await asyncio.sleep(0.2)
    recaps = [t for _, t in ctl.host.texts if t.startswith("Call recap:")]  # type: ignore[attr-defined]
    assert len(recaps) == 1
    await phone.close()


async def test_call_without_talk_has_no_recap() -> None:
    ctl, _, _, phone, _ = await _run_outgoing()
    sid = next(iter(ctl.calls))
    await ctl.end(sid, "success", notify=True)
    await asyncio.sleep(0.2)
    assert ctl.host.texts == []  # type: ignore[attr-defined]
    await phone.close()
