from __future__ import annotations

import subprocess
from typing import Final, Literal

from pydantic import ValidationError

from app.models import DashboardState, TailscalePrefs, TailscaleStatus

ADMIN_CONSOLE_URL: Final[str] = "https://login.tailscale.com/admin/machines"
DEFAULT_ROUTE_V4: Final[str] = "0.0.0.0/0"
DEFAULT_ROUTE_V6: Final[str] = "::/0"


class TailscaleCommandError(RuntimeError):
    def __init__(self, command: tuple[str, ...], stderr: str) -> None:
        self.command: tuple[str, ...] = command
        self.stderr: str = stderr
        super().__init__(f"{' '.join(command)} failed: {stderr}")


def _run_tailscale(*args: str) -> str:
    command = ("tailscale", *args)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise TailscaleCommandError(command, completed.stderr.strip())
    return completed.stdout


def parse_prefs(payload: str) -> TailscalePrefs:
    try:
        return TailscalePrefs.model_validate_json(payload)
    except ValidationError as error:
        message = "Invalid tailscale debug prefs payload"
        raise ValueError(message) from error


def parse_status(payload: str) -> TailscaleStatus:
    try:
        return TailscaleStatus.model_validate_json(payload)
    except ValidationError as error:
        message = "Invalid tailscale status payload"
        raise ValueError(message) from error


def advertises_exit_node(prefs: TailscalePrefs) -> bool:
    advertised = set(prefs.advertise_routes or [])
    return DEFAULT_ROUTE_V4 in advertised and DEFAULT_ROUTE_V6 in advertised


def _has_forwarding_warning(status: TailscaleStatus) -> bool:
    return any("IP forwarding is disabled" in warning for warning in status.health)


def get_dashboard_state(service_url: str) -> DashboardState:
    prefs = parse_prefs(_run_tailscale("debug", "prefs"))
    status = parse_status(_run_tailscale("status", "--json"))
    self_node = status.self_node
    return DashboardState(
        machine_name=self_node.host_name,
        dns_name=self_node.dns_name,
        tailnet_ip=self_node.tailscale_ips[0],
        advertises_exit_node=advertises_exit_node(prefs),
        has_forwarding_warning=_has_forwarding_warning(status),
        admin_console_url=ADMIN_CONSOLE_URL,
        service_url=service_url,
    )


def set_exit_node_advertising(action: Literal["enable", "disable"]) -> None:
    target = "true" if action == "enable" else "false"
    _ = _run_tailscale("set", f"--advertise-exit-node={target}")
