from datetime import datetime

def normalize_row(row):
    row = dict(row)  # RowMapping → dict

    for key, value in row.items():
        if isinstance(value, datetime):
            row[key] = value.isoformat()

    return row
