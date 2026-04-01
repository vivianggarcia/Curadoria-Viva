from flask import Blueprint, request, render_template, redirect, flash
from db import conectar

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios')
def listar():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    dados = cursor.fetchall()
    conn.close()
    return render_template('usuarios/listar.html', usuarios=dados)

@usuarios_bp.route('/usuarios/add', methods=['GET','POST'])
def add():
    if request.method == 'POST':
        data = request.form
        foto = data.get('foto', '')
        if foto == '':
            foto = None
        elif len(foto) > 500:
            foto = foto[:500]
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (nome, email, telefone, foto) VALUES (%s, %s, %s, %s)', (data['nome'], data['email'], data['telefone'], foto))
        conn.commit()
        conn.close()
        return redirect('/usuarios')

    return render_template('usuarios/add.html', user=None)

@usuarios_bp.route('/usuarios/edit/<int:id>', methods=['GET','POST'])
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
        cursor.execute('UPDATE usuarios SET nome=%s, email=%s, telefone=%s, foto=%s WHERE id=%s', (data['nome'], data['email'], data['telefone'], foto, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/usuarios')

    cursor.execute('SELECT * FROM usuarios WHERE id=%s', (id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('usuarios/edit.html', user=user)

@usuarios_bp.route('/usuarios/delete/<int:id>')
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