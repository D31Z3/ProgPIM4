####################################################################
#Programação requirements

#region: Requirements

from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from functools import wraps

#endregion

####################################################################
#Programação inicio

#region: Inicio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://JOAOHERMENEGILD/FazendaUrbanaLotus?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Lista de caminhos de URL que não exigem login
rotas_livres = ['/', '/login']

@app.before_request
def check_login():
    # Verifica se a rota atual é uma exceção com base no caminho da URL
    if request.path not in rotas_livres and 'user_id' not in session:
        flash('Por favor, faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))


@app.route('/')
def index():
    
    return render_template('index.html')

def verificar_acesso(setores_permitidos):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario_setor = session.get('setor')  # Armazene o setor do usuário na sessão ao fazer login
            if usuario_setor not in setores_permitidos:
                flash("Você não tem acesso a essa área, contate seu administrador", "danger")
                return redirect(url_for('pagina_erro'))  # Redirecionar para uma página de erro ou página inicial
            return func(*args, **kwargs)
        return wrapper
    return decorator

#endregion

####################################################################
#Programação colaboradores
#region: Colaboradores

class Colaborador(db.Model):
    __tablename__ = 'Colaborador'
    id = db.Column('id_Colaborador', db.Integer, primary_key=True, nullable=False)
    nome = db.Column('nome_Colaborador', db.String(100), nullable=False)
    email = db.Column('email_Colaborador', db.String(120), unique=True, nullable=False)
    setor = db.Column('setor_Colaborador', db.String(50), nullable=False)
    usuario = db.Column('usuario_Colaborador', db.String(50), unique=True, nullable=False)
    senha = db.Column('senha_Colaborador', db.String(128), nullable=False)  # Armazena a senha criptografada

    #pedidos = db.relationship('Pedido', backref='colaborador', lazy=True)



@app.route('/colaborador')
@verificar_acesso(['Recursos humanos', 'Administrador'])
def colaborador():
    colaboradores = Colaborador.query.all()
    return render_template('colaborador/Colaborador.html', colaboradores=colaboradores)

@app.route('/adicionar_colaborador', methods=['GET', 'POST'])
def adicionar_colaborador():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        setor = request.form['setor']
        usuario = request.form['usuario']
        senha = request.form['senha']

        # Validação básica
        if not nome or not email or not usuario or not senha:
            flash('Por favor, preencha todos os campos.')
            return redirect('/adicionar_colaborador')  # Redireciona para o formulário

        # Criptografando a senha
        senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

        novo_colaborador = Colaborador(nome=nome, email=email, setor=setor, usuario=usuario, senha=senha_criptografada)
        db.session.add(novo_colaborador)
        db.session.commit()

        flash('Colaborador adicionado com sucesso!')
        return redirect('/colaborador')  # Redireciona para a página de colaboradores

@app.route('/editar_colaborador/<int:colaborador_id>', methods=['GET', 'POST'])
def editar_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)
    if request.method == 'POST':
        colaborador.nome = request.form['nome']
        colaborador.email = request.form['email']
        db.session.commit()
        flash('Colaborador atualizado com sucesso!')  # Mensagem de sucesso ao atualizar
        return redirect(url_for('colaborador'))  # Redireciona para a página de colaboradores

    return render_template('colaborador/item_Colaborador.html', colaborador=colaborador)


@app.route('/excluir_colaborador/<int:colaborador_id>', methods=['POST'])
def excluir_colaborador(colaborador_id):
    colaborador = Colaborador.query.get_or_404(colaborador_id)

    # Verifica se o colaborador é administrador
    if colaborador.setor == 'Administrador':
        flash('Não é possível excluir um administrador.', 'danger')
        return redirect(url_for('colaborador'))

    db.session.delete(colaborador)
    db.session.commit()
    flash('Colaborador excluído com sucesso!', 'success')
    return redirect(url_for('colaborador'))


@app.route('/pesquisar_colaborador', methods=['GET'])
def pesquisar_colaborador():
    nome = request.args.get('nome', '').strip()
    if nome:
        colaboradores = Colaborador.query.filter(Colaborador.nome.like(f"%{nome}%")).all()
    else:
        colaboradores = Colaborador.query.all()
    return render_template('colaborador/Colaborador.html', colaboradores=colaboradores)

