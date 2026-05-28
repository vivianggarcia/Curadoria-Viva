from flask import Blueprint, request, render_template, redirect, flash, url_for, session
from db import conectar
from functools import wraps

emprestimo_livro_bp = Blueprint('emprestimo_livro', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@emprestimo_livro_bp.route('/emprestimo_livro')
@login_required
def listar():
    q = request.args.get('q', '').strip()
    emprestimo_id = request.args.get('emprestimo', '').strip()
    livro_id = request.args.get('livro', '').strip()
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
        where_clauses.append('(l.titulo LIKE %s OR e.id LIKE %s)')
        params.extend([f'%{q}%', f'%{q}%'])
    if emprestimo_id:
        where_clauses.append('e.id = %s')
        params.append(emprestimo_id)
    if livro_id:
        where_clauses.append('l.id = %s')
        params.append(livro_id)

    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM emprestimos ORDER BY id DESC')
    emprestimos = cursor.fetchall()
    cursor.execute('SELECT * FROM livros ORDER BY titulo ASC')
    livros = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) AS total FROM emprestimo_livro el JOIN emprestimos e ON el.id_emprestimo = e.id JOIN livros l ON el.id_livro = l.id ' + where_sql, params)
    total = cursor.fetchone()['total']

    cursor.execute(
        'SELECT el.id, e.id AS emprestimo, l.id AS id_livro, l.titulo AS livro, l.capa AS capa FROM emprestimo_livro el JOIN emprestimos e ON el.id_emprestimo = e.id JOIN livros l ON el.id_livro = l.id ' + where_sql + ' ORDER BY el.id DESC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    dados = cursor.fetchall()
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template(
        'emprestimo_livro/listar.html',
        dados=dados,
        emprestimos=emprestimos,
        livros=livros,
        q=q,
        emprestimo_id=emprestimo_id,
        livro_id=livro_id,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page
    )

@emprestimo_livro_bp.route('/emprestimo_livro/add', methods=['GET','POST'])
def add_relacao():
    conn = conectar()
    
    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT * FROM emprestimos")
    emprestimos = cursor1.fetchall()
    cursor1.close()

    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM livros")
    livros = cursor2.fetchall()
    cursor2.close()

    if request.method == 'POST':
        data = request.form
        
        # Verificar se a relação já existe
        cursor_check = conn.cursor()
        cursor_check.execute(
            "SELECT COUNT(*) as count FROM emprestimo_livro WHERE id_emprestimo = %s AND id_livro = %s",
            (data['id_emprestimo'], data['id_livro'])
        )
        result = cursor_check.fetchone()
        cursor_check.close()
        
        if result[0] > 0:
            flash('Esta relação entre empréstimo e livro já existe!', 'error')
            conn.close()
            return redirect('/emprestimo_livro/add')
        
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO emprestimo_livro (id_emprestimo, id_livro) VALUES (%s, %s)", (data['id_emprestimo'], data['id_livro']))
            conn.commit()
            flash('Relação criada com sucesso!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao criar relação: {str(e)}', 'error')
        finally:
            cursor.close()
        
        conn.close()
        return redirect('/emprestimo_livro')

    conn.close()
    return render_template(
        'emprestimo_livro/add.html',
        emprestimos=emprestimos,
        livros=livros
    )

@emprestimo_livro_bp.route('/emprestimo_livro/delete/<int:id>')
def delete_relacao(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM emprestimo_livro WHERE id = %s", (id,))

    conn.commit()
    conn.close()

    flash('Relação removida com sucesso!', 'success')

    return redirect('/emprestimo_livro')

@emprestimo_livro_bp.route('/emprestimo_livro/edit/<int:id>', methods=['GET', 'POST'])
def edit_relacao(id):
    conn = conectar()
    if request.method == 'POST':
        id_emprestimo = request.form['id_emprestimo']
        id_livro = request.form['id_livro']
        
        # Verificar se a relação já existe em outro registro
        cursor_check = conn.cursor()
        cursor_check.execute(
            "SELECT COUNT(*) as count FROM emprestimo_livro WHERE id_emprestimo = %s AND id_livro = %s AND id != %s",
            (id_emprestimo, id_livro, id)
        )
        result = cursor_check.fetchone()
        cursor_check.close()
        
        if result[0] > 0:
            flash('Esta relação entre empréstimo e livro já existe!', 'error')
            conn.close()
            return redirect(f'/emprestimo_livro/edit/{id}')
        
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE emprestimo_livro SET id_emprestimo = %s, id_livro = %s WHERE id = %s", (id_emprestimo, id_livro, id))
            conn.commit()
            flash('Vínculo atualizado com sucesso!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar relação: {str(e)}', 'error')
        finally:
            cursor.close()
        
        conn.close()
        return redirect('/emprestimo_livro')

    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT * FROM emprestimo_livro WHERE id = %s", (id,))
    relacao = cursor1.fetchone()
    cursor1.close()

    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM emprestimos")
    emprestimos = cursor2.fetchall()
    cursor2.close()

    cursor3 = conn.cursor(dictionary=True)
    cursor3.execute("SELECT * FROM livros")
    livros = cursor3.fetchall()
    cursor3.close()

    conn.close()

    return render_template(
        'emprestimo_livro/edit.html',
        relacao=relacao,
        emprestimos=emprestimos,
        livros=livros
    )

