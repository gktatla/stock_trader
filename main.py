from flask import Flask, request
from flask_restful import Api, Resource

# Routes
from routes.order import OrderResource

from db import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
db.init_app(app)
api = Api(app)

api.add_resource(OrderResource, '/order')

if __name__ == '__main__':
    app.run(debug=True)

