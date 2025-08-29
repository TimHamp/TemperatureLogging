#!/usr/bin/env python3
from flask import Flask, jsonify
from datetime import datetime, timedelta
import os
import csv

app = Flask(__name__)

DATA_PATH = "/home/pi/conditions_log"

def read_last_row():
    csv_file = os.path.join(DATA_PATH, f"{datetime.now().strftime('%Y-%m-%d')}.csv")
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)
            if not rows:
                return None
            last = rows[-1]
            return row_to_dict(last)
    except Exception as e:
        return {"error": str(e)}

def read_last_24h():
    cutoff = datetime.now() - timedelta(hours=24)
    data = []

    try:
        # Collect data from today and yesterday’s file
        for days_back in (1, 0):
            filename = os.path.join(DATA_PATH, f"{(datetime.now()-timedelta(days=days_back)).strftime('%Y-%m-%d')}.csv")
            if not os.path.exists(filename):
                continue
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    ts = parse_timestamp(row[0], filename)
                    if ts and ts >= cutoff:
                        data.append(row_to_dict(row, ts))
    except Exception as e:
        return {"error": str(e)}

    return data

def parse_timestamp(timestr, filename):
    """Turn hh:mm:ss into a datetime with the date taken from the filename."""
    try:
        # Extract date from filename (YYYY-MM-DD.csv)
        basename = os.path.basename(filename).replace(".csv", "")
        file_date = datetime.strptime(basename, "%Y-%m-%d").date()
        t = datetime.strptime(timestr, "%H:%M:%S").time()
        return datetime.combine(file_date, t)
    except Exception:
        return None

def row_to_dict(row, ts=None):
    try:
        return {
            "timestamp": row[0],
            "datetime": ts.isoformat() if ts else None,
            "indoor_temp": float(row[1]),
            "indoor_humidity": float(row[2]),
            "kernel_temp": float(row[3]),
            "reserved": row[4],
            "outdoor_temp": float(row[5]),
            "outdoor_humidity": float(row[6]),
            "clouds": float(row[7]),
        }
    except Exception:
        return {"raw": row}

@app.route("/latest")
def latest():
    return jsonify(read_last_row())

@app.route("/last24h")
def last24h():
    return jsonify(read_last_24h())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
