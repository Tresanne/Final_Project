

from flask import Flask,request,redirect, url_for
from flask import render_template
import sqlite3
from datetime import date, datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
import requests

def get_db_conn():
	conn = sqlite3.connect('books.db')
	print("Opened database successfully")
	return conn

app = Flask(__name__)
app.config.update(
    TEMPLATES_AUTO_RELOAD=True
)

app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')


@app.route('/getbooks')
def getbooks():
	conn = get_db_conn()
	c = conn.cursor()
	Username = session['user_id']
	user_books = c.execute("SELECT DISTINCT Username, isbn_number,BookTitle from users_books WHERE Username=(?)",(Username,)).fetchall()
	conn.close()
	return render_template('books.html', user_books=user_books)


@app.route('/searchbooks', methods=['GET', 'POST'])
def searchbooks():
	if request.method=='POST':
		try:
			isbn = request.form['isbn']
			url_ = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+ isbn
			res_ = requests.get(url_)
			if res_.status_code == 200:
				book_data = res_.json()['items']
				return render_template('results.html', book_data=book_data, isbn=isbn)
		except:
			return render_template('search.html', error_messages="No Book is there with this isbn number" )
	else:
		return render_template('search.html')

@app.route('/addbooks/<isbn>/<title>')
def addbooks(isbn, title):
	try:
		conn = get_db_conn()
		c = conn.cursor()
		Username = session['user_id']
		c.execute("INSERT INTO users_books VALUES(?,?,?)",(Username, isbn, title,))
		conn.commit()
		conn.close()
		return redirect('getbooks')
	except:
		return redirect('getbooks')

@app.route('/deletebooks/<isbn>')
def deletebooks(isbn):
	try:
		conn = get_db_conn()
		c = conn.cursor()
		Username = session['user_id']
		c.execute("DELETE FROM users_books WHERE Username=(?) and isbn_number=(?)",(Username, isbn,))
		conn.commit()
		conn.close()
		return redirect('getbooks')
	except:
		return redirect('getbooks')

@app.route('/login', methods=['GET','POST'])
def login():
	# forget any user_id
    session.clear()
    error_messages = ""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            error_messages = "must provide username"
            return render_template("login.html", error_messages=error_messages)

        # ensure password was submitted
        elif not request.form.get("password"):
            error_messages = "must provide password"
            return render_template("login.html", error_messages=error_messages)

        # query database for username
        conn=get_db_conn()
        c=conn.cursor()
        rows = c.execute("SELECT * FROM users WHERE Username = (?)", (request.form["username"],)).fetchall()
        conn.close()
        # ensure username exists and password is correct
        if len(rows) != 1 or request.form["password"]=='':
            error_messages = "invalid username and/or password"
            return render_template("login.html", error_messages=error_messages)

        # remember which user has logged in
        session["user_id"] = rows[0][0]

        # redirect user to administrator's main page
        return redirect('getbooks')

    
    else:
        return render_template("login.html",error_messages=error_messages)

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for("login"))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form["username"].lower().strip()
        password = request.form["password"]
        password2 = request.form["password2"]
        full_name = request.form["FullName"]
        email_id = request.form["EmailID"]

        error_messages = ""

        if username == "" or password == "":
            error_messages = "missing username and/or password"
            print(error_messages)
            return render_template("register.html", error_messages=error_messages)

        if password != password2:
            error_messages = "Passwords Don't match"
            print(error_messages)
            return render_template("register.html", error_messages=error_messages)

        if full_name == "":
            error_messages = "missing Full Name"
            print(error_messages)
            return render_template("register.html", error_messages=error_messages)

        if email_id == "":
            error_messages = "missing email id"
            print(error_messages)
            return render_template("register.html", error_messages=error_messages)

        conn = get_db_conn()
        c = conn.cursor()
        rows = c.execute("SELECT * FROM users WHERE Username=(?)", (username,)).fetchall()
        conn.close()
        if(len(rows) > 0):
            error_messages = "Username already taken"
            return render_template("register.html", error_messages=error_messages)
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('''INSERT INTO users VALUES(?, ?, ?, ?)''', (username, full_name, email_id, password))
        conn.commit()
        rows = c.execute("SELECT * FROM users WHERE Username = (?)", (username,)).fetchall()
        conn.close()
        session["user_id"] = rows[0][0]

        if error_messages:
            return render_template("register.html", error_messages=error_messages)
        return redirect(url_for("getbooks"))
    else:
    	return render_template('register.html')

if __name__ == '__main__':
	app.run(debug = True, host='127.0.0.1', port=5000)