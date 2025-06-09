import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
import random
import string
import unicodedata

# --- CONFIGURAÇÃO INICIAL E CARREGAMENTO DE DADOS ---
try:
    stopwords.words('portuguese')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

try:
    filmes_df = pd.read_csv('filmes.csv')
    GENEROS_VALIDOS = filmes_df['genero'].unique().tolist()
except FileNotFoundError:
    print("Erro: Arquivo 'filmes.csv' não encontrado. Crie o arquivo para o chatbot funcionar.")
    exit()

# --- DEFINIÇÕES E DICIONÁRIOS GLOBAIS ---
EMOCAO_GENEROS = {
    "triste": "comédia", "chateado": "comédia", "pra baixo": "comédia",
    "feliz": "aventura", "alegre": "aventura", "contente": "aventura",
    "animado": "ação", "empolgado": "ação",
    "entediado": "ficção",
    "romântico": "romance", "apaixonado": "romance",
    "assustado": "terror", "com medo": "terror",
    "curioso": "drama", "pensativo": "drama"
}

STOP_WORDS = set(stopwords.words('portuguese'))
RESPOSTAS_SAUDACAO = ["Olá! Como posso te ajudar a escolher um filme hoje?", "Oi! Me diga que tipo de filme você quer ver ou como está se sentindo.", "E aí! Pronto para uma sugestão de filme?"]
RESPOSTAS_DESPEDIDA = ["Até mais! Espero ter ajudado.", "Tchau! Bom filme!", "Qualquer coisa, é só chamar. Até logo!"]
RESPOSTAS_AGRADECIMENTO = ["De nada! Fico feliz em ajudar. Bom filme! 🍿", "Por nada! Se precisar de mais alguma coisa, é só chamar.", "Disponha! Aproveite a dica!"]
RESPOSTAS_SEM_IDEIA = ["Me diga um gênero que você gosta (ação, comédia...) ou como você está se sentindo (triste, animado...).", "Não entendi. Você pode me dizer um gênero ou um sentimento?", "Hmm, para te ajudar preciso saber que gênero de filme você busca."]
FRASES_DE_TRANSICAO = ["Ok, sem problemas. ", "Entendi. Que tal esta outra opção? ", "Certo, buscando outra sugestão... "]


# --- FUNÇÕES AUXILIARES ---
def remover_acentos(texto):
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def limpar_texto(texto):
    texto = texto.lower()
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(texto, language='portuguese')
    tokens_filtrados = [t for t in tokens if t not in STOP_WORDS]
    return tokens_filtrados

def recomendar_por_genero(genero, estado_conversa):
    filmes_disponiveis = filmes_df[(filmes_df['genero'].str.contains(genero, case=False)) & (~filmes_df['titulo'].isin(estado_conversa['filmes_ja_sugeridos']))]
    if not filmes_disponiveis.empty:
        filme_sugerido = filmes_disponiveis.sample().iloc[0]
        titulo = filme_sugerido['titulo']
        frases_sugestao = [
            f"🎬 Que tal assistir {titulo}? É um ótimo filme de {genero}! O que me diz?",
            f"Para {genero}, eu recomendo {titulo}. Parece bom ou quer outra sugestão?",
            f"Encontrei uma boa opção de {genero}: {titulo}. Gostou da ideia?"
        ]
        nova_mensagem = random.choice(frases_sugestao)
        estado_conversa['ultimo_genero_sugerido'] = genero
        estado_conversa['filmes_ja_sugeridos'].append(titulo)
    else:
        nova_mensagem = f"Puxa, já te sugeri todos os filmes de {genero} que conheço. Que tal outro gênero?"
        estado_conversa['ultimo_genero_sugerido'] = None
    return nova_mensagem, estado_conversa

