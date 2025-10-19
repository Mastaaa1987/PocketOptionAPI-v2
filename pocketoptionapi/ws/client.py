import asyncio, websockets, json, ssl
from datetime import datetime, timedelta, timezone

import pocketoptionapi.constants as OP_code
import pocketoptionapi.global_value as global_value
from pocketoptionapi.constants import REGION
from pocketoptionapi.ws.objects.timesync import TimeSync
from pocketoptionapi.ws.objects.time_sync import TimeSynchronizer

# logger = logging.getLogger(__name__)

timesync = TimeSync()
sync = TimeSynchronizer()


async def on_open():
    global_value.logger("CONNECTED SUCCESSFUL", "INFO")
    global_value.logger("Websocket client connected.", "DEBUG")
    global_value.websocket_is_connected = True


async def send_ping(ws):
    while global_value.websocket_is_connected is False:
        await asyncio.sleep(0.1)
    pass
    while True:
        await asyncio.sleep(20)
        await ws.send('42["ps"]')


async def process_message(message):
    try:
        data = json.loads(message)
        global_value.logger("Received message: %s" % str(data), "DEBUG")

        if isinstance(data, dict) and 'uid' in data:
            uid = data['uid']
            global_value.logger("UID: %s" % str(uid), "DEBUG")
        elif isinstance(data, list) and len(data) > 0:
            event_type = data[0]
            event_data = data[1]
            global_value.logger("Event type: %s, Event data: %s" %(str(event_type), str(event_data)), "DEBUG")

    except json.JSONDecodeError as e:
        global_value.logger("JSON decode error: %s" % str(e), "ERROR")
    except KeyError as e:
        global_value.logger("Key error: %s" % str(e), "ERROR")
    except Exception as e:
        global_value.logger("Error processing message: %s" % str(e), "ERROR")


