from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TailscalePrefs(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, populate_by_name=True)

    advertise_routes: list[str] | None = Field(alias="AdvertiseRoutes")


class TailscaleSelf(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, populate_by_name=True)

    host_name: str = Field(alias="HostName")
    dns_name: str = Field(alias="DNSName")
    tailscale_ips: list[str] = Field(alias="TailscaleIPs")

    @field_validator("dns_name")
    @classmethod
    def normalize_dns_name(cls, value: str) -> str:
        return value.rstrip(".")


class TailscaleStatus(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, populate_by_name=True)

    self_node: TailscaleSelf = Field(alias="Self")
    health: list[str] = Field(alias="Health", default_factory=list)


class DashboardState(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    machine_name: str
    dns_name: str
    tailnet_ip: str
    advertises_exit_node: bool
    has_forwarding_warning: bool
    admin_console_url: str
    service_url: str
