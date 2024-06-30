from flask import Flask, request, make_response, jsonify 
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
CORS(app, supports_credentials=True) 

@app.route('/SignUp', methods = ['GET', 'POST'])
def SignUp():
    if request.is_json:
        data = request.json
    response = make_response(jsonify({'message': 'request success'}))
    response.set_cookie('testCookie', 'sdkjhahdasdkjdd')
    return response






if __name__ == "__main__":
    app.run(debug=True)
