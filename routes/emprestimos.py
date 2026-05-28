from flask import Blueprint, request, render_template, redirect, flash, url_for, session
from db import conectar
from functools import wraps
import datetime

now = datetime.datetime.now()
emprestimos_bp = Blueprint('emprestimos', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@emprestimos_bp.route('/emprestimos')
@login_required
def listar_emprestimos():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
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
        where_clauses.append('(u.nome LIKE %s OR l.titulo LIKE %s OR e.id LIKE %s)')
        params.extend([f'%{q}%'] * 3)

    if status == 'finalizado':
        where_clauses.append('e.data_devolucao IS NOT NULL AND e.data_devolucao < CURDATE()')
    elif status == 'andamento':
        where_clauses.append('e.data_devolucao IS NOT NULL AND e.data_devolucao >= CURDATE()')
    elif status == 'sem_data':
        where_clauses.append('e.data_devolucao IS NULL')

    where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS total FROM emprestimos e JOIN usuarios u ON e.id_usuario = u.id LEFT JOIN emprestimo_livro el ON el.id_emprestimo = e.id LEFT JOIN livros l ON l.id = el.id_livro ' + where_sql, params)
    total = cursor.fetchone()['total']

    cursor.execute(
        'SELECT e.id, u.nome AS usuario, u.foto AS foto_usuario, e.data_emprestimo, e.data_devolucao, l.titulo AS livro, l.id AS id_livro, l.capa FROM emprestimos e JOIN usuarios u ON e.id_usuario = u.id LEFT JOIN emprestimo_livro el ON el.id_emprestimo = e.id LEFT JOIN livros l ON l.id = el.id_livro ' + where_sql + ' ORDER BY e.id DESC LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )
    emprestimos = cursor.fetchall()
    cursor.close()
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template(
        'emprestimos/listar.html',
        emprestimos=emprestimos,
        now=now,
        q=q,
        status=status,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page
    )

@emprestimos_bp.route('/emprestimos/add', methods=['GET', 'POST'])
def add_emprestimo():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        id_usuario = request.form['id_usuario']
        data_emprestimo = request.form['data_emprestimo']
        data_devolucao = request.form.get('data_devolucao')

        if data_devolucao:
            d1 = datetime.datetime.strptime(data_emprestimo, "%Y-%m-%d")
            d2 = datetime.datetime.strptime(data_devolucao, "%Y-%m-%d")
            if d2 < d1:
                return """
                <script>
                    alert('A data de devolução não pode ser anterior à data de empréstimo!');
                    window.history.back();
                </script>
                """
        id_livros = request.form.getlist('id_livro')

        cursor.execute("INSERT INTO emprestimos (id_usuario, data_emprestimo, data_devolucao) VALUES (%s, %s, %s)", (id_usuario, data_emprestimo, data_devolucao))

        id_emprestimo = cursor.lastrowid

        for id_livro in id_livros:
            cursor.execute("INSERT INTO emprestimo_livro (id_emprestimo, id_livro) VALUES (%s, %s)", (id_emprestimo, id_livro))

        conn.commit()
        return redirect('/emprestimos')

    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT * FROM usuarios")
    usuarios = cursor1.fetchall()
    cursor1.close()

    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM livros")
    livros = cursor2.fetchall()
    cursor2.close()
    
    conn.close()
    return render_template(
        'emprestimos/add.html',
        usuarios=usuarios,
        livros=livros
    )

@emprestimos_bp.route('/emprestimos/delete/<int:id>')
def delete_emprestimo(id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM emprestimos WHERE id = %s", (id,))
        existe = cursor.fetchone()[0]

        if existe == 0:
            return """
            <script>
                alert('Empréstimo não encontrado.');
                window.location.href = '/emprestimos';
            </script>
            """
        cursor.execute("DELETE FROM emprestimo_livro WHERE id_emprestimo = %s", (id,))
        cursor.execute("DELETE FROM emprestimos WHERE id = %s", (id,))

        conn.commit()

        return """
        <script>
            alert('Empréstimo excluído com sucesso!');
            window.location.href = '/emprestimos';
        </script>
        """

    except Exception as e:
        print("erro ao deletar:", e)

        return """
        <script>
            alert('Erro ao excluir empréstimo.');
            window.location.href = '/emprestimos';
        </script>
        """

    finally:
        conn.close()

@emprestimos_bp.route('/emprestimos/edit/<int:id>', methods=['GET', 'POST'])
def edit_emprestimo(id):
    if request.method == 'POST':
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        id_usuario = request.form['id_usuario']
        id_livro = request.form['id_livro']
        data_emprestimo = request.form['data_emprestimo']
        data_devolucao = request.form.get('data_devolucao') or None
        if data_devolucao:
            d1 = datetime.datetime.strptime(data_emprestimo, "%Y-%m-%d")
            d2 = datetime.datetime.strptime(data_devolucao, "%Y-%m-%d")
            if d2 < d1:
                conn.close()
                return """
                <script>
                    alert('Data de devolução não pode ser menor que a de empréstimo!');
                    window.history.back();
                </script>
                """
        cursor.execute("UPDATE emprestimos SET id_usuario = %s, data_emprestimo = %s, data_devolucao = %s WHERE id = %s", (id_usuario, data_emprestimo, data_devolucao, id))
        cursor.execute("DELETE FROM emprestimo_livro WHERE id_emprestimo = %s", (id,))
        cursor.execute("INSERT INTO emprestimo_livro (id_emprestimo, id_livro) VALUES (%s, %s)", (id, id_livro))

        conn.commit()
        conn.close()
        return redirect('/emprestimos')

    conn = conectar()
    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT e.*, el.id_livro FROM emprestimos e LEFT JOIN emprestimo_livro el ON el.id_emprestimo = e.id WHERE e.id = %s", (id,))
    resultado = cursor1.fetchall()
    emprestimo = resultado[0] if resultado else None
    cursor1.close()

    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM usuarios")
    usuarios = cursor2.fetchall()
    cursor2.close()

    cursor3 = conn.cursor(dictionary=True)
    cursor3.execute("SELECT * FROM livros")
    livros = cursor3.fetchall()
    cursor3.close()

    conn.close()

    return render_template(
    'emprestimos/edit.html',
    emprestimo=emprestimo,
    usuarios=usuarios,
    livros=livros,
    now=datetime.datetime.now()
)