from flask import Flask, render_template, request, redirect, url_for, flash, session
import fdb

app = Flask(__name__)

app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

host = 'localhost'
database = r'C:\Users\Aluno\Downloads\orca_facil\VENDA.FDB'
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)

class cadastro:
    def __init__(self, id_cadastro, nome, email, senha):
        self.id_cadastro = id_cadastro
        self.nome = nome
        self.email = email
        self.senha = senha

class despesa:
    def __init__(self, id_despesa, valor_ultima_despesas, fonte_ultima_despesas, data_ultima_despesas, id_usuario):
        self.id_despesa = id_despesa
        self.valor_ultima_despesas = valor_ultima_despesas
        self.fonte_ultima_despesas = fonte_ultima_despesas
        self.data_ultima_despesas = data_ultima_despesas
        self.id_usuario = id_usuario

class receita:
    def __init__(self, id_receitas, valor_ultima_receitas, fonte_ultima_receitas, data_ultima_receitas, id_usuario):
        self.id_receitas = id_receitas
        self.valor_ultima_receitas = valor_ultima_receitas
        self.fonte_ultima_receitas = fonte_ultima_receitas
        self.data_ultima_receitas = data_ultima_receitas
        self.id_usuario = id_usuario

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/principal')
def principal():


    total_receitas = 0
    total_despesas = 0

    if 'id_usuario' not in session:
        flash('Voce precisa estar logado nesse belisssimo sistema')
        return redirect(url_for('login'))

    cursor = con.cursor()
    id_usuario = session['id_usuario']
    nome = session['nome']

    cursor.execute("SELECT coalesce(valor_ultima_receitas, 0) FROM receitas where id_usuario = ?", (id_usuario, ))
    for valor in cursor.fetchall():
        total_receitas = total_receitas + valor[0]

    cursor.execute("SELECT coalesce(valor_ultima_despesas, 0) FROM despesa where id_usuario = ?", (id_usuario,))
    for valor in cursor.fetchall():
        total_despesas = total_despesas + valor[0]

    saldo = total_receitas - total_despesas
    cursor.close()

    return render_template('index.html', saldo=saldo, nome=nome)
@app.route('/receitas', methods=['GET', 'POST'])
def receitas():
    id_usuario = session['id_usuario']
    if request.method == 'POST':
        valor = request.form['valor']
        fonte = request.form['fonte']
        data = request.form['data']
        id_usuario = session['id_usuario']

        valor_float = float(valor)
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO receitas (valor_ultima_receitas, fonte_ultima_receitas, data_ultima_receitas, id_usuario) VALUES (?, ?, ?, ?)",
            (valor_float, fonte, data, id_usuario)
        )
        con.commit()
        cursor.close()
        return redirect(url_for('receitas'))

    if request.method =='GET':
        cursor = con.cursor()
        cursor.execute('select id_receita, valor_ultima_receitas, fonte_ultima_receitas, data_ultima_receitas from receitas where id_usuario = ?', (id_usuario,))
        receitas = cursor.fetchall()
        return render_template('receitas.html', receitas=receitas)

@app.route('/despesas', methods=['GET', 'POST'])
def despesas():
    id_usuario = session['id_usuario']
    if request.method == 'POST':
        valor = request.form['valor']
        fonte = request.form['fonte']
        data = request.form['data']



        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO despesa (valor_ultima_despesas, fonte_ultima_despesas, data_ultima_despesas, id_usuario) VALUES (?, ?, ?, ?)",
            (valor, fonte, data, id_usuario)
        )
        con.commit()
        cursor.close()
        return redirect(url_for('despesas'))

    if request.method =='GET':
        cursor = con.cursor()
        cursor.execute('select id_despesa, valor_ultima_despesas, fonte_ultima_despesas, data_ultima_despesas from despesa where id_usuario = ?', (id_usuario,))
        despesas = cursor.fetchall()
        print(despesas)
        return render_template('despesas.html', despesas=despesas)


@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        flash('Login não necessário. Você está logado como visitante.', 'info')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/entrar', methods=['POST'])
def entrar():
    email = request.form['email']
    senha = request.form['senha']

    cursor = con.cursor()

    cursor.execute("SELECT c.ID_CADASTRO, c.NOME, c.EMAIL FROM CADASTRO c WHERE c.EMAIL = ? AND c.SENHA = ?", (email, senha))
    usuario = cursor.fetchone()

    if usuario:
        session['id_usuario'] = usuario[0]
        session['nome'] = usuario[1]
        return redirect(url_for('principal'))
    flash("Login ou senha incorretos.")
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        cursor = con.cursor()
        cursor.execute('select id_cadastro, nome, email, senha from cadastro where email = ?', (email,))
        if cursor.fetchone():
            flash('Este email já esta sendo usado em outra conta')
            return redirect(url_for('cadastrar'))

        cursor.execute("INSERT INTO cadastro (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
        con.commit()
        cursor.close()
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('cadastrar.html')


@app.route('/atualizar')
def atualizar():
    return render_template('editar.html', titulo='Editar Receita')


@app.route('/editar_outro/<int:id>', methods=['GET', 'POST'], endpoint='editar_outro')
def editar_outro(id):

    id_usuario = session['id_usuario']
    cursor = con.cursor()  # Abre o cursor

    # Buscar a despesa específico para edição
    cursor.execute("SELECT id_despesa, valor_ultima_despesas, fonte_ultima_despesas, data_ultima_despesas, id_usuario FROM despesa WHERE id_despesa = ?", (id,id_usuario))
    despesa = cursor.fetchone()

    if not despesa:
        cursor.close()  # Fecha o cursor se o livro não for encontrado
        flash("Despesa não encontrada!", "error")
        return redirect(url_for('despesas'))  # Redireciona para a página principal se o livro não for encontrado

    if request.method == 'POST':
        # Coleta os dados do formulário
        valor = request.form['valor']
        fonte = request.form['fonte']
        data = request.form['data']

        # Atualiza o livro no banco de dados
        cursor.execute("UPDATE despesa SET valor_ultima_despesas = ?, fonte_ultima_despesas = ?, data_ultima_despesas = ? WHERE id_despesa = ?",
                       (valor, fonte, data, id))
        con.commit()  # Salva as mudanças no banco de dados
        cursor.close()  # Fecha o cursor
        flash("Despesa atualizada com sucesso!", "success")
        return redirect(url_for('despesas'))  # Redireciona para a página principal após a atualização

    cursor.close()  # Fecha o cursor ao final da função, se não for uma requisição POST
    return render_template('editar_outro.html', despesa=despesa, titulo='Editar Despesa')  # Renderiza a página de edição


@app.route('/editar/<int:id>', methods=['GET', 'POST'], endpoint='editar')
def editar(id):
    id_usuario = session['id_usuario']
    cursor = con.cursor()  # Abre o cursor

    # Buscar o livro específico para edição

    cursor.execute("SELECT id_receita, valor_ultima_receitas, fonte_ultima_receitas, data_ultima_receitas FROM receitas WHERE id_receita = ? and id_usuario = ?", (id, id_usuario))
    receita = cursor.fetchone()

    if not receita:
        cursor.close()  # Fecha o cursor se o livro não for encontrado
        flash("Receita não encontrada!", "error")
        return redirect(url_for('receitas'))  # Redireciona para a página principal se a receita não for encontrado

    if request.method == 'POST':
        # Coleta os dados do formulário
        valor = request.form['valor']
        fonte = request.form['fonte']
        data = request.form['data']

        # Atualiza o livro no banco de dados
        cursor.execute("UPDATE receitas SET valor_ultima_receitas = ?, fonte_ultima_receitas = ?, data_ultima_receitas = ? WHERE id_receita = ?",
                       (valor, fonte, data, id))
        con.commit()  # Salva as mudanças no banco de dados
        cursor.close()  # Fecha o cursor
        flash("Receita atualizada com sucesso!", "success")
        return redirect(url_for('receitas'))  # Redireciona para a página principal após a atualização

    cursor.close()  # Fecha o cursor ao final da função, se não for uma requisição POST
    return render_template('editar.html', receita=receita, titulo='Editar Receita')  # Renderiza a página de edição


@app.route('/deletar/<int:id>', methods=('POST',))
def deletar(id):
    cursor = con.cursor()  # Abre o cursor

    try:
        cursor.execute('DELETE FROM receitas WHERE id_receita = ?', (id,))
        con.commit()  # Salva as alterações no banco de dados
        flash('Receita excluído com sucesso!', 'success')  # Mensagem de sucesso
    except Exception as e:
        con.rollback()  # Reverte as alterações em caso de erro
        flash('Erro ao excluir a receita.', 'error')  # Mensagem de erro
    finally:
        cursor.close()  # Fecha o cursor independentemente do resultado

    return redirect(url_for('receitas'))  # Redireciona para a página principal

@app.route('/deletar_outro/<int:id>', methods=('POST',))
def deletar_outro(id):
    cursor = con.cursor()  # Abre o cursor

    try:
        cursor.execute('DELETE FROM despesa WHERE id_despesa = ?', (id,))
        con.commit()  # Salva as alterações no banco de dados
        flash('Despesa excluído com sucesso!', 'success')  # Mensagem de sucesso
    except Exception as e:
        con.rollback()  # Reverte as alterações em caso de erro
        flash('Erro ao excluir a despesa.', 'error')  # Mensagem de erro
    finally:
        cursor.close()  # Fecha o cursor independentemente do resultado

    return redirect(url_for('despesas'))  # Redireciona para a página principal

@app.route('/sobre')
def sobre():



    return render_template('sobre.html')


if __name__ == '__main__':
    app.run(debug=True)