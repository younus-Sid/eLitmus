# Python standard libraries
import json


# Third party libraries
from flask import Flask, redirect, request, url_for, render_template, session, abort
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient
import requests
import mysql.connector


# Configuration
GOOGLE_CLIENT_ID = "563541197470-e9atk478ql5arqm5qok35473cautg94m.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)


# Flask app setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/elitmusdb"
app.config["SECRET_KEY"] = "mysecretkey"
db = SQLAlchemy(app)


# User session management setup https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


# All the models
class allanswers(db.Model, UserMixin):
    Ansid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Answer = db.Column(db.String(100), nullable=False)

class users(db.Model, UserMixin):
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Analytics = db.relationship("useranalytics", backref="owner")
    def get_id(self):
        return (self.Id)
    
class useranalytics(db.Model, UserMixin):
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Stagenum = db.Column(db.Integer)
    Accuracy = db.Column(db.Float)
    Mistakecount = db.Column(db.Integer)
    Timetaken = db.Column(db.Integer)
    Ownerid = db.Column(db.Integer, db.ForeignKey("users.Id"))


# All forms
class LoginForm(FlaskForm):
    email = StringField("email", validators=[InputRequired(), Length(max=100), Email(message="Invalid Email")])
    password = PasswordField("password", validators=[InputRequired(), Length(min=6, max=20)])
    rememberme = BooleanField("remember me")

class SignUpForm(FlaskForm):
    name = StringField("name", validators=[InputRequired(), Length(min=4, max=100)])
    email = StringField("email", validators=[InputRequired(), Length(max=100), Email(message="Invalid Email")])
    password = PasswordField("password", validators=[InputRequired(), Length(min=6, max=20)])


# Flask admin panel
class SecureModelView(ModelView):
    def is_accessible(self):
        if "logged_in" in session:
            return True
        else:
            abort(403)
            
admin = Admin(app)
admin.add_view(SecureModelView(users, db.session))
admin.add_view(SecureModelView(useranalytics, db.session))


# PythonAnyWhere MySQL Database password:= mysql123
mysql = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="elitmusdb",
)


# Fetching all the answers from database
mycur = mysql.cursor()
answers = mycur.execute("SELECT * FROM allanswers")
answers = mycur.fetchall()
mycur.close()


# Class containing all the functions to update user analytics
class UpdateAnalytics():
    def increaseStagenum(num, val):
        ans = (num, val)
        if ans in answers:
            if num == 6:
                return (num + 1, True)
            else:
                mycur = mysql.cursor()
                mycur.execute(
                    "UPDATE useranalytics SET Stagenum = Stagenum+1 WHERE Id = %s", (current_user.Id,)
                    )
                mysql.commit()
                mycur.close()
                return (num + 1, True)
        else:
            if num == 4 or num == 6:
                mycur = mysql.cursor()
                mycur.execute(
                    "UPDATE useranalytics SET Stagenum = 1 WHERE Id = %s", (current_user.Id,)
                    )
                mysql.commit()
                mycur.close()
                num = 1
            UpdateAnalytics.updateMistakecount()
            return (num, False)
        
    def updateMistakecount():
        mycur = mysql.cursor()
        mycur.execute(
            "UPDATE useranalytics SET Mistakecount = Mistakecount+1 WHERE Id = %s", (current_user.Id,)
            )
        mysql.commit()
        mycur.close()
        UpdateAnalytics.updateAccuracy()

    def updateAccuracy():
        mycur = mysql.cursor()
        mycur.execute(
            "UPDATE useranalytics SET Accuracy = ROUND(100-(Mistakecount*100)/(Mistakecount+Stagenum),2) WHERE Id = %s",
            (current_user.Id,)
            )
        mysql.commit()
        mycur.close()    


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return users.query.get(int(user_id))


@app.route("/")
def index():
    usersData = useranalytics.query.order_by(useranalytics.Mistakecount)
    return render_template("index.html", allUsers=usersData)


@app.route("/signuppage", methods=['GET', 'POST'])
def signuppage():
    signupform = SignUpForm()
    if signupform.validate_on_submit():
        hashed_password = generate_password_hash(signupform.password.data, method="scrypt")
        new_user = users(Name=signupform.name.data, Email=signupform.email.data, Password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        new_player = useranalytics(Id=new_user.Id, Name=signupform.name.data, Stagenum=1, Accuracy=0, 
                            Mistakecount=0, Timetaken=0, Ownerid=new_user.Id)
        db.session.add(new_player)
        db.session.commit()
        return redirect(url_for('loginpage'))
    return render_template("signuppage.html", form=signupform)


@app.route("/loginpage", methods=['GET', 'POST'])
def loginpage():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        # Checking if user is admin
        if loginform.email.data == "coyousisesi@gmail.com" and loginform.password.data == "abc@123":
            session['logged_in'] = True
        else:
            # Removing admin access
            if "logged_in" in session:
                session.pop("logged_in")

        user = users.query.filter_by(Email=loginform.email.data).first()
        if user:
            if check_password_hash(user.Password, loginform.password.data):
                login_user(user, remember=loginform.rememberme.data)
                return redirect(url_for('index'))
            else:
                return "<h1>Password is incorrect!</h1>" 
        else:
            return "<h1>You have not sign up!<br>Please sign up to login.</h1>" 
            
    return render_template("loginpage.html", form=loginform)


# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Removing admin access
    if "logged_in" in session:
        session.pop("logged_in")

    user = users.query.filter_by(Email=users_email).first()
    # If user doesn't exist in database
    if not user:
        # Create a user in our db with the information provided by Google
        new_user = users(Name=users_name, Email=users_email, Password="")
        db.session.add(new_user)
        db.session.commit()
        # Adding the user in analytics database
        new_player = useranalytics(Id=new_user.Id, Name=users_name, Stagenum=1, Accuracy=0, 
                            Mistakecount=0, Timetaken=0, Ownerid=new_user.Id)
        db.session.add(new_player)
        db.session.commit()
        # Begin user session by logging the user in
        login_user(new_user)
    else:
        # User exists in database
        login_user(user)
    

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    # Removing admin access
    if "logged_in" in session:
        session.pop("logged_in")
    logout_user()
    return redirect(url_for("index"))


@app.route("/treasurehunt", methods=["GET", "POST"])
def treasurehunt():
    mycur = mysql.cursor()
    player = mycur.execute(
            "SELECT * FROM useranalytics WHERE Id = %s", (current_user.Id,)
        )
    player = mycur.fetchone()
    mycur.close()
    if player is None:
        player = (current_user.Id, current_user.Name, 1)
    
    if request.method == "POST":
        result = (request.form.get("answer")).upper()
        num = UpdateAnalytics.increaseStagenum(player[2], result)
        return render_template("stages.html", stageValue=num[0], isCorrect=num[1])
    return render_template("stages.html", stageValue=player[2], isCorrect=True)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


if __name__ == "__main__":
    app.run(debug=True,ssl_context="adhoc")
