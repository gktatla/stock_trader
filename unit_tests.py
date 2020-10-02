import unittest

from unittest import mock

from datetime import datetime, timedelta

from app import db

from routes.order import matching

from db.TransactionModel import Transaction, transaction_schema
from db.BuyOrderModel import BuyOrder, buy_order_schema
from db.SellOrderModel import SellOrder, sell_order_schema



class TestApp(unittest.TestCase):

    test_buy_order = BuyOrder(
            user_id = 9,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 20.00
    )

    test_sell_order = SellOrder(
            user_id = 9,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 20.00
    )

    no_match_sell_order = SellOrder(
            user_id = 9,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 200.00
    )

    no_match_buy_order = BuyOrder(
            user_id = 9,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 5.00
    )

    valid_buy_order = BuyOrder(
    		id = 10,
            user_id = 9,
            stock_symbol = "zm",
            units = 20,
            units_fulfilled = 0,
            limit_price = 40.00
    )

    test_sell_list = [SellOrder(id = 1, user_id = 1, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 50.00, order_time = datetime.now()),
    SellOrder(id = 2, user_id = 2, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 30.00, order_time = datetime.now()),
    SellOrder(id = 3, user_id = 3, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 60.00, order_time = datetime.now()),
    SellOrder(id = 3, user_id = 3, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 30.00, order_time = datetime.now()-timedelta(days=1)),
    SellOrder(id = 4, user_id = 4, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 80.00, order_time = datetime.now())]

    test_buy_list = [BuyOrder(id = 1, user_id = 5, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 100.00, order_time = datetime.now()),
    BuyOrder(id = 2, user_id = 6, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 90.00, order_time = datetime.now()),
    BuyOrder(id = 3, user_id = 7, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 110.00, order_time = datetime.now()),
    BuyOrder(id = 4, user_id = 8, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 85.00, order_time = datetime.now()),
    BuyOrder(id = 5, user_id = 9, stock_symbol = "zm", units = 20, units_fulfilled = 0, limit_price = 20.00, order_time = datetime.now())]

    @mock.patch('app.db.session')
    def test_matching_no_sell_list(self, mock_session): 
    	#test when we add a buy order but there is no sell list
    	#first is sell, second is buy
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.all.side_effect = [None, self.test_buy_list]

        results = matching(self.test_buy_order, "buy")
        self.assertEqual(results, "no sell list")

    @mock.patch('app.db.session')
    def test_matching_no_buy_list(self, mock_session):
    	#test when we add a sell order bu there is no buy list
    	#first is sell, second is buy
    	mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, None]

    	results = matching(self.test_sell_order, "sell")
    	self.assertEqual(results, "no buy list")

    @mock.patch('app.db.session')
    def test_matching_no_matching_buy(self, mock_session):
    	#test when there is a buy list but no rows that match
    	#first is sell, second is buy 
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, self.test_buy_list]

        #insert sell order that won't have a match
        results = matching(self.no_match_sell_order, "sell")
        self.assertEqual(results, "order has no match")

    @mock.patch('app.db.session')
    def test_matching_no_matching_sell(self, mock_session):
    	#test when there is a sell list but no rows that match
    	#first is sell, second is buy 
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, self.test_buy_list]

        #insert buy order that will have no match
        results = matching(self.no_match_buy_order, "buy")
        self.assertEqual(results, "order has no match")


    # @mock.patch('routes.order.add_to_transactions')
    # @mock.patch('app.db.session')
    # def test(self, mock_session, mock_add_to_transactions): 
    #     mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.all.side_effect = [self.test_sell_list, None]
    #     results = matching(self.valid_buy_order, "buy")

    #     mock_add_to_transactions.assert_called_with(1, "zm", 10, 3, 20, 35.00)







