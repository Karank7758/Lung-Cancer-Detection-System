from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# from index import d_dtcn

import os
import numpy as np

# Keras
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image


# Flask utils
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import tensorflow_hub as hub
from markupsafe import Markup
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)




class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    uname = db.Column(db.String(20), unique=True, nullable=False)
    lname = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
   
    pass1 = db.Column(db.String(60), nullable=False)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')

@app.route("/")
def base():
    return render_template("base.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            session['user_id'] = user.id
            return redirect(url_for('user_home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match.', 'danger')

    return render_template('register.html')

@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('base'))


@app.route("/user_home",methods=['GET', 'POST'])
def user_home():
    
        return render_template("user_home.html")



@app.route("/contact",methods=['GET', 'POST'])
def contact():
    
        return render_template("contact.html")


@app.route('/predict')
def predict():
    
    return render_template('upload.html')



@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            session['user_id'] = user.id
            return redirect(url_for('admin_home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_register/', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('admin_login'))
        else:
            flash('Passwords do not match.', 'danger')

    return render_template('admin_register.html')

@app.route('/admin_logout/')
def admin_logout():
    session.pop('user_id', None)
    return redirect(url_for('base'))


@app.route("/admin_home")
def admin_home():
    users = User.query.all()
    queries = Contact.query.order_by(Contact.submitted_on.desc()).all()
    total_users = User.query.count()
    total_queries= Contact.query.count()
    return render_template("admin_home.html",  total_users=total_users, total_queries=total_queries, users=users, queries=queries)

@app.route("/update_query_status/<int:query_id>/<string:status>")
def update_query_status(query_id, status):
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        query = Contact.query.get_or_404(query_id)
        query.status = status
        db.session.commit()
        flash('Query status updated successfully', 'success')
    except Exception as e:
        print(f"Error updating query: {str(e)}")
        flash('Error updating query status', 'danger')
    
    return redirect(url_for('admin_home'))

@app.route("/view_user")
def view_user():
    users = User.query.all()
    return render_template('view_user.html', users=users)



# Model saved with Keras model.save()
model = load_model(('ml_test2/ct_cnn_best_model.hdf5'), custom_objects={'KerasLayer': hub.KerasLayer})
# print(model)

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def model_predict(img_path, model):
    classes_dir = ["Adenocarcinoma", "Large cell carcinoma", "Normal", "Squamous cell carcinoma"]
    img = image.load_img(img_path, target_size=(64,64))
    norm_img = image.img_to_array(img) / 255
    input_arr_img = np.array([norm_img])
    preds = model.predict(input_arr_img)[0]
    preds_softmax = softmax(preds)

    most_likely_idx = np.argmax(preds_softmax)
    most_likely = classes_dir[most_likely_idx]
    confidence = preds_softmax[most_likely_idx]

    if most_likely == "Normal":
        result = f"<b>Result: Normal</b>"
    else:
        result = f"<b>Type of Cancer:</b> {most_likely}<br><b>Probability:</b> {confidence*100:.2f}%"

    return Markup(result)


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        preds = model_predict(file_path, model)
        return preds  # This will now return the percentage results as HTML
    return None

@app.route('/getintouch', methods=['POST'])
def getintouch():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('desc')
        print(f"Received contact form submission: {name}, {email}, {phone}, {message}")
        try:
            new_query = Contact(
                name=name,
                email=email,
                phone=phone,
                message=message,
                submitted_on=datetime.utcnow()
            )
            db.session.add(new_query)
            db.session.commit()
            flash('Thank you for contacting us! We will get back to you soon.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    return redirect(url_for('contact'))

@app.route('/export_data')
def export_data():
    # Example data
    data = [
        {'User ID': 1, 'Prediction': 'Positive', 'Confidence': 0.92},
        {'User ID': 2, 'Prediction': 'Negative', 'Confidence': 0.85},
    ]
    df = pd.DataFrame(data)
    df.to_csv('user_data.csv', index=False)
    return "Data exported to user_data.csv"




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
