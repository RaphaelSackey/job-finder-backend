from flask import Flask, request, make_response, jsonify 
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
CORS(app)
CORS(app, supports_credentials=True) 

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

@app.route('/SignUp', methods = ['POST'])
def signUp():
    def checkUserExistence(email: str) -> bool:
        try:
            cursor = mysql.connection.cursor()
            query = 'select * from users where email = %s'
            cursor.execute(query, (email,))
            results = cursor.fetchone()
            if results:
                return True
            return False
        except Exception as e:
            return e 

    if request.is_json:
        data = request.json
        username = data['username']
        email = data['email']
        password = data['password']
        if checkUserExistence(email) == True:
            response = make_response(jsonify({'message': 'user already exists'}))
            return response
        elif checkUserExistence(email) != False:
            response = make_response(jsonify({'message': 'something went wrong'}), 500)
            return response
        hashed_password = generate_password_hash(password)
        try:
            cursor = mysql.connection.cursor()
            query = f'insert into users(username, password_hash,email) values (%s,%s,%s)'
            cursor.execute(query, (username, hashed_password, email))
            mysql.connection.commit()
            response = make_response(jsonify({'message': 'user added'}), 200)
        except Exception as e:
            response = make_response(jsonify({'message': 'could not connect to database', 'error': e}))
            mysql.connection.rollback()
        finally:
            cursor.close()
            return response



@app.route('/logIn', methods = ['POST'])
def logIn():
   if request.is_json:     
       data = request.json
       print(data)
       response = None
       try:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT DATABASE()')
            rv = cursor.fetchone()
            response = make_response(jsonify({'message': 'successfully connected to database', 'data': data})) 
       except Exception as e:
            response = make_response(jsonify({'message': 'successfully connected to database', 'error': e}))        
            mysql.connection.rollback()

       finally:
           cursor.close()
           return response






if __name__ == "__main__":
    app.run(debug=True, port= 5001)
