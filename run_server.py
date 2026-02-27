import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

from app import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
