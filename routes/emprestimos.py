from flask import Blueprint, request, render_template, redirect
from db import conectar
import datetime

now = datetime.datetime.now() 
emprestimos_bp = Blueprint('emprestimos', __name__)

@emprestimos_bp.route('/emprestimos')
def listar_emprestimos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT e.id, u.nome AS usuario, u.foto AS foto_usuario, e.data_emprestimo, e.data_devolucao, l.titulo AS livro, l.id AS id_livro, l.capa FROM emprestimos e JOIN usuarios u ON e.id_usuario = u.id LEFT JOIN emprestimo_livro el ON el.id_emprestimo = e.id LEFT JOIN livros l ON l.id = el.id_livro ORDER BY e.id DESC")
    emprestimos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        'emprestimos/listar.html',
        emprestimos=emprestimos,
        now=now
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