from flask_restful import Api, Resource
import json
from datetime import datetime
from flask import request

from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema
from db.TransactionModel import Transaction, transaction_schema

from app import db

def match(self, sell, buy):
	if buy >= self.orderbook.best_ask():
	# Buy order crossed the spread
		filled = 0
		consumed_asks = []
		for i in range(len(self.orderbook.asks)):
			ask = self.orderbook.asks[i]

			if ask.price > order.price:
				break # Price of ask is too high, stop filling order
			elif filled == order.quantity:
				break # Order was filled

			if filled + ask.quantity <= order.quantity: # order not yet filled, ask will be consumed whole
				filled += ask.quantity
				trade = Trade(ask.price, ask.quantity)
				self.trades.append(trade)
				consumed_asks.append(ask)
			elif filled + ask.quantity > order.quantity: # order is filled, ask will be consumed partially
				volume = order.quantity-filled
				filled += volume
				trade = Trade(ask.price, volume)
				self.trades.append(trade)
				ask.quantity -= volume

		# Place any remaining volume in LOB
		if filled < order.quantity:
			self.orderbook.add(Order("limit", "buy", order.price, order.quantity-filled))

		# Remove asks used for filling order
		for ask in consumed_asks:
			self.orderbook.remove(ask)


	elif order.side == 'sell' and order.price <= self.orderbook.best_bid():

		# Sell order crossed the spread
		filled = 0
		consumed_bids = []
		for i in range(len(self.orderbook.bids)):
			bid = self.orderbook.bids[i]

			if bid.price < order.price:
				break # Price of bid is too low, stop filling order
			if filled == order.quantity:
				break # Order was filled

			if filled + bid.quantity <= order.quantity: # order not yet filled, bid will be consumed whole
				filled += bid.quantity
				trade = Trade(bid.price, bid.quantity)
				self.trades.append(trade)
				consumed_bids.append(bid)
			elif filled + bid.quantity > order.quantity: # order is filled, bid will be consumed partially
				volume = order.quantity-filled
				filled += volume
				trade = Trade(bid.price, volume)
				self.trades.append(trade)
				bid.quantity -= volume

		# Place any remaining volume in LOB
		if filled < order.quantity:
			self.orderbook.add(Order("limit", "sell", order.price, order.quantity-filled))

		#Remove bids used for filling order
		for bid in consumed_bids:
			self.orderbook.remove(bid)

	else:
		# Order did not cross the spread, place in order book
		self.orderbook.add(order)


class OrderResource(Resource):

    def post(self):    

    	if request.json["type"] == "buy":
    		new_order = BuyOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
    		db.session.add(new_order)
    		db.session.commit()
    		return { "statusCode": 200, "message": "Ok" }
    	else:
    		new_order = SellOrder(
    			user_id = request.json["user_id"],
    			stock_symbol = request.json["stock_symbol"],
    			units = request.json["units"],
    			units_fulfilled = 0,
    			limit_price = request.json["limit_price"]
    		)
	    	db.session.add(new_order)
	    	db.session.commit()
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
