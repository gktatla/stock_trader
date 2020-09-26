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

def matching(order, order_type):

	#get only sell orders that have not been fulfilled completely, and order them by acesending price
	sell_list = db.session.query(SellOrder).filter(SellOrder.units!=SellOrder.units_fulfilled).filter(SellOrder.stock_symbol==order.stock_symbol).order_by(SellOrder.limit_price.desc()).order_by(SellOrder.order_time).all()

	#get only buy orders that have not been fulfilled completely and order them by descending price
	buy_list = db.session.query(BuyOrder).filter(BuyOrder.units!=BuyOrder.units_fulfilled).filter(SellOrder.stock_symbol==order.stock_symbol).order_by(BuyOrder.limit_price).all()

	if sell_list:
		best_ask = sell_list[0].limit_price
	else:
		#nothing to sell
		return

	if buy_list:
		best_bid = buy_list[0].limit_price
	else:
		#nothing buy
		return

	if order_type == 'buy' and order.limit_price >= best_ask:
		# Buy order crossed the spread, there is a match
		shares_to_fill = order.units
		shares_filled = 0

		#create a savepoint in case of race condition
		db.session.begin_nested()

		completed = False
		
		#run this loop until we've completed the transaction
		while not(completed):
			try:
				#searching sell list from best to worst sell (lowest price to highest)
				for i in range(len(sell_list)):

					ask_price = sell_list[i].limit_price
					bid_price = order.limit_price

					midpoint = (ask_price + bid_price) / 2

					shares_to_buy = order.units - order.units_fulfilled
					shares_to_sell = sell_list[i].units - sell_list[i].units_fulfilled

					shares_exchanged = 0

					shares_exchanged = min(shares_to_buy, shares_to_sell)
					shares_filled = shares_filled + shares_exchanged

					#increment shares exchanged
					order.units_fulfilled = shares_exchanged
					sell_list[i].units_fulfilled = sell_list[i].units_fulfilled + order.units_fulfilled
					db.session.commit()

					add_to_transactions(order.stock_symbol, order.id, sell_list[i].id, shares_exchanged, midpoint)

					if shares_filled == shares_to_fill:
						#order complete, don't loop through the rest
						break
					completed = True
			except Exception as e:
				#the orders failed due to concurrent transaction, rollback to before exchange was attempted and try again
				print (e)
				db.session.rollback() 

	elif order_type == 'sell' and order.limit_price <= best_bid:
		# Buy order crossed the spread, there is a match
		shares_to_fill = order.units
		shares_filled = 0

		#create a savepoint in case of race condition
		db.session.begin_nested()

		completed = False
		
		#run this loop until we've completed the transaction
		while not(completed):
			try:
				#searching buy list from best to worst buy (highest price to lowest)
				for i in range(len(buy_list)):

					bid_price = buy_list[i].limit_price
					ask_price = order.limit_price

					midpoint = (ask_price + bid_price) / 2

					shares_to_buy = order.units - order.units_fulfilled
					shares_to_sell = buy_list[i].units - buy_list[i].units_fulfilled

					shares_exchanged = min(shares_to_buy,shares_to_sell)
					shares_filled = shares_filled + shares_exchanged

					#increment shares exchanged
					order.units_fulfilled = shares_exchanged
					buy_list[i].units_fulfilled = buy_list[i].units_fulfilled + shares_exchanged
					db.session.commit()

					add_to_transactions(order.stock_symbol, order.id, buy_list[i].id, shares_exchanged, midpoint)

					if shares_filled == shares_to_fill:
						#order complete, don't loop through the rest
						break
				#finished, and can exit loop
				completed = True
			except Exception as e:
				#the orders failed due to concurrent transaction, rollback to before exchange was attempted and try again
				print (e)
				db.session.rollback() 
	else:
		# Order did not cross the spread
		pass

class OrderResource(Resource):

    def post(self):    
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
    	
    	matching(order, request.json["type"])

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
	       		matching(order, request.json["type"])
	       		return { "statusCode": 200, "message": "Ok" }

	       	else:
	       		return { "statusCode": 403, "message": "No change in order" }

    def delete(self):

    	try:
    		if request.json["type"] == "buy": 
    			order = BuyOrder.query.get(request.json["id"])
    		else: 
    			order = SellOrder.query.get(request.json["id"])
    	except Exception as e:
    		return {"statusCode":403, "message": "id not found"}

    	if order is None:
    		return {"statusCode":404, "message":"Order not found"}
    	else:
    		if order.units_fulfilled != 0:
    			#order has been partially or fully fulfilled, can not delete
    			return {"statusCode":403, "message":"Order cannot be deleted"}
    		else:
	    		db.session.delete(order)
	    		db.session.commit()
	    		return { "statusCode": 200, "message": "OK" }

