import asyncio, threading, sys, json, time, operator, math
from datetime import datetime
from tzlocal import get_localzone
from pocketoptionapi.api import PocketOptionAPI
import pocketoptionapi.constants as OP_code
import pocketoptionapi.global_value as global_value
from collections import defaultdict
from collections import deque
import pandas as pd

local_zone_name = get_localzone()

# logger = logging.getLogger(__name__)

def get_balance():
    return global_value.balance

class PocketOption:
    __version__ = "1.0.0"

    def __init__(self, ssid, demo):
        self.size = [1, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800,
                     3600, 7200, 14400, 28800, 43200, 86400, 604800, 2592000]
        global_value.SSID = ssid
        global_value.DEMO = demo
        global_value.logger("Modo Demo: %s" % str(demo), "INFO")
        self.suspend = 0.5
        self.thread = None
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0
        self.SESSION_HEADER = {
            "User-Agent": r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          r"Chrome/66.0.3359.139 Safari/537.36"}
        self.SESSION_COOKIE = {}
        self.api = PocketOptionAPI()
        self.loop = asyncio.get_event_loop()

    def get_server_timestamp(self):
        return self.api.time_sync.server_timestamp

    def Stop(self):
        sys.exit()

    def get_server_datetime(self):
        return self.api.time_sync.server_datetime

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    def get_async_order(self, buy_order_id=None):
        if buy_order_id:
            if self.api.order_async["deals"][0]["id"] == buy_order_id:
                return self.api.order_async["deals"][0]
            else:
                return None
        else:
            return self.api.order_async

    def get_async_order_id(self, buy_order_id):
        return self.api.order_async["deals"][0][buy_order_id]

    def start_async(self):
        asyncio.run(self.api.connect())

    def disconnect(self):
        try:
            if global_value.websocket_is_connected:
                asyncio.run(self.api.close())
                global_value.websocket_is_connected = False
                # logger.debug("WebSocket connection closed successfully.")
                global_value.logger("WebSocket connection closed successfully.", "DEBUG")
            else:
                # logger.debug("WebSocket was not connected.")
                global_value.logger("WebSocket was not connected.", "DEBUG")

            if self.loop is not None:
                for task in asyncio.all_tasks(self.loop):
                    task.cancel()

                if not self.loop.is_closed():
                    self.loop.stop()
                    self.loop.close()
                    # logger.debug("Event loop stopped and closed successfully.")
                    global_value.logger("Event loop stopped and closed successfully.", "DEBUG")

            if self.api.websocket_thread is not None and self.api.websocket_thread.is_alive():
                self.api.websocket_thread.join()
                # logger.debug("WebSocket thread closed successfully.")
                global_value.logger("WebSocket thread closed successfully.", "DEBUG")

        except Exception as e:
            # logging.error(f"Error during disconnection: {e}")
            global_value.logger("Error during disconnection: %s" % str(e), "ERROR")

    def connect(self):
        try:
            websocket_thread = threading.Thread(target=self.api.connect, daemon=True)
            websocket_thread.start()

        except Exception as e:
            # logging.error(f"Error connecting: {e}")
            global_value.logger("Error connecting: %s" % str(e), "ERROR")
            return False
        return True

    def get_pairs(self):
        try:
            data = json.loads(self.api.GetPayoutData())
            dat = {}
            for pair in data:
                if len(pair) == 19:
                    if pair[14] == True:
                        p = {}
                        p['id'] = pair[0]
                        p['payout'] = pair[5]
                        p['type'] = pair[3]
                        dat[pair[1]] = p
            return dat
        except:
            return None

    def GetPayout(self, pair):
        try:
            data = self.api.GetPayoutData()
            data = json.loads(data)
            data2 = None
            for i in data:
                if i[1] == pair:
                    data2 = i
            return data2[5]
        except:
            return None

    @staticmethod
    def check_connect():
        if global_value.websocket_is_connected == 0:
            return False
        elif global_value.websocket_is_connected is None:
            return False
        else:
            return True

    @staticmethod
    def get_balance():
        if global_value.balance_updated:
            return global_value.balance
        else:
            return None

    @staticmethod
    def check_open():
        return global_value.order_open

    @staticmethod
    def check_order_closed(ido):
        while ido not in global_value.order_closed:
            time.sleep(0.1)

        for pack in global_value.stat:
            if pack[0] == ido:
               # logger.debug('Closed Order',pack[1])
               global_value.logger("Closed Order %s" % str(pack[1]), "DEBUG")

        return pack[0]

    def buy(self, amount, active, action, expirations):
        self.api.buy_multi_option = {}
        self.api.buy_successful = None
        req_id = "buy"

        try:
            if req_id not in self.api.buy_multi_option:
                self.api.buy_multi_option[req_id] = {"id": None}
            else:
                self.api.buy_multi_option[req_id]["id"] = None
        except Exception as e:
            global_value.logger("Error initializing buy_multi_option: %s" % str(e), "ERROR")
            return False, None

        global_value.order_data = None
        global_value.result = None

        self.api.buyv3(amount, active, action, expirations, req_id)

        start_t = time.time()
        while True:
            if global_value.result is not None and global_value.order_data is not None:
                break
            if time.time() - start_t >= 5:
                if isinstance(global_value.order_data, dict) and "error" in global_value.order_data:
                    global_value.logger(str(global_value.order_data["error"]), "ERROR")
                else:
                    global_value.logger("Unknown error occurred during purchase operation", "ERROR")
                return False, None
            time.sleep(0.1)

        return global_value.result, global_value.order_data.get("id", None)

    def check_win(self, id_number=None):
        if not id_number:
            order_info = self.get_async_order()
            return order_info
        start_t = time.time()
        order_info = None

        while True:
            try:
                order_info = self.get_async_order(id_number)
                if order_info and "id" in order_info and order_info["id"] is not None:
                    break
            except:
                pass

            if time.time() - start_t >= 180:
                # logger.error("Timeout: Unable to retrieve order information in time.")
                global_value.logger("Timeout: Unable to retrieve order information in time.", "ERROR")
                return None, "unknown"

            time.sleep(0.1)

        if order_info and "profit" in order_info:
            status = "win" if order_info["profit"] > 0 else "loose"
            return order_info["profit"], status
        else:
            # logger.error("Invalid order information retrieved.")
            global_value.logger("Invalid order information retrieved.", "ERROR")
            return None, "unknown"

    @staticmethod
    def last_time(timestamp, period):
        timestamp_arredondado = (timestamp // period) * period
        return int(timestamp_arredondado)

    def get_payout(self):
        return self.api.GetPayoutData()

    def get_deals(self):
        return self.api.GetClosedDeals()

    @staticmethod
    def process_data_history(data, period):
        df = pd.DataFrame(data['history'], columns=['timestamp', 'price'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['minute_rounded'] = df['datetime'].dt.floor(f'{period / 60}min')

        ohlcv = df.groupby('minute_rounded').agg(
            open=('price', 'first'),
            high=('price', 'max'),
            low=('price', 'min'),
            close=('price', 'last')
        ).reset_index()

        ohlcv['time'] = ohlcv['minute_rounded'].apply(lambda x: int(x.timestamp()))
        ohlcv = ohlcv.drop(columns='minute_rounded')

        ohlcv = ohlcv.iloc[:-1]

        ohlcv_dict = ohlcv.to_dict(orient='records')

        return ohlcv_dict

    @staticmethod
    def process_candle(candle_data, period):
        data_df = pd.DataFrame(candle_data)
        data_df.sort_values(by='time', ascending=True, inplace=True)
        data_df.drop_duplicates(subset='time', keep="first", inplace=True)
        data_df.reset_index(drop=True, inplace=True)
        data_df.ffill(inplace=True)

        diferencas = data_df['time'].diff()
        diff = (diferencas[1:] == period).all()
        return data_df, diff

    def get_symbol(self, active, period):
        return self.get_candles(active, period)

    def wait(self, sleep=True, period=60):
        dt = int(datetime.now().timestamp()) - int(datetime.now().second)
        if period == 60:
            dt += 60
        elif period == 30:
            if datetime.now().second < 30: dt += 30
            else: dt += 60
            if not sleep: dt -= 30
        elif period == 15:
            if datetime.now().second >= 45: dt += 60
            elif datetime.now().second >= 30: dt += 45
            elif datetime.now().second >= 15: dt += 30
            else: dt += 15
            if not sleep: dt -= 15
        elif period == 10:
            if datetime.now().second >= 50: dt += 60
            elif datetime.now().second >= 40: dt += 50
            elif datetime.now().second >= 30: dt += 40
            elif datetime.now().second >= 20: dt += 30
            elif datetime.now().second >= 10: dt += 20
            else: dt += 10
            if not sleep: dt -= 10
        elif period == 5:
            if datetime.now().second >= 55: dt += 60
            elif datetime.now().second >= 50: dt += 55
            elif datetime.now().second >= 45: dt += 50
            elif datetime.now().second >= 40: dt += 45
            elif datetime.now().second >= 35: dt += 40
            elif datetime.now().second >= 30: dt += 35
            elif datetime.now().second >= 25: dt += 30
            elif datetime.now().second >= 20: dt += 25
            elif datetime.now().second >= 15: dt += 20
            elif datetime.now().second >= 10: dt += 15
            elif datetime.now().second >= 5: dt += 10
            else: dt += 5
            if not sleep: dt -= 5
        elif period == 120:
            dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 2) * 2), 0).timestamp())
            dt += 120
        elif period == 180:
            dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 3) * 3), 0).timestamp())
            dt += 180
        elif period == 300:
            dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 5) * 5), 0).timestamp())
            dt += 300
        elif period == 600:
            dt = int(datetime(int(datetime.now().year), int(datetime.now().month), int(datetime.now().day), int(datetime.now().hour), int(math.floor(int(datetime.now().minute) / 10) * 10), 0).timestamp())
            dt += 600

        return dt

    def get_dataframe(self, active, period):
        if active in global_value.pairs:
            if 'dataframe' in global_value.pairs[active]:
                df0 = global_value.pairs[active]['dataframe']
            else:
                df0 = None
            if 'history' in global_value.pairs[active]:
                history = []
                history.extend(global_value.pairs[active]['history'])
                df1 = pd.DataFrame(history).reset_index(drop=True)
                df1 = df1.sort_values(by='time').reset_index(drop=True)
                df1['time'] = pd.to_datetime(df1['time'], unit='s')
                df1.set_index('time', inplace=True)
                # df1.index = df1.index.floor('1s')

                df = df1['price'].resample(f'{period}s').ohlc()
                df.dropna(inplace=True)
                df.reset_index(inplace=True)
                df = df.loc[df['time'] < datetime.fromtimestamp(self.wait(False, period))]

                if df0 is not None:
                    ts = datetime.timestamp(df.loc[0]['time'])
                    for x in range(0, len(df0)):
                        ts2 = datetime.timestamp(df0.loc[x]['time'])
                        if ts2 < ts:
                            df = df._append(df0.loc[x], ignore_index = True)
                        else:
                            break
                    df = df.sort_values(by='time').reset_index(drop=True)
                    df.set_index('time', inplace=True)
                    df.reset_index(inplace=True)

                return df
        return None

    def change_symbol(self, active, period):
        return self.api.change_symbol(active, period)

    def sync_datetime(self):
        return self.api.synced_datetime

    def get_history(self, active, period, start_time=None, end_time=None, count_request=1):
        try:
            if start_time is None:
                time_sync = self.get_server_timestamp()
                time_red = self.last_time(time_sync, period)
            else:
                time_red = start_time
                time_sync = self.get_server_timestamp()

            all_candles = []

            time_red = int(datetime.now().timestamp())
            while True:
                try:
                    self.api.history_data = None
                    self.api.getcandles(active, period, time_red)

                    for i in range(1, 100):
                        if self.api.history_data is None:
                            time.sleep(0.1)
                        elif self.api.history_data is not None or i == 99:
                            break

                    if self.api.history_data is not None:
                        all_candles.extend(self.api.history_data)
                        if end_time is None:
                            break
                        else:
                            self.api.history_data = sorted(self.api.history_data, key=lambda x: x["time"])
                            _ = int(self.api.history_data[len(self.api.history_data)-1]["time"]) - int(self.api.history_data[0]["time"])
                            time_red = time_red - _
                            if time_red < end_time:
                                break
                except Exception as e:
                    global_value.logger(str(e), "ERROR")
            all_candles = sorted(all_candles, key=lambda x: x["time"])
            global_value.set_cache(global_value.pairs[active]["id"], all_candles)
            return True

            if len(his['candles']) > 0:
                for can in his['candles']:
                    c = {'time': can[0], 'open': can[1], 'high': can[3], 'low': can[4], 'close': can[2]}
                    c0.append(c)
                c0 = sorted(c0, key=lambda x: x["time"])
            for hist in his['history']:
                h = {'time': hist[0], 'price': hist[1]}
                c1.append(h)
            c1 = sorted(c1, key=lambda x: x["time"])
            if not active in global_value.pairs:
                global_value.pairs[active] = {}
            if active in global_value.pairs:
                global_value.pairs[active]['history'] = c1
                if len(c0) > 0:
                    df = pd.DataFrame(c0)
                    df = df.sort_values(by='time').reset_index(drop=True)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('time', inplace=True)
                    df.reset_index(inplace=True)
                    global_value.pairs[active]['dataframe'] = df

        except:
            global_value.logger("except get_candles", "DEBUG")
            return False

    def get_candles(self, active, period, start_time=None, count=6000, count_request=3):
        try:
            if start_time is None:
                time_sync = self.get_server_timestamp()
                time_red = self.last_time(time_sync, period)
            else:
                time_red = start_time
                time_sync = self.get_server_timestamp()

            all_candles = []

            self.api.history_new = None

            i = 0
            while True:
                i += 1
                try:
                    self.api.change_symbol(active, period)

                    for i in range(1, 100):
                        if self.api.history_new is None:
                            time.sleep(0.1)
                        elif self.api.history_new is not None or i == 99:
                            break

                    if self.api.history_new is not None:
                        his = self.api.history_new
                        break

                except Exception as e:
                    # logging.error(e)
                    global_value.logger(str(e), "ERROR")
            c0, c1 = [], []
            if period < 60 or count_request > 1:
                time_red = int(datetime.now().timestamp())
                x = 0
                while True:
                    x += 1
                    try:
                        self.api.history_data = None
                        self.api.getcandles(active, period, time_red)

                        for i in range(1, 100):
                            if self.api.history_data is None:
                                time.sleep(0.1)
                            elif self.api.history_data is not None or i == 99:
                                break

                        if self.api.history_data is not None:
                            c1.extend(self.api.history_data)
                            if x == count_request:
                                break
                            else:
                                self.api.history_data = sorted(self.api.history_data, key=lambda x: x["time"])
                                _ = int(self.api.history_data[len(self.api.history_data)-1]["time"]) - int(self.api.history_data[0]["time"])
                                time_red = time_red - _

                    except Exception as e:
                        # logger.error(e)
                        global_value.logger(str(e), "ERROR")
            if len(his['candles']) > 0:
                for can in his['candles']:
                    c = {'time': can[0], 'open': can[1], 'high': can[3], 'low': can[4], 'close': can[2]}
                    c0.append(c)
            c0 = sorted(c0, key=lambda x: x["time"])
            for hist in his['history']:
                h = {'time': hist[0], 'price': hist[1]}
                c1.append(h)
            c1 = sorted(c1, key=lambda x: x["time"])
            if not active in global_value.pairs:
                global_value.pairs[active] = {}
            if active in global_value.pairs:
                global_value.pairs[active]['history'] = c1
                if len(c0) > 0:
                    df = pd.DataFrame(c0)
                    df = df.sort_values(by='time').reset_index(drop=True)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('time', inplace=True)
                    df.reset_index(inplace=True)
                    global_value.pairs[active]['dataframe'] = df
            return True

        except:
            global_value.logger("except get_candles", "INFO")
            return False
