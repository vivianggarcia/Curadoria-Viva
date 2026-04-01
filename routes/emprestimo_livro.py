from flask import Blueprint, request, render_template, redirect, flash
from db import conectar

emprestimo_livro_bp = Blueprint('emprestimo_livro', __name__)

@emprestimo_livro_bp.route('/emprestimo_livro')
def listar():
    conn = conectar()
    
    cursor1 = conn.cursor(dictionary=True)
    cursor1.execute("SELECT el.id, e.id AS emprestimo, l.id AS id_livro, l.titulo AS livro, l.capa AS capa FROM emprestimo_livro el JOIN emprestimos e ON el.id_emprestimo = e.id JOIN livros l ON el.id_livro = l.id")
    dados = cursor1.fetchall()
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
        'emprestimo_livro/listar.html',
        dados=dados,
        emprestimos=emprestimos,
        livros=livros
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
        cursor = conn.cursor()
        cursor.execute("INSERT INTO emprestimo_livro (id_emprestimo, id_livro) VALUES (%s, %s)", (data['id_emprestimo'], data['id_livro']))
        conn.commit()
        cursor.close()
        return redirect('/emprestimo_livro')

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
        cursor = conn.cursor()
        cursor.execute("UPDATE emprestimo_livro SET id_emprestimo = %s, id_livro = %s WHERE id = %s", (id_emprestimo, id_livro, id))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Vínculo atualizado com sucesso!', 'success')
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

