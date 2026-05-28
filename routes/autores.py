from flask import Blueprint, request, render_template, redirect, flash, url_for, session
from db import conectar
from functools import wraps

autores_bp = Blueprint('autores', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@autores_bp.route('/autores')
@login_required
def listar_autores():
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
        where_clauses.append('nome LIKE %s')
        params.append(f'%{q}%')

    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SELECT COUNT(*) AS total FROM autores {where_sql}', params)
    total = cursor.fetchone()['total']

    cursor.execute(
        f'SELECT * FROM autores {where_sql} ORDER BY nome ASC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    autores = cursor.fetchall()
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template('autores/listar.html', autores=autores, q=q, page=page, total_pages=total_pages, total=total, per_page=per_page)

@autores_bp.route('/autores/add', methods=['GET','POST'])
def add_autor():
    if request.method == 'POST':
        nome = request.form['nome']
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO autores (nome) VALUES (%s)', (nome,))
        conn.commit()
        conn.close()
        return redirect('/autores')
    return render_template('autores/add.html')

@autores_bp.route('/autores/edit/<int:id>', methods=['GET', 'POST'])
def edit_autor(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        cursor.execute('UPDATE autores SET nome=%s WHERE id=%s', (nome, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/autores')

    cursor.execute('SELECT * FROM autores WHERE id=%s', (id,))
    autor = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('autores/edit.html', autor=autor)

@autores_bp.route('/autores/delete/<int:id>')
def delete_autor(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM livros WHERE id_autor = %s", (id,))
    total = cursor.fetchone()[0]

    if total > 0:
        flash('Não é possível excluir: autor possui livros vinculados.', 'error')
    else:
        cursor.execute('DELETE FROM autores WHERE id=%s', (id,))
        conn.commit()
        flash('Autor excluído com sucesso!', 'success')

    conn.close()
    return redirect('/autores')