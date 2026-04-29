from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this' # Required for sessions and flashing


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('Users')
res_table = dynamodb.Table('Reservations')

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    response = users_table.get_item(Key={'username': username})
    if 'Item' in response and response['Item']['password'] == password:
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    user_name = session['username']

    # Fetch existing reservations for this specific user
    response = res_table.scan(
        FilterExpression=Attr('username').eq(user_name)
    )
    user_reservations = response.get('Items', [])

    return render_template('dashboard.html', name=user_name, reservations=user_reservations)

@app.route('/reserve', methods=['POST'])
def reserve():
    if 'username' not in session:
        return redirect(url_for('home'))

    date = request.form['date']
    time = request.form['time']

    
    existing_bookings = res_table.scan(
        FilterExpression=Attr('date').eq(date) & Attr('time').eq(time)
    )

    if existing_bookings['Count'] > 0:
        flash(f"The slot for {date} at {time} is already taken.")
        return redirect(url_for('dashboard'))

    
    reservation_id = str(uuid.uuid4())
    res_table.put_item(
       Item={
            'reservation_id': reservation_id,
            'username': session['username'],
            'date': date,
            'time': time
        }
    )
    flash(f"Successfully booked for {date} at {time}!")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
