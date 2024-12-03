import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
from utils import MonthlyRecommends, MONTHS

TZ = dt.UTC
MAX_R = 9000000 # CS2 at about 8.8 million

def fix_data(string):
    result = []
    for item in string.strip("[]").split(","):
        date = item[:item.find(":")]
        up = item[item.find("UP ")+3:item.find(" D")]
        down = item[item.find("DOWN ")+5:]
        result.append(MonthlyRecommends(date, int(up), int(down)))
    return result


def import_data():
    import_df = pd.read_csv("normalised_data.csv")
    import_df["time_series"] = import_df["time_series"].apply(fix_data)
    return import_df


def true_pos(data, date = dt.datetime.now(tz=TZ).timestamp()):
    return sum(x.up for x in data if int(x.date) < date)


def true_total(data, date = dt.datetime.now(tz=TZ).timestamp()):
    return sum(x.up + x.down for x in data if int(x.date) < date)


def create_review_count_data(df, step = 1, multiplier = 10, type_ = "All"):
    results = []
    if type_ != "All":
        df = df.loc[df["type"] == type_]
    while step < MAX_R:
        next_ = step * multiplier
        temp_df = df.loc[(df["total_reviews"] >= step) & (df["total_reviews"] < next_)]
        count = len(temp_df.index)
        if count == 0:
            break
        reviews = sum(temp_df["total_reviews"])
        review_score = (sum(temp_df.at[i,"positive_reviews"]/temp_df.at[i,"total_reviews"]
                            for i in temp_df.index)/len(temp_df.index))*100
        results.append((reviews, count, review_score, f"{step:,} - {next_-1:,}"))
        step = next_
    # Add in the data for zero reviews, and use the first review score to make the data look neat
    temp_df = df.loc[(df["total_reviews"] == 0)]
    reviews = sum(temp_df["total_reviews"])
    count = len(temp_df.index)
    results.insert(0,[reviews, count, results[0][2], "0"])
    return results


def plot_review_count_graph(df, colour = "b", style = "o", type_ = "All", x_off=1, y_off=0):
    data = create_review_count_data(df, type_=type_)
    ax.plot([x[3] for x in data], [x[2] for x in data], colour+style)
    ax.set(xlabel="Number of reviews", ylabel="Mean review score (% reviews positive for each game)",
        title="Avg Steam review score by number of reviews")
    for y in data:
        ax.annotate(f"{type_}: {y[1]:,}",
                    xy=(y[3], y[2]), xycoords="data",
                    xytext=(x_off,y_off), textcoords="offset points",
                    color=colour)


def create_game_time_data(df, type_ = "All"):
    results = []
    if type_ != "All":
        df = df.loc[df["type"] == type_]
    for month in MONTHS:
        temp_df = df.loc[df["review_start"] == month]
        count = len(temp_df.index)
        if count == 0:
            review_score = np.nan
        else:
            review_score = (sum(temp_df.at[i,"positive_reviews"]/temp_df.at[i,"total_reviews"]
                            for i in temp_df.index)/len(temp_df.index))*100
        results.append((count, review_score))
    return results


def plot_game_time_data(df, counts, type_ = "All", colour = "b", style = "o--"):
    df = df.loc[(df["total_reviews"] >= counts[0]) & (df["total_reviews"] < counts[1])]
    number = len(df.index)
    data = create_game_time_data(df, type_ = type_)
    dates = np.arange(np.datetime64('2010-10'), np.datetime64('2024-12'),
                  np.timedelta64(1, 'M'))
    scores = [x[1] for x in data]
    ax.plot(range(len(dates)), scores, colour+style, label=f"Games with between {counts[0]} and {counts[1]-1} reviews. ({number} Games)")
    ax.set(xlabel="Steam Release Month", ylabel="Mean review score (% reviews positive for each game)",
        title="Avg Steam review score by release month")
    while np.nan in scores: # Messy, but only affects 2 out of ~180 values so no real impact
        i = scores.index(np.nan)
        if i == len(scores) - 1:
            scores[i] = scores[i-1]
        else:
            scores[i] = (scores[i+1]+scores[i-1])/2
    coeff = np.polyfit(range(len(dates)), scores, 2)
    ax.plot(range(len(dates)), np.polyval(coeff, range(len(dates))), colour)
    ax.xaxis.set_ticks(range(len(dates)))
    ax.xaxis.set_ticklabels(dates)
    ax.xaxis.set_major_locator(tkr.MultipleLocator(6))
    ax.xaxis.set_minor_locator(tkr.MultipleLocator(1))


