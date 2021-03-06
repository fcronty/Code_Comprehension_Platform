from flask import Flask, render_template, request, url_for, redirect
from flask_migrate import Migrate
from src.pylintTest import PylintTest
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
import random
#from src import routes, utils as u
#from src.models import db
#from src.settings import Settings as S
#from src.tasks import make_celery
#import io


file_text = "def __init__(): self.number = 1"
button = "Log In"

    #@classmethod
    #def boot(cls):
    #    """Begin the application"""
    #    app = cls()
    #    app.run()
    #    return app
class Application:

    def __init__(self):
        #self.init_flask()
        self.pylintTest = PylintTest()
        self.flask_app = Flask(__name__, static_url_path='/static')
        self.init_routes()

    '''def init_flask(self):
        # Init Flask
        self.flask_app = Flask(__name__, static_url_path='/static')
        self.flask_app.config.from_object(S)

        # Register the public routes
        for blueprint in [routes.counter]:
            self.flask_app.register_blueprint(blueprint)

        # Init Celery
        self.celery = make_celery(self.flask_app)

        # Init Flask-SQLAlchemy
        self.db = db
        self.db.init_app(self.flask_app)

        # Init Flask-Migrate
        u.wait_for_service('postgres', 5432, timeout=30.0)
        self.migrate = Migrate(self.flask_app, self.db)'''

    def init_routes(self):

        @self.flask_app.route("/")
        def index():
            button="Log In"
            if current_user.is_authenticated:
                button = "Log Out"
            return render_template("base.html", file_text = file_text, file_io="", button=button)

        @self.flask_app.route("/process", methods=["POST"])
        def process_code():
            file_text = request.form.get("codeinput")
            file_io, suggestions, score = analyze(file_text)
            fileDict = self.pylintTest.parseOutput()
            button="Log In"
            if current_user.is_authenticated:
                button = "Log Out"
            return render_template("base.html", file_text = file_text, button=button, file_io=file_io, suggestions=suggestions, score=score)

        def setup_user(user):
            user.level = 1
            user.xp = 0
            user.name = ""
            num = random.randint(1,7)
            user.icon = "{}.png".format(num)

        def logout():
            logout_user()
            button="Log In"
            return redirect('/')

        @self.flask_app.route("/login", methods=["POST", "GET"])
        def login_page():
            if current_user.is_authenticated:
                return logout()
            return render_template("login.html", correct=True)

        @self.flask_app.route("/register", methods=["POST", "GET"])
        def choose_action():
            if request.form["submit_button"] == "log in":
                return login_acct()
            else:
                return register_user()

        def register_user():
            if current_user.is_authenticated:
                return render_template("base.html", file_text = file_text)

            if request.method == 'POST':
                email = request.form['email']
                username = request.form['username']
                password = request.form['password']
                print("***",UserModel.query.filter_by(email=email),"***")
                if UserModel.query.filter_by(email=email).count()!=0:
                    return ('<h1>Please Enter Valid Credentials</h1>')

                user = UserModel(email=email, username=username)
                user.set_password(password)
                db.session.add(user)
                setup_user(user)
                db.session.commit()
            return render_template("login.html", correct=True)

        def login_acct():
            if current_user.is_authenticated:
                button = "Log Out"
                return render_template("base.html", button=button)

            if request.method == 'POST':
                email = request.form['email']
                user = UserModel.query.filter_by(email = email).first()
                if user is not None and user.check_password(request.form['password']):
                    button="Log Out"
                    login_user(user)
                    return render_template("base.html", button=button)

                return render_template('login.html', correct=False, text="Try Again!")

        def analyze(file_text):
            file_io = self.pylintTest.analyze(file_text)
            fileDict = self.pylintTest.parseOutput()

            score_index =file_io.index('Your code has been rated at')
            len_string = len('Your code has been rated at')
            score = file_io[score_index+len_string:]

            dash_index =file_io.index("---------")

            file_io = file_io[:dash_index]

            suggestions =[]

            # Bad Indentation
            if "W0311" in file_io:
                suggestions.append("Indentation")
            # Invalid Name
            if "C0103" in file_io:
                suggestions.append("Naming Conventions")
            # Missing module docstring
            if "C0114" in file_io:
                suggestions.append("Docstrings")
            # Consider using enumerate
            if "C0200" in file_io:
                suggestions.append("Consider using enumerate")

            # Check Function Name Length
            warnings = check_function_name_length(file_text)
            suggestions += warnings

            # Check get method does not return
            warnings_1 = check_get_not_return(file_text)
            suggestions += warnings_1

            # Check get method does not return
            warnings_2 = check_set_returns(file_text)
            suggestions += warnings_2

            return file_io, suggestions, score

        def check_function_name_length(string):
            warnings = []
            def_indices = [m.start() for m in re.finditer('def', string)]
            name_indices = [i + 4 for i in def_indices]

            for idx in name_indices:
                paren_idx = idx + string[idx:].index('(')
                # underscore
                if '_' in string[idx:paren_idx]:
                    words = string[idx:paren_idx].split('_')
                # camel case
                else:
                    words = camel_case_split(string[idx:paren_idx])

                if len(words) > 7:
                    warnings.append(f'Function name too long: {len(words)} words in ' + string[idx:paren_idx] + '()')

            return warnings

        def camel_case_split(str):
            return re.findall(r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str)

        def check_get_not_return(string):
            warnings = []
            def_indices = [m.start() for m in re.finditer('def', string)]
            name_indices = [i + 4 for i in def_indices]

            for i in range(len(name_indices)):
                idx = name_indices[i]
                paren_idx = idx + string[idx:].index('(')
                if len(def_indices) > i+1:
                    next_def_idx = def_indices[i+1]
                    if 'get' in string[idx:paren_idx] and 'return' not in string[paren_idx:next_def_idx]:
                        warnings.append('"Get" method does not return')
                else:
                    if 'get' in string[idx:paren_idx] and 'return' not in string[paren_idx:]:
                        warnings.append('"Get" method does not return')

            return warnings

        def check_set_returns(string):
            warnings = []
            def_indices = [m.start() for m in re.finditer('def', string)]
            name_indices = [i + 4 for i in def_indices]

            for i in range(len(name_indices)):
                idx = name_indices[i]
                paren_idx = idx + string[idx:].index('(')
                if len(def_indices) > i+1:
                    next_def_idx = def_indices[i+1]
                    if 'set' in string[idx:paren_idx] and 'return' in string[paren_idx:next_def_idx]:
                        warnings.append('"Set" method returns')
                else:
                    if 'set' in string[idx:paren_idx] and 'return' in string[paren_idx:]:
                        warnings.append('"Set" method returns')

            return warnings

        @self.flask_app.route('/tutorials/')
        def tutorials():
            button="Log In"
            if current_user.is_authenticated:
                button = "Log Out"
            return render_template("tutorials.html", button=button)

        @self.flask_app.route('/reference/')
        def reference():
            button="Log In"
            if current_user.is_authenticated:
                button = "Log Out"
            return render_template("references.html",button=button)

        @self.flask_app.route('/dashboard/')
        def dashboard():
            button="Log Out"
            if not current_user.is_authenticated:
                return login_page()

            return render_template("dashboard.html", button=button, email=current_user.email, name=current_user.username,level=current_user.level,xp=current_user.xp, icon=current_user.icon)

        @self.flask_app.route('/quiz1', methods=["POST", "GET"])
        def quiz1():
            button="Log Out"
            if not current_user.is_authenticated:
                return login_page()
            return render_template("quizzes/quiz1.html", button=button)


app = Application()
app.flask_app.secret_key = '1248612'
app.flask_app.debug = True
# adding configuration for using a sqlite database
app.flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site3.db'
app.flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app.flask_app)
db.init_app(app.flask_app)
# Creating an SQLAlchemy instance
login = LoginManager()
login.init_app(app.flask_app)
login.login_view = 'login'


#db.create_all()


class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.Integer)
    badge = db.Column(db.Integer)
    datapath = db.Column(db.String(80))


class UserModel(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String())
    level = db.Column(db.Integer)
    xp = db.Column(db.Integer)
    name = db.Column(db.String(40))
    icon = db.Column(db.String(40))
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

def get_user_by_email(email):
    return UserModel.query.filter_by(email=email)

@login.user_loader
def load_user(id):
    return UserModel.query.get(int(id))

if __name__ == "__main__":
    app.flask_app.run(debug=True)
