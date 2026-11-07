from xml.etree import ElementTree as ET

from xmpp_calls.turn import parse_services

XML = """<services xmlns="urn:xmpp:extdisco:2">
<service type="stun" host="turn.example" port="3478" transport="udp"/>
<service type="turn" host="turn.example" port="3478" transport="udp" username="u" password="p"/>
<service type="turn" host="turn.example" port="3478" transport="tcp" username="u" password="p"/>
<service type="turns" host="turn.example" port="5349" transport="tcp" username="u" password="p"/>
<service type="turn" host="2001:db8::1" port="3478" username="u" password="p"/>
</services>"""


def test_parse_keeps_udp_stun_and_turn_only() -> None:
    servers = parse_services(ET.fromstring(XML))
    assert [s.urls for s in servers] == [
        "stun:turn.example:3478",
        "turn:turn.example:3478?transport=udp",
        "turn:[2001:db8::1]:3478?transport=udp",
    ]
    assert (servers[1].username, servers[1].credential) == ("u", "p")
