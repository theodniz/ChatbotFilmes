# Adicionamos 'jsonify' para poder enviar respostas em JSON
from flask import Flask, render_template, request, session, jsonify
from chatbot import chatbot_responder
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/")
def home():
    session.clear()
    return render_template("index.html")

# 1. MUDANÇA DE ROTA E MÉTODO: De '/get' para '/chat', aceitando POST
@app.route("/chat", methods=['POST'])
def chat():
    # 2. MUDANÇA NA LEITURA DA MENSAGEM: Lendo o JSON enviado pelo JavaScript
    # Em vez de request.args, usamos request.json
    try:
        user_text = request.json.get('mensagem')
        if not user_text:
            return jsonify({'resposta': 'Erro: mensagem vazia.'})
    except Exception as e:
        return jsonify({'resposta': f'Erro ao ler a mensagem: {e}'})

    # Pega o estado da conversa da sessão ou cria um novo
    estado_atual = session.get('estado_conversa', {
        "ultimo_genero_sugerido": None,
        "filmes_ja_sugeridos": []
    })

    # A chamada para o "cérebro" do bot continua a mesma
    resposta_bot, novo_estado = chatbot_responder(user_text, estado_atual)

    # Salva o estado atualizado de volta na sessão
    session['estado_conversa'] = novo_estado

    # 3. MUDANÇA NO FORMATO DA RESPOSTA: Retornando um JSON
    # O seu JavaScript espera um JSON com a chave "resposta"
    return jsonify({'resposta': resposta_bot})


if __name__ == "__main__":
    app.run(debug=True)