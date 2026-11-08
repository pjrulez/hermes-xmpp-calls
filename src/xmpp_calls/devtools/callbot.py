"""Conversation bot (task B3): like the echo bot, but the caller talks to a Hermes agent.

Run: uv run python -m xmpp_calls.devtools.callbot   (reads .scratch/bot.env)
Env: CALLBOT_TOOLSETS (default "web") limits what the agent may use during calls.
"""

import asyncio
import logging
import sys

from xmpp_calls import turn
from xmpp_calls.conversation import Conversation
from xmpp_calls.devtools.echobot import EchoBot
from xmpp_calls.devtools.logbot import SCRATCH, load_env
from xmpp_calls.media import CallMedia
from xmpp_calls.providers import HermesCLIResponder, HermesSpeech

GREETING = "Hi, I'm here. What can I do for you?"


class CallBot(EchoBot):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._background: set[asyncio.Task[None]] = set()  # strong refs for greeting tasks

    async def new_media(self, sid: str) -> CallMedia:
        async def hang_up() -> None:
            await self.end(sid, "success", notify=True)

        convo = Conversation(HermesSpeech(), HermesCLIResponder(), hang_up)
        media = CallMedia(await turn.fetch(self), make_outgoing=convo.attach)
        media.pc.on("connectionstatechange", lambda: self._on_state(media, convo))
        greeting = asyncio.create_task(self._greet(media, convo))
        self._background.add(greeting)
        greeting.add_done_callback(self._background.discard)
        return media

    async def _greet(self, media: CallMedia, convo: Conversation) -> None:
        await media.connected.wait()
        await convo.say(GREETING)

    @staticmethod
    def _on_state(media: CallMedia, convo: Conversation) -> None:
        if media.pc.connectionState in ("closed", "failed"):
            convo.stop()


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
