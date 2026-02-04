from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'helpbank-secret-key-2026'

# ================= CONFIG =================
DATABASE = 'leads.db'
WHATSAPP_EMPRESA = '5581995294741'  # WhatsApp da Help Bank (55 + DDD + número)

# ================= DATABASE =================
def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT NOT NULL,
                data_nascimento TEXT NOT NULL,
                email TEXT NOT NULL,
                celular TEXT NOT NULL,
                tipo_servico TEXT NOT NULL,
                data_criacao TEXT NOT NULL
            )
        """)

# ================= VALIDATION =================
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10

    return dig1 == int(cpf[9]) and dig2 == int(cpf[10])

# ================= ROUTES =================
@app.route('/simulacao', methods=['GET'])
def simulacao_get():
    return render_template('simulacao.html')

@app.route('/simulacao', methods=['POST'])
def simulacao_post():
    try:
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        tipo_servico = request.form.get('tipo_servico')

        if not validar_cpf(cpf):
            return jsonify(success=False, message="CPF inválido"), 400

        data_criacao = datetime.now().strftime('%d/%m/%Y %H:%M')

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO leads 
                (nome, cpf, data_nascimento, email, celular, tipo_servico, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nome,
                cpf,
                data_nascimento,
                email,
                celular,
                tipo_servico,
                data_criacao
            ))

        # ================= MENSAGEM WHATSAPP (NEGRITO) =================
        mensagem = (
            "*Olá! Vim do site Help Bank e gostaria de fazer uma simulação:*\n\n"
            f"*Nome:* {nome}\n"
            f"*CPF:* {cpf}\n"
            f"*Data de Nascimento:* {data_nascimento}\n"
            f"*E-mail:* {email}\n"
            f"*Celular:* {celular}\n"
            f"*Serviço:* {tipo_servico}\n\n"
            "Aguardo retorno!"
        )

        return jsonify(
            success=True,
            whatsapp_number=WHATSAPP_EMPRESA,
            whatsapp_message=mensagem
        )

    except Exception as e:
        print("ERRO NO BACKEND:", e)
        return jsonify(success=False, message="Erro interno"), 500

# ================= START =================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
