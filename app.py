from __future__ import division, print_function
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import io
import numpy as np
import pandas as ps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.utils import secure_filename
import urllib.request
from datetime import datetime
import os
import re
  
  
app = Flask(__name__)
  
model = load_model('vgg19model.h5')

  
app.secret_key = 'xyzsdfg'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'leaf_disease'
  
mysql = MySQL(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
  
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
  
@app.route('/')
@app.route('/main')
def main():
    return render_template('table.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            session['phone'] = user['phone']
            mesage = 'Logged in successfully !'
            return render_template('user.html', mesage = mesage)
        else:
            mesage = 'Please enter correct email / password !'
    return render_template('login2.html', mesage = mesage)

  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    session.pop('phone', None)
    return redirect(url_for('main'))

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/home')
def home():
    return render_template('user.html')


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        img = request.files['file']
        img_bytes = img.read()
        img = Image.open(io.BytesIO(img_bytes))
        img = img.resize((224,224))
        x = image.img_to_array(img)
        x = x / 255
        x = np.expand_dims(x, axis=0)
        preds = model.predict(x)
        l=['Bacterial Pustule','Frogeye Leaf Spot','Healty','Rust','Sudden Death Syndrome','Target Leaf Spot','Yellow Mosaic']
        pred_index = np.argmax(preds)
        result = l[pred_index]
        #1.Copper fungicides
        #2.group 3 (DMI-triazole) and group 11 (QoI-strobilurins)
        #4.Triazoles
        #5.FORTIX® FUNGICIDE
        #6.Spray Mancozeb @ 2g/L or Carbenzadium (500 mg/L)
        #7.Thiamethoxam or Methyl demeton
        f={"Bacterial Pustule" : "Disease Name: Bacterial Pustule and Treatment: Copper fungicides", "Frogeye Leaf Spot" : "Disease Name: Frogeye Leaf Spot and Treatment: group 3 (DMI-triazole) and group 11 (QoI-strobilurins)", "Healty" : "Healty Plant", "Rust" : "Disease Name: Rust and Treatment:Triazoles", "Sudden Death Syndrome" : "Disease Name: Sudden Death Syndrome and Treatment: FORTIX® FUNGICIDE", "Target Leaf Spot" : "Disease Name: Target Leaf Spot and Treatment: Spray Mancozeb or Carbenzadium", "Yellow Mosaic" : "Disease Name: Yellow Mosaic and Treatment: Thiamethoxam or Methyl demeton"}
        f1=f.get(result)

        return f1
    return None


@app.route('/save', methods=['GET','POST'])
def save():
    cursor = mysql.connection.cursor()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # now = datetime.now()
    if request.method == 'POST':
        files = request.files.getlist('result_img[]')
        #print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("INSERT INTO images (file_name) VALUES (%s)",[filename])
                mysql.connection.commit()
            print(file)
        cur.close()   
        flash('File(s) successfully uploaded')

    return render_template('history.html')


@app.route('/register', methods =['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name1' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form :
        userName = request.form['name1']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            mesage = 'Account already exists !'
        elif not userName or not password or not email or not phone:
            mesage = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s, % s)', (userName, email, phone , password, ))
            mysql.connection.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template('register.html', mesage = mesage)
    
if __name__ == "__main__":
    app.run(debug=True)