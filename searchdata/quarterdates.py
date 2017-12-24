from datetime import datetime
from pytz import timezone

class quarter:
    def __init__(self, season, year, begin, end):
        self.season = season
        self.year = year
        self.begin = begin
        self.end = end

quarters = []

f17 = quarter("Fall", "2017", datetime.strptime("2017-09-25", "%Y-%m-%d").astimezone(timezone('US/Pacific')), datetime.strptime("2017-12-15", "%Y-%m-%d").astimezone(timezone('US/Pacific')))
w18 = quarter("Winter", "2018", datetime.strptime("2018-01-03", "%Y-%m-%d").astimezone(timezone('US/Pacific')), datetime.strptime("2018-03-23", "%Y-%m-%d").astimezone(timezone('US/Pacific')))
sp18 = quarter("Spring", "2018", datetime.strptime("2018-03-28", "%Y-%m-%d").astimezone(timezone('US/Pacific')), datetime.strptime("2018-06-15", "%Y-%m-%d").astimezone(timezone('US/Pacific')))
##su18 = quarter("Summer", "2018",)

quarters.append(f17)
quarters.append(w18)
quarters.append(sp18)
##quarters.append(su18)