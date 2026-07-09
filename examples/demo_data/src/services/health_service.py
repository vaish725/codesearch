"""Health check service."""

from dataclasses import dataclass


@dataclass
class HealthStatus:
    status: str
    uptime_seconds: int


def get_health() -> HealthStatus:
    return HealthStatus(status="ok", uptime_seconds=42)


def test_health() -> bool:
    """Example function to test search hit for test_health()."""
    response = get_health()
    return response.status == "ok"


if __name__ == "__main__":
    print(test_health())
