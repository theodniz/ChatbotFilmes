
from flask import Flask, render_template, request, session, jsonify
from chatbot import chatbot_responder
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/")
def home():
    session.clear()
    return render_template("index.html")


@app.route("/chat", methods=['POST'])
def chat():
    
    try:
        user_text = request.json.get('mensagem')
        if not user_text:
            return jsonify({'resposta': 'Erro: mensagem vazia.'})
    except Exception as e:
        return jsonify({'resposta': f'Erro ao ler a mensagem: {e}'})

    
    estado_atual = session.get('estado_conversa', {
        "ultimo_genero_sugerido": None,
        "filmes_ja_sugeridos": []
    })

    
    resposta_bot, novo_estado = chatbot_responder(user_text, estado_atual)

    
    session['estado_conversa'] = novo_estado

    
    return jsonify({'resposta': resposta_bot})


if __name__ == "__main__":
    app.run(debug=True)