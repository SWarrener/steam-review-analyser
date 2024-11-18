import json
import requests
import pandas as pd

df = pd.read_csv("data.csv")

# Add new columns to the database if we don't have them.
if "total_reviews" not in df.columns.to_list():
    review_columns = ["total_reviews", "positive_reviews", "negative_reviews", "review_desc", "review_score"]
    df = df.reindex(df.columns.to_list() + review_columns, axis=1)
    df["review_desc"] = df["review_desc"].fillna("Unknown")
    df = df.fillna(0)
    df = df.astype(dtype={
        "appid":"str",
        "name":"str",
        "total_reviews": "int",
        "positive_reviews": "int",
        "negative_reviews": "int",
        "review_desc": "str",
        "review_score": "int"
    })

try:
    with open("lastidx.txt", "r", encoding="utf-8-sig") as f:
        last_id = int(f.read().strip())
except FileNotFoundError:
    last_id = 0

params = { # The mixed types is intentional, Valve do it this way
    "language": "all",
    "purchase_type": "all",
    "num_per_page": "0", # Stops getting any individual reviews as we don't care about them
    "filter_offtopic_activity": 0
}

for i in df.index:
    if "Unknown" not in df["review_desc"].tolist():
        break
    if i < last_id:
        continue
    appid = df.at[i,"appid"]
    req = requests.get(f"https://store.steampowered.com/appreviews/{appid}?json=1", params=params, timeout=5)
    req.encoding = "utf-8"
    data = json.loads(req.text)["query_summary"]
    df.iloc[i, 2:7] = {
        "total_reviews": data["total_reviews"],
        "positive_reviews": data["total_positive"], 
        "negative_reviews": data["total_negative"],
        "review_desc": data["review_score_desc"], 
        "review_score": data["review_score"]
    }

    if i % 200 == 0:
        df.to_csv("data.csv", index=False)
        with open("lastidx.txt", "w", encoding="utf-8-sig") as f:
            f.write(str(i))
        print(f"Reached index {i}")

# Find the index which marks the change between DLC and games, add an
# identifier in a new column.
if "Type" not in df.columns.to_list():
    prev_id = 0
    for i in df.index:
        cur_id = df.at[i,"appid"]
        if cur_id < prev_id:
            change_idx = i
            break
        prev_id = cur_id

    df.loc[df.index < change_idx, "Type"] = "DLC"
    df.loc[df.index >= change_idx, "Type"] = "Game"

df.to_csv("data.csv", index=False)