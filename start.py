import time
from pocketoptionapi.stable_api import PocketOption

ssid = """42["auth",{"session":"abcdefghijklm12nopqrstuvwx","isDemo":1,"uid":12345678,"platform":2}]"""
demo = True

api = PocketOption(ssid,demo)

# Connect to API
api.connect()

time.sleep(1)

pairs = api.GetPairs()

print(pairs)

time.sleep(1)

symbol = api.ChangeSymbol('AEDCNY_otc', 60)

print(symbol)

time.sleep(1)

buy, bid = api.Buy(5, 'AEDCNY_otc', 'put', 15)

print(buy, bid)

time.sleep(1)

profit, status = api.CheckWin(bid)

print(profit, status)

time.sleep(1)

history = api.GetHistory('AEDCNY_otc')

print(len(history))

for i in range(0, 10):
    time.sleep(1)
    ticks = api.GetTicks('AEDCNY_otc')
    print(len(ticks))
