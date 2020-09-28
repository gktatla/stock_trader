# Design Problem

This is a stock trading service

## Installation

Python 3.7 must be installed

Then create a virtual envirnment, activate it and install dependencies.

```bash
pip install venv
```

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

## To POST a buy or sell order (localhost:5000/order):
```bash
{
	"user_id": 2,
	"stock_symbol": "zm",
	"units": 150,
	"limit_price": 50.00,
	"type": "sell"
}
```

## To edit an order, use PATCH with the id of the order (localhost:5000/order):
```bash
{
	"id": "2",
	"stock_symbol": "zm",
	"units": 20,
	"limit_price": 20
}
```

## To DELETE an order (localhost:5000/order):
```bash
{
	"id": 2,
	"type": "buy"
}
```

## Assumptions: 
	if user updates their order, the time is updated
	if user attemps to update something but no data is changed, don't update the time
	only stock_symbol, units and limit_price can change
	since every order is executable and user accounts don't matter, there is not a need to keep a user table