def plot_review_histogram(df, range_):
    df = df.loc[(df["total_reviews"] >= range_[0]) & (df["total_reviews"] < range_[1])]
    review_scores = [(df.at[i,"positive_reviews"]/df.at[i,"total_reviews"])*100 for i in df.index]
    counts, bins = np.histogram(review_scores, np.arange(1, 101))
    total = sum(counts)
    milestones = (10,25,50,75,90)
    cumsum = np.cumsum(counts)
    sig_ranges = "\n"
    for i in milestones:
        per = total * i/100
        high = max(x for x in cumsum if x <= per)
        idx = list(cumsum).index(high)
        sig_ranges += f"{i}th percentile is {bins[idx]}% positive\n"
    ax.hist(bins[:-1], bins, weights=counts, histtype="bar", rwidth=0.90, cumulative=True, density=True,
            label=f"Games with between {range_[0]} and {range_[1]-1} reviews. ({total} Games)" + sig_ranges)
    ax.set(xlabel="Percent of positive reviews",
           ylabel="Cumulative Probability (% of games with a score lower than x)",
           title="CDF of positive review percentages of steam games")


def create_review_score_over_time(df: pd.DataFrame):
    df = df.loc[df["total_reviews"] >= 1000]
    deltas = {x: [] for x in range(145)}
    for i in df.index:
        series = [x for x in df.at[i, "time_series"] if int(x.get_date()) >= df.at[i, "review_start"]]
        for idx, month in enumerate(series):
            if idx > 144: #12 years, to avoid the last values being skewed by the small sample size of older games
                break
            score = month.get_score()
            if score:
                deltas[idx].append(score)
    return [sum(v)/len(v) for v in deltas.values()]


def plot_review_score_over_time(df: pd.DataFrame):
    data = create_review_score_over_time(df)
    ax.plot(data, "b--")
    ax.set(xlabel="Months Since release", ylabel="Average Review score (monthly)",
        title="Avg Steam review score by number of months since release. Games with over 1000 reviews")

time_df = import_data()

#simple_df = pd.read_csv("data.csv")

#df["positive_reviews"] = df["time_series"].apply(true_pos)
#df["total_reviews"] = df["time_series"].apply(true_total)

#df = df.loc[(df["total_reviews"] > 0) & (df["total_reviews"] < 1000000)]

fig, ax = plt.subplots()

# Graphs for Game/DLC/All reviews by number of reviews
#plot_review_count_graph(simple_df, x_off=-50, y_off=5)
#plot_review_count_graph(simple_df, colour = "r", style="x", type_ = "Game",  x_off=5, y_off=0)
#plot_review_count_graph(simple_df, colour = "g", style="x", type_ = "DLC", y_off=5)

#plot_game_time_data(time_df, (10, 1000)) # total_reviews >= 10
#plot_game_time_data(time_df, (100, 1000), colour="r", style="x--")
#plot_game_time_data(time_df, (1000, 10000), colour="g", style="x--")
#plot_game_time_data(time_df, (10000, 10000000), colour="y", style="x--")

#plot_review_histogram(simple_df, (10, 1000))
#plot_review_histogram(simple_df, (1000, 10000000))

plot_review_score_over_time(time_df)

ax.legend()
plt.show()
