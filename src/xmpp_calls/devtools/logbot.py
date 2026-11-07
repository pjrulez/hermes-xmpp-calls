"""Throwaway call logger (task R3): advertises call caps, accepts presence from one JID,
answers a Jingle Message Initiation `propose` with `proceed`, records every call stanza
with secrets redacted, then declines the session.

Run: uv run python -m xmpp_calls.devtools.logbot   (reads .scratch/bot.env)
"""

import asyncio
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from xml.etree import ElementTree as ET

import slixmpp
from slixmpp.xmlstream import StanzaBase
from slixmpp.xmlstream.handler import CoroutineCallback
from slixmpp.xmlstream.matcher import MatchXPath

JINGLE = "urn:xmpp:jingle:1"
JMI = "urn:xmpp:jingle-message:0"
CALL_FEATURES = [
    JINGLE,
    "urn:xmpp:jingle:transports:ice-udp:1",
    "urn:xmpp:jingle:apps:rtp:1",
    "urn:xmpp:jingle:apps:dtls:0",
    "urn:xmpp:jingle:apps:rtp:audio",
    JMI,
]
SCRATCH = Path(".scratch")
REDACT = [
    (
        re.compile(r'(pwd|ufrag|ip|address|rel-addr|id-hash|username|password|credential)="[^"]*"'),
        r'\1="X"',
    ),
    (re.compile(r"(<fingerprint[^>]*>)[^<]*(</fingerprint>)"), r"\1X\2"),
]


def redact(xml: str) -> str:
    for pattern, repl in REDACT:
        xml = pattern.sub(repl, xml)
    return xml


def load_env(path: Path) -> dict[str, str]:
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
    return {key.strip(): value.strip() for key, value in pairs}


class LogBot(slixmpp.ClientXMPP):
    def __init__(self, jid: str, password: str, allowed: str, outdir: Path) -> None:
        super().__init__(jid, password)
        self.allowed = allowed
        self.outdir = outdir
        self.roster.auto_authorize = False
        self.roster.auto_subscribe = False
        for plugin in ("xep_0030", "xep_0115"):
            self.register_plugin(plugin)
        self.add_event_handler("session_start", self.on_start)
        self.add_event_handler("presence_subscribe", self.on_subscribe)
        self.add_filter("in", self.record_in)
        self.add_filter("out", self.record_out)
        for verb in ("propose", "retract", "proceed", "accept", "reject", "finish"):
            path = f"{{{self.default_ns}}}message/{{{JMI}}}{verb}"
            self.register_handler(CoroutineCallback(f"jmi-{verb}", MatchXPath(path), self.on_jmi))
        path = f"{{{self.default_ns}}}iq/{{{JINGLE}}}jingle"
        self.register_handler(CoroutineCallback("jingle", MatchXPath(path), self.on_jingle))

    def record(self, direction: str, xml: str) -> None:
        if JINGLE not in xml and JMI not in xml:
            return
        resource = re.search(r'(?:from|to)="[^"/]*/([^"]*)"', xml)
        tag = re.sub(r"\W+", "_", resource.group(1))[:24] if resource else "unknown"
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%f")
        (self.outdir / f"{stamp}-{direction}-{tag}.xml").write_text(redact(xml) + "\n")

    def wire(self, direction: str, xml: str) -> None:
        """Append every stanza (redacted, one line) to wire.log to see what a client did."""
        stamp = datetime.now(UTC).strftime("%H:%M:%S.%f")
        with (self.outdir / "wire.log").open("a") as log:
            log.write(f"{stamp} {direction} {redact(xml)[:700]}\n")

    def record_in(self, stanza: StanzaBase) -> StanzaBase:
        self.record("in", str(stanza))
        self.wire("in", str(stanza))
        return stanza

    def record_out(self, stanza: StanzaBase) -> StanzaBase:
        self.record("out", str(stanza))
        self.wire("out", str(stanza))
        return stanza

    async def on_start(self, _event: object) -> None:
        # Features must be added after bind: slixmpp keys them by the current JID, and a bare
        # JID registered before bind means disco#info to our full JID shows no call features.
        for feature in CALL_FEATURES:
            self.plugin["xep_0030"].add_feature(feature)
        await self.plugin["xep_0115"].update_caps()
        await self.get_roster()
        self.send_presence()
        logging.info("online as %s", self.boundjid.bare)

    def on_subscribe(self, presence: slixmpp.Presence) -> None:
        peer = presence["from"].bare
        if peer != self.allowed:
            return
        self.send_presence(pto=peer, ptype="subscribed")
        self.send_presence(pto=peer, ptype="subscribe")

    async def on_jmi(self, stanza: StanzaBase) -> None:
        msg = cast(slixmpp.Message, stanza)
        child = next((c for c in msg.xml if c.tag.startswith(f"{{{JMI}}}")), None)
        if child is None:
            return
        verb = child.tag.rsplit("}", 1)[1]
        logging.info("jmi %s from %s", verb, msg["from"])
        if verb != "propose" or msg["from"].bare != self.allowed:
            return
        await self.log_features(msg["from"])
        # XEP-0353: accept to ourselves stops other devices ringing; proceed is for the caller.
        for target, tag in ((self.boundjid.bare, "accept"), (msg["from"], "proceed")):
            reply = self.make_message(mto=target, mtype="chat")
            reply.xml.append(ET.Element(f"{{{JMI}}}{tag}", id=child.get("id", "")))
            reply.send()

    async def log_features(self, jid: slixmpp.JID) -> None:
        """Record the caller's advertised disco features (the call button logic)."""
        try:
            info = await self["xep_0030"].get_info(jid=jid, timeout=10)
        except Exception as error:
            logging.warning("disco#info failed: %s", error)
            return
        tag = re.sub(r"\W+", "_", jid.resource)[:24]
        features = "\n".join(sorted(info["disco_info"]["features"]))
        (self.outdir / f"features-{tag}.txt").write_text(features + "\n")

    async def on_jingle(self, stanza: StanzaBase) -> None:
        iq = cast(slixmpp.Iq, stanza)
        jingle = iq.xml.find(f"{{{JINGLE}}}jingle")
        if jingle is None or iq["type"] != "set":
            return
        iq.reply().send()
        action, sid = jingle.get("action"), jingle.get("sid", "")
        logging.info("jingle %s from %s", action, iq["from"])
        if action == "session-initiate":
            await asyncio.sleep(1)
            term = ET.Element(f"{{{JINGLE}}}jingle", action="session-terminate", sid=sid)
            ET.SubElement(ET.SubElement(term, f"{{{JINGLE}}}reason"), f"{{{JINGLE}}}decline")
            self.make_iq_set(sub=term, ito=iq["from"]).send()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    env = load_env(SCRATCH / "bot.env")
    outdir = SCRATCH / "captures"
    outdir.mkdir(parents=True, exist_ok=True)
    bot = LogBot(env["BOT_JID"], env["BOT_PASSWORD"], env["ALLOWED"], outdir)
    bot.connect()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        bot.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    main()
