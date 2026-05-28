from flask import Flask, render_template, session, redirect, url_for
from routes.usuarios import usuarios_bp, login_required
from routes.autores import autores_bp
from routes.livros import livros_bp
from routes.emprestimos import emprestimos_bp
from routes.emprestimo_livro import emprestimo_livro_bp
from routes.auth import auth_bp
from datetime import datetime
from config import config

app = Flask(__name__)

app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.FLASK_DEBUG

app.register_blueprint(auth_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(autores_bp)
app.register_blueprint(livros_bp)
app.register_blueprint(emprestimos_bp)
app.register_blueprint(emprestimo_livro_bp)

app.jinja_env.globals['now'] = datetime.now

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=config.FLASK_DEBUG)