@app.route('/alterar_senha', methods=['GET', 'POST'])
def alterar_senha():
    usuario_id = session.get('user_id')  # Obtém o ID do usuário logado
    colaborador = Colaborador.query.get(usuario_id)  # Busca o colaborador pelo ID

    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']

        # Verifica se a senha atual está correta
        if bcrypt.check_password_hash(colaborador.senha, senha_atual):
            # Criptografa a nova senha
            nova_senha_criptografada = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            colaborador.senha = nova_senha_criptografada  # Atualiza a senha
            db.session.commit()  # Salva as alterações
            flash('Senha alterada com sucesso!', 'success_alterar_senha')  # Mensagem de sucesso
        else:
            flash('Senha atual incorreta. Tente novamente.', 'danger_alterar_senha')  # Mensagem de erro

    # Retorna para a mesma página com as mensagens flash
    return render_template('configuracoes/alterarSenha.html', colaborador=colaborador)



#endregion

####################################################################
#PROGRAMAÇÃO producao
#region: Producao


class Producao(db.Model):
    __tablename__ = 'Producao'
    id = db.Column('id_Producao', db.Integer, primary_key=True, nullable=False)
    nome = db.Column('nome_Producao', db.String(100), nullable=True)
    fornecedor = db.Column('fornecedor_Producao', db.String(100), nullable=True)
    quantidade = db.Column('quantidade_Producao', db.Integer, nullable=True)
    data = db.Column('data_Producao', db.Date, nullable=True)
    preco = db.Column('preco_Producao', db.Float, nullable=True)

    #pedidos = db.relationship('Pedido', backref='produto', lazy=True)    


@app.route('/producao')  # Atualizando a rota
@verificar_acesso(['Producao', 'Administrador'])
def producao():
    producoes = Producao.query.all()  # Atualizando a consulta para 'Produção'
    return render_template('producao/Producao.html', producoes=producoes)  # Atualizando o template

@app.route('/adicionar_producao', methods=['GET', 'POST'])  # Atualizando a rota
def adicionar_producao():  # Atualizando a função
    if request.method == 'POST':
        nome = request.form['nome']
        fornecedor = request.form['fornecedor']
        quantidade = request.form['quantidade']
        data = datetime.strptime(request.form['data'],'%Y-%m-%d').date()
        preco = request.form['preco']

        # Validação básica
        if not nome or not fornecedor or not quantidade or not data or not preco:
            flash('Por favor, preencha todos os campos.')
            return redirect('/adicionar_producao')  # Atualizando o redirecionamento

        nova_producao = Producao(
            nome=nome,
            fornecedor=fornecedor,
            quantidade=quantidade,
            data=data,
            preco=preco
        )  # Atualizando para 'Produção'
        db.session.add(nova_producao)
        db.session.commit()

        flash('Produção adicionada com sucesso!')  # Atualizando a mensagem
        return redirect('/producao')  # Atualizando o redirecionamento


@app.route('/editar_producao/<int:producao_id>', methods=['POST'])
def editar_producao(producao_id):
    producao = Producao.query.get_or_404(producao_id)
    if request.method == 'POST':
        producao.nome = request.form['nome']
        producao.fornecedor = request.form['fornecedor']
        producao.quantidade = request.form['quantidade']
        producao.data = datetime.strptime(request.form['data'],'%Y-%m-%d').date()
        producao.preco = request.form['preco']
        db.session.commit()
        return redirect(url_for('producao', producao_id = producao.id))  # Redireciona para a lista de produções


@app.route('/excluir_producao/<int:producao_id>', methods=['POST'])
def excluir_producao(producao_id):
    try:
        producao = Producao.query.get_or_404(producao_id)
        print(f'Tentando excluir a produção: {producao}')
        db.session.delete(producao)
        db.session.commit()
        flash('Produção excluída com sucesso!', 'success')
    except Exception as e:
        print(f'Erro ao excluir produção: {e}')  # Imprime o erro no console
        flash(f'Ocorreu um erro ao excluir a produção: {e}', 'danger')
    return redirect(url_for('producao'))

