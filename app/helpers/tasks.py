def build_cron_expression(time_str, frequency, time_zone=None):
    # time_str format: "HH:MM" or "HH:MM:SS"
    parts = time_str.split(":")
    
    # ensure we have HH and MM
    hour = parts[0]
    minute = parts[1]

    # base: minute hour dom month dow
    if frequency == "everyday":
        cron = f"{minute} {hour} * * *"
    elif frequency == "everyweekday":
        cron = f"{minute} {hour} * * 1-5"
    else:
        raise ValueError("Unsupported frequency")

    if time_zone:
        cron = f"CRON_TZ={time_zone} {cron}"
    return cron
