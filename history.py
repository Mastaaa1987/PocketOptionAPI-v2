import time, math, asyncio, json, threading
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption
import pocketoptionapi.global_value as global_value
# import talib.abstract as ta
import numpy as np
import pandas as pd
#import freqtrade.vendor.qtpylib.indicators as qtpylib

global_value.loglevel = 'INFO'

# Session configuration
start_counter = time.perf_counter()

### REAL SSID Format::
#ssid = """42["auth",{"session":"a:4:{s:10:\\"session_id\\";s:32:\\"aa11b2345c67d89e0f1g23456h78i9jk\\";s:10:\\"ip_address\\";s:11:\\"11.11.11.11\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1234567890;}1234a5b678901cd2efghi34j5678kl90","isDemo":0,"uid":12345678,"platform":2}]"""
#demo = False

### DEMO SSID Format::
#ssid = """42["auth",{"session":"abcdefghijklm12nopqrstuvwx","isDemo":1,"uid":12345678,"platform":2}]"""
#demo = True

ssid = """42["auth",{"session":"abcdefghijklm12nopqrstuvwx","isDemo":1,"uid":12345678,"platform":2}]"""
demo = True

days = 365
min_payout = 80
period = 60
expiration = 60

pair_list = ["CADJPY_otc"]

api = PocketOption(ssid,demo)

# Connect to API
api.connect()


def get_payout():
    try:
        d = json.loads(global_value.PayoutData)
        for pair in d:
            # |0| |  1  |  |  2  |  |  3  | |4 | 5 |6 | 7 | 8| 9| 10 |11| 12| 13        | 14   | | 15,                                                                                                                                                                                     |  16| 17| 18        |
            # [5, '#AAPL', 'Apple', 'stock', 2, 50, 60, 30, 3, 0, 170, 0, [], 1743724800, False, [{'time': 60}, {'time': 120}, {'time': 180}, {'time': 300}, {'time': 600}, {'time': 900}, {'time': 1800}, {'time': 2700}, {'time': 3600}, {'time': 7200}, {'time': 10800}, {'time': 14400}], -1, 60, 1743784500],
            if len(pair) == 19:
                global_value.logger('id: %s, name: %s, typ: %s, active: %s' % (str(pair[1]), str(pair[2]), str(pair[3]), str(pair[14])), "DEBUG")
                #if pair[14] == True and pair[5] >= min_payout and "_otc" not in pair[1] and pair[3] == "currency":         # Get all non OTC Currencies with min_payout
                #if pair[14] == True and pair[5] >= min_payout and "_otc" in pair[1]:                                       # Get all OTC Markets with min_payout
                #if pair[14] == True and pair[3] == "cryptocurrency" and pair[5] >= min_payout and "_otc" not in pair[1]:   # Get all non OTC Cryptocurrencies
                #if pair[14] == True:                                                                                       # Get All that online
                if len(pair_list) > 0:
                    if pair[1] in pair_list:
                        p = {}
                        p['id'] = pair[0]
                        p['payout'] = pair[5]
                        p['type'] = pair[3]
                        global_value.pairs[pair[1]] = p
                else:
                    if pair[14] == True:
                        p = {}
                        p['id'] = pair[0]
                        p['payout'] = pair[5]
                        p['type'] = pair[3]
                        global_value.pairs[pair[1]] = p
                        break
        return True
    except:
        return False


def prepare():
    try:
        data = get_payout()
        if data: return True
        else: return False
    except:
        return False


def get_history():
    try:
        i = 0
        for pair in global_value.pairs:
            i += 1
            df = api.get_candles(pair, period)
            global_value.logger('%s (%s/%s)' % (str(pair), str(i), str(len(global_value.pairs))), "INFO")
            time.sleep(1)
        return True
    except:
        return False


def save_live_data():
    for pair in global_value.pairs:
        if 'history' in global_value.pairs[pair]:
            history = []
            history.extend(global_value.pairs[pair]['history'])
            df1 = pd.DataFrame(history).reset_index(drop=True)
            df1 = df1.sort_values(by='time').reset_index(drop=True)
            df1['time'] = pd.to_datetime(df1['time'], unit='s')
            df1.set_index('time', inplace=True)
            # df1.index = df1.index.floor('1s')

            df = df1['price'].resample(f'{period}s').ohlc()
            df.reset_index(inplace=True)
            df = df.loc[df['time'] < datetime.fromtimestamp(int(datetime.now().timestamp()) - int(datetime.now().second) + 60)]
            df['ts'] = df.time.values.astype(np.int64) // 10 ** 9
            if global_value.check_csv(pair, 'data'):
                csv = global_value.get_csv(pair, 'data')
                d = csv[1].split(',')[0]
                val = []
                for i in range(1, len(df)):
                    if int(df.loc[len(df)-i]['ts']) > int(d):
                        val.insert(0, {'time': df.loc[len(df)-i]['ts'], 'open': df.loc[len(df)-i]['open'], 'close': df.loc[len(df)-i]['close'], 'high': df.loc[len(df)-i]['high'], 'low': df.loc[len(df)-i]['low']})
                    else:
                        break
                if len(val) > 0:
                    if len(val) == 1:
                        val.insert(0, {'time': 0, 'open': 0, 'close': 0, 'high': 0, 'low': 0})
                    global_value.set_csv(pair, val)
                print(df.loc[len(df)-1]['time'], df.loc[len(df)-1]['ts'])
    return True


def save_history():
    I = 0
    for pair in global_value.pairs:
        offset = int(datetime.now().timestamp()) - int(datetime.utcnow().timestamp())
        time_start = int(datetime.now().timestamp()) + offset
        time_red = int(datetime.now().timestamp()) + offset - 86400 * days
        I += 1
        global_value.logger('! %s (%s/%s)' % (str(pair), str(I), str(len(global_value.pairs))), "INFO")
        if global_value.check_csv(pair, 'data'):
            csv = global_value.get_csv(pair, 'data')
            d = csv[1].split(',')[0]
            if int(d) < time_start:
                time_redd = int(d)
                df = api.get_history(pair, period, start_time=time_start, end_time=time_redd)
            if csv[len(csv)-1] == '': c = csv[len(csv)-2].split(',')[0]
            else: c = csv[len(csv)-1].split(',')[0]
            if int(c) > time_red:
                time_start = int(c)
                df = api.get_history(pair, period, start_time=time_start, end_time=time_red)
        else:
            df = api.get_history(pair, period, start_time=time_start, end_time=time_red)
    return True


def start():
    while global_value.websocket_is_connected is False:
        time.sleep(0.1)
    time.sleep(2)
    saldo = api.get_balance()
    global_value.logger('Account Balance: %s' % str(saldo), "INFO")
    prep = prepare()
    if prep:
        his = save_history()
        if his:
            start = get_history() # This Command started to collecting Live Tick Data ...
            if start:
                save = save_live_data()
                if save:
                    print('Data Sucessful saved ...')
                    print('Now sleeping 60 sec. (to hold the websocket connection ...)')
                    time.sleep(60)
                    save = save_live_data()
                    if save:
                        print('Data Sucessful saved ...')
                        print('Exit now!')
    return




if __name__ == "__main__":
    start()
    end_counter = time.perf_counter()
    rund = math.ceil(end_counter - start_counter)
    # print(f'CPU-gebundene Task-Zeit: {rund} {end_counter - start_counter} Sekunden')
    global_value.logger("CPU-gebundene Task-Zeit: %s Sekunden" % str(int(end_counter - start_counter)), "INFO")

