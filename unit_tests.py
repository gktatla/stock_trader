import unittest

from unittest import mock

from datetime import datetime, timedelta

from app import db

from routes.order import matching

from db.TransactionModel import Transaction, transaction_schema
from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema

class TestApp(unittest.TestCase):

    test_order = BuyOrder(
            user_id = 1,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 20.00
    )

    test_sell_list = [SellOrder(id = 1, user_id = 1, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "50.00", order_time = datetime.now()),
    SellOrder(id = 2, user_id = 2, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "30.00", order_time = datetime.now()),
    SellOrder(id = 3, user_id = 3, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "60.00", order_time = datetime.now()),
    SellOrder(id = 3, user_id = 3, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "30.00", order_time = datetime.now()-timedelta(days=1)),
    SellOrder(id = 4, user_id = 4, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "80.00", order_time = datetime.now())]

    test_buy_list = [BuyOrder(id = 1, user_id = 5, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "50.00", order_time = datetime.now()),
    BuyOrder(id = 2, user_id = 6, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "30.00", order_time = datetime.now()),
    BuyOrder(id = 3, user_id = 7, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "60.00", order_time = datetime.now()),
    BuyOrder(id = 4, user_id = 8, stock_symbol = "zm", units = "20", units_fulfilled = "0", limit_price = "50.00", order_time = datetime.now())]

    @mock.patch('app.db.session')
    def test_matching_no_sell_list(self, mock_session): 
    	#first is sell, second is buy
        mock_session.query.return_value.filter.return_value.filter.return_value.with_for_update.return_value.order_by.return_value.order_by.return_value.all.side_effect = [None, self.test_buy_list]

        results = matching(self.test_order, "buy")
        self.assertEqual(results, "no sell list")

    @mock.patch('app.db.session')
    def test_matching_no_buy_list(self, mock_session):
    	#first is sell, second is buy
    	mock_session.query.return_value.filter.return_value.filter.return_value.with_for_update.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, None]

    	results = matching(self.test_order, "buy")
    	self.assertEqual(results, "no buy list")

    # @mock.patch('app.db.session')
    # def test_no_matching_buy(self, mock_session):
    # 	#first is sell, second is buy 
    #     mock_session.query.return_value.filter.return_value.filter.return_value.with_for_update.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, self.test_buy_list]

    #     #sell order to update, buy order to update
    #     mock_session.query.return_value.filter.return_value.with_for_update.return_value.one.return_value = [self.test_sell_list[3], self.test_order]

    #     results = matching(self.test_order, "buy")
    #     self.assertEqual(results, "order has no match")