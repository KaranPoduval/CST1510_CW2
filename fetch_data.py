from pathlib import Path
import pandas as pd
import requests

# ---- Settings: the only part you change for your own data ----------------

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PARAMS = {
    "format": "geojson",
    "minmagnitude": 2.5,       # skip the thousands of tiny quakes nobody feels
    "orderby": "time",         # newest first
    # no "starttime" given, so USGS returns the last 30 days by default
}
RECORDS_KEY = "features"       # the list of quakes sits under "features"

RENAME = {
    "properties_time": "time",
    "properties_place": "place",
    "properties_mag": "mag",
    "properties_magType": "mag_type",
    "properties_sig": "sig",
    "properties_tsunami": "tsunami",
    "properties_alert": "alert",
    "properties_status": "status",
    "geometry_coordinates": "coordinates",
}
KEEP = ["time", "place", "mag", "mag_type", "latitude", "longitude",
        "depth", "sig", "tsunami", "alert", "status"]

MUST_HAVE = ["time", "mag", "latitude", "longitude"]                 # drop any row that is empty in these columns

RAW_FILE = Path(__file__).parent / "DATA" / "raw.csv"


def get_data(url, params):
    """Ask the API for data. Returns the JSON reply, or None if something went wrong."""
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()          # turns 404, 500 ... into an error
        return response.json()
    except requests.RequestException as error:
        print("Could not get the data:", error)
        return None


def make_table(data, records_key):
    """Turn the JSON reply into a pandas table."""
    records = data[records_key] if records_key else data
    return pd.json_normalize(records, sep="_")      # nested {"a": {"b": 1}} becomes column a_b


def tidy_data(df):
    """Rename, keep and clean the columns."""
    df = df.rename(columns=RENAME)
    df[["longitude", "latitude", "depth"]] = pd.DataFrame(df["coordinates"].tolist(), index=df.index)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df = df[KEEP]
    df = df.dropna(subset=MUST_HAVE)
    return df


def save_data(df, path):
    """Save the table as a CSV file."""
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    data = get_data(URL, PARAMS)
    if data is not None:
        table = make_table(data, RECORDS_KEY)
        table = tidy_data(table)
        print(table.head())
        save_data(table, RAW_FILE)

