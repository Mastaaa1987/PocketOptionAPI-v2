import asyncio, datetime, time, json, threading, requests, ssl, atexit
from collections import deque
from pocketoptionapi.ws.client import WebsocketClient
from pocketoptionapi.ws.channels.get_balances import *
from pocketoptionapi.ws.channels.ssid import Ssid
from pocketoptionapi.ws.channels.candles import GetCandles
from pocketoptionapi.ws.channels.buyv3 import *
from pocketoptionapi.ws.objects.timesync import TimeSync
from pocketoptionapi.ws.objects.candles import Candles
import pocketoptionapi.global_value as global_value
from pocketoptionapi.ws.channels.change_symbol import ChangeSymbol
from collections import defaultdict
from pocketoptionapi.ws.objects.time_sync import TimeSynchronizer


class PocketOptionAPI(object):

    socket_option_opened = {}
    time_sync = TimeSync()
    sync = TimeSynchronizer()
    timesync = None
    candles = Candles()
    api_option_init_all_result = []
    api_option_init_all_result_v2 = []
    underlying_list_data = None
    position_changed = None
    buy_multi_option = {}
    result = None
    history_data = None
    history_new = None
    server_timestamp = None
    sync_datetime = None
    order_data = None
    buy_order_id = None
    order_async = None
    strike_list = None
    pairs = {}

    def __init__(self, proxies=None):
        self.websocket_client = None
        self.websocket_thread = None
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False
        self.proxies = proxies
        self.buy_successful = None
        self.loop = asyncio.get_event_loop()
        self.websocket_client = WebsocketClient(self)

    @property
    def websocket(self):
        return self.websocket_client
    
    def GetPayoutData(self):
        return global_value.PayoutData

    def GetClosedDeals(self):
        return global_value.closed_deals

    def send_websocket_request(self, name, msg, request_id="", no_force_send=True):
        # logger = logging.getLogger(__name__)

        data = f'42{json.dumps(msg)}'

        while (global_value.ssl_Mutual_exclusion or global_value.ssl_Mutual_exclusion_write) and no_force_send:
            pass
        global_value.ssl_Mutual_exclusion_write = True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.websocket.send_message(data))

        global_value.logger(data, "DEBUG")
        global_value.ssl_Mutual_exclusion_write = False

    def start_websocket(self):
        global_value.websocket_is_connected = False
        global_value.check_websocket_if_error = False
        global_value.websocket_error_reason = None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.websocket.connect())
        loop.run_forever()

        while True:
            try:
                if global_value.check_websocket_if_error:
                    return False, global_value.websocket_error_reason
                if global_value.websocket_is_connected is False:
                    return False, "Websocket connection closed."
                elif global_value.websocket_is_connected is True:
                    return True, None
            except:
                pass

    def connect(self):
        global_value.ssl_Mutual_exclusion = False
        global_value.ssl_Mutual_exclusion_write = False

        check_websocket, websocket_reason = self.start_websocket()

        if not check_websocket:
            return check_websocket, websocket_reason

        self.time_sync.server_timestamps = None
        while True:
            try:
                if self.time_sync.server_timestamps is not None:
                    break
            except:
                pass
        return True, None

    async def close(self, error=None):
        await self.websocket.on_close(error)
        self.websocket_thread.join()

    def websocket_alive(self):
        return self.websocket_thread.is_alive()

    @property
    def get_balances(self):
        return Get_Balances(self)

    @property
    def buyv3(self):
        return Buyv3(self)

    @property
    def getcandles(self):
        return GetCandles(self)

    @property
    def change_symbol(self):
        return ChangeSymbol(self)

    @property
    def synced_datetime(self):
        try:
            if self.time_sync is not None:
                self.sync.synchronize(self.time_sync.server_timestamp)
                self.sync_datetime = self.sync.get_synced_datetime()
            else:
                global_value.logger("timesync is not set", "ERROR")
                self.sync_datetime = None
        except Exception as e:
            global_value.logger(e, "ERROR")
            self.sync_datetime = None

        return self.sync_datetime
