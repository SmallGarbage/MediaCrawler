import time


def get_unix_timestamp():
    return int(time.time())


def get_unix_time_from_time_str(time_str):
    try:
        format_str = "%Y-%m-%d %H:%M:%S"
        tm_object = time.strptime(str(time_str), format_str)
        return int(time.mktime(tm_object))
    except Exception as e:
        return 0
    pass


def get_current_timestamp() -> int:
    return int(time.time() * 1000)


def get_current_date() -> str:
    return time.strftime('%Y-%m-%d', time.localtime())
