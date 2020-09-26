from flask_restful import Api, Resource
import json
from datetime import datetime
from flask import request

from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema
from db.TransactionModel import Transaction, transaction_schema

from app import db

def add_to_transactions(stock_symbol, buy_order_id, sell_order_id, units, price):
 	new_transaction = Transaction(
    	stock_symbol = stock_symbol,
    	buy_order_id = buy_order_id,
    	sell_order_id = sell_order_id,
    	units = units,
    	price = price
    	)
 	db.session.add(new_transaction)
 	db.session.commit()

def best_price(orders):
	options = []
	best_price = orders[0].limit_price
	for item in orders:
		if item.limit_price != best_price:
			#no more options at that price
			exit()
		options.append(item)

	#if there were multiple options at best price, sort by time
	options.sort(key=lambda x: x.datetime)
	return options[0].limit_price

def matching(order, order_type):

	#add where clauses
	sell_list = SellOrder.query.all()
	sell_list.sort(key=lambda x: x.limit_price)

	buy_list = BuyOrder.query.all()
	buy_list.sort(key=lambda x: x.limit_price, reverse=True)

	if order_type == 'buy' and order.limit_price >= best_price(sell_list):
		# Buy order crossed the spread
		filled = 0
		consumed_asks = []
		for i in range(len(buy_list)):
			ask = buy_list[i]

			if ask.limit_price > order.limit_price:
				break # Price of ask is too high, stop filling order
			elif filled == order.units:
				break # Order was filled

			if filled + ask.units <= order.units: # order not yet filled, ask will be consumed whole
				filled += ask.units

				#change database and add to transaction table
				ask.units_fulfilled = ask.units
				db.session.commit()
				add_to_transactions(ask.stock_symbol, order.id, ask.id, ask.units, ask.limit_price)

			elif filled + ask.units > order.units: # order is filled, ask will be consumed partially
				volume = order.units-filled
				filled += volume

				#change database and add to transaction table
				ask.units_fulfilled = ask.units_fulfilled + volume
				db.session.commit()
				add_to_transactions(ask.stock_symbol, order.id, ask.id, ask.units, ask.limit_price)

	elif order_type == 'sell' and order.limit_price <= best_price(buy_list):

		# Sell order crossed the spread
		filled = 0
		consumed_bids = []
		for i in range(len(sell_list)):
			bid = sell_list[i]

			if bid.limit_price < order.limit_price:
				break # Price of bid is too low, stop filling order
			if filled == order.units:
				break # Order was filled

			if filled + bid.units <= order.units: # order not yet filled, bid will be consumed whole
				filled += bid.units

				#change database and add to transaction table
				bid.units_fulfilled = bid.units
				db.session.commit()
				add_to_transactions(ask.stock_symbol, bid.id, order.id, bid.units, bid.limit_price)

			elif filled + bid.units > order.units: # order is filled, bid will be consumed partially
				volume = order.units-filled
				filled += volume

				#change database and add to transaction table
				bid.units_fulfilled = bid.units_fulfilled + volume
				db.session.commit()
				add_to_transactions(ask.stock_symbol, bid.id, order.id, bid.units, bid.limit_price)

	else:
		# Order did not cross the spread
		pass


class OrderResource(Resource):

    def post(self):    

    	new_transaction = Transaction(
	    	stock_symbol = "somethinggggg",
	    	buy_order_id = 43,
	    	sell_order_id = 5435,
	    	units = 345345,
	    	price = 54.54
	    	)
    	db.session.add(new_transaction)
    	db.session.commit()

    	if request.json["type"] == "buy":
    		order = BuyOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
    		db.session.add(order)
    		db.session.commit()
    	else:
    		order = SellOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
	    	db.session.add(order)
	    	db.session.commit()
    	
    	# matching(order, request.json["type"])

    	return { "statusCode": 200, "message": "Ok" }


    def patch(self):

    	#check to see if it is a buy or sell order
        if request.json["type"] == "buy" : order = BuyOrder.query.get(request.json["id"])
        elif request.json["type"] == "sell" : order = SellOrder.query.get(request.json["id"])

        #if order doesn't exist or units have been fully or partially fullfilled, don't edit and return respective error codes
        if order is None : return {"statusCode":404, "message":"Order not found"}
        if order.units_fulfilled != 0: return {"statusCode":403, "message":"Order cannot be modified"}

        #update the order
        else:
        	changed = False
        	for item in request.json:
                #only attempt to edit stock_symbol, units or limit price as long as value given is not the same
	       		if item == "stock_symbol" and order.stock_symbol != request.json[item]: 
	       			order.stock_symbol = request.json[item]
	       			changed = True

	       		if item == "units" and order.units != request.json[item]: 
	       			order.units = request.json[item]
	       			changed = True

	       		if item == "limit_price" and order.limit_price != request.json[item]: 
	       			order.limit_price = request.json[item]
	       			changed = True
	       
	       	if changed:
	       		#if changed, only then update order time
		       	order.order_time = datetime.now()
	       		order.user_id = 0
	       		db.session.commit()  
	       		return { "statusCode": 200, "message": "Ok" }

	       	else:
	       		return { "statusCode": 403, "message": "No change in order" }

    def delete(self):

    	if request.json["type"] == "buy": order = BuyOrder.query.get(request.json["id"])
    	else : order = SellOrder.query.get(request.json["id"])

    	if order is None:
    		return {"statusCode":404, "message":"Order not found"}
    	else:
    		db.session.delete(order)
    		db.session.commit()
    		return { "statusCode": 200, "message": "OK" }
