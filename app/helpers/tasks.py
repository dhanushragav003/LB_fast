from datetime import datetime
from zoneinfo import ZoneInfo

def convert_to_utc(hour: int, minute: int, time_zone: str):
    now_local = datetime.now(ZoneInfo(time_zone))

    local = now_local.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
    )
    scheduled_utc = local.astimezone(ZoneInfo("UTC"))
    return scheduled_utc.hour, scheduled_utc.minute

def build_cron_expression(time_str, frequency, time_zone=None):
    parts = time_str.split(":")
    hour = parts[0]
    minute = parts[1]-1
    if time_zone:
        hour , minute  = convert_to_utc(hour,minute,time_zone)
    if frequency == "everyday":
        cron = f"{minute} {hour} * * *"
    elif frequency == "everyweekday":
        cron = f"{minute} {hour} * * 1-5"
    else:
        raise ValueError("Unsupported frequency")
    return cron

