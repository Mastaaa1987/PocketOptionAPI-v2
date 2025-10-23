# 🚀 PocketOption API

[![GitHub](https://img.shields.io/badge/GitHub-AdminhuDev-blue?style=flat-square&logo=github)](https://github.com/Mastaaa1987)
[![Website](https://img.shields.io/badge/Website-Portfolio-green?style=flat-square&logo=google-chrome)](https://Mastaaa1987.github.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> The Python API is robust and modern for integration with PocketOption, offering a simple and efficient interface for automatic operation.

![Preview of API](pocketoption.png)

## ✨ Highlights

- 🔐 **Secure Authentication**: Login via SSID and robust session management
- 💹 **Automated Trading**: Programmatic buying and selling operations
- 📊 **Real Time Data**: WebSocket for quotes and operations
- 📈 **Technical Analysis**: Access to historical data and indicators
- 🛡️ **Stability**: Automatic reconnection and error handling
- 🔄 **Universal**: Demo and real account support

## 🛠️ Installation

### For development (recommended):
```bash
git clone https://github.com/Mastaaa1987/PocketOptionAPI-v2.git
cd PocketOptionAPI-v2
pip install -e .
```

### Via pip:
```bash
pip install git+https://github.com/Mastaaa1987/PocketOptionAPI-v2.git
```

## 📖 Basic Use

```python
from pocketoptionapi.stable_api import PocketOption
import time

# Session configuration
ssid = """42["auth",{"session":"asdasdasddsad","isDemo":1,"uid":12345465,"platform":2}]"""
demo = True  # True for demo account, False for real account

symbol = "CADCHF_otc"
period = 30

# Initialize API
api = PocketOption(ssid, demo)

# Connect
api.connect()

time.sleep(3)

# Check balance
saldo = api.get_balance()

print(saldo)

time.sleep(1)

pairs = api.get_pairs()

#print(pairs)
for pair in pairs:
    print(pair, pairs[pair])

time.sleep(1)

result = api.get_symbol(symbol, period)

print(result) # True or False

time.sleep(1)

df = api.get_dataframe(symbol, period)

print(df)


```

## 🎯 Advanced Features

### Get History Data
```python
pair = "EURUSD_otc"
period = 60
days = 1
time_start = int(datetime.now().timestamp())
time_end = time_start - 86400 * days
df = api.get_history(
    pair, 
    period, 
    start_time=time_start, 
    end_time=time_end)
```

## 🔧 Settings

### Main Dependencies
```txt
websocket-client>=1.6.1
requests>=2.31.0
python-dateutil>=2.8.2
pandas>=2.1.3
```

### Getting the SSID
To get the SSID required for authentication:

1. Log in to the PocketOption platform via browser
2. Open Developer Tools (F12)
3. Go to the "Network" tab
4. Look for WebSocket connections
5. Find the authentication message that contains the SSID
6. Copy the full SSID in the format shown in the example

How To get SSID.docx [HERE](https://github.com/Mastaaa1987/PocketOptionAPI/raw/refs/heads/master/How%20to%20get%20SSID.docx)

## 🤝 Contributing

Your contribution is very welcome! Follow these steps:

1. 🍴 Fork this repository
2. 🔄 Create a branch for your feature
   ```bash
   git checkout -b feature/MinhaFeature
   ```
3. 💻 Make your changes
4. ✅ Commit using conventional messages
   ```bash
   git commit -m "feat: Adds new functionality"
   ```
5. 📤 Push to your branch
   ```bash
   git push origin feature/MinhaFeature
   ```
6. 🔍 Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is an unofficial implementation and has no connection with PocketOption. Use at your own risk.

## 📞 Support

- 📧 Email: [sebastianspaaa@gmail.com](mailto:sebastianspaaa@gmail.com)
- 💬 Telegram: [@mastaaa667](https://t.me/mastaaa667)
- 🌐 Website: [mastaaa1987.site](https://mastaaa1987.github.io)

---

<p align="center">
  Powered ❤️ by <a href="https://github.com/Mastaaa1987">Mastaaa1987</a>
</p> 
