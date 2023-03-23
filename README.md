# payment-microservice

create payment example input 'http://localhost:5001/payment' [POST]:
payment_json = {
                "name": "Jack",
                "price": $10 * 100,
                "quantity": 1,
                "orderID": 1
            }
            
refund payment http://localhost:5001/payment/refund 'http://localhost:5001/payment/refund/<int:orderID>' [GET]. Dont need any json input.       
