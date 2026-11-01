from __future__ import annotations

from html import escape
import os
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.tailscale_client import get_dashboard_state, set_exit_node_advertising

if TYPE_CHECKING:
    from app.models import DashboardState

SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:8094")
app = FastAPI()


def _status_badge(state: DashboardState) -> str:
    if state.advertises_exit_node:
        return '<span class="badge badge-on">Advertising exit node</span>'
    return '<span class="badge badge-off">Not advertising</span>'


def _warning_block(state: DashboardState) -> str:
    if not state.has_forwarding_warning:
        return ""
    return (
        '<section class="card warning">'
        '<p class="eyebrow">Attention</p>'
        "<h2>Kernel forwarding still needs attention</h2>"
        "<p>"
        "Tailscale is warning that IP forwarding is disabled. Exit-node traffic will not work "
        "correctly until that is fixed on this host."
        "</p>"
        "</section>"
    )


def _action_copy(state: DashboardState) -> tuple[str, str]:
    if state.advertises_exit_node:
        return ("disable", "Stop advertising exit node")
    return ("enable", "Start advertising exit node")


def render_dashboard(state: DashboardState) -> str:
    action, label = _action_copy(state)
    badge = _status_badge(state)
    warning = _warning_block(state)
    machine_name = escape(state.machine_name)
    dns_name = escape(state.dns_name)
    tailnet_ip = escape(state.tailnet_ip)
    service_url = escape(state.service_url)
    admin_url = escape(state.admin_console_url)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>example-host Tailscale Control</title>
    <meta name="description" content="Tailnet-only Tailscale exit-node control for example-host.">
    <style>
      :root {{
        color-scheme: dark;
        --surface-primary: #0b0d12; --surface-secondary: #11151d; --surface-elevated: #181d27;
        --text-primary: #f5f7fb; --text-secondary: #b9c3d4; --text-tertiary: #8b95a7;
        --border-default: #232b38; --border-subtle: #1a2230; --accent-primary: #6f81ff;
        --accent-hover: #8292ff; --status-success: #34c97b; --status-warning: #f1b54d;
        --status-error: #ff6b6b; --shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0; min-height: 100dvh; font-family: Inter, system-ui, sans-serif;
        background: radial-gradient(circle at top, #151a24 0, var(--surface-primary) 44%);
        color: var(--text-primary);
      }}
      a {{ color: var(--text-primary); }}
      .shell {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 48px; }}
      .hero {{ display: grid; gap: 18px; margin-bottom: 24px; }}
      .eyebrow {{
        margin: 0; color: var(--text-tertiary); font-size: 11px; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase;
      }}
      h1, h2, p {{ margin: 0; }}
      h1 {{ font-size: clamp(2rem, 4vw, 2.5rem); line-height: 1.05; }}
      .lede {{ max-width: 58ch; color: var(--text-secondary); font-size: 15px; line-height: 1.6; }}
      .layout {{ display: grid; gap: 16px; }}
      .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; }}
      .card {{
        background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015));
        border: 1px solid var(--border-default); border-radius: 16px; padding: 20px;
        box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.04);
      }}
      .card h2 {{ font-size: 1.1rem; margin-top: 10px; margin-bottom: 8px; }}
      .metric {{ font-size: 1.1rem; font-weight: 600; word-break: break-word; }}
      .muted {{ color: var(--text-secondary); font-size: 13px; line-height: 1.5; }}
      .badge {{
        display: inline-flex; align-items: center; gap: 8px; border-radius: 999px;
        padding: 8px 12px; border: 1px solid var(--border-default); font-size: 13px; font-weight: 600;
      }}
      .badge-on {{ color: #dff8ea; background: rgba(52,201,123,0.14); border-color: rgba(52,201,123,0.35); }}
      .badge-off {{ color: #e7ebf4; background: rgba(255,255,255,0.04); }}
      .warning {{ border-color: rgba(241,181,77,0.35); background: rgba(241,181,77,0.08); }}
      .actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; }}
      button, .link-button {{
        min-height: 44px; padding: 0 16px; border-radius: 12px; font: inherit; font-weight: 650;
        transition: transform 140ms ease-out, background-color 140ms ease-out, border-color 140ms ease-out;
      }}
      button {{
        border: 1px solid transparent; background: var(--accent-primary); color: white; cursor: pointer;
      }}
      button:hover, button:focus-visible {{ background: var(--accent-hover); transform: translateY(-1px); }}
      .link-button {{
        display: inline-flex; align-items: center; justify-content: center; text-decoration: none;
        border: 1px solid var(--border-default); background: rgba(255,255,255,0.02); color: var(--text-primary);
      }}
      .link-button:hover, .link-button:focus-visible {{ border-color: #394355; transform: translateY(-1px); }}
      .footer {{ margin-top: 12px; color: var(--text-tertiary); font-size: 13px; }}
      @media (prefers-reduced-motion: reduce) {{
        button, .link-button {{ transition: none; }}
        button:hover, button:focus-visible, .link-button:hover, .link-button:focus-visible {{ transform: none; }}
      }}
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <p class="eyebrow">Tailnet control</p>
        <h1>{machine_name}</h1>
        <p class="lede">
          Tailnet-only control panel for this host's exit-node advertising state. The UI is served
          through Tailscale and the backend uses local Tailscale operator permissions instead of a
          shared sudo password.
        </p>
        {badge}
      </section>
      <section class="layout">
        <div class="summary">
          <section class="card">
            <p class="eyebrow">Hostname</p>
            <h2>Tailnet DNS</h2>
            <p class="metric">{dns_name}</p>
          </section>
          <section class="card">
            <p class="eyebrow">Tailnet IP</p>
            <h2>IPv4</h2>
            <p class="metric">{tailnet_ip}</p>
          </section>
          <section class="card">
            <p class="eyebrow">Service URL</p>
            <h2>HTTPS endpoint</h2>
            <p class="metric"><a href="{service_url}">{service_url}</a></p>
          </section>
        </div>
        <section class="card">
          <p class="eyebrow">Exit node</p>
          <h2>Advertising control</h2>
          <p class="muted">
            This toggles whether <span style="font-family: 'JetBrains Mono', monospace;">{machine_name}</span>
            advertises itself as an exit node to the tailnet.
          </p>
          <div class="actions">
            <form method="post" action="/toggle">
              <input type="hidden" name="action" value="{action}">
              <button type="submit">{label}</button>
            </form>
            <a class="link-button" href="{admin_url}" target="_blank" rel="noreferrer">Open admin console</a>
          </div>
        </section>
        {warning}
        <p class="footer">Refresh this page after making admin-console approvals if your tailnet requires them.</p>
      </section>
    </main>
  </body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    state = get_dashboard_state(service_url=SERVICE_URL)
    return HTMLResponse(render_dashboard(state))


@app.post("/toggle")
async def toggle(
    request: Request,
    action: Annotated[Literal["enable", "disable"], Form()],
) -> RedirectResponse:
    set_exit_node_advertising(action=action)
    redirect_target = request.url_for("index")
    return RedirectResponse(url=str(redirect_target), status_code=303)
