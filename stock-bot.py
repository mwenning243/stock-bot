import sqlite3
import robin_stocks.robinhood as robin
import datetime
import time

db = sqlite3.connect("stocks.db")

cur = db.cursor()

create = """
    create table if not exists logs(
    i integer primary key autoincrement,
    ticker text not null,
    action integer not null,
    price real not null,
    trade integer not null,
    time timestamp not null
    );
"""
cur.execute(create)

def has_been_recently_traded(ticker):
    select = """
        select * from logs
        where ticker = ? and time > datetime('now', '-1 day', '-1 hour');
    """
    cur.execute(select, (ticker, ))
    rows = cur.fetchall()
    return len(rows) > 0

def insert_action(ticker, action, price):
    day_trade = has_been_recently_traded(ticker)
    insert = """
        insert into logs(ticker, action, price, trade, time)
        values(?, ?, ?, ?, datetime('now'));
    """
    cur.execute(insert, (ticker, action, price, day_trade))
    db.commit()
    print(str(action) + " " + ticker + " for " + str(price) + "    day_trade = " + str(day_trade))

def get_num_day_trades():
    select = """
        select * from logs
        where time > datetime('now', '-7 days', '-1 hour')
        and trade = 1;
    """
    cur.execute(select)
    rows = cur.fetchall()
    return len(rows)

def get_recent_info(ticker):
    select = """
        select * from logs
        where ticker = ?;
    """
    cur.execute(select, (ticker, ))
    rows = cur.fetchall()
    return rows

def show_table():
    select = """
        select * from logs;
    """
    cur.execute(select)
    rows = cur.fetchall()
    print("-------------")
    for row in rows:
        print(row)
    print("-------------")

def get_recent_price(ticker):
    return float(robin.stocks.get_latest_price(ticker)[0])

email = "XXXXX"
password = "XXXXX"

def login():
	robin.login(email, password, expiresIn=86400, by_sms=True)

def logout():
	robin.logout()

buy_mode = 0
sell_mode = 1

class watcher():
    def __init__(self, ticker):
        self.ticker = ticker
        self.recent_prices = []
        recent_info = get_recent_info(self.ticker)
        if len(recent_info) > 0:
            self.mode = recent_info[0][2] > 0
            self.price = recent_info[0][3] if self.mode == sell_mode else get_recent_price(self.ticker)
        else:
            self.mode = 0
            self.price = get_recent_price(self.ticker)
    
    def update_price(self):
        self.recent_prices.append(self.price)
        self.price = get_recent_price(self.ticker)
        if len(self.recent_prices) > 20:
            self.recent_prices.pop(0)

    def should_stock_be_bought(self):
        if (get_num_day_trades() > 2 and has_been_recently_traded(self.ticker)) or len(self.recent_prices) < 3:
            return False
        return self.price / max(self.recent_prices) < 0.98
    
    def should_stock_be_sold(self):
        if get_num_day_trades() > 2 and has_been_recently_traded(self.ticker):
            return False
        return self.price / get_recent_price(self.ticker) > 1.02
    
    def buy_stock(self):
        # robin.orders.order_buy_market(self.ticker, 1)
        self.price = get_recent_price(self.ticker)
        insert_action(self.ticker, 1, self.price)
        self.mode = sell_mode
        self.recent_prices = []

    def sell_stock(self):
        # robin.orders.order_sell_market(self.ticker, 1)
        self.price = get_recent_price(self.ticker)
        insert_action(self.ticker, -1, self.price)
        self.mode = buy_mode
        self.recent_prices = []

    def iterate(self):
        if self.mode == buy_mode:
            if self.should_stock_be_bought():
                self.buy_stock()
            self.update_price()
        else:
            if self.should_stock_be_sold():
                self.sell_stock()


login()

watchers = [watcher("XXXXX"), watcher("XXXXX"), watcher("XXXXX"), watcher("XXXXX")]
iteration = 0
while datetime.datetime.now().hour < 16:
    print("iteration " + str(iteration))
    for w in watchers:
        w.iterate()
    iteration = iteration + 1
    if iteration % 50 == 0:
        show_table()
    time.sleep(30)

show_table()
logout()
