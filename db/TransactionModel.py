from . import db

from marshmallow import fields, Schema

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_symbol = db.Column(db.String(4), nullable=False)
    buy_order_id = db.Column(db.Integer, db.ForeignKey('buy_orders.id'), nullable=False)
    sell_order_id = db.Column(db.Integer, db.ForeignKey('sell_orders.id'), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    price = db.Column(db.DECIMAL(65,2), nullable=False)


class TransactionSchema(Schema):
    class Meta:
        fields = ("id", "stock_symbol", "buy_order_id", "sell_order_id", "units", "price")


transaction_schema = TransactionSchema()
