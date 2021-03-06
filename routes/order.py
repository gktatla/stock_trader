from flask_restful import Api, Resource
import json
from datetime import datetime
from flask import request

from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema
from db.TransactionModel import Transaction, transaction_schema

from app import db

import time

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

	completed = False
	transactions = []

	while not completed:

		print ("try again")

		db.session.begin_nested()

		try:

			# get only sell orders that have not been fulfilled completely, and order them by acesending price, make sure it's not same user

			sell_list=(db.session.query(SellOrder)
				.filter(SellOrder.units>SellOrder.units_fulfilled)
				.filter(SellOrder.stock_symbol==order.stock_symbol)
				.filter(SellOrder.user_id!=order.user_id)
				.filter(SellOrder.limit_price<=order.limit_price)
				.order_by(SellOrder.limit_price)
				.order_by(SellOrder.order_time)
				.all()
			)

			# get only buy orders that have not been fulfilled completely and order them by descending price, make sure it's not same user
			buy_list=(db.session.query(BuyOrder)
				.filter(BuyOrder.units > BuyOrder.units_fulfilled)
				.filter(BuyOrder.stock_symbol == order.stock_symbol)
				.filter(BuyOrder.user_id != order.user_id)
				.filter(BuyOrder.limit_price >= order.limit_price)
				.order_by(BuyOrder.limit_price.desc())
				.order_by(BuyOrder.order_time)
				.all()
			)

			if order_type == 'buy':
				#if sell list is not empty, calculate best ask, otherwise return since nothing to sell
				if sell_list: 
					best_ask = sell_list[0].limit_price
					#get the buy order to update and lock it
					buy_order_to_update = db.session.query(BuyOrder).filter(BuyOrder.id==order.id).with_for_update().one()
				else: 
					return "no sell list"

			elif order_type == 'sell':
				#if buy list is not empty, calculate best bid, otherwise return since nothing to buy
				if buy_list: 
					best_bid = buy_list[0].limit_price
					#get the sell order to update and lock it
					sell_order_to_update = db.session.query(SellOrder).filter(SellOrder.id==order.id).with_for_update().one()

				else: 
					return "no buy list"

			if order_type == 'buy' and order.limit_price >= best_ask:
				# Buy order crossed the spread, there is a match
				shares_to_fill = order.units
				shares_filled = 0

				#run this loop until we've completed the transaction
				#searching sell list from best to worst sell (lowest price to highest)
				for i in range(len(sell_list)):

					#get the sell order to update and lock it
					sell_order_to_update = db.session.query(SellOrder).filter(SellOrder.id==sell_list[i].id).with_for_update().one()

					#calculate price
					midpoint = (sell_order_to_update.limit_price + buy_order_to_update.limit_price) / 2

					#calculate shares to buy and sell
					shares_to_buy = sell_order_to_update.units - sell_order_to_update.units_fulfilled
					shares_to_sell = buy_order_to_update.units - buy_order_to_update.units_fulfilled

					#shares that can be exchanged is equal to the smaller of 2 units
					shares_exchanged = min(shares_to_buy, shares_to_sell)

					#increment shares filled
					shares_filled = shares_filled + shares_exchanged

					#increment shares filled in database
					sell_order_to_update.units_fulfilled = sell_order_to_update.units_fulfilled + shares_exchanged
					buy_order_to_update.units_fulfilled = buy_order_to_update.units_fulfilled + shares_exchanged

					transaction = Transaction(
						stock_symbol = buy_order_to_update.stock_symbol,
						buy_order_id = buy_order_to_update.id,
						sell_order_id = sell_order_to_update.id,
						units = shares_exchanged,
						price = midpoint
					)

					transactions.append(transaction)

					if shares_filled == shares_to_fill:
						#order complete, don't loop through the rest
						print ("shares filled")
						break

			elif order_type == 'sell' and order.limit_price <= best_bid:
				# Buy order crossed the spread, there is a match
				shares_to_fill = order.units
				shares_filled = 0
				
				#run this loop until we've completed the transaction
				#searching buy list from best to worst buy (highest price to lowest)
				for i in range(len(buy_list)):

					#get the buy order to update and lock it
					buy_order_to_update = db.session.query(BuyOrder).filter(BuyOrder.id==buy_list[i].id).with_for_update().one()

					#calculate price
					midpoint = (buy_order_to_update.limit_price + sell_order_to_update.limit_price) / 2

					#calculate shares to buy and to sell
					shares_to_buy = sell_order_to_update.units - sell_order_to_update.units_fulfilled
					shares_to_sell = buy_order_to_update.units - buy_order_to_update.units_fulfilled

					#shares that can be exchanged is equal to the smaller of the 2 units
					shares_exchanged = min(shares_to_buy,shares_to_sell)

					#increment shares filled
					shares_filled = shares_filled + shares_exchanged

					#increment shares filled in the database
					sell_order_to_update.units_fulfilled = sell_order_to_update.units_fulfilled + shares_exchanged
					buy_order_to_update.units_fulfilled = shares_exchanged + buy_order_to_update.units_fulfilled

					transaction = Transaction(
						stock_symbol = sell_order_to_update.stock_symbol,
						buy_order_id = buy_order_to_update.id,
						sell_order_id = sell_order_to_update.id,
						units = shares_exchanged,
						price = midpoint
					)

					transactions.append(transaction)

					if shares_filled == shares_to_fill:
						#order complete, don't loop through the rest
						print ("shares filled")
						break

			#order did not cross spread
			else: 
				return "order has no match"

			completed = True

			for item in transactions:
				db.session.add(item)

			db.session.commit()
				
		except Exception as e:
			#the orders failed due to concurrent transaction, rollback to before exchange was attempted and try again
			db.session.rollback() 
			#this is for when a row is locked, to wait for it to unlock so the buy/sell list doesn't falsely come up empty
			#when a row is locked, it wont return in the query even if orders are unfullfilled
			time.sleep(2)

class OrderResource(Resource):

    def post(self):    
    	if request.json["type"] == "buy":
    		order = BuyOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"],
    			order_time = datetime.now()
    		)
    		db.session.add(order)
    		db.session.commit()
    	else:
    		order = SellOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"],
    			order_time = datetime.now()
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

    	#get order from the buy table or sell table

    	if request.json["type"] == "buy": order = BuyOrder.query.get(request.json["id"])

    	else: order = SellOrder.query.get(request.json["id"])

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