@app.route('/pesquisar_producao', methods=['GET'])
def pesquisar_producao():
    nome = request.args.get('nome', '').strip()
    if nome:
        producoes = Producao.query.filter(Producao.nome.like(f"%{nome}%")).all()
    else:
        producoes = Producao.query.all()
    return render_template('producao/Producao.html', producoes=producoes)


#endregion

####################################################################
#PROGRAMAÇÃO fornecedor
#region: Fornecedor

class Fornecedor(db.Model):
    __tablename__ = 'Fornecedor'
    id = db.Column('id_Fornecedor', db.Integer, primary_key=True, nullable=False)
    nome = db.Column('nome_Fornecedor', db.String(100), nullable=False)
    endereco = db.Column('endereco_Fornecedor', db.String(200), nullable=True)
    cnpj_pf = db.Column('cnpj_pf_Fornecedor', db.String(18), nullable=True)
    contato = db.Column('contato_Fornecedor', db.String(100), nullable=True)
    email = db.Column('email_Fornecedor', db.String(100), nullable=True)

    #pedidos = db.relationship('Pedido', backref='fornecedor', lazy=True)
    
    


@app.route('/fornecedores')
@verificar_acesso(['Vendas', 'Administrador'])
def fornecedores():
    fornecedores = Fornecedor.query.all()
    return render_template('fornecedor/Fornecedor.html', fornecedores=fornecedores)

@app.route('/adicionar_fornecedor', methods=['GET', 'POST'])
def adicionar_fornecedor():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        cnpj_pf = request.form['cnpj_pf']
        contato = request.form['contato']
        email = request.form['email']

        if not nome:
            flash('Por favor, preencha o nome do fornecedor.')
            return redirect('/adicionar_fornecedor')

        novo_fornecedor = Fornecedor(
            nome=nome,
            endereco=endereco,
            cnpj_pf=cnpj_pf,
            contato=contato,
            email=email
        )
        db.session.add(novo_fornecedor)
        db.session.commit()
        flash('Fornecedor adicionado com sucesso!')
        return redirect('/fornecedores')

@app.route('/editar_fornecedor/<int:fornecedor_id>', methods=['POST'])
def editar_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    if request.method == 'POST':
        fornecedor.nome = request.form['nome']
        fornecedor.endereco = request.form['endereco']
        fornecedor.cnpj_pf = request.form['cnpj_pf']
        fornecedor.contato = request.form['contato']
        fornecedor.email = request.form['email']
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!')
        return redirect(url_for('fornecedores', fornecedor_id=fornecedor.id))

@app.route('/excluir_fornecedor/<int:fornecedor_id>', methods=['POST'])
def excluir_fornecedor(fornecedor_id):
    try:
        fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
        db.session.delete(fornecedor)
        db.session.commit()
        flash('Fornecedor excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro ao excluir o fornecedor: {e}', 'danger')
    return redirect(url_for('fornecedores'))

@app.route('/pesquisar_fornecedor', methods=['GET'])
def pesquisar_fornecedor():
    nome = request.args.get('nome', '').strip()
    if nome:
        fornecedores = Fornecedor.query.filter(Fornecedor.nome.like(f"%{nome}%")).all()
    else:
        fornecedores = Fornecedor.query.all()
    return render_template('fornecedor/Fornecedor.html', fornecedores=fornecedores)


#endregion

####################################################################
#PROGRAMAÇÃO cliente
#region: Cliente
class Cliente(db.Model):
    __tablename__ = 'Cliente'
    id = db.Column('id_Cliente', db.Integer, primary_key=True, nullable=False)
    nome = db.Column('nome_Cliente', db.String(100), nullable=False)
    endereco = db.Column('endereco_Cliente', db.String(200), nullable=True)
    cnpj_pf = db.Column('cnpj_pf_Cliente', db.String(18), nullable=True)
    contato = db.Column('contato_Cliente', db.String(100), nullable=True)
    email = db.Column('email_Cliente', db.String(100), nullable=True)

    #pedidos = db.relationship('Pedido', backref='cliente', lazy=True)
    
  


