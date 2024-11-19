import json
import pandas as pd


def get_data(app_list: list, filename: str, filecount: int):
    for i in range(filecount):
        with open(f"{filename}{i}.json", "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            app_list += data["response"]["apps"]
    return app_list


apps = get_data([], "DLCdata", 5)
apps = get_data(apps, "gamedata", 12)

df = pd.DataFrame(data=apps, columns=["appid", "name"])

df.to_csv("data.csv", index=False)
