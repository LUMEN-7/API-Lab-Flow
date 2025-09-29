# Sistema de Gestão de Laboratório – API RESTful

## Descrição do Projeto

Projeto acadêmico desenvolvido em Python utilizando **Flask** para criação de uma **API RESTful** de gerenciamento de laboratórios. Este repositório contém o **backend**, responsável pelo cadastro e controle de usuários, insumos, exames, pedidos e estoques, com **autenticação JWT** e controle de permissões para administradores. O sistema simula um ambiente de gestão de laboratórios clínicos, incluindo funcionalidades de histórico de movimentações e controle de estoque.

## Funcionalidades

* **CRUD de usuários**: criação, listagem, atualização e remoção com autenticação e permissões.
* **CRUD de insumos e exames**: gerenciamento de materiais e testes laboratoriais.
* **CRUD de pedidos**: criação e acompanhamento de pedidos de exames.
* **CRUD de unidades**: gestão das unidades de atendimento.
* **Controle de estoque**: entrada, saída e atualização de insumos com registro de histórico.
* **Autenticação e autorização**: login via JWT, permissões diferenciadas para usuários administradores.
* **Histórico de movimentações**: registro detalhado de entradas, saídas e descartes de insumos.

## Tecnologias Utilizadas

* Python 3.x
* Flask
* Flask-CORS
* PostgreSQL (via psycopg2)
* JWT para autenticação
* bcrypt para hash de senhas

## Estrutura da API

* **/usuarios** – gerenciamento de usuários
* **/insumos** – gerenciamento de insumos
* **/exames** – gerenciamento de exames
* **/pedidos** – gerenciamento de pedidos
* **/unidades** – gerenciamento de unidades
* **/estoque** – gerenciamento de estoques
* **/historico** – consulta de movimentações de estoque
* **/login** – autenticação de usuários

## Como Executar

1. Clone o repositório:

   ```bash
   git clone https://github.com/LUMEN-7/API-Lab-Flow
   cd API-Lab-Flow
   ```
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente:

   * `DATABASE_URL` → URL de conexão com o PostgreSQL
   * `SECRET_KEY` → chave secreta para JWT
4. Execute a API:

   ```bash
   python app.py
   ```
5. A API estará disponível em `http://localhost:5000/`.

## Observações

* Projeto desenvolvido individualmente como **projeto pessoal de portfólio**.
* Foco em backend; não inclui interface frontend.
* Segurança básica implementada via JWT e hash de senhas.
* A API está **online e funcional** em: [https://api-lab-flow.onrender.com](https://api-lab-flow.onrender.com)

Perfeito! Vou adicionar uma seção de **Exemplos de Requisições** para o README, mostrando como interagir com a API usando **cURL** e **JSON**, o que deixa o portfólio muito mais completo e profissional.


## Exemplos de Requisições

### 1. Autenticação (Login)

```bash
curl -X POST https://api-lab-flow.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_user": "usuario@exemplo.com",
    "senha_user": "senha123"
  }'
```

**Resposta:**

```json
{
  "mensagem": "Login bem-sucedido!",
  "token": "<JWT_TOKEN_AQUI>"
}
```

> O token retornado deve ser usado em requisições que exigem autenticação.

---

### 2. Criar Usuário (Admin)

```bash
curl -X POST https://api-lab-flow.onrender.com/usuarios \
  -H "Content-Type: application/json" \
  -d '{
    "cpf": "12345678900",
    "nome_usuario": "João Silva",
    "email_usuario": "joao@exemplo.com",
    "senha_usuario": "senha123",
    "administrador": "S"
  }'
```

**Resposta:**

```json
{
  "mensagem": "Usuário criado com sucesso!",
  "email_usuario": "joao@exemplo.com"
}
```

---

### 3. Listar Insumos (Com Token)

```bash
curl -X GET https://api-lab-flow.onrender.com/insumos \
  -H "Authorization: Bearer <JWT_TOKEN_AQUI>"
```

**Resposta:**

```json
[
  {
    "id_insumo": 1,
    "nome_insumo": "Luvas Descartáveis"
  },
  {
    "id_insumo": 2,
    "nome_insumo": "Máscara Cirúrgica"
  }
]
```

---

### 4. Criar Pedido

```bash
curl -X POST https://api-lab-flow.onrender.com/pedidos \
  -H "Authorization: Bearer <JWT_TOKEN_AQUI>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_lab_cpf": "12345678900",
    "grau_urgencia": "ALTO",
    "status": "PENDENTE"
  }'
```

**Resposta:**

```json
{
  "mensagem": "Pedido criado com sucesso!",
  "n_pedido": 1
}
```

---

### 5. Checar Estoque de Insumo

```bash
curl -X GET https://api-lab-flow.onrender.com/checar_estoque/1/2 \
  -H "Authorization: Bearer <JWT_TOKEN_AQUI>"
```

**Resposta:**

```json
{
  "status": "Estoque ok",
  "quantidade": 150,
  "limite_minimo": 50
}
```