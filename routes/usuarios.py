from flask import Blueprint, request, render_template, redirect, flash, url_for, session
from db import conectar
from functools import wraps
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint('usuarios', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@usuarios_bp.route('/usuarios')
@login_required
def listar():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', '1')
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    per_page = 6
    offset = (page - 1) * per_page

    where_clauses = []
    params = []
    if q:
        where_clauses.append('(nome LIKE %s OR email LIKE %s OR telefone LIKE %s)')
        params.extend([f'%{q}%'] * 3)

    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f'SELECT COUNT(*) AS total FROM usuarios {where_sql}', params)
    total = cursor.fetchone()['total']

    cursor.execute(
        f'SELECT * FROM usuarios {where_sql} ORDER BY nome ASC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    dados = cursor.fetchall()
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template(
        'usuarios/listar.html',
        usuarios=dados,
        q=q,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page
    )

@usuarios_bp.route('/usuarios/add', methods=['GET','POST'])
@login_required
def add():
    if request.method == 'POST':
        data = request.form
        foto = data.get('foto', '')
        if foto == '':
            foto = None
        elif len(foto) > 500:
            foto = foto[:500]
        
        # Hash da senha
        senha = data.get('senha', '').strip()
        if not senha:
            flash('Senha é obrigatória.', 'error')
            return render_template('usuarios/add.html', user=None)
        
        senha_hash = generate_password_hash(senha)
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (nome, email, telefone, foto, senha) VALUES (%s, %s, %s, %s, %s)', (data['nome'], data['email'], data['telefone'], foto, senha_hash))
        conn.commit()
        conn.close()
        flash('Usuário criado com sucesso!', 'success')
        return redirect('/usuarios')

    return render_template('usuarios/add.html', user=None)

@usuarios_bp.route('/usuarios/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data = request.form
        foto = data.get('foto', '')
        if foto == '':
            foto = None
        elif len(foto) > 500:
            foto = foto[:500]
        
        # preparar dados para update
        update_fields = ['nome=%s', 'email=%s', 'telefone=%s', 'foto=%s']
        update_values = [data['nome'], data['email'], data['telefone'], foto]
        
        # se senha foi fornecida atualizar tb
        senha = data.get('senha', '').strip()
        if senha:
            update_fields.append('senha=%s')
            update_values.append(generate_password_hash(senha))
        
        update_values.append(id)
        
        update_sql = 'UPDATE usuarios SET ' + ', '.join(update_fields) + ' WHERE id=%s'
        cursor.execute(update_sql, update_values)
        conn.commit()
        cursor.close()
        conn.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect('/usuarios')

    cursor.execute('SELECT * FROM usuarios WHERE id=%s', (id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('usuarios/edit.html', user=user)

@usuarios_bp.route('/usuarios/delete/<int:id>')
@login_required
def delete(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM emprestimos WHERE id_usuario = %s", (id,))
    total = cursor.fetchone()[0]
    cursor.close()

    if total > 0:
        flash('Nao eh possivel excluir: usuario possui emprestimos vinculados.', 'error')
    else:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM usuarios WHERE id=%s', (id,))
        conn.commit()
        cursor.close()
        flash('Usuario excluido com sucesso!', 'success')

    conn.close()
    return redirect('/usuarios')