
from flask import Flask
from modules.routes import init_routes

app = Flask(__name__, template_folder='templates', static_folder='static')

#session management
app.secret_key = 'your_secret_key_here'


init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