class WebsocketClient(object):
    def __init__(self, api) -> None:
        self.updateHistoryNew = None
        self.updateStream = None
        self.loadHistoryPeriod = None
        self.updateClosedDeals = False
        self.successcloseOrder = False
        self.updateStream = False
        self.api = api
        self.message = None
        self.url = None
        self.ssid = global_value.SSID
        self.websocket = None
        self.region = REGION()
        self.loop = asyncio.get_event_loop()

    async def websocket_listener(self, ws):
        try:
            async for message in ws:
                await self.on_message(message)
        except Exception as e:
            # logger.warning(f"Error occurred: {e}")
            global_value.logger("Error occurred: %s" % str(e), "WARNING")

    async def connect(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            await self.api.close()
        except:
            pass

        while not global_value.websocket_is_connected:
            for url in self.region.get_regions(global_value.DEMO):
                global_value.logger(str(url), "INFO")
                try:
                    async with websockets.connect(
                            url,
                            ssl=ssl_context,
                            additional_headers={
                                "Origin": "https://pocketoption.com",
                                "Cache-Control": "no-cache",
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                            }
                    ) as ws:
                        self.websocket = ws
                        self.url = url
                        global_value.websocket_is_connected = True

                        # Create and run tasks
                        on_message_task = asyncio.create_task(self.websocket_listener(ws))
                        sender_task = asyncio.create_task(self.send_message(self.message))
                        ping_task = asyncio.create_task(send_ping(ws))

                        await asyncio.gather(on_message_task, sender_task, ping_task)

                except websockets.ConnectionClosed as e:
                    global_value.websocket_is_connected = False
                    await self.on_close(e)
                    # logger.warning("Trying another server")
                    global_value.logger("Trying another server", "WARNING")

                except Exception as e:
                    global_value.websocket_is_connected = False
                    await self.on_error(e)

            await asyncio.sleep(1)

        return True

    async def send_message(self, message):
        while global_value.websocket_is_connected is False:
            await asyncio.sleep(0.1)

        self.message = message

        if global_value.websocket_is_connected and message is not None:
            try:
                await self.websocket.send(message)
            except Exception as e:
                # logger.warning(f"Error sending message: {e}")
                global_value.logger("Error sending message: %s" % str(e), "WARNING")
        elif message is not None:
            # logger.warning("WebSocket not connected")
            global_value.logger("WebSocket not connected", "WARNING")

    @staticmethod
    def dict_queue_add(self, dict, maxdict, key1, key2, key3, value):
        if key3 in dict[key1][key2]:
            dict[key1][key2][key3] = value
        else:
            while True:
                try:
                    dic_size = len(dict[key1][key2])
                except:
                    dic_size = 0
                if dic_size < maxdict:
                    dict[key1][key2][key3] = value
                    break
                else:
                    # Remove the smallest key
                    del dict[key1][key2][sorted(dict[key1][key2].keys(), reverse=False)[0]]

    async def on_message(self, message):
        """Method for processing websocket messages."""

        if type(message) is bytes:
            message2 = message.decode('utf-8')
            message = message.decode('utf-8')
            message = json.loads(message)

            if "balance" in message:
                if "uid" in message:
                    global_value.balance_id = message["uid"]
                global_value.balance = message["balance"]
                global_value.balance_type = message["isDemo"]

            elif "requestId" in message and message["requestId"] == 'buy':
                global_value.order_data = message
                global_value.open_orders.insert(0, message)

            elif self.updateClosedDeals and isinstance(message, list):
                global_value.closed_deals = message
                self.updateClosedDeals = False

            elif self.successcloseOrder and isinstance(message, dict):
                self.api.order_async = message
                global_value.closed_orders.insert(0, message)
                self.successcloseOrder = False

            elif self.loadHistoryPeriod and isinstance(message, dict):
                self.loadHistoryPeriod = False
                self.api.history_data = sorted(message["data"], key=lambda x: x["time"])

            elif self.updateStream and isinstance(message, list):
                self.updateStream = False
                if len(message[0]) == 3:
                    self.api.time_sync.server_timestamp = message[0][1]
                    if message[0][0] in global_value.pairs:
                        if 'history' in global_value.pairs[message[0][0]]:
                            h = {'time': message[0][1], 'price': message[0][2]}
                            global_value.pairs[message[0][0]]['history'].append(h)

            elif self.updateHistoryNew and isinstance(message, dict):
                self.updateHistoryNew = False
                self.api.history_new = message

            elif '[[5,"#AAPL","Apple","stock' in message2:
                global_value.PayoutData = message2
            return

        else:
            pass

        if message.startswith('0') and "sid" in message:
            await self.websocket.send("40")

        elif message == "2":
            await self.websocket.send("3")

        elif "40" and "sid" in message:
            await self.websocket.send(self.ssid)

        elif message.startswith('451-['):
            json_part = message.split("-", 1)[1]

            message = json.loads(json_part)

            if message[0] == "successauth":
                await on_open()

            elif message[0] == "successupdateBalance":
                global_value.balance_updated = True
            elif message[0] == "successopenOrder":
                global_value.result = True

            elif message[0] == "updateClosedDeals":
                self.updateClosedDeals = True

            elif message[0] == "successcloseOrder":
                self.successcloseOrder = True

            elif message[0] == "loadHistoryPeriod":
                self.loadHistoryPeriod = True

            elif message[0] == "loadHistoryPeriodFast":
                self.loadHistoryPeriod = True

            elif message[0] == "updateStream":
                self.updateStream = True

            elif message[0] == "updateHistoryNew":
                self.updateHistoryNew = True

            elif message[0] == "updateHistoryNewFast":
                self.updateHistoryNew = True

        elif message.startswith("42") and "NotAuthorized" in message:
            # logging.error("User not Authorized: Please Change SSID for one valid")
            global_value.logger("User not Authorized: Please Change SSID for one valid", "ERROR")
            global_value.ssl_Mutual_exclusion = False
            await self.websocket.close()

    async def on_error(self, error):
        # logger.error(error)
        global_value.logger(str(error), "ERROR")
        global_value.websocket_error_reason = str(error)
        global_value.check_websocket_if_error = True

    async def on_close(self, error):
        # logger.debug("Websocket connection closed.")
        # logger.warning(f"Websocket connection closed. Reason: {error}")
        global_value.websocket_is_connected = False
