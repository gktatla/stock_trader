from . import db

from datetime import datetime
from marshmallow import fields, Schema

class SellOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    stock_symbol = db.Column(db.String(4), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    units_fulfilled = db.Column(db.Integer, nullable=False)
    limit_price = db.Column(db.DECIMAL(65,2), nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.now())

class SellOrderSchema(Schema):
    class Meta:
        fields = ("id", "user_id", "stock_symbol", "units", "units_fulfilled", "limit_price", "order_time")

sell_order_schema = SellOrderSchema()