from flask import Flask, request, make_response, jsonify 
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token

#some line

app = Flask(__name__)
CORS(app)
CORS(app, supports_credentials=True) 
jwt = JWTManager(app)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES')) if os.getenv('JWT_ACCESS_TOKEN_EXPIRES') else 60
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES')) if os.getenv('JWT_REFRESH_TOKEN_EXPIRES') else 300

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
       try:
           cursor = mysql.connection.cursor()
           query = 'select password_hash from users where email = %s'
           cursor.execute(query, (data['email'],))
           email = cursor.fetchone()
           if email:
                is_password_correct = check_password_hash(email[0],data['password'])
                if is_password_correct:
                    access_token,refresh_token = generateTokens(data['email'])
                    
                    response = make_response(jsonify({'message': 'log in success', 'access_token':access_token, 'refresh_token':refresh_token}))
                else:
                    response = make_response(jsonify({'message': 'password does not match'}))
           else:
                response = make_response(jsonify({'message': 'not registered'}))

       except Exception as e:  
           response = make_response(jsonify({'message': 'something went wrong', 'error':e}))
           mysql.connection.rollback()
       finally:
           cursor.close()
           return response
       
@app.route('/postjob', methods = ['POST'])
@jwt_required()
def postJobs():
    response = jsonify({'message':'somehting is wrong'})
    if request.is_json:
        data = request.json
        pay = data['Pay']
        description = data['description']
        jobName = data['jobName']
        user = get_jwt_identity()
        jobType = data['jobType']
        location = data['location']

        try:
            cursor = mysql.connection.cursor()
            query = 'insert into jobs (user_email, title, description, pay, type, location) values (%s,%s,%s,%s,%s,%s)'
            cursor.execute(query, (user, jobName, description, pay, jobType, location))
            mysql.connection.commit()
            response = make_response(jsonify({'message': 'jop posted'}),200)
        except Exception as e:
            response = make_response(jsonify({'message': 'something went wrong', 'error': e}),500)
            mysql.connection.rollback()
        finally:
            cursor.close()
            return response

@app.route('/getjobs', methods = ['post'])
def getjobs():
    # not using this function right now. get the posted jobs by location
    def getQuery(location):
        if not location:
            location = 'New York, NY'
        
        query  = 'select * from jobs where location = %s'
        values = (location,)

        return query, values

                    
    if request.is_json:
        data = request.json
        location = data['location']

        query = 'select * from jobs'
        try:
           cursor = mysql.connection.cursor()
           cursor.execute(query)
           results = cursor.fetchall()
           response = make_response(jsonify({'data': results, 'message': 'job data retrieved'}))

        except Exception as e:
            response = make_response(jsonify({'message': 'something went wrong', 'error': e}))
            mysql.connection.rollback()
            
        finally:
            cursor.close()
            return response

        


@app.route('/protected', methods = ['POST', 'GET'])
@jwt_required()
def protected():
    data = request.json
    id = get_jwt_identity()
    response = make_response(jsonify({'data': data, 'message': 'you were able to access protected', 'id':id }))
    return response

@app.route('/refreshToken', methods = ['POST'])
@jwt_required(refresh = True)
def refresh():
    id = get_jwt_identity()
    access_token = generateTokens(id, False)
    response = make_response(jsonify({'access_token': access_token }))
    return response


def generateTokens(email, refreshIncluded = True):
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email) if refreshIncluded else ''
    return access_token, refresh_token if refresh_token else ''

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'status': 401,
        'sub_status': 42,
        'msg': 'The token has expired'
    }), 401



@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'status': 422,
        'sub_status': 43,
        'msg': 'The token is invalid'
    }), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'status': 401,
        'sub_status': 44,
        'msg': 'Request does not contain an access token'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'status': 401,
        'sub_status': 45,
        'msg': 'The token has been revoked'
    }), 401


if __name__ == "__main__":
    app.run(debug=True, port= 5000)
