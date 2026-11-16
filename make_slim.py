import os

import pandas as pd

SRC = "label/labeled_rides.csv"
OUT = "label/app_rides.csv"

df = pd.read_csv(SRC, encoding="utf-8-sig")
slim = pd.DataFrame({
    "map_name": df["map_name"],
    "match_id": pd.factorize(df["match_id"])[0],
    "vehicle": df["vehicle"],
    "elapsed_time": df["elapsed_time"].round(1),
    "nearest_dist_m": df["nearest_dist_m"].round(1),
    "created_at": pd.to_datetime(df["created_at"], errors="coerce").dt.strftime("%Y-%m-%d"),
    "x": df["x"].round().astype(int),
    "y": df["y"].round().astype(int),
})
slim.to_csv(OUT, index=False, encoding="utf-8-sig")

before = os.path.getsize(SRC) / 1024 / 1024
after = os.path.getsize(OUT) / 1024 / 1024
print(f"{SRC}: {before:.1f}MB")
print(f"{OUT}: {after:.1f}MB ({len(slim):,}건)")
