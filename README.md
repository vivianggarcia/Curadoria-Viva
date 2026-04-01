# Curadoria Viva - Sistema de Biblioteca

Sistema completo de gerenciamento de biblioteca desenvolvido com Flask e MySQL.

## Requisitos

- Python 3.8+
- MySQL Server

## Instalação

### 1. Ativar o Ambiente Virtual

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

## Configuração

### Variáveis de Ambiente (.env)

O arquivo `.env` contém as configurações sensíveis:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=biblioteca
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

**Importante:** Nunca commitar o arquivo `.env` no Git. Ele está no `.gitignore`.

### Para Produção

Copie o `.env` e altere as valores:

```bash
cp .env .env.production
```

Edite `.env.production` com suas credenciais de produção.

## Executar a Aplicação

Com o venv ativado:

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## Estrutura do Projeto

```
api_biblioteca/
├── venv/                 # Ambiente virtual (NÃO commitar)
├── routes/              # Blueprints de rotas
│   ├── usuarios.py
│   ├── livros.py
│   ├── autores.py
│   ├── emprestimos.py
│   └── emprestimo_livro.py
├── templates/           # Templates HTML (Jinja2)
├── app.py              # Aplicação principal
├── db.py               # Conexão com banco de dados
├── config.py           # Carregamento de configurações
├── requirements.txt    # Dependências Python
├── .env               # Variáveis de ambiente (NÃO commitar)
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Este arquivo
```

## Funcionalidades

-  Gerenciamento de Usuários
-  Cadastro de Livros
- Cadastro de Autores
-  Sistema de Empréstimos
-  Relação Livro-Empréstimo
-  Interface Responsiva
-  Design Moderno com Tailwind CSS

## Desativar o Venv

```bash
deactivate
```

## Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'config'`
Certifique-se de que está na pasta do projeto e o venv está ativado.

### Erro: `mysql.connector.errors.ProgrammingError`
Verifique se:
- MySQL Server está rodando
- Credenciais do `.env` estão corretas
- Banco de dados `biblioteca` existe

### Erro: `python-dotenv not found`
Execute: `pip install -r requirements.txt`

## Desenvolvido com

- Flask 3.0.0
- MySQL Connector Python 8.2.0
- Tailwind CSS
- Material Design Icons

---

Desenvolvido por Vivian
