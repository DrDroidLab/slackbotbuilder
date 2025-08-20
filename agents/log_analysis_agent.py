# (a) eyeball_logs(order_by=['desc','random'],limit=1000) 
# (b) analyse_logs(type=['grep','regex'],query,limit=1000)
# (c) see_in_context(query,limit=1000)
# (d) aggregate_counts()


def eyeball_logs(logs_data,order_by='desc',limit=1000):
    # other possibilities order_by --> random, ascending.
    pass

def filter_logs(logs_data,query,type='grep',limit=1000):
    # other possibilities type --> regex.
    pass

def see_in_context(logs_data,context_time,duration_before_after='1h',limit=1000):
    # this should filter for logs from context_time - duration_before_after to context_time + duration_before_after, with limit of 500 on each side.
    pass

def aggregate_counts(logs_data,type='count',window_size='5m',query=None):
    # this should just give count(logs), distributed by window_size and optionally filtered by query.
    pass