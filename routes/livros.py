from flask import Blueprint, request, render_template, redirect, flash
from db import conectar

livros_bp = Blueprint('livros', __name__)


@livros_bp.route('/livros')
def listar_livros():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT l.id, l.titulo, l.ano, l.capa, a.nome AS autor FROM livros l JOIN autores a ON l.id_autor = a.id")
    livros = cursor.fetchall()
    return render_template('livros/listar.html', livros=livros)

@livros_bp.route('/livros/add', methods=['GET','POST'])
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