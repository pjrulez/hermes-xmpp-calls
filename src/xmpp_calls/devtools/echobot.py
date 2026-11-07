"""Echo-call bot (task T9): answers a real call from the allowed JID and plays the caller's
own voice back, so the operator can judge signaling, ICE/DTLS and audio on Dino/Conversations.

Run: uv run python -m xmpp_calls.devtools.echobot   (reads .scratch/bot.env)
"""

import asyncio
import logging
import sys
from typing import cast

import slixmpp
from slixmpp.xmlstream import StanzaBase

from xmpp_calls import turn
from xmpp_calls.devtools.logbot import JINGLE, SCRATCH, LogBot, load_env
from xmpp_calls.jingle import wire
from xmpp_calls.jingle.model import Jingle, JingleError
from xmpp_calls.jingle.session import IllegalTransition, Session
from xmpp_calls.media import CallMedia

MAX_CALL_SECONDS = 120  # dev bot: never leave a call open


class Call:
    def __init__(self, peer: slixmpp.JID, session: Session, media: CallMedia) -> None:
        self.peer, self.session, self.media = peer, session, media
        self.timer: asyncio.Task[None] | None = None


class EchoBot(LogBot):
    calls: dict[str, Call]

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.calls = {}

    async def on_jingle(self, stanza: StanzaBase) -> None:
        iq = cast(slixmpp.Iq, stanza)
        element = iq.xml.find(f"{{{JINGLE}}}jingle")
        if element is None or iq["type"] != "set" or iq["from"].bare != self.allowed:
            return
        iq.reply().send()
        jingle = wire.parse(element)
        logging.info("jingle %s sid=%s", jingle.action, jingle.sid)
        try:
            await self.dispatch(iq["from"], jingle)
        except JingleError as error:
            logging.warning("refusing call: %s", error)
            await self.end(jingle.sid, error.reason, notify=iq["from"])
        except IllegalTransition as error:
            logging.warning("illegal transition: %s", error)
        except Exception:
            logging.exception("call failed")
            await self.end(jingle.sid, "general-error", notify=iq["from"])

    async def dispatch(self, peer: slixmpp.JID, jingle: Jingle) -> None:
        if jingle.action == "session-initiate":
            session = Session(jingle.sid, we_initiated=False)
            session.apply("session-initiate", sent_by_us=False)
            media = CallMedia(await turn.fetch(self))
            call = self.calls[jingle.sid] = Call(peer, session, media)
            content = await media.answer(jingle)
            session.apply("session-accept", sent_by_us=True)
            accept = Jingle("session-accept", jingle.sid, contents=(content,), group=jingle.group)
            self.make_iq_set(sub=wire.build(accept), ito=peer).send()
            call.timer = asyncio.create_task(self.hang_up_later(jingle.sid))
            asyncio.create_task(self.report(jingle.sid))  # noqa: RUF006  short-lived log task
            return
        call = self.calls.get(jingle.sid)
        if call is None:
            return
        call.session.apply(jingle.action, sent_by_us=False)
        if jingle.action == "transport-info":
            for content in jingle.contents:
                for candidate in content.transport.candidates if content.transport else ():
                    await call.media.add_candidate(candidate)
        elif jingle.action == "session-terminate":
            await self.end(jingle.sid, None)

    async def hang_up_later(self, sid: str) -> None:
        await asyncio.sleep(MAX_CALL_SECONDS)
        await self.end(sid, "success", notify=True)

    async def report(self, sid: str) -> None:
        """Log RTP packet counts every 5 s while the call is open: the proof audio flows."""
        while sid in self.calls:
            await asyncio.sleep(5)
            if sid in self.calls:
                logging.info("rtp received/sent %s", await self.calls[sid].media.packets())

    async def end(self, sid: str, reason: str | None, notify: slixmpp.JID | bool = False) -> None:
        """Close one call; with `reason`, tell the peer (`notify`: its JID, or True)."""
        call = self.calls.pop(sid, None)
        if call is None and not notify:
            return
        if call is not None:
            if call.timer:
                call.timer.cancel()
            logging.info("call ended, rtp %s", await call.media.packets())
            await call.media.close()
        peer = call.peer if call is not None and notify is True else notify
        if reason and isinstance(peer, slixmpp.JID):
            self.make_iq_set(
                sub=wire.build(Jingle("session-terminate", sid, reason=reason)), ito=peer
            ).send()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    env = load_env(SCRATCH / "bot.env")
    outdir = SCRATCH / "captures"
    outdir.mkdir(parents=True, exist_ok=True)
    bot = EchoBot(env["BOT_JID"], env["BOT_PASSWORD"], env["ALLOWED"], outdir)
    bot.connect()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        bot.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    main()
