from app.tailscale_client import advertises_exit_node, parse_prefs, parse_status


def test_parse_prefs_detects_exit_node_routes() -> None:
    prefs = parse_prefs('{"AdvertiseRoutes":["0.0.0.0/0","::/0"]}')

    assert advertises_exit_node(prefs) is True


def test_parse_status_normalizes_dns_name() -> None:
    status = parse_status(
        '{"Self":{"HostName":"example-host","DNSName":"example.tail.ts.net.","TailscaleIPs":["100.1.2.3"]},"Health":[]}'
    )

    assert status.self_node.dns_name == "example.tail.ts.net"


def test_parse_prefs_handles_disabled_routes() -> None:
    prefs = parse_prefs('{"AdvertiseRoutes":null}')

    assert advertises_exit_node(prefs) is False
