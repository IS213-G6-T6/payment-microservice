import os
from flask import Flask, abort, request, jsonify
import stripe
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

stripe.api_key = "sk_test_51MnQhqITNu1JSEIlV6jSExaOvLFCYslzBlVeXMhSmcnmBJ49kszteRoQhe633LR2DqVHkKmm08p8pTWsVq9F03Y100l4nOYu6y"

class Payment(db.Model):
    __tablename__ = 'payment'

    paymentID = db.Column(db.String(255), primary_key=True)
    checkoutID = db.Column(db.String(255), nullable=False)
    orderID = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    def json(self):
        dto = {
            'paymentID': self.paymentID,
            'checkoutID': self.checkoutID,
            'orderID': self.orderID,
            'amount': self.amount,
            'timestamp': self.timestamp
        }

        return dto

@app.route('/payment', methods=['POST'])
def order():
    name = request.json.get('name', None)
    price = request.json.get('price', None)
    quantity = request.json.get('quantity', None)
    adjustable_quantity = "False"
    orderID = request.json.get('orderID', None)

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                'price_data': {
                    'product_data': {
                        'name': name,
                    },
                    'unit_amount': price,
                    'currency': 'sgd',
                },
                'quantity': quantity,
                'adjustable_quantity': {
                    "enabled": adjustable_quantity
                },
            },
        ],
        payment_method_types=['card'],
        mode='payment',
        success_url='http://localhost:5100/' + 'payment/success/' + orderID,
        cancel_url='http://localhost:5100/' + 'payment/cancel/' + orderID,
    )

    payment = Payment(paymentID=checkout_session.id, checkoutID="NA", orderID=orderID, amount=price/100)
    db.session.add(payment)
    db.session.commit()

    return jsonify(
            {
                "code": 200,
                "url": checkout_session.url
            }
        )


@app.route('/payment/success/<int:orderID>')
def success(orderID):
    payment = Payment.query.filter_by(orderID=orderID).first()
    session = stripe.checkout.Session.retrieve(payment.paymentID)
    payment.checkoutID = session.payment_intent
    db.session.commit()
    return jsonify(
            {
                "code": 200,
                "payment": "success",
                "order_ID": orderID
            }
        )


@app.route('/payment/cancel')
def cancel():
    return jsonify(
            {
                "code": 400,
                "payment": "failed"
            }
        )

@app.route('/payment/refund/<int:orderID>')
def refund(orderID):
    payment = Payment.query.filter_by(orderID=orderID).first()
    session = stripe.Refund.create(payment_intent=payment.checkoutID)
    return jsonify(
            {
                "code": 200,
                "payment": "refund success",
                "all_info": session
            }
        )



@app.route('/event', methods=['POST'])
def new_event():
    event = None
    payload = request.data
    signature = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, "sk_test_51MnQhqITNu1JSEIlV6jSExaOvLFCYslzBlVeXMhSmcnmBJ49kszteRoQhe633LR2DqVHkKmm08p8pTWsVq9F03Y100l4nOYu6y")
    except Exception as e:
        # the payload could not be verified
        abort(400)

    if event['type'] == 'checkout.session.completed':
      session = stripe.checkout.Session.retrieve(
          event['data']['object'].id, expand=['line_items'])
      print(f'Sale to {session.customer_details.email}:')
      for item in session.line_items.data:
          print(f'  - {item.quantity} {item.description} '
                f'${item.amount_total/100:.02f} {item.currency.upper()}')

    return {'success': True}

if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage orders ...")
    app.run(host='0.0.0.0', port=5001, debug=True)
