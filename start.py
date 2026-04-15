import time
from pocketoptionapi.stable_api import PocketOption

ssid = """42["auth",{"session":"abcdefghijklm12nopqrstuvwx","isDemo":1,"uid":12345678,"platform":2}]"""
demo = True

api = PocketOption(ssid,demo)

# Connect to API
api.connect()

time.sleep(1)

# Check balance
saldo = api.GetBalance()

print(saldo)

time.sleep(1)

# Get Pairs
pairs = api.GetPairs()

print(pairs)

time.sleep(1)

# Change Symbol
status = api.ChangeSymbol('AEDCNY_otc', 60) # api.ChangeSymbol(pair, expirations)

print(status)

time.sleep(1)

# Trade
status, id = api.Buy(5, 'AEDCNY_otc', 'put', 15) # api.Buy(amount, pair, action, expirations)

print(status, ID)

time.sleep(1)

# Check Trade
profit, status = api.CheckWin(id)

print(profit, status)

time.sleep(1)

# Get History Data
history = api.GetHistory('AEDCNY_otc') # api.GetHistory(pair)

print(len(history))

# Get Live Ticks
for i in range(0, 10):
    time.sleep(1)
    ticks = api.GetTicks('AEDCNY_otc') # api.GetTicks(pair)
    print(len(ticks))
