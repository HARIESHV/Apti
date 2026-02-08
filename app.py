from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__)
app.secret_key = 'aptitude_secret_key'

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'aptitude.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Allowed Users
ALLOWED_USERS = {
    'admin@aptitude.com': {
        'password': 'admin123', 
        'name': 'Administrator', 
        'role': 'admin'
    },
    'gopika@aptitude.com': {
        'password': 'gopika123', 
        'name': 'Gopika', 
        'role': 'user'
    },
    'hari@aptitude.com': {
        'password': 'hari123', 
        'name': 'Hari', 
        'role': 'user'
    },
    'guest@aptitude.com': {
        'password': 'guest123', 
        'name': 'Guest User', 
        'role': 'user'
    }
}

# Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(10), nullable=False)

    @property
    def options(self):
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d
        }

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(120), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    questions = Question.query.all()
    return render_template('explore.html', questions=questions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in ALLOWED_USERS and ALLOWED_USERS[email]['password'] == password:
            session['user'] = email
            session['user_name'] = ALLOWED_USERS[email]['name']
            session['role'] = ALLOWED_USERS[email]['role']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials. This access is restricted.')
            
    return render_template('login.html')

@app.route('/post_question', methods=['GET', 'POST'])
def post_question():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        category = request.form.get('category')
        question_text = request.form.get('question')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_answer = request.form.get('correct_answer')
        
        new_question = Question(
            author=session['user_name'],
            category=category,
            text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            answer=correct_answer
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('explore'))
        
    return render_template('post_question.html')

@app.route('/question/<int:q_id>')
def view_question(q_id):
    question = Question.query.get_or_404(q_id)
    return render_template('question_page.html', q=question)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    question_id = data.get('question_id')
    selected_option = data.get('answer')
    
    # Handle anonymous users
    user_email = session.get('user', 'guest@anonymous')
    user_name = session.get('user_name', 'Guest')

    submission = Answer(
        student_email=user_email,
        student_name=user_name,
        question_id=int(question_id),
        answer=selected_option,
        timestamp=today
    )
    db.session.add(submission)
    db.session.commit()
    return jsonify({"status": "success", "message": "Answer saved!"})

import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Initialize with sample question if empty
        if not Question.query.first():
            sample_q = Question(
                author='Hari',
                category='Quantitative',
                text='Find next number 1, 3, 5, 7, ?',
                option_a='9',
                option_b='11',
                option_c='13',
                option_d='15',
                answer='A'
            )
            db.session.add(sample_q)
            db.session.commit()

    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