# --- FUNÇÃO PRINCIPAL DO CHATBOT ---
def chatbot_responder(mensagem_usuario, estado_conversa):
    tokens = limpar_texto(mensagem_usuario)
    nova_mensagem = ""

    if any(s in tokens for s in ["oi", "ola", "opa", "bom", "dia", "boa", "tarde", "noite"]):
        nova_mensagem = random.choice(RESPOSTAS_SAUDACAO)
        estado_conversa = {"ultimo_genero_sugerido": None, "filmes_ja_sugeridos": []}
    elif any(d in tokens for d in ["tchau", "adeus", "flw", "ate", "mais"]):
        nova_mensagem = random.choice(RESPOSTAS_DESPEDIDA)
        estado_conversa = {"ultimo_genero_sugerido": None, "filmes_ja_sugeridos": []}
    
    # MUDANÇA: Criamos um bloco SÓ para o "sim", que agora é sensível ao contexto
    elif 'sim' in tokens:
        ultimo_genero = estado_conversa.get("ultimo_genero_sugerido")
        if ultimo_genero:
            # Se já havia um gênero na conversa, "sim" significa "sim, quero outro"
            recomendacao, estado_conversa_atualizado = recomendar_por_genero(ultimo_genero, estado_conversa)
            transicao = random.choice(FRASES_DE_TRANSICAO)
            nova_mensagem = transicao + recomendacao
            estado_conversa = estado_conversa_atualizado
        else:
            # Se a conversa está no começo, "sim" significa "sim, me ajude"
            filme = filmes_df.sample().iloc[0]
            nova_mensagem = f"Claro! Que tal algo aleatório para começar? Veja: {filme['titulo']} ({filme['genero']}). O que acha?"
            estado_conversa['ultimo_genero_sugerido'] = filme['genero']
            estado_conversa['filmes_ja_sugeridos'] = [filme['titulo']]

    # MUDANÇA: O "sim" foi removido desta lista para ter seu próprio tratamento
    elif any(t in tokens for t in ["obrigado", "obrigada", "valeu", "gostei", "perfeito", "ok"]):
        nova_mensagem = random.choice(RESPOSTAS_AGRADECIMENTO)
        
    elif any(n in tokens for n in ["nao", "outro", "outra", "diferente", "mais"]):
        ultimo_genero = estado_conversa.get("ultimo_genero_sugerido")
        if ultimo_genero:
            recomendacao, estado_conversa_atualizado = recomendar_por_genero(ultimo_genero, estado_conversa)
            transicao = random.choice(FRASES_DE_TRANSICAO)
            nova_mensagem = transicao + recomendacao
            estado_conversa = estado_conversa_atualizado
        else:
            nova_mensagem = "Outro o quê? Você precisa pedir uma sugestão primeiro."
    else:
        genero_detectado = None
        for token in tokens:
            token_sem_acento = remover_acentos(token)
            for genero_valido in GENEROS_VALIDOS:
                if token_sem_acento == remover_acentos(genero_valido):
                    genero_detectado = genero_valido
                    break
            if genero_detectado:
                break
        
        if not genero_detectado:
            mensagem_sem_acento = remover_acentos(mensagem_usuario.lower())
            for emocao, genero_mapeado in EMOCAO_GENEROS.items():
                if remover_acentos(emocao) in mensagem_sem_acento:
                    genero_detectado = genero_mapeado
                    break

        if genero_detectado:
            estado_conversa["filmes_ja_sugeridos"] = []
            nova_mensagem, estado_conversa = recomendar_por_genero(genero_detectado, estado_conversa)
        elif "qualquer" in tokens or "tanto faz" in mensagem_usuario.lower():
            filme = filmes_df.sample().iloc[0]
            nova_mensagem = f"Ok! Que tal algo aleatório? Veja: {filme['titulo']} ({filme['genero']}). O que acha?"
            estado_conversa['ultimo_genero_sugerido'] = filme['genero']
            estado_conversa['filmes_ja_sugeridos'] = [filme['titulo']]
        else:
            nova_mensagem = random.choice(RESPOSTAS_SEM_IDEIA)
            
    return nova_mensagem, estado_conversa

# --- BLOCO DE TESTE NO TERMINAL ---
if __name__ == '__main__':
    estado_conversa_atual = {"ultimo_genero_sugerido": None, "filmes_ja_sugeridos": []}
    print("Chatbot de Filmes iniciado para teste no terminal! Digite 'tchau' para sair.")
    while True:
        mensagem = input("Você: ")
        if mensagem.lower() == 'tchau':
            print("Bot: " + random.choice(RESPOSTAS_DESPEDIDA))
            break
        resposta_bot, estado_conversa_atual = chatbot_responder(mensagem, estado_conversa_atual)
        print(f"Bot: {resposta_bot}")