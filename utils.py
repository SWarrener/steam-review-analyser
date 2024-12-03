import datetime as dt

pre_zero = lambda x: f"0{x}" if x < 10 else f"{x}"
string_dates = [f"{year}-{pre_zero(x)}-01T00:00:00Z" for year in range(2011,dt.date.today().year)
                for x in range(1,13)] # Add the full years
string_dates += [f"2010-{pre_zero(x)}-01T00:00:00Z" for x in range(10,13)] # Add end of 2010
string_dates += [f"{dt.date.today().year}-{pre_zero(x)}-01T00:00:00Z" # Add the months of this year
                 for x in range(1,dt.date.today().month)] # including the current one TODO (add +1 back in when sharing code)

MONTHS = sorted([int(dt.datetime.fromisoformat(date).timestamp()) for date in string_dates])

class MonthlyRecommends:

    def __init__(self, date: str, up: int, down: int):
        if int(date) in MONTHS:
            self.date = str(date)
        else:
            self.date = str(max(month for month in MONTHS if month < int(date)))
        self.up = up
        self.down = down
        self.total = up + down
        self.year = dt.datetime.fromtimestamp(int(self.date),tz=dt.UTC).year
        self.month = dt.datetime.fromtimestamp(int(self.date),tz=dt.UTC).month

    def __eq__(self, other):
        if not isinstance(other, MonthlyRecommends):
            return False
        return self.date == other.date

    def __lt__(self, other):
        if not isinstance(other, MonthlyRecommends):
            return False
        return int(self.date) < int(other.date)

    def __add__(self, other):
        if not isinstance(other, MonthlyRecommends) or self.date != other.date:
            return NotImplementedError
        return MonthlyRecommends(self.date, self.up+other.up, self.down+other.down)

    def __repr__(self) -> str:
        return f"{self.date}: UP {self.up} DOWN {self.down}"

    def get_date(self):
        return self.date

    def get_year(self):
        return self.year

    def get_month(self):
        return self.month

    def get_score(self):
        if self.total > 0:
            return (self.up / self.total) * 100
        return None
