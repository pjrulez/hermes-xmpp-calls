"""Dev call bot: the real CallController on the logger bot's account, with the Hermes CLI as the
agent. Wire log and captures stay on (see logbot).

Run: uv run python -m xmpp_calls.devtools.callbot   (reads .scratch/bot.env)
Env: CALLBOT_TOOLSETS (default "web") limits what the agent may use during calls.
"""

import asyncio
import logging
import sys
from typing import Any

from xmpp_calls.controller import CallController
from xmpp_calls.devtools.logbot import SCRATCH, LogBot, load_env
from xmpp_calls.devtools.providers import HermesCLIResponder, HermesSpeech


class DevHost:
    def __init__(self, allowed: str) -> None:
        self.allowed = allowed
        self.speech = HermesSpeech()
        self._agents: dict[str, HermesCLIResponder] = {}

    def authorized(self, bare_jid: str) -> bool:
        return bare_jid == self.allowed

    async def ask(self, peer: str, call_id: str, text: str) -> str:
        return await self._agents.setdefault(call_id, HermesCLIResponder())(text)

    async def steer(self, peer: str, call_id: str, text: str) -> bool:
        return False  # a CLI turn cannot be steered; the speech is queued

    async def post_text(self, peer: str, text: str) -> None:
        logging.warning("could not speak; text reply: %s", text)


class CallBot(LogBot):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.controller = CallController(self, DevHost(self.allowed))
        self.controller.install()
        self.add_event_handler("message", self.on_chat)

    async def on_start(self, _event: object) -> None:
        await super().on_start(_event)
        await self.controller.advertise()

    async def on_chat(self, msg: Any) -> None:
        """Dev triggers: "call me" (greeting) and "brief me" (uninterruptible briefing)."""
        if msg["from"].bare != self.allowed:
            return
        text = msg["body"].strip().lower()
        if text == "call me":
            opening = "Hello. This is the test bot calling you, as you asked."
            status = await self.controller.place_call(self.allowed, opening)
        elif text == "brief me":
            briefing = (
                "Good morning. Here is your test briefing. Today there were three top options: "
                "the first was about calls, the second about noise, and the third about cron. "
                "I chose the first one because it unlocks the others. "
                "Today's note reads: calls now ring you, and nothing interrupts a briefing. "
                "That is the end of the briefing. You can ask me a question now."
            )
            status = await self.controller.place_call(self.allowed, briefing, uninterruptible=True)
        else:
            return
        msg.reply(status).send()

    # The controller owns call signaling; the logger's own call handlers step aside.
    async def on_jmi(self, stanza: Any) -> None: ...

    async def on_jingle(self, stanza: Any) -> None: ...


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    env = load_env(SCRATCH / "bot.env")
    outdir = SCRATCH / "captures"
    outdir.mkdir(parents=True, exist_ok=True)
    bot = CallBot(env["BOT_JID"], env["BOT_PASSWORD"], env["ALLOWED"], outdir)
    bot.connect()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        bot.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    main()
