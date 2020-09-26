# Design Problem

This is a stock trading service

## Installation

Python must be installed

Then create a virtual envirnment, activate it and install dependencies.

```bash
python -m venv env
```

```bash
source env/bin/activate
```

```bash
pip install -r requirements.txt
```

## Usage

```python
from main import db
db.create_all()
exit()
```

```bash
python main.py
```



## Assumptions: 
	if user updates their order, the time is updated
	if user attemps to update something but no data is changed, don't update the time
	only stock_symbol, units and limit_price can change
	since every order is executable and user accounts don't matter, there is not a need to keep a user table
