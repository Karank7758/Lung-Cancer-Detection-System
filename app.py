from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import imghdr  # Add this import
import pandas as pd  # Add this import


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
    phone = db.Column(db.String(20))  # New field
    registered_on = db.Column(db.String(20))  # New field
    is_active = db.Column(db.Boolean, default=True)  # New field

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
            session['last_login_' + str(user.id)] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return redirect(url_for('user_home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']  # Add phone field
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            hashed_password = generate_password_hash(password)
            # Add registration timestamp
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                phone=phone,  # Store phone number
                registered_on=registration_date,  # Store registration date
                is_active=True  # Default active status
            )
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

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Create new contact query
            new_query = Contact(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                message=request.form.get('desc')
            )
            db.session.add(new_query)
            db.session.commit()
            flash('Thank you for contacting us! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    return render_template("contact.html")

@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            # Get the file from post request
            f = request.files['file']
            
            # Validate if a file was actually uploaded
            if not f:
                return 'No file uploaded', 400

            # Validate file type
            if not validate_image(f.stream):
                return 'Invalid image format. Please upload a valid image file.', 400

            # Check if it's a lung CT scan or X-ray image (you can add more specific validation)
            # For example, check image dimensions, contents, etc.
            img = image.load_img(f, target_size=(64, 64))
            
            # Save the file to ./uploads
            basepath = os.path.dirname(__file__)
            file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
            f.save(file_path)

            # Make prediction
            try:
                preds = model_predict(file_path, model)
                result = preds
                return result
            except Exception as e:
                print(f"Prediction error: {str(e)}")
                return 'Error processing image. Please try a different lung scan image.', 400

        except Exception as e:
            print(f"Upload error: {str(e)}")
            return 'Error uploading file', 400
            
    return None

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
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Get all users and queries
        users = User.query.all()
        queries = Contact.query.order_by(Contact.submitted_on.desc()).all()
        
        return render_template("admin_home.html", 
                             users=users,
                             queries=queries)
    except Exception as e:
        print(f"Error in admin_home: {str(e)}")
        flash('Error loading dashboard data', 'danger')
        return redirect(url_for('admin_login'))

# Add these new routes for managing queries
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
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    users = User.query.all()
    user_data = []
    for user in users:
        last_login = session.get('last_login_' + str(user.id), 'Never')
        user_info = {
            'username': user.username,
            'email': user.email,
            'last_login': last_login,
            'status': 'Active' if session.get('user_id') == user.id else 'Inactive'
        }
        user_data.append(user_info)
    return render_template('view_user.html', users=user_data)

@app.route('/metrics')
def metrics():
    # Example metrics (replace with actual values)
    metrics = {'Accuracy': 0.85, 'F1 Score': 0.82, 'Precision': 0.84}
    return render_template('metrics.html', metrics=metrics)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
