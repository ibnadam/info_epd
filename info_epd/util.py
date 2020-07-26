import datetime


def secs_til_midnight():
    tomorrow = datetime.datetime.now() + datetime.timedelta(1)
    midnight = datetime.datetime(year=tomorrow.year, month=tomorrow.month, 
                                 day=tomorrow.day, hour=0, minute=0, second=0)
    return (midnight - datetime.datetime.now()).seconds

def get_today():
    return datetime.date.today()

def get_tomorrow():
    return get_today() + datetime.timedelta(days=1)

def get_now():
    return datetime.datetime.now()
