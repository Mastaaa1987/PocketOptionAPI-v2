from datetime import datetime
import os, json

rp = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + '/../')
dp = os.path.join(rp, 'history')
if not os.path.exists(dp):
    os.makedirs(dp)
if not os.path.exists(os.path.join(dp, 'data')):
    os.makedirs(os.path.join(dp, 'data'))
if not os.path.exists(os.path.join(dp, 'live')):
    os.makedirs(os.path.join(dp, 'live'))

# Global variables
websocket_is_connected = False
# try fix ssl.SSLEOFError: EOF occurred in violation of protocol (_ssl.c:2361)
ssl_Mutual_exclusion = False  # mutex read write
# if false websocket can sent self.websocket.send(data)
# else can not sent self.websocket.send(data)
ssl_Mutual_exclusion_write = False  # if thread write

SSID = None
DEMO = None

check_websocket_if_error = False
websocket_error_reason = None

balance_id = None
balance = None
balance_type = None
balance_updated = None
result = None
order_data = {}
order_open = []
order_closed = []
closed_deals = []
open_orders = []
closed_orders = []
trades = {}
stat = []
pairs = {}

loglevel = 'INFO'

# To get the payment details for the different pairs
PayoutData = None

def logger(message, lvl):
    if loglevel == 'DEBUG':
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print('%s :[DEBUG]: %s' %(str(dt), str(message)))
    elif loglevel == lvl:
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print('%s :[%s]: %s' %(str(dt), str(lvl), str(message)))
    elif lvl == 'ERROR':
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print('%s :[ERROR]: %s' %(str(dt), str(message)))
    return


def set_csv(key, value, path=None):
    try:
        if path:
            file = os.path.join(dp, path, str(key))
        else:
            if 'price' in value[0]:
                file = os.path.join(dp, 'live', str(key))
            else:
                file = os.path.join(dp, 'data', str(key))
        if not os.path.exists(file+".csv"):
            csv_file = open(file+".csv", "w")
            if 'price' in value[0]:
                csv_file.write("time,price\n")
            else:
                csv_file.write("time,open,close,high,low\n")
            if len(value) == 1:
                if 'price' in value[0]:
                    csv_file.write("%s,%s\n" %(str(value[0]['time']), str(value[0]['price'])))
                else:
                    csv_file.write("%s,%s,%s,%s,%s\n" %(str(value[0]['time']), str(value[0]['open']), str(value[0]['close']), str(value[0]['high']), str(value[0]['low'])))
            else:
                for v in range(0, len(value)-1):
                    if 'price' in value[len(value)-1-v]:
                        csv_file.write("%s,%s\n" %(str(value[len(value)-1-v]['time']), str(value[len(value)-1-v]['price'])))
                    else:
                        csv_file.write("%s,%s,%s,%s,%s\n" %(str(value[len(value)-1-v]['time']), str(value[len(value)-1-v]['open']), str(value[len(value)-1-v]['close']), str(value[len(value)-1-v]['high']), str(value[len(value)-1-v]['low'])))
        else:
            if len(value) == 1:
                csv_file = open(file+".csv", "a")
                if 'price' in value[0]:
                    csv_file.write("%s,%s\n" %(str(value[0]['time']), str(value[0]['price'])))
                else:
                    csv_file.write("%s,%s,%s,%s,%s\n" %(str(value[0]['time']), str(value[0]['open']), str(value[0]['close']), str(value[0]['high']), str(value[0]['low'])))
            else:
                with open(file+".csv") as k:
                    csv = k.read().replace('\n', '|').split('|')
                c = int(csv[1].split(',')[0])
                if int(value[len(value)-1]["time"]) > c:
                    os.remove(file+".csv")
                    csv_file = open(file+".csv", "w")
                    csv_file.write("%s\n" % str(csv[0]))
                    for v in range(1, len(value)):
                        if int(value[len(value)-v]['time']) > c:
                            if 'price' in value[len(value)-v]:
                                csv_file.write("%s,%s\n" %(str(value[len(value)-v]['time']), str(value[len(value)-v]['price'])))
                            else:
                                csv_file.write("%s,%s,%s,%s,%s\n" %(str(value[len(value)-v]['time']), str(value[len(value)-v]['open']), str(value[len(value)-v]['close']), str(value[len(value)-v]['high']), str(value[len(value)-v]['low'])))
                        else:
                            break
                    for i in range(1, len(csv)-1):
                        csv_file.write("%s\n" % str(csv[i]))
                else:
                    csv_file = open(file+".csv", "a")
                    for v in range(0, len(value)-1):
                        if 'price' in value[len(value)-1-v]:
                            csv_file.write("%s,%s\n" %(str(value[len(value)-1-v]['time']), str(value[len(value)-1-v]['price'])))
                        else:
                            csv_file.write("%s,%s,%s,%s,%s\n" %(str(value[len(value)-1-v]['time']), str(value[len(value)-1-v]['open']), str(value[len(value)-1-v]['close']), str(value[len(value)-1-v]['high']), str(value[len(value)-1-v]['low'])))
        csv_file.close()
        return True
    except:
        return False


def get_csv(key, path=None):
    try:
        if path: file = os.path.join(dp, path, str(key))
        else: file = os.path.join(dp, str(key))
        if os.path.exists(file+".csv"):
            with open(file+".csv") as k:
                return k.read().replace('\n', '|').split('|')
    except:
        return None


def check_csv(key, path=None):
    try:
        if path: file = os.path.join(dp, path, str(key))
        else: file = os.path.join(dp, str(key))
        if os.path.exists(file+".csv"):
            return True
        return False
    except:
        return None


def set_cache(key, value, path=None):
    #data={"timestamp": int(time.time()), "value": value}
    data={"value": value}
    file = os.path.join(dp, str(key))
    if os.path.exists(file+".json"):
        os.remove(file+".json")
    with open(file+".json", "w") as k:
        json.dump(data, k, indent=4)


def check_cache(key, path=None):
    try:
        if path: file = os.path.join(dp, path, str(key))
        else: file = os.path.join(dp, str(key))
        if os.path.exists(file+".json"):
            return True
        return False
    except:
        return None


def get_cache(key, path=None):
    try:
        if path: file = os.path.join(dp, path, str(key))
        else: file = os.path.join(dp, str(key))
        with open(file+".json") as k:
            r = json.load(k)
        value = r.get('value')
        return value
    except:
        return None

