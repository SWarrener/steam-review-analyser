# https://store.steampowered.com/appreviews/881100?json=1&language=all&purchase_type=all # This gets number of reviews, pos and neg

# https://store.steampowered.com/appreviewhistogram/881100?l=all # review histogram

# https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json For the list of games.
# Can filter out playtest and demo relatively easily, not sure about DLC.

# https://api.steampowered.com/IStoreService/GetAppList/v1/
# See here for details https://steamapi.xpaw.me/#IStoreService/GetAppList

# Compare review score for all reviews and steam purchases only as histogram is steam purchases only

from argparse import ArgumentParser
import json
import sys
import requests

# Get the request and return it.
def make_request(params):
    req = requests.get("https://api.steampowered.com/IStoreService/GetAppList/v1/",
                       params=params, timeout=5)
    req.encoding = "utf-8"

    return req

# Make files for each JSON request we get back, each file should have 10k results in it.
def store_data(params, filename):
    counter = 0

    finished = False

    while not finished:
        req = make_request(params)
        with open(f"{filename}{str(counter)}.json", "+w", encoding="utf-8") as f:
            f.write(req.text)
        counter += 1
        data = json.loads(req.text)
        # have_more_results is true if there are and non-existant if there aren't
        if "have_more_results" in data["response"].keys():
            last_id = data["response"]["last_appid"]
            params["last_appid"] = last_id
        else:
            finished = True


def __main__():

    parser = ArgumentParser()

    parser.add_argument(
        "-k",
        "--key",
        action="store",
        dest="key",
        default="",
        help="REQUIRED: Your steam API key"
    )

    args = parser.parse_args()
    apikey = args.key

    if apikey == "":
        print("ERROR: API credentials must be supplied.")
        sys.exit()

    store_data({"key": apikey}, "gamedata")
    store_data({"key": apikey, "include_games": False, "include_dlc": True}, "DLCdata")
