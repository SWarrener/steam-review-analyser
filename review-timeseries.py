import json
import requests
import pandas as pd

df = pd.read_csv("data.csv")

if "time_series" not in df.columns.to_list():
    time_columns = ["release_month", "time_series"]
    df = df.reindex(df.columns.to_list() + time_columns, axis=1)
    df["release_month"] = df["release_month"].fillna(0)
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
        "release_month": "int",
        "time_series": "object"
        })

try:
    relevant_df= pd.read_csv("time_data.csv")
except FileNotFoundError:
    relevant_df = df.loc[df["total_reviews"] >= 10]
    relevant_df = relevant_df.reindex()

try:
    with open("timelastidx.txt", "r", encoding="utf-8-sig") as f:
        last_id = int(f.read().strip())
except FileNotFoundError:
    last_id = 0

for i in relevant_df.index:
    if "Unkown" not in relevant_df["time_series"].tolist():
        break
    if i < last_id:
        continue
    appid = relevant_df.at[i,"appid"]
    req = requests.get(f"https://store.steampowered.com/appreviewhistogram/{appid}?l=all", timeout=5)
    req.encoding = "utf-8"
    data = json.loads(req.text)["results"]
    relevant_df.at[i,"release_month"] = int(data["start_date"])
    relevant_df.at[i,"time_series"] = data["rollups"]
    
    if i % 200 == 0:
        relevant_df.to_csv("time_data.csv", index=False)
        with open("timelastidx.txt", "w", encoding="utf-8-sig") as f:
            f.write(str(i))
        print(f"Reached index {i}")

relevant_df.to_csv("time_data.csv", index=False)

# For some newer games the time series isn't in months, will have to transform the data to deal with that
# In many games the time series skips over some months, I assume these are all zero, so will just fill them. 