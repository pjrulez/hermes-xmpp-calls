"""Speech and agent providers for the dev call bot.

STT and TTS run the `command` providers already configured in Hermes (`stt.provider`,
`tts.provider` in config.yaml), so no Hermes config changes are needed. The agent turn is the
`hermes chat` CLI: slow (seconds) but identical to a text turn. Inside the Hermes gateway the
real plugin replaces `HermesCLIResponder` with a session turn.
"""

import asyncio
import os
import re
import shlex
import tempfile
from pathlib import Path

import numpy as np
import yaml

from .audio import STT_RATE, decode_to_out_rate, wav_bytes

CONFIG = Path.home() / ".hermes" / "config.yaml"
CALL_PROMPT = (
    "You are on a live phone call with your operator. Answer in one to three short spoken "
    "sentences, plain words, no markdown, no lists, and no closing notes about what you skipped "
    "or checked. If the caller says goodbye, end your reply with [[hangup]]. The caller said: "
)


async def run(args: list[str], limit: float) -> tuple[int, str]:
    """Run a command without a shell; the process is killed if we are cancelled or time out."""
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), limit)
    except BaseException:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode or 0, out.decode(errors="replace")


class HermesSpeech:
    """STT and TTS through the commands configured in Hermes."""

    def __init__(self, config: Path = CONFIG, timeout: float = 120) -> None:
        settings = yaml.safe_load(config.read_text())
        self._stt = self._command(settings, "stt")
        self._tts = self._command(settings, "tts")
        self._timeout = timeout

    @staticmethod
    def _command(settings: dict, kind: str) -> list[str]:
        section = settings[kind]
        return shlex.split(section["providers"][section["provider"]]["command"])

    async def _run(self, template: list[str], input_path: Path, output_path: Path) -> None:
        args = [
            a.replace("{input_path}", str(input_path)).replace("{output_path}", str(output_path))
            for a in template
        ]
        code, output = await run(args, self._timeout)
        if code:
            raise RuntimeError(f"{Path(args[0]).name} failed ({code}): {output[-200:]}")

    async def transcribe(self, pcm: np.ndarray) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            # tiny temp files: blocking I/O here is microseconds
            wav, txt = Path(tmp, "in.wav"), Path(tmp, "out.txt")
            wav.write_bytes(wav_bytes(pcm, STT_RATE))  # noqa: ASYNC240
            await self._run(self._stt, wav, txt)
            return " ".join(txt.read_text().split())  # noqa: ASYNC240

    async def synthesize(self, text: str) -> np.ndarray:
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp, "in.txt"), Path(tmp, "out.wav")
            src.write_text(text)  # noqa: ASYNC240
            await self._run(self._tts, src, out)
            return await asyncio.to_thread(decode_to_out_rate, str(out))


class HermesCLIResponder:
    """One `hermes chat` turn per utterance, resuming one session for the whole call."""

    def __init__(
        self, toolsets: str = os.environ.get("CALLBOT_TOOLSETS", "web"), timeout: float = 120
    ) -> None:
        self._toolsets, self._timeout = toolsets, timeout
        self._session: str | None = None

    async def __call__(self, text: str) -> str:
        args = [
            "hermes",
            "chat",
            "-Q",
            "--max-turns",
            "4",
            "-t",
            self._toolsets,
        ]
        if self._session:
            args += ["--resume", self._session, "-q", text]
        else:
            args += ["-q", CALL_PROMPT + text]
        code, output = await run(args, self._timeout)
        if code:
            raise RuntimeError(f"hermes chat failed ({code}): {output[-200:]}")
        found = re.search(r"\n\s*session_id:\s*(\S+)\s*$", output)
        if found:
            self._session = found.group(1)
            output = output[: found.start()]
        lines = [line for line in output.splitlines() if not line.startswith("↻")]  # resume banner
        return "\n".join(lines).strip()
