from flask import Blueprint, request, render_template, redirect, session, flash, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from db import conectar
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'error')
            return redirect('/login')
        
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, email, senha, nome FROM usuarios WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_nome'] = user['nome']
            flash(f'Bem-vindo, {user["nome"]}!', 'success')
            return redirect('/')
        else:
            flash('Email ou senha incorretos.', 'error')
        
        return redirect('/login')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'success')
    return redirect('/login')
