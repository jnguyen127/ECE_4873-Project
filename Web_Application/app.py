#!flask/bin/python
import boto3
import re
import json
import time
import random
from datetime import datetime, timedelta
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, USER_TABLE, SES_SOURCE, SECRET_SALT, FLASK_SECRET_KEY
from flask import Flask, jsonify, abort, request, make_response, url_for, session, render_template, redirect, flash, get_flashed_messages, stream_with_context, Response
from flask_session import Session
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt
from decimal import Decimal

############################################################################################
##################################### Useful variables #####################################
############################################################################################
dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
ses = boto3.client('ses', aws_access_key_id=AWS_ACCESS_KEY,
                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
iot = boto3.client('iot', aws_access_key_id=AWS_ACCESS_KEY,
                   aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
USER_TABLE = dynamodb.Table(USER_TABLE)
app = Flask(__name__)
serializer = URLSafeTimedSerializer(SECRET_SALT)
bcrypt = Bcrypt(app)

time_format = "%m-%d-%y %H:%M:%S"
# Give at least 2(?) seconds delay between the microcontroller and web application! Can also be used to change timezone!
offset = 2 + (60 * 60 * 4)

############################################################################################
##################################### Useful functions #####################################
############################################################################################



def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Object of type '%s' is not JSON serializable" %
                    type(obj).__name__)


def check_password(password):
    password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
    if re.fullmatch(password_pattern, password):
        return True
    else:
        return False


@app.errorhandler(400)
def bad_request(error):
    """ 400 page route.
    get:
        description: Endpoint to return a bad request 400 page.
        responses: Returns 400 object.
    """
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    """ 404 page route.
    get:
        description: Endpoint to return a not found 404 page.
        responses: Returns 404 object.
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        if len(results):
            flash("Email already exists!", 'incorrect')
            return render_template('signup.html', firstName=firstName, lastName=lastName, password=password, confirmPassword=confirmPassword)
        if password != confirmPassword:
            flash("Passwords do not match!", 'incorrect')
            return render_template('signup.html', email=email, firstName=firstName, lastName=lastName, password=password, confirmPassword=confirmPassword)
        if not check_password(password):
            flash("Please make sure your password has the following: Has minimum 8 characters in length. At least one uppercase English letter. At least one lowercase English letter. At least one digit. At least one special character (i.e. #?!@$%^&*-)", 'incorrect')
            return render_template('signup.html', email=email, firstName=firstName, lastName=lastName, password=password, confirmPassword=confirmPassword)
        try:
            confirmationToken = serializer.dumps(email, SECRET_SALT)
            ses.send_email(
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Body': {
                        'Text': {
                            'Data': 'Please follow the link below to confirm your account! This link will expire in 24 hours and your account will be deleted!\n\nhttp://ec2-100-26-221-67.compute-1.amazonaws.com:5000/confirm_account/' + confirmationToken,
                        },
                    },
                    'Subject': {
                        'Data': 'Confirmation Email from Power Tap',
                    },
                },
                Source=SES_SOURCE
            )
            encryptedPassword = bcrypt.generate_password_hash(
                password).decode('utf8')
            USER_TABLE.put_item(
                Item={
                    "Email": email,
                    "First Name": firstName,
                    "Last Name": lastName,
                    "Password": encryptedPassword,
                    "Status": "Not Confirmed",
                    "Device Name": ""
                }
            )
        except ClientError as e:
            flash("Something went wrong! Please try again later!", 'incorrect')
            print(e)
        flash(
            "Account Created! Please check your email to confirm your account!", 'correct')
        return redirect('/')
    else:
        return render_template('signup.html')


@app.route('/confirm_account/<confirmationToken>', methods=['GET'])
def confirm_account_page(confirmationToken):
    try:
        email = serializer.loads(
            confirmationToken, salt=SECRET_SALT, max_age=86400)
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        if results[0]['Status'] == "Confirmed":
            flash("Your account is already confirmed!", 'incorrect')
            return redirect('/')
        USER_TABLE.update_item(
            Key={'Email': email},
            AttributeUpdates={"Status": {
                'Value': "Confirmed"}},
            ReturnValues="UPDATED_NEW"
        )
        flash("Your account has been confirmed!", 'correct')
    except:
        flash("This link has been expired!", 'incorrect')
    return redirect('/')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password_page():
    if request.method == 'POST':
        email = request.form['email']
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        if len(results) > 0 and results[0]['Status'] == "Confirmed":
            token = serializer.dumps(email, SECRET_SALT)
            try:
                ses.send_email(
                    Destination={
                        'ToAddresses': [email],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Please follow the link below to reset your password! This link will expire in 24 hours!\n\nhttp://ec2-100-26-221-67.compute-1.amazonaws.com:5000/reset_password/' + token,
                            },
                        },
                        'Subject': {
                            'Data': 'Reset Password from Power Tap',
                        },
                    },
                    Source=SES_SOURCE
                )
            except ClientError as e:
                flash("Something went wrong! Please try again later!", 'incorrect')
                print(e)
        flash("If this account exists and is confirmed, check your email to reset your password!", 'correct')
        return redirect('/')
    else:
        return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_page(token):
    if request.method == 'POST':
        newPassword = request.form['newPassword']
        confirmNewPassword = request.form['confirmNewPassword']
        if newPassword != confirmNewPassword:
            flash("Passwords do not match!", 'incorrect')
            return render_template('reset_password.html', newPassword=newPassword, confirmNewPassword=confirmNewPassword)
        if not check_password(newPassword):
            flash("Please make sure your password has the following: Has minimum 8 characters in length. At least one uppercase English letter. At least one lowercase English letter. At least one digit. At least one special character (i.e. #?!@$%^&*-)", 'incorrect')
            return render_template('reset_password.html', newPassword=newPassword, confirmNewPassword=confirmNewPassword)
        encryptedPassword = str(
            bcrypt.generate_password_hash(newPassword).decode('utf8'))
        results = USER_TABLE.scan()['Items']
        for attribute in results:
            email = attribute['Email']
            if email == serializer.loads(token, salt=SECRET_SALT):
                USER_TABLE.update_item(
                    Key={'Email': email},
                    AttributeUpdates={"Password": {
                        'Value': encryptedPassword}},
                    ReturnValues="UPDATED_NEW"
                )
                break
        flash("Password has been successfully reset!", 'correct')
        return redirect('/')
    else:
        try:
            serializer.loads(token, salt=SECRET_SALT, max_age=86400)
            return render_template('reset_password.html')
        except:
            flash("This link has been expired! Please resend an email!", 'incorrect')
            return render_template('forgot_password.html')


@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        if len(results) and bcrypt.check_password_hash(results[0]['Password'], password) and results[0]["Status"] == "Confirmed":
            rememberMe = "Yes" if 'checkBox' in request.form else "No"
            set_session(email, rememberMe)
            return redirect('/home')
        elif len(results) and results[0]["Status"] != "Confirmed":
            flash("The account is not confirmed. Another email has been sent to confirm your email!", 'incorrect')
            try:
                confirmationToken = serializer.dumps(email, SECRET_SALT)
                ses.send_email(
                    Destination={
                        'ToAddresses': [email],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Please follow the link below to confirm your account! This link will expire in 24 hours and your account will be deleted!\n\nhttp://ec2-100-26-221-67.compute-1.amazonaws.com:5000/confirm_account/' + confirmationToken,
                            },
                        },
                        'Subject': {
                            'Data': 'Confirmation Email from Power Tap',
                        },
                    },
                    Source=SES_SOURCE
                )
            except ClientError as e:
                flash("Something went wrong! Please try again later!", 'incorrect')
                print(e)
        else:
            flash("The email/password you entered is incorrect! Try again!", 'incorrect')
        return render_template('login.html', email=email)
    else:
        if check_session():
            return redirect('/home')
        else:
            [session.pop(key)
             for key in list(session.keys()) if key != '_flashes']
            return render_template('login.html')


def check_session():
    results = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(serializer.loads(session['email'], salt=SECRET_SALT)))[
        'Items'] if 'email' in session else ""
    if 'email' in session and session['rememberMe'] == "Yes" and len(results):
        try:
            serializer.loads(session['email'],
                             salt=SECRET_SALT, max_age=604800)
            return True
        except:
            [session.pop(key)
             for key in list(session.keys()) if key != '_flashes']
            flash("Session has been expired. Please log back in!", 'incorrect')
            return False
    elif 'email' in session and session['rememberMe'] == "No" and len(results):
        try:
            serializer.loads(session['email'], salt=SECRET_SALT, max_age=1800)
            return True
        except:
            [session.pop(key)
             for key in list(session.keys()) if key != '_flashes']
            flash("Session has been expired. Please log back in!", 'incorrect')
            return False
    else:
        return False


def set_session(email, rememberMe):
    session_token = serializer.dumps(email, SECRET_SALT)
    session['email'] = session_token
    session['rememberMe'] = "Yes" if rememberMe == "Yes" else "No"


@ app.route('/home', methods=['GET'])
def home_page():
    if check_session():
        email = serializer.loads(session['email'], salt=SECRET_SALT)
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        if not results[0]['Device Name']:
            flash('Please go to \'<a href="/account_info" style="color: red">Account Info</a>\' and register your device!', 'incorrect')
            return render_template('home.html', average_kwh=0)
        tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
            'Items'][0]['Device Name'].upper() + "_TABLE"
        DATA_TABLE = dynamodb.Table(tableName)
        sum = 0
        entries = 0
        avg = 0
        # Last 10 minutes data
        for x in range(600, 0, -1):
            offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
            offsetTime = str(offsetTime.strftime(time_format))  # Time Formatted
            results = DATA_TABLE.query(KeyConditionExpression=Key(
                'Timestamp').eq(offsetTime))['Items']
            if not results:
                continue
            for data in results:
                sum += float(data['Power'])
                entries += 1
            if (entries == 0):
                avg = 0
            else: 
                avg = sum * (10/60) / (entries * 1000)
        return render_template('home.html', average_kwh=round(avg, 3))
    else:
        return redirect('/')

@ app.route('/reload', methods=['GET'])
def reload_kwh():
    if check_session():
        email = serializer.loads(session['email'], salt=SECRET_SALT)
        tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
                'Items'][0]['Device Name'].upper() + "_TABLE"
        DATA_TABLE = dynamodb.Table(tableName)
        sum = 0
        entries = 0
        avg = 0
        # Last 10 minutes data
        for x in range(600, 0, -1):
            offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
            offsetTime = str(offsetTime.strftime(time_format))  # Time Formatted
            results = DATA_TABLE.query(KeyConditionExpression=Key(
                'Timestamp').eq(offsetTime))['Items']
            if not results:
                continue
            for data in results:
                sum += float(data['Power'])
                entries += 1
            if (entries == 0):
                avg = 0
            else: 
                avg = sum * (10/60) / (entries * 1000)
        return jsonify(round(avg, 3))
    else:
        return redirect('/')

# This will grab the data necessary and provide it
@ app.route('/generate_chart')
def generate_chart():
    def chart_data():
        global offset
        global time_format
        email = serializer.loads(session['email'], salt=SECRET_SALT)
        tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
            'Items'][0]['Device Name'].upper() + "_TABLE"
        DATA_TABLE = dynamodb.Table(tableName)
        while True:
            offsetTime = datetime.now() - timedelta(seconds=offset)  # Current time - offset
            offsetTime = str(offsetTime.strftime(time_format))  # Time Formated
            print(offsetTime)
            results = DATA_TABLE.query(KeyConditionExpression=Key(
                'Timestamp').eq(offsetTime))['Items']
            if not results:
                time.sleep(1)
                continue
            json_data = json.dumps(
                {'Time': results[0]['Timestamp'], 'Value': results[0]['Power']}, default=default)
            yield f"data:{json_data}\n\n"
            time.sleep(1)
    response = Response(stream_with_context(chart_data()),
                        mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@ app.route('/getChartDataNow')
def get_chart_data_now():
    global offset
    global time_format
    email = serializer.loads(session['email'], salt=SECRET_SALT)
    tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
        'Items'][0]['Device Name'].upper() + "_TABLE"
    DATA_TABLE = dynamodb.Table(tableName)
    labels = []
    data = []
    # Last 10 seconds data
    for x in range(10, 0, -1):
        offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
        offsetTime = str(offsetTime.strftime(time_format))  # Time Formatted
        results = DATA_TABLE.query(KeyConditionExpression=Key(
            'Timestamp').eq(offsetTime))['Items']
        if not results:
            continue
        labels.append(results[0]['Timestamp'])
        data.append(results[0]['Power'])
    return jsonify({'labels': labels, 'data': data})

@ app.route('/getChartData1M')
def get_chart_data_1m():
    global offset
    global time_format
    email = serializer.loads(session['email'], salt=SECRET_SALT)
    tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
        'Items'][0]['Device Name'].upper() + "_TABLE"
    DATA_TABLE = dynamodb.Table(tableName)
    labels = []
    data = []
    # Last 1 minute data
    for x in range(60, 0, -1):
        offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
        offsetTime = str(offsetTime.strftime(time_format))  # Time Formated
        results = DATA_TABLE.query(KeyConditionExpression=Key(
            'Timestamp').eq(offsetTime))['Items']
        if not results:
            continue
        labels.append(results[0]['Timestamp'])
        data.append(results[0]['Power'])
    return jsonify({'labels': labels, 'data': data})

@ app.route('/getChartData5M')
def get_chart_data_5m():
    global offset
    global time_format
    email = serializer.loads(session['email'], salt=SECRET_SALT)
    tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
        'Items'][0]['Device Name'].upper() + "_TABLE"
    DATA_TABLE = dynamodb.Table(tableName)
    labels = []
    data = []
    # Last 5 minutes data
    for x in range(300, 0, -1):
        offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
        offsetTime = str(offsetTime.strftime(time_format))  # Time Formated
        results = DATA_TABLE.query(KeyConditionExpression=Key(
            'Timestamp').eq(offsetTime))['Items']
        if not results:
            continue
        labels.append(results[0]['Timestamp'])
        data.append(results[0]['Power'])
    return jsonify({'labels': labels, 'data': data})

@ app.route('/getChartData10M')
def get_chart_data_10m():
    global offset
    global time_format
    email = serializer.loads(session['email'], salt=SECRET_SALT)
    tableName = USER_TABLE.query(KeyConditionExpression=Key('Email').eq(email))[
        'Items'][0]['Device Name'].upper() + "_TABLE"
    DATA_TABLE = dynamodb.Table(tableName)
    labels = []
    data = []
    # Last 10 minutes data
    for x in range(600, 0, -1):
        offsetTime = datetime.now() - timedelta(seconds=(x + offset))  # Current time - (x seconds + offset for timezone)
        offsetTime = str(offsetTime.strftime(time_format))  # Time Formated
        results = DATA_TABLE.query(KeyConditionExpression=Key(
            'Timestamp').eq(offsetTime))['Items']
        if not results:
            continue
        labels.append(results[0]['Timestamp'])
        data.append(results[0]['Power'])
    return jsonify({'labels': labels, 'data': data})

@ app.route('/account_info', methods=['GET', 'POST'])
def account_info_page():
    if check_session():
        email = serializer.loads(session['email'], salt=SECRET_SALT)
        results = USER_TABLE.query(
            KeyConditionExpression=Key('Email').eq(email))['Items']
        firstName = results[0]['First Name']
        lastName = results[0]['Last Name']
        currentDeviceName = results[0]['Device Name']
        if request.method == 'POST':
            currentPassword = request.form['currentPassword']
            newPassword = request.form['newPassword']
            confirmNewPassword = request.form['confirmNewPassword']
            newDeviceName = request.form['deviceName']
            if request.form['firstName'] != "" and request.form['firstName'] != firstName:
                USER_TABLE.update_item(
                    Key={'Email': email},
                    AttributeUpdates={
                        "First Name": {
                            'Value': request.form['firstName']}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                flash("First Name changed!", 'correct')
            if request.form['lastName'] != "" and request.form['lastName'] != lastName:
                USER_TABLE.update_item(
                    Key={'Email': email},
                    AttributeUpdates={
                        "Last Name": {
                            'Value': request.form['lastName']}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                flash("Last Name changed!", 'correct')
            if newDeviceName != currentDeviceName:
                if currentDeviceName == "" and newDeviceName != "":
                    currentDeviceName = newDeviceName
                    flash("Device added!", 'correct')
                elif currentDeviceName != "" and newDeviceName != "":
                    currentDeviceName = newDeviceName
                    flash("Device changed!", 'correct')
                else:
                    currentDeviceName = ""
                    flash("Device removed!", 'incorrect')
                USER_TABLE.update_item(
                    Key={'Email': email},
                    AttributeUpdates={
                        "Device Name": {
                            'Value': currentDeviceName}
                    },
                    ReturnValues="UPDATED_NEW"
                )
            if currentPassword != "" and bcrypt.check_password_hash(results[0]['Password'], currentPassword) and newPassword != "" and newPassword == confirmNewPassword and check_password(newPassword):
                encryptedPassword = bcrypt.generate_password_hash(
                    newPassword).decode('utf8')
                USER_TABLE.update_item(
                    Key={'Email': email},
                    AttributeUpdates={
                        "Password": {
                            'Value': encryptedPassword}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                flash("Password updated!", 'correct')
            elif newPassword != "" and not check_password(newPassword):
                flash("Please make sure your password has the following: Has minimum 8 characters in length. At least one uppercase English letter. At least one lowercase English letter. At least one digit. At least one special character (i.e. #?!@$%^&*-)", 'incorrect')
            else:
                flash("That is your current password. Please enter a different password", 'incorrect')
            return redirect('/account_info')
        else:
            if results[0]['Status'] == "Confirmed":
                visibility = "hidden"
            else:
                visibility = "visible"
            return render_template('account_info.html', visibility=visibility, email=email, firstName=firstName, lastName=lastName, deviceName=currentDeviceName)
    else:
        return redirect('/')


@ app.route('/logout', methods=['GET'])
def logout_page():
    session.clear()
    flash("You have logged out!", 'correct')
    return redirect('/')


# Runs the Web-Application
if __name__ == '__main__':
    app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, host="0.0.0.0", port=5000)
