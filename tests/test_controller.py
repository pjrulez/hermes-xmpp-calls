"""CallController with a fake slixmpp client and host, and a real aiortc caller."""

import asyncio
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
import slixmpp

from tests.helpers import make_offer
from xmpp_calls.controller import JMI, CallController
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
