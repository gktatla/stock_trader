from flask_restful import Api, Resource
import json
from flask import request

from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema
from db.TransactionModel import Transaction, transaction_schema

from app import db

class OrderResource(Resource):
    def post(self):    	
    	if request.json["type"] == "buy":
    		new_order = BuyOrder(
    			user_id = request.json["type"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
    		db.session.add(new_order)
    		db.session.commit()
    		return { "statusCode": 200 }
    	else:
    		new_order = SellOrder(
    			user_id = request.json["type"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
	    	db.session.add(new_order)
	    	db.session.commit()
	    	return { "statusCode": 200 }

    def patch(self):
        print ("patch!")

    def delete(self):
        print ("delete!")
