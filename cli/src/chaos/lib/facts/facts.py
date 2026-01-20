from pyinfra.api.facts import FactBase

class RamUsage(FactBase):
    """
    Returns the current RAM usage as a percentage.
    """

    def command(self):
        return "cat /proc/meminfo"

    def process(self, output):
        data = {}

        for line in output:
            parts = line.split(":")
            if len(parts) != 2:
                raise ValueError(f"Unexpected line format: {line}")

            key = parts[0].strip()
            try:
                value_kb = int(parts[1].strip().split()[0])
                data[key] = value_kb
            except ValueError:
                continue

        total_kb = data.get("MemTotal", 0)
        available_kb = data.get("MemAvailable")

        if available_kb is None:
            free_kb = data.get("MemFree", 0) + data.get("Buffers", 0) + data.get("Cached", 0)
            buffers_kb = data.get("Buffers", 0)
            cached_kb = data.get("Cached", 0)
            available_kb = free_kb + buffers_kb + cached_kb

        used_kb = total_kb - available_kb

        percent = 0.0
        if total_kb > 0:
            percent = (used_kb / total_kb) * 100

        return {
            "total_mb": round(total_kb / 1024, 2),
            "used_mb": round(used_kb / 1024, 2),
            "available_mb": round(available_kb / 1024, 2),
            "percent": round(percent, 1),
        }

class LoadAverage(FactBase):
    """
    Returns the system load averages for the past 1, 5, and 15 minutes.
    """
    def command(self) -> str:
        return "cat /proc/loadavg"

    def process(self, output):
        lines = list(output)
        if not lines:
            return [0.0, 0.0, 0.0]
        try:
            parts = lines[0].split()
            return [float(x) for x in parts[:3]]
        except (IndexError, ValueError):
            return [0.0, 0.0, 0.0]
