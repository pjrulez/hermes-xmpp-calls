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


class CallBot(LogBot):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.controller = CallController(self, DevHost(self.allowed))
        self.controller.install()

    async def on_start(self, _event: object) -> None:
        await super().on_start(_event)
        await self.controller.advertise()

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