@app.route('/clientes')
@verificar_acesso(['Vendas', 'Administrador'])
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes/Clientes.html', clientes=clientes)

@app.route('/adicionar_cliente', methods=['GET', 'POST'])
def adicionar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        cnpj_pf = request.form['cnpj_pf']
        contato = request.form['contato']
        email = request.form['email']

        if not nome:
            flash('Por favor, preencha o nome do cliente.')
            return redirect('/adicionar_cliente')

        novo_cliente = Cliente(
            nome=nome,
            endereco=endereco,
            cnpj_pf=cnpj_pf,
            contato=contato,
            email=email
        )
        db.session.add(novo_cliente)
        db.session.commit()
        flash('Cliente adicionado com sucesso!')
        return redirect('/clientes')

@app.route('/editar_cliente/<int:cliente_id>', methods=['POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.endereco = request.form['endereco']
        cliente.cnpj_pf = request.form['cnpj_pf']
        cliente.contato = request.form['contato']
        cliente.email = request.form['email']
        db.session.commit()
        flash('Cliente atualizado com sucesso!')
        return redirect(url_for('clientes', cliente_id=cliente.id))

@app.route('/excluir_cliente/<int:cliente_id>', methods=['POST'])
def excluir_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Ocorreu um erro ao excluir o cliente: {e}', 'danger')
    return redirect(url_for('clientes'))

@app.route('/pesquisar_cliente', methods=['GET'])
def pesquisar_cliente():
    nome = request.args.get('nome', '').strip()
    if nome:
        clientes = Cliente.query.filter(Cliente.nome.like(f"%{nome}%")).all()
    else:
        clientes = Cliente.query.all()
    return render_template('clientes/Clientes.html', clientes=clientes)


#endregion

####################################################################
#PROGRAMAÇÃO pedido
#region: Pedido

class Pedido(db.Model):
    __tablename__ = 'Pedido'
    id = db.Column('id_Pedido', db.Integer, primary_key=True, nullable=False)
    tipo = db.Column('tipo_Pedido', db.String(20), nullable=False)
    quantidade = db.Column('quantidade_Pedido', db.Integer, nullable=False)
    total = db.Column('total_Pedido', db.Float, nullable=False)
    data = db.Column('data_Pedido', db.Date, nullable=False)

    # Chaves estrangeiras
    colaborador_id = db.Column(db.Integer, db.ForeignKey('Colaborador.id_Colaborador'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('Fornecedor.id_Fornecedor'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Cliente.id_Cliente'), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('Producao.id_Producao'), nullable=False)

    # Relacionamentos
    colaborador = db.relationship('Colaborador', backref='pedidos_colaborador', lazy=True)
    fornecedor = db.relationship('Fornecedor', backref='pedidos', lazy=True)
    cliente = db.relationship('Cliente', backref='pedidos', lazy=True)
    produto = db.relationship('Producao', backref='pedidos', lazy=True)

    def __init__(self, tipo, colaborador_id, produto_id, quantidade, data=None, fornecedor_id=None, cliente_id=None):
        self.tipo = tipo
        self.colaborador_id = colaborador_id
        self.produto_id = produto_id
        self.quantidade = quantidade
        self.data = data if data else db.func.current_date()  # Usa a data do sistema se não fornecido
        self.fornecedor_id = fornecedor_id
        self.cliente_id = cliente_id
        
        # Verifica a quantidade disponível antes de criar o pedido
        if not self.verificar_quantidade_disponivel():
            raise ValueError("Quantidade solicitada maior do que a quantidade disponível no estoque.")
        
        self.total = self.calcular_total()

    def verificar_quantidade_disponivel(self):
        # Verifica a quantidade disponível no banco de dados na tabela Producao
        produto = Producao.query.get(self.produto_id)
        if produto:
            # Garante que tanto produto.quantidade quanto self.quantidade são inteiros
            if int(produto.quantidade) >= int(self.quantidade):
                return True
        return False

    def calcular_total(self):
        # Acessa o preço diretamente a partir do produto relacionado
        produto = Producao.query.get(self.produto_id)  # Busca o produto com o id
        if produto:
            # Garante que o preço seja um valor numérico antes de calcular
            return self.quantidade * float(produto.preco)  # Calcula o total com o preço do produto
        return 0.0  # Retorna 0 caso o produto não exista


    

@app.route('/pedido')
def pedido():
    pedidos = Pedido.query.all()
    return render_template('pedido/Pedido.html', pedidos=pedidos)


@app.route('/adicionar_pedido', methods=['GET', 'POST'])
def adicionar_pedido():
    if request.method == 'POST':
        tipo_pedido = request.form['tipo_pedido']
        fornecedor_id = request.form['fornecedor']  # Para pedidos de recebimento
        cliente_id = request.form['cliente']  # Para pedidos de venda
        produto_id = request.form['produto']
        quantidade = request.form['quantidade']
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        # Validação
        if not tipo_pedido or not produto_id or not quantidade or not data:
            flash('Por favor, preencha todos os campos obrigatórios.')
            return redirect('/adicionar_pedido')

        # Criando o pedido
        novo_pedido = Pedido(
            tipo=tipo_pedido,  # Usando 'tipo', como definido na classe Pedido
            fornecedor_id=fornecedor_id if tipo_pedido == 'recebimento' else None,  # Somente para recebimento
            cliente_id=cliente_id if tipo_pedido == 'venda' else None,  # Somente para venda
            produto_id=produto_id,
            quantidade=quantidade,
            data=data,
            colaborador_id=session['user_id']  # ID do colaborador logado
        )
        db.session.add(novo_pedido)
        db.session.commit()

        flash('Pedido adicionado com sucesso!')
        return redirect('/pedido')  # Redirecionando para a página de pedidos
    
    # Se for um GET, retorna o formulário de adicionar pedido
    fornecedores = Fornecedor.query.all()  # Recuperando os fornecedores do banco
    clientes = Cliente.query.all()  # Recuperando os clientes do banco
    producao = Producao.query.all()  # Recuperando os produtos da produção
    return render_template('pedido/adicionar_pedido.html', fornecedores=fornecedores, clientes=clientes, producao=producao)


#endregion


####################################################################
#PROGRAMAÇÃO login
#region: Login

# Decorador para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Verificando sessão:", session.get('user_id'))  # Verifica se 'user_id' existe
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota para o perfil
@app.route('/perfil', methods=['GET'])
def perfil():
    # Obtém o ID do colaborador logado da sessão
    colaborador_id = session.get('user_id')

    if colaborador_id:
        colaborador = Colaborador.query.get(colaborador_id)
        
        if colaborador:
            # Passa o objeto colaborador para o template `home.html`
            return render_template('home.html', colaborador=colaborador)
        else:
            flash("Colaborador não encontrado.", "danger")
            return redirect(url_for('home'))
    else:
        flash("Você não está logado.", "danger")
        return redirect(url_for('login'))



# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        # Busca o colaborador no banco de dados
        colaborador = Colaborador.query.filter_by(usuario=usuario).first()
        
        if colaborador:
            if bcrypt.check_password_hash(colaborador.senha, senha):
                session['user_id'] = colaborador.id
                session['setor'] = colaborador.setor
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('perfil'))  # Redireciona para a rota /perfil
            else:
                flash('Senha incorreta.', 'danger')
        else:
            flash('Colaborador não encontrado.', 'danger')

    return render_template('cripto/login.html')


# Rota para Logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa a sessão ao fazer logout
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('login'))



@app.route('/pagina_erro')
def pagina_erro():
    return render_template('cripto/erroAcesso.html') 



#endregion

#####################################################################
#Programação home

#region: Home

# Rota Home protegida com verificação direta
@app.route('/home')
def home():
    
    # Exibe a página home normalmente se o usuário estiver logado
    return render_template('home.html')


#endregion

#####################################################################
#Programação main

#region: Main


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas do banco de dados
    app.run(debug=True)

#endregion
