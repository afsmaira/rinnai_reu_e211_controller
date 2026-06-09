# Brazilian Rinnai REU E211 Controller for PC

Unofficial community project. Not affiliated with, endorsed by, or supported by Rinnai.

Rinnai is a trademark of its respective owner.

Use at your own risk. Test carefully before using in real scenarios.

## Requirements

- Python 3.10+
- Same local network as the heater module

## Quick Start

```bash
python3 rinnai.py
```

## Import In Another Script

```python
from rinnai_controller import Controller

controller = Controller()
print(controller.getModel())
print(controller.getTemp())
```

## Install With pip

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

For development mode (editable install):

```bash
python -m pip install -e .
```

Install directly from GitHub (after push):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "git+https://github.com/<user>/<repo>.git"
```

Install a specific branch or tag:

```bash
python -m pip install "git+https://github.com/<user>/<repo>.git@main"
python -m pip install "git+https://github.com/<user>/<repo>.git@v0.1.0"
```

## Endpoints

- `/ip:null:pri`: keep-alive
- `/inc`: increases temperature and returns something like it `41,0,0,401,46992,0,null:pri,10,545,Aug 26 2024,14,0,0,0` (10 is `T-32` in celsius)
- `/dec`: decreases temperature and returns something like it `41,0,0,401,46992,0,null:pri,10,545,Aug 26 2024,14,0,0,0` (10 is `T-32` in celsius)
- `/tela_`: returns the current screen data (`41,0,0,401,46992,0,p,10,599,Aug 26 2024,14,0,0,0` where 10 is `T-32`)
- `/read_modelo`: returns the model code (`REUE211FEHBN3` for example)
- `/bus`: returns all data
- `/historico`: returns use history
- `/erros`: returns errors history
- `/lig`: turns it on/off and returns data
- `/hardware`:
- `/pre_heat_set_date_time/<date>`: 
- `/connect`: returns the MAC address
- `/modelo/14/<modelo>`: returns MAC address
- `/country/2`:
- `/SSID:ESP-RINNAI:PASSWORD:12345678:MODELO:0:FIM`:

## Notes

- Payload field mapping is still under reverse-engineering and may change.
- Sample data below is anonymized.

## History (trying to understand all of these data)

### /tela_

> 42,0,1,409,47544,815,null,4,15741,Aug 26 2024,14,0,0,0
On state during a 36 celcius degrees shower 2026-06-09 16:00
> 41,0,0,409,47544,0,null,4,16349,Aug 26 2024,14,0,0,0
Standby 2026-06-09 16:00

### /bus

> 41,0,0,1600,409,47544,10000,0,0,0,2196,3294,0,286,216,3600,192.168.0.2,null,4,20463085,16674,0,Aug 26 2024,14,Power on,ab:cd:ef:ab:cd:ef,0,0,0,0,0,0,0,0,0,0,0,-81,[0],2