from flask import Blueprint, request, render_template, redirect, flash
from db import conectar

autores_bp = Blueprint('autores', __name__)

@autores_bp.route('/autores')
def listar_autores():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM autores')
    autores = cursor.fetchall()
    return render_template('autores/listar.html', autores=autores)

@autores_bp.route('/autores/add', methods=['GET','POST'])
def add_autor():
    if request.method == 'POST':
        nome = request.form['nome']
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO autores (nome) VALUES (%s)', (nome,))
        conn.commit()
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