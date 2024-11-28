from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes,CallbackQueryHandler
import logging
from qbittorrentapi import Client
import requests
from uuid import uuid4
import os

################################################################################################
#                                       CONFIGURAÇÃOES BASICAS                                 #
################################################################################################


# Configuração de logs para depuração
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Substitua pelo token do bot
TELEGRAM_TOKEN = "7956168457:AAG7Y9qqPT8dPIsSJbtJ3YG_w_U4mtqVGiU"

#API de torrents
YTS_API = "https://yts.mx/api/v2/list_movies.json"

# Dicionário para armazenar os magnet links temporariamente
magnet_links_cache = {}

#Conexão com qbittorrent web
qb = Client(host='http://127.0.0.1:8080', username='admin', password='adminadmin')

################################################################################################
#                                   FUNCIONALIDADES DO BOT                                     #
################################################################################################

# Função para o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Comando /start recebido de {update.effective_user.first_name}")
    await update.message.reply_text("""Bem-vindo ao Bot de Torrents! Aqui você pode buscar, baixar e acessar arquivos diretamente no Telegram.
Comandos disponíveis:
- /buscar <termo>: Procurar torrents.
- /downloads: Verificar downloads ativos.
- /arquivos: Listar arquivos disponíveis.""")

# Função para adicionar um usuário ao grupo
async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Verifica se o bot tem permissões de administrador
        chat = update.effective_chat
        bot_member = await chat.get_member(context.bot.id)

        if bot_member.status != "administrator":
            await update.message.reply_text("Eu preciso ser administrador para adicionar membros!")
            return

        # Gera um link de convite para o grupo
        invite_link = await context.bot.create_chat_invite_link(chat_id=chat.id, member_limit=1)
        await update.message.reply_text(f"Compartilhe este link para adicionar membros: {invite_link.invite_link}")
    except Exception as e:
        logger.error(f"Erro ao criar link de convite: {e}")
        await update.message.reply_text(f"Erro ao adicionar usuário: {e}")

# Função para remover um usuário do grupo
async def remover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Verifica se o bot tem permissões de administrador
        chat = update.effective_chat
        bot_member = await chat.get_member(context.bot.id)

        if bot_member.status != "administrator":
            await update.message.reply_text("Eu preciso ser administrador para remover membros!")
            return

        if context.args:
            user_id = int(context.args[0])
            await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_id)
            await update.message.reply_text(f"Usuário {user_id} foi removido do grupo!")
        else:
            await update.message.reply_text("Por favor, forneça o ID do usuário a ser removido.")
    except Exception as e:
        logger.error(f"Erro ao remover usuário: {e}")
        await update.message.reply_text(f"Erro ao remover usuário: {e}")

# Função para adicioanr torrent ao qbittorrent
async def adicionar_torrent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Verifica se o argumento foi passado
        if not context.args:
            await update.message.reply_text("Por favor, forneça o link magnet do torrent.")
            return
        
        # Adiciona o torrent
        magnet_link = " ".join(context.args)
        qb.auth_log_in()
        qb.torrents_add(urls=magnet_link)
        
        # Resposta de sucesso
        await update.message.reply_text(f"Torrent adicionado com sucesso: {magnet_link}")
        logger.info(f"Torrent adicionado: {magnet_link}")
    except Exception as e:
        # Registro detalhado do erro
        error_message = f"Erro ao adicionar torrent: {e}"
        logger.error(error_message)
        logger.debug(traceback.format_exc())  # Registro detalhado com traceback
        await update.message.reply_text(error_message)

# Função para listar os torrents do usuario
async def listar_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qb.auth_log_in()
        torrents = qb.torrents_info()
        if not torrents:
            await update.message.reply_text("Nenhum download ativo.")
            return

        mensagem = "Downloads Ativos:\n"
        for torrent in torrents:
            mensagem += f"{torrent['name']} - {torrent['progress']*100:.2f}%\n"
        await update.message.reply_text(mensagem)
    except Exception as e:
        await update.message.reply_text(f"Erro ao listar downloads: {e}")
        print(f"Erro ao listar downloads: {e}")

# Função para pausar torrent em execução
async def pausar_torrent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args:
            nome = " ".join(context.args)
            qb.auth_log_in()
            torrents = qb.torrents_info()
            for torrent in torrents:
                if nome.lower() in torrent['name'].lower():
                    qb.torrents_pause(torrent_hashes=torrent['hash'])
                    await update.message.reply_text(f"Torrent pausado: {torrent['name']}")
                    return
            await update.message.reply_text("Torrent não encontrado.")
        else:
            await update.message.reply_text("Por favor, forneça o nome do torrent para pausar.")
    except Exception as e:
        await update.message.reply_text(f"Erro ao pausar torrent: {e}")
        print(f"Erro ao pausar torrent: {e}")

# Função para buscar torrent na API
async def buscar_torrents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Por favor, forneça o termo para busca. Exemplo: /buscar <nome do filme>")
            return
        
        termo = " ".join(context.args)
        params = {"query_term": termo, "limit": 5}  # Limitar a 5 resultados
        response = requests.get(YTS_API, params=params)
        
        if response.status_code != 200:
            await update.message.reply_text("Erro ao buscar torrents.")
            return

        data = response.json()
        if not data.get("data", {}).get("movies"):
            await update.message.reply_text("Nenhum torrent encontrado.")
            return

        # Construindo lista de resultados
        keyboard = []
        for movie in data["data"]["movies"]:
            title = movie["title"]
            torrents = movie["torrents"]
            for torrent in torrents:
                quality = torrent["quality"]
                magnet = f"magnet:?xt=urn:btih:{torrent['hash']}&dn={title}&tr=udp://tracker.openbittorrent.com:80"

                # Gerar um ID único para armazenar o magnet
                magnet_id = str(uuid4())
                magnet_links_cache[magnet_id] = magnet

                # Adicionar botão com ID no callback_data
                button = InlineKeyboardButton(
                    text=f"{title} ({quality})",
                    callback_data=magnet_id
                )
                keyboard.append([button])  # Cada botão em uma nova linha

        # Envia a mensagem com botões
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Selecione um torrent para adicionar:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"Erro ao buscar torrents: {e}")
        print(f"Erro ao buscar torrents: {e}")

# Função que adicona o torrent buscado
async def adicionar_por_botao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        magnet_id = query.data  # ID único recebido no callback_data

        # Recuperar o magnet link do cache
        magnet_link = magnet_links_cache.get(magnet_id)
        if not magnet_link:
            await query.answer("Erro: Magnet link não encontrado.")
            return

        # Adicionar o torrent ao cliente
        qb.auth_log_in()
        qb.torrents_add(urls=magnet_link)

        # Confirmação ao usuário
        await query.answer("Torrent adicionado com sucesso!")
        await query.edit_message_text(text="Torrent adicionado com sucesso!")
        print(f"Torrent adicionado: {magnet_link}")
    except Exception as e:
        await query.answer("Erro ao adicionar torrent.")
        print(f"Erro ao adicionar torrent: {e}")

# Função que verifica periodicamente se o download foi concluido
async def verificar_downloads(context: ContextTypes.DEFAULT_TYPE):
    try:
        qb.auth_log_in()
        torrents = qb.torrents_info()

        for torrent in torrents:
            if torrent["state"] == "completed":  # Estado "completed" detectado
                arquivo_path = os.path.join(torrent["save_path"], torrent["name"])

                # Enviar o arquivo para o chat
                chat_id = context.job.data["chat_id"]
                nome_arquivo = torrent["name"]
                await enviar_arquivo_para_chat(context.bot, chat_id, arquivo_path, nome_arquivo)

                # Notificar o usuário
                await context.bot.send_message(chat_id, text=f"Download concluído: {nome_arquivo}")

    except Exception as e:
        print(f"Erro ao verificar downloads: {e}")
# Função que envia o arquivo depois de baixado para o chat
async def enviar_arquivo_para_chat(bot, chat_id, arquivo_path, nome_arquivo):
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(arquivo_path):
            await bot.send_message(chat_id, f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
            return

        # Envia o arquivo como documento ou vídeo
        if nome_arquivo.lower().endswith((".mp4", ".mkv", ".avi")):
            with open(arquivo_path, "rb") as video:
                await bot.send_video(chat_id, video=video, supports_streaming=True, caption=f"🎥 {nome_arquivo}")
        else:
            with open(arquivo_path, "rb") as document:
                await bot.send_document(chat_id, document=document, caption=f"📁 {nome_arquivo}")

    except Exception as e:
        print(f"Erro ao enviar arquivo '{arquivo_path}': {e}")
# Função para listar os arquivos baixados
async def listar_arquivos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id
    conn = sqlite3.connect("historico.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome_arquivo, arquivo_id FROM historico WHERE usuario_id = ?", (usuario_id,))
    arquivos = cursor.fetchall()
    conn.close()

    if not arquivos:
        await update.message.reply_text("Você não tem nenhum arquivo disponível.")
        return

    mensagem = "📂 Seus Arquivos:\n"
    for nome, arquivo_id in arquivos:
        mensagem += f"- {nome}: /arquivo_{arquivo_id}\n"

    await update.message.reply_text(mensagem)

# Função que envia o historico de arquivos baixados
async def enviar_arquivo_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text
    arquivo_id = comando.split("_")[-1]

    conn = sqlite3.connect("historico.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome_arquivo, arquivo_id FROM historico WHERE arquivo_id = ?", (arquivo_id,))
    arquivo = cursor.fetchone()
    conn.close()

    if not arquivo:
        await update.message.reply_text("Arquivo não encontrado.")
        return

    nome_arquivo, arquivo_id = arquivo
    await update.message.reply_document(document=arquivo_id, caption=f"📁 {nome_arquivo}")

async def listar_concluidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qb.auth_log_in()
        torrents = qb.torrents_info()
        chat_id = update.effective_chat.id

        concluidos = [torrent for torrent in torrents if torrent["state"] == "completed"]

        if not concluidos:
            await update.message.reply_text("Nenhum download concluído encontrado.")
            return

        # Enviar arquivos concluídos
        for torrent in concluidos:
            arquivo_path = os.path.join(torrent["save_path"], torrent["name"])
            nome_arquivo = torrent["name"]

            await enviar_arquivo_para_chat(context.bot, chat_id, arquivo_path, nome_arquivo)

        await update.message.reply_text("Todos os downloads concluídos foram enviados para o chat.")

    except Exception as e:
        print(f"Erro ao listar e enviar downloads concluídos: {e}")
        await update.message.reply_text("Ocorreu um erro ao listar downloads concluídos.")
        
################################################################################################
#                                       FUNÇÕES AUXILIARES                                     #
################################################################################################

        
from threading import Timer
# Função para limpar o cache a cada 10 minutos
def limpar_cache():
    global magnet_links_cache
    magnet_links_cache = {}
    print("Cache de magnet links limpo.")
# Agendar a limpeza do cache
def agendar_limpeza():
    Timer(600, limpar_cache).start()  # 600 segundos = 10 minutos


import sqlite3
# Iniciando o banco de dados
def init_db():
    conn = sqlite3.connect("historico.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome_arquivo TEXT NOT NULL,
            arquivo_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Função para salvar no banco de dados
def salvar_no_historico(usuario_id, nome_arquivo, arquivo_id):
    conn = sqlite3.connect("historico.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO historico (usuario_id, nome_arquivo, arquivo_id) VALUES (?, ?, ?)",
                   (usuario_id, nome_arquivo, arquivo_id))
    conn.commit()
    conn.close()
    

# Função principal para rodar o bot
def main():
    try:
        # Inicializa o Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Adiciona os handlers para comandos
        application.add_handler(CommandHandler("adicionar_user", adicionar))
        application.add_handler(CommandHandler("remover_user", remover))
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("torrent",adicionar_torrent))
        application.add_handler(CommandHandler("downloads", listar_downloads))
        application.add_handler(CommandHandler("pausar", pausar_torrent))
        application.add_handler(CommandHandler("buscar", buscar_torrents))
        application.add_handler(CommandHandler("arquivos", listar_arquivos))
        application.add_handler(CommandHandler("arquivo_", enviar_arquivo_historico))
        application.add_handler(CommandHandler("adicionar",verificar_downloads))
        application.add_handler(CommandHandler("listar_concluidos", listar_concluidos))
        application.add_handler(CallbackQueryHandler(adicionar_por_botao)) 

                
        # Inicia o bot
        logger.info("Bot iniciado. Aguardando mensagens...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")

if __name__ == "__main__":
    agendar_limpeza()
    
    init_db()  # Inicializa o banco de dados

    main()
