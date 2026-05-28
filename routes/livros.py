from flask import Blueprint, request, render_template, redirect, flash, url_for, session
from db import conectar
from functools import wraps

livros_bp = Blueprint('livros', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@livros_bp.route('/livros')
@login_required
def listar_livros():
    q = request.args.get('q', '').strip()
    autor_id = request.args.get('autor', '').strip()
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
        where_clauses.append('(l.titulo LIKE %s OR a.nome LIKE %s)')
        params.extend([f'%{q}%'] * 2)
    if autor_id:
        where_clauses.append('l.id_autor = %s')
        params.append(autor_id)

    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM autores ORDER BY nome ASC')
    autores = cursor.fetchall()

    cursor.execute(f'SELECT COUNT(*) AS total FROM livros l JOIN autores a ON l.id_autor = a.id {where_sql}', params)
    total = cursor.fetchone()['total']

    cursor.execute(
        f'SELECT l.id, l.titulo, l.ano, l.capa, a.nome AS autor FROM livros l JOIN autores a ON l.id_autor = a.id {where_sql} ORDER BY l.titulo ASC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    livros = cursor.fetchall()
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template(
        'livros/listar.html',
        livros=livros,
        autores=autores,
        q=q,
        autor_id=autor_id,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page
    )

@livros_bp.route('/livros/add', methods=['GET','POST'])
@login_required
def add_livro():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM autores')
    autores = cursor.fetchall()

    if request.method == 'POST':
        data = request.form
        cursor = conn.cursor()
        capa = data.get('capa', '')
        if capa == '':
            capa = None
        elif len(capa) > 500:
            capa = capa[:500]
        try:
            ano = int(data.get('ano', 0))
            if ano < 1900 or ano > 2100:
                return "<script>alert('Ano deve estar entre 1900 e 2100'); window.history.back();</script>"
        except ValueError:
            return "<script>alert('Ano invalido'); window.history.back();</script>"
        cursor.execute('INSERT INTO livros (titulo,ano,id_autor,capa) VALUES (%s,%s,%s,%s)', (data['titulo'], ano, data['id_autor'], capa))
        conn.commit()
        return redirect('/livros')

    return render_template('livros/add.html', autores=autores)

@livros_bp.route('/livros/delete/<int:id>')
@login_required
def delete_livro(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM emprestimo_livro WHERE id_livro = %s", (id,))
    total = cursor.fetchone()[0]
    if total > 0:
        flash('Não é possível excluir: livro está vinculado a empréstimos.', 'error')
    else:
        cursor.execute('DELETE FROM livros WHERE id=%s', (id,))
        conn.commit()
        flash('Livro excluído com sucesso!', 'success')

    conn.close()
    return redirect('/livros')



@livros_bp.route('/livros/edit/<int:id>', methods=['GET', 'POST'])
def edit_livro(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        titulo = request.form['titulo']
        id_autor = request.form['id_autor']
        ano = request.form['ano']
        capa = request.form.get('capa')
        try:
            ano = int(ano)
            if ano < 1900 or ano > 2100:
                conn.close()
                return "<script>alert('Ano deve estar entre 1900 e 2100'); window.history.back();</script>"
        except ValueError:
            conn.close()
            return "<script>alert('Ano invalido'); window.history.back();</script>"
        if capa == '':
            capa = None
        elif capa and len(capa) > 500:
            capa = capa[:500]
        cursor.execute("UPDATE livros SET titulo = %s, id_autor = %s, ano = %s, capa = %s WHERE id = %s", (titulo, id_autor, ano, capa, id))

        conn.commit()
        conn.close()
        flash('Livro atualizado com sucesso!', 'success')
        return redirect('/livros')

    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT * FROM livros WHERE id = %s", (id,))
    livro = cursor1.fetchone() or {}
    cursor1.close()
    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM autores")
    autores = cursor2.fetchall()
    cursor2.close()

    conn.close()

    return render_template(
        'livros/edit.html',
        livro=livro,
        autores=autores
    )