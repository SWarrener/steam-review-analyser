import datetime as dt
import pandas as pd
from utils import MonthlyRecommends, MONTHS

df = pd.read_json("time_data.json")
tz = dt.UTC

# The steam review histogram shows the number of reviews for each month, with the month
# being identified by a string of the unix timestamp at midnight UCT on the 1st of each month
# However, some months with zero reviews are excluded. Any month before the game released is
# excluded.
# Earliest reviews are from October 2010.
# Any game less than 2 years old uses weekly steps instead of monthly.
# Games with few reviews, but less than 3 (?) years old use weeks, but only the weeks where there
# are reviews, and some empty weeks.
# It is necessary to process this data and normalise the data so all games are using monthly scales
# Where a week crosses two months reviews are assigned to a month in proportion to the number
# of days in that week which is in each month.
# Any month is identified by midnight UTC of the 1st of the month.
# Weeks are done with the week starting on the day of the week of the game's release, identified
# by midnight UTC for that day.


def check_weekly(data):
    timestamps = [dt.datetime.fromtimestamp(int(x["date"]),tz=tz) for x in data]
    deltas = [timestamps[n] - timestamps[n-1] for n in range(1,len(data))]
    if all(x == dt.timedelta(days=7) for x in deltas):
        return True
    return False


def move_weekly_data(data):
    date = data["date"]
    up, down = int(data["recommendations_up"]), int(data["recommendations_down"])
    timestamp = dt.datetime.fromtimestamp(int(date))
    six_days = timestamp + dt.timedelta(days=6)
    if timestamp.month == six_days.month:
        return (MonthlyRecommends(date, up, down),None)
    change_day = 0
    for i in range(1,7):
        new_date = timestamp+dt.timedelta(days=i)
        if timestamp.month != new_date.month:
            change_day = i
            break
    if change_day == 0:
        print("change date is 0, something has gone wrong")
    month1 = MonthlyRecommends(date, round(up*(change_day/7)), round(down*(change_day/7)))
    new_date = timestamp + dt.timedelta(days=change_day)
    month2 = MonthlyRecommends(int(new_date.timestamp()), round(up*((7-change_day)/7)),
                               round(down*((7-change_day)/7)))
    return (month1, month2)


def normalise_month_data(data):
    new_data = []
    timestamps = [int(x["date"]) for x in data]
    if all(x in MONTHS for x in timestamps):
        for date in MONTHS:
            if date in timestamps:
                monthly = data[timestamps.index(date)]
                new_data.append(
                    MonthlyRecommends(monthly["date"],
                                      int(monthly["recommendations_up"]),
                                      int(monthly["recommendations_down"])
                    )
                )
            else:
                new_data.append(MonthlyRecommends(date, 0, 0))
        return sorted(new_data)
    for point in data:
        month1, month2 = move_weekly_data(point)
        for month in (month1, month2):
            if month and month not in new_data:
                new_data.append(month)
            elif month:
                new_data[new_data.index(month)] += month
    for month in MONTHS:
        if month not in timestamps and month not in [int(x.get_date()) for x in new_data]:
            new_data.append(MonthlyRecommends(month, 0, 0))
    return sorted(new_data)


def normalise_review_start_data(date: int):
    if date not in MONTHS:
        date = max(month for month in MONTHS if month < date)
    return date


df["time_series"] = df["time_series"].apply(normalise_month_data)
df["review_start"] = df["review_start"].apply(normalise_review_start_data)

df.to_csv("normalised_data.csv", index=False)
