"""XEP-0215 external service discovery: STUN/TURN servers and short-lived credentials."""

from xml.etree import ElementTree as ET

from aiortc import RTCIceServer

EXTDISCO = "urn:xmpp:extdisco:2"


def parse_services(services: ET.Element) -> list[RTCIceServer]:
    """UDP stun/turn services only; `turns:` and TCP are skipped (our transport is ice-udp)."""
    servers = []
    for service in services.findall(f"{{{EXTDISCO}}}service"):
        kind, host = service.get("type", ""), service.get("host", "")
        if kind not in ("stun", "turn") or not host or service.get("transport", "udp") != "udp":
            continue
        host = f"[{host}]" if ":" in host else host
        url = f"{kind}:{host}:{service.get('port', '3478')}"
        if kind == "turn":
            servers.append(
                RTCIceServer(
                    f"{url}?transport=udp", service.get("username"), service.get("password")
                )
            )
        else:
            servers.append(RTCIceServer(url))
    return servers


async def fetch(client) -> list[RTCIceServer]:
    """Ask our own server for ICE servers. [] on any failure: calls then try direct paths."""
    iq = client.make_iq_get(ito=client.boundjid.domain)
    iq.xml.append(ET.Element(f"{{{EXTDISCO}}}services"))
    try:
        result = await iq.send(timeout=10)
    except Exception:
        return []
    services = result.xml.find(f"{{{EXTDISCO}}}services")
    return parse_services(services) if services is not None else []
