import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime
import sys

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.error('{}, Article with id {} does not exists'.format(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),post_id))
        return render_template('404.html'), 404
    else:
        logger.info('{}, Article "{}" retrieved!'.format(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), post['title']))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.info('"About Us" page was retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logger.info('Article "{}" created'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz', methods=['GET'])
def healthz():

    response_body = {'result': 'OK - healthy'}
    status_code = 200

    try:
        db_checks()
    except Exception as exc:
        response_body = {
            'result': 'ERROR - unhealthy',
            'details': str(exc),
        }
        status_code = 500

    response = app.response_class(
        response=json.dumps(response_body),
        status=status_code,
        mimetype='application/json')

    return response

@app.route('/metrics', methods=['GET'])
def metrics():
    
    response = app.response_class(
        response=json.dumps(get_system_matrices()),
        status=200,
        mimetype='application/json')

    return response

def db_checks():
    try:
        connection = get_db_connection()
        connection.execute('SELECT * FROM posts limit 1').fetchone()
        connection.close()
    except:
        raise Exception("Table 'posts' does not exist")

def get_system_matrices():
    metrics_obj = {
        'db_connection_count': 0,
        'post_count': None,
    }
    connection = get_db_connection()
    article_count = connection.execute('SELECT count(*) FROM posts').fetchone()
    connection.close()

    metrics_obj['db_connection_count'] += 1
    metrics_obj['post_count'] = article_count[0]
    
    return metrics_obj

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(filename='app.log',level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
