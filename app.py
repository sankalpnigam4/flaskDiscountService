import json
import string
import random
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify

app = Flask(__name__)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Sample application cache, to be replaced by redis server
redis_cache_ref = {}


# DB Model class for DiscountCodes
class DiscountCodes(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    code = db.Column(db.String(60), unique=True, nullable=False)
    expiry_days = db.Column(db.Integer, default=7)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    brand_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(60), default='all')
    tags = db.Column(db.String(60), default='all')
    price = db.Column(db.Integer, nullable=False)
    limit = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean(), default=True)


# Function to generate random discount code for the brand
def generate_codes(codes_count):
    code_list = []
    code_length = 10
    for i in range(0, codes_count):
        code = ''.join(random.choices(string.ascii_uppercase +
                                      string.digits, k=code_length))
        code_list.append(code)
    return code_list


# API to store given number for discount codes into the database.
@app.route("/discount/api/<brand_id>", methods=['POST'])
def discount_post(brand_id):
    data = None
    message = "Something went wrong"
    status_code = 500
    global redis_cache_ref
    try:
        if request.method == 'POST':
            data = json.loads(request.data)
            code_count = data.get("code_count")
            price = data.get("price")

            # Check if all mandatory fields are passed on.
            if not code_count or not brand_id or not price:
                message = "code_count, brand_id and price are mandatory integer fields"
                status_code = 500
                return jsonify({"message": message, "code": status_code, "data": data})
            code_list = generate_codes(code_count)

            # Iterate over all generated codes and insert them into database.
            for code in code_list:
                dis_code = DiscountCodes(code=code, brand_id=brand_id, price=price)
                db.session.add(dis_code)
                db.session.commit()

            data = code_list
            if brand_id in redis_cache_ref:
                redis_cache_ref[brand_id].extend(code_list)
            else:
                redis_cache_ref[brand_id] = code_list

            status_code = 200
            message = "Successfully created {} codes".format(code_count)
    except Exception as ex:
        print("Error occurred while creating discount codes, err: {}".format(str(ex)))
        message = '{}_{}'.format(message, str(ex))

    return jsonify({"message": message, "code": status_code, "data": data})


@app.route("/discount/api/<brand_id>", methods=['GET'])
def discount_get(brand_id):
    data = None
    message = "Something went wrong"
    status_code = 500
    global redis_cache_ref
    try:
        if request.method == 'GET':
            # Return discount codes from cache if exists.
            if brand_id in redis_cache_ref and len(redis_cache_ref[brand_id]) > 0:
                data = redis_cache_ref[brand_id]
            else:
                # Fetching discount codes from database and update cache.
                all_codes = DiscountCodes.query.filter_by(brand_id=brand_id)
                fetched_codes = []
                for code in all_codes:
                    fetched_codes.append(code.code)

                if brand_id in redis_cache_ref:
                    redis_cache_ref[brand_id].extend(fetched_codes)
                else:
                    redis_cache_ref[brand_id] = fetched_codes
                data = fetched_codes
            status_code = 200
            message = "Successfully fetched all discount codes"
            if not data:
                message = "No discount code found for the brand id or the brand id doesn't exist."
    except Exception as ex:
        print("Error occurred while fetching codes, err: {}".format(str(ex)))
        message = '{}_{}'.format(message, str(ex))

    return jsonify({"message": message, "code": status_code, "data": data})


if __name__ == "__main__":
    app.run(debug=True)
