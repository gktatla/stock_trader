from flask_restful import Api, Resource

from flask import request

from db.BuyOrderModel import BuyOrder, buy_order_schema
# from db.SellOrderModel import SellOrder, sell_order_schema
# from db.TransactionModel import Transaction, transaction_schema


class OrderResource(Resource):
    def post(self):
    	print(request.json)


    def patch(self):
        print ("patch!")

    def delete(self):
        print ("delete!")