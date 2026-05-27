import psutil
from datetime import datetime, timezone


def get_system_metrics() -> dict:
    """Return real system metrics from psutil."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    uptime_seconds = (datetime.now(timezone.utc) - boot_time).total_seconds()

    return {
        "cpu_usage": round(cpu, 1),
        "memory_usage": round(mem.percent, 1),
        "memory_used_mb": round(mem.used / 1024 / 1024, 1),
        "memory_total_mb": round(mem.total / 1024 / 1024, 1),
        "disk_usage": round(disk.percent, 1),
        "uptime_seconds": int(uptime_seconds),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
