from flask_restful import Api

from app import app, db
from routes.order import OrderResource


api = Api(app)

api.add_resource(OrderResource, '/order')

if __name__ == '__main__':
    app.run(debug=True)

