from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import joblib
#import pickle
#import string
#import nltk
#from nltk.stem import PorterStemmer
import mysql.connector

# Charger le modèle et le CountVectorizer
model = joblib.load('spam_classifier_svm_model.pkl')
vectorizer = joblib.load('count_vectorizer.pkl')

app = Flask(__name__)
app.secret_key = '1c8073775dbc85a92ce20ebd44fd6a4fd832078f59ef16ec' # a secure secret key

# Define my database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2003",
    database="DESNS"
)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/predict', methods=['POST'])
def predict():
    email_text = request.form['message']
    email_features = vectorizer.transform([email_text])
    result = model.predict(email_features)[0]
    prediction = "Spam" if result == 1 else "Not Spam"
    
    # Insert into email_history
    user_id = session['user'][0]  # assuming 'user' session contains the user record
    cur = db.cursor()
    cur.execute("INSERT INTO email_history (user_id, email_text, prediction) VALUES (%s, %s, %s)",
                (user_id, email_text, prediction))
    
    # Insert into prediction table
    cur.execute("INSERT INTO prediction (user_id, email_text, resultat_predict) VALUES (%s, %s, %s)",
                (user_id, email_text, prediction))
    db.commit()
    cur.close()

    return render_template('result.html', prediction=prediction)



@app.route('/history')
def history():
    if 'user' in session:
        user_id = session['user'][0]
        cur = db.cursor()
        cur.execute("SELECT email_text, prediction, prediction_date FROM email_history WHERE user_id = %s ORDER BY prediction_date DESC", (user_id,))
        history = cur.fetchall()
        cur.close()
        return render_template('history.html', history=history)
    else:
        return redirect(url_for('signin'))


@app.route('/delete_history', methods=['POST'])
def delete_history():
    cur = db.cursor()
    cur.execute("DELETE FROM email_history WHERE user_id = %s", (session['user'][0],))
    db.commit()
    cur.close()
    flash('Historique des prédictions supprimé avec succès.', 'success')
    return redirect(url_for('history'))


@app.route('/signin')
def signin():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('signin.html')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # Ensure the password and confirm_password match
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return "Password and Confirm Password do not match."

        # Insert data into MySQL
        cur = db.cursor()
        cur.execute("INSERT INTO users (full_name, username, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                    (full_name, username, email, phone, password))
        db.commit()
        cur.close()

        flash('Registration successful', 'success')
        return redirect('/signin')

    return "Invalid request method"


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = request.form.get('remember_me')  # Get the 'remember_me' checkbox value

        # Query the database to check if the email and password match
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user'] = user

            if remember_me:
                session.permanent = True
            return redirect(url_for('index'))
        else:
            return "Login failed. Check your email and password."

    return "Invalid request method"


@app.route('/index')
def index():
    # Check if the 'user' session variable exists (i.e., the user is logged in)
    if 'user' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('signin'))  # Redirect to the sign-in page if the user is not logged in


@app.route('/logout')
def logout():
    # Clear the user session to log out
    session.pop('user', None)
    return redirect(url_for('home'))  # Redirect to the sign-in page after logging out

#serveur WSGI
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
