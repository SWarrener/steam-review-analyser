import json
import requests
import pandas as pd

df = pd.read_csv("data.csv")

# Add new columns to the database if we don't have them.
if "time_series" not in df.columns.to_list():
    time_columns = ["review_start", "time_series"]
    df = df.reindex(df.columns.to_list() + time_columns, axis=1)
    df["review_start"] = df["review_start"].fillna(0)
    df["time_series"] = df["time_series"].fillna("Unknown")
    df = df.astype(dtype={
        "appid":"str",
        "name":"str",
        "total_reviews": "int",
        "positive_reviews": "int",
        "negative_reviews": "int",
        "review_desc": "str",
        "review_score": "int",
        "type": "str",
        "review_start": "int",
        "time_series": "object"
        })

try:
    relevant_df= pd.read_json("time_data.json")
except FileNotFoundError:
    relevant_df = df.loc[df["total_reviews"] >= 10]
    relevant_df = relevant_df.reindex()

try:
    with open("timelastidx.txt", "r", encoding="utf-8-sig") as f:
        last_id = int(f.read().strip())
except FileNotFoundError:
    last_id = 0

# Go through the df line by line getting the review data.
for i in relevant_df.index:
    if "Unknown" not in relevant_df["time_series"].tolist():
        break
    if i < last_id:
        continue
    appid = relevant_df.at[i,"appid"]
    req = requests.get(f"https://store.steampowered.com/appreviewhistogram/{appid}?l=all", timeout=5)
    req.encoding = "utf-8"
    data = json.loads(req.text)["results"]
    relevant_df.at[i,"review_start"] = int(data["start_date"])
    relevant_df.at[i,"time_series"] = data["rollups"]
    
    if i % 200 == 0: # Save every 200 games
        relevant_df.to_json("time_data.json", index=False)
        with open("timelastidx.txt", "w", encoding="utf-8-sig") as f:
            f.write(str(i))
        print(f"Reached index {i}")

relevant_df.to_json("time_data.json", index=False)

# For some newer games the time series isn't in months, will have to transform the data to deal with that
# In many games the time series skips over some months, I assume these are all zero, so will just fill them. 