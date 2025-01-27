import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
from utils import MonthlyRecommends, MONTHS

TZ = dt.UTC
MAX_R = 9000000 # CS2 at about 8.8 million

# Turn the strings in the dataframe into my custom Object.
def fix_data(string):
    result = []
    for item in string.strip("[]").split(","):
        date = item[:item.find(":")]
        up = item[item.find("UP ")+3:item.find(" D")]
        down = item[item.find("DOWN ")+5:]
        result.append(MonthlyRecommends(date, int(up), int(down)))
    return result

# Helper function to import the data with the time series
def import_data():
    import_df = pd.read_csv("normalised_data.csv")
    import_df["time_series"] = import_df["time_series"].apply(fix_data)
    return import_df

# Replaces the positive review count from the data with the summed version from the time-series
# data, which effectively applies the "exclude non-steam purchases" option
def true_pos(data, date = dt.datetime.now(tz=TZ).timestamp()):
    return sum(x.up for x in data if int(x.date) < date)

# Replaces the total review count from the data with the summed version from the time-series
# data, which effectively applies the "exclude non-steam purchases" option
def true_total(data, date = dt.datetime.now(tz=TZ).timestamp()):
    return sum(x.up + x.down for x in data if int(x.date) < date)

# Creates the data for the review count graph. Creates buckets where the boundary for each
# bucket is 10x higher than the previous boundary (1, 10, 100, 1000...)
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

# Plots the steam review score against the number of reviews as a bar chart.
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

# Creates the data for the release steam review score by release month graph.
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

# Plots average steam review score against the release month of the game.
def plot_game_time_data(df, counts, type_ = "All", colour = "b", style = "o--"):
    df = df.loc[(df["total_reviews"] >= counts[0]) & (df["total_reviews"] < counts[1])]
    data = create_game_time_data(df, type_ = type_)
    dates = np.arange(np.datetime64('2010-10'), np.datetime64('2024-12'),
                  np.timedelta64(1, 'M'))
    scores = [x[1] for x in data]
    ax.plot(range(len(dates)), scores, colour+style, label=f"Games with between {counts[0]} and {counts[1]-1} reviews. ({len(df.index)} Games)")
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

# Plots a histogram of steam review scores, and prints some significant milestones
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

# Creates the data for avg review score by number of months since release
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

# Plots the steam review score against the number of months since the products release
def plot_review_score_over_time(df: pd.DataFrame):
    data = create_review_score_over_time(df)
    ax.plot(data, "b--")
    ax.set(xlabel="Months Since release", ylabel="Average Review score (monthly)",
        title="Avg Steam review score by number of months since release. Games with over 1000 reviews")

# Prints a list of how many games comprise each 10% of reviews.
def review_count_percentiles(df: pd.DataFrame):
    total = sum(df["total_reviews"])
    df = df.sort_values(by=["total_reviews"], ascending=False)
    for j in (0.1*x for x in range(1,10)):
        counter = 0
        for i, num in enumerate(df["total_reviews"]):
            counter += num
            if counter > total*j:
                print(f"{round(j*100)}% of reviews are for {i+1} games ({round((i+1)/len(df.index)*100,3)}% of all games)")
                break

# Create the data for review score by month of review graph
def create_all_reviews_by_month_data(df: pd.DataFrame):
    result = []
    series = df["time_series"]
    for i in range(len(MONTHS)):
        total, pos = 0, 0
        for x in series:
            month = x[i]
            total += month.total
            pos += month.up
        result.append((pos/total)*100)
    return result

# Plots steam review score by the month of the review being made.
def plot_all_reviews_by_month(df: pd.DataFrame, colour = "b", style = "o--"):
    df["total_reviews"] = df["time_series"].apply(true_total)
    df = df.loc[df["total_reviews"] >= 0]
    scores = create_all_reviews_by_month_data(df)
    dates = np.arange(np.datetime64('2010-10'), np.datetime64('2024-12'),
                  np.timedelta64(1, 'M'))
    ax.plot(range(len(dates)), scores, colour+style, label=f"{len(df.index)} Games")
    ax.set(xlabel="Month", ylabel="Review score (% reviews positive)",
        title="Steam review score by month of review")
    coeff = np.polyfit(range(len(dates)), scores, 2)
    ax.plot(range(len(dates)), np.polyval(coeff, range(len(dates))), colour)
    ax.xaxis.set_ticks(range(len(dates)))
    ax.xaxis.set_ticklabels(dates)
    ax.xaxis.set_major_locator(tkr.MultipleLocator(6))
    ax.xaxis.set_minor_locator(tkr.MultipleLocator(1))

# Time df has the time-series data, but makes the program take much longer to run,
# so use simple_df if you don't need it.
# time_df = import_data()
# simple_df = pd.read_csv("data.csv")

# Uncomment these two lines if you want to exclude non-steam reviews.
# df["positive_reviews"] = df["time_series"].apply(true_pos)
# df["total_reviews"] = df["time_series"].apply(true_total)

fig, ax = plt.subplots()

# Graphs for Game/DLC/All reviews by number of reviews
# simple_df = simple_df.loc[(df["total_reviews"] > 0) & (simple_df["total_reviews"] < 1000000)]
# plot_review_count_graph(simple_df, x_off=-50, y_off=5)
# plot_review_count_graph(simple_df, colour = "r", style="x", type_ = "Game",  x_off=5, y_off=0)
# plot_review_count_graph(simple_df, colour = "g", style="x", type_ = "DLC", y_off=5)

# Graphs for game review score by release date
# plot_game_time_data(time_df, (10, 1000)) # total_reviews >= 10
# plot_game_time_data(time_df, (100, 1000), colour="r", style="x--")
# plot_game_time_data(time_df, (1000, 10000), colour="g", style="x--")
# plot_game_time_data(time_df, (10000, 10000000), colour="y", style="x--")

# Histogram of review scores
# plot_review_histogram(simple_df, (10, 1000))
# plot_review_histogram(simple_df, (1000, 10000000))

# Monthly review score by months since release date
# plot_review_score_over_time(time_df)

# Number of games by percentile of reviews
# review_count_percentiles(simple_df)

# Review score across all games by month of review being made.
# plot_all_reviews_by_month(time_df)

# Other ideas:
    # Some more complex stat stuff?
    # Tidy everything up and add some doc strings.
    # Make a github pages showing everything in a neat fashion.

ax.legend()
plt.show()
