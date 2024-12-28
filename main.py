from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes,CallbackQueryHandler
import logging
import requests
from uuid import uuid4
from dotenv import load_dotenv
import os

################################################################################################
#                                       CONFIGURAÇÃOES BASICAS                                 #
################################################################################################


# Configuração de logs para depuração
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Substitua pelo token do bot
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Lista de IDs dos administradores autorizados
ADMIN_IDS = os.getenv("ADMIN_IDS") 
GROUP_ID = os.getenv("GROUP_ID")


################################################################################################
#                                   FUNCIONALIDADES DO BOT                                     #
################################################################################################

# Função para o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Comando /start recebido de {update.effective_user.first_name}")
    await update.message.reply_text(
        """Bem-vindo ao Bot de Gerenciamento de Grupos! Aqui você pode gerenciar membros e enviar notificações de forma prática.        
Comandos disponíveis:

**Gerenciamento de Membros:**
- `/adicionar`: Gerar um link de convite para adicionar membros ao grupo.
- `/remover <ID do usuário>`: Remover um membro do grupo pelo ID.

**Notificações:**
- `/notificar <ID ou @username> <mensagem>`: Enviar uma mensagem para um membro ou grupo específico.
        """
    )

async def painel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Verifica se o usuário é um administrador autorizado
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Você não tem permissão para acessar o painel administrativo.")
        return

    # Envia a mensagem com as opções do painel
    keyboard = [
        [InlineKeyboardButton("Listar Usuários", callback_data="listar_usuarios")],
        [InlineKeyboardButton("Enviar Notificação", callback_data="enviar_notificacao")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Painel Administrativo:\nEscolha uma ação:", reply_markup=reply_markup)



async def listar_usuarios_painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        chat_id = -1001234567890  # Substitua pelo ID do grupo que será gerenciado
        membros = await context.bot.get_chat_members(chat_id)

        # Cria botões para cada usuário
        keyboard = []
        for membro in membros:
            user = membro.user
            if not user.is_bot:
                keyboard.append(
                    [InlineKeyboardButton(f"Remover {user.first_name}", callback_data=f"remover:{user.id}")]
                )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Selecione um usuário para remover:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Erro ao listar usuários no painel: {e}")
        await query.edit_message_text(f"Erro ao listar usuários: {e}")



async def remover_usuario_painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("remover:"):
            user_id = int(data.split(":")[1])
            chat_id = GROUP_ID  # Substitua pelo ID do grupo

            # Remove o usuário
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await query.edit_message_text(f"Usuário com ID {user_id} foi removido do grupo!")
    except Exception as e:
        logger.error(f"Erro ao remover usuário pelo painel: {e}")
        await query.edit_message_text(f"Erro ao remover usuário: {e}")
        
# Função para adicionar um usuário ao grupo
async def adicionar_membro(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def remover_membro(update: Update, context: ContextTypes.DEFAULT_TYPE):
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



async def enviar_notificacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Uso: /notificar <ID ou @username> <mensagem>")
            return

        # Extrai os argumentos
        target = context.args[0]
        mensagem = " ".join(context.args[1:])

        # Envia a mensagem
        await context.bot.send_message(chat_id=target, text=mensagem)
        await update.message.reply_text(f"Mensagem enviada para {target}!")
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {e}")
        await update.message.reply_text(f"Erro ao enviar notificação: {e}")

async def listar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat  # Grupo onde o comando foi chamado
        bot_member = await chat.get_member(context.bot.id)

        # Verifica se o bot tem permissões de administrador
        if bot_member.status != "administrator":
            await update.message.reply_text("Eu preciso ser administrador para listar membros!")
            return

        # Obtém todos os membros do grupo
        membros = await context.bot.get_chat_administrators(chat_id=chat.id)

        # Cria uma lista com botões para cada membro
        keyboard = []
        for membro in membros:
            user = membro.user
            if not user.is_bot:  # Ignorar bots
                keyboard.append(
                    [InlineKeyboardButton(f"Remover {user.first_name}", callback_data=f"remover:{user.id}")]
                )

        # Envia a lista de botões ao administrador
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Selecione um usuário para remover:", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        await update.message.reply_text(f"Erro ao listar usuários: {e}")


async def callback_remover_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # Extrai o ID do usuário do callback_data
        data = query.data
        if data.startswith("remover:"):
            user_id = int(data.split(":")[1])
            chat_id = query.message.chat.id

            # Remove o usuário do grupo
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await query.edit_message_text(f"Usuário com ID {user_id} foi removido do grupo!")
    except Exception as e:
        logger.error(f"Erro ao remover usuário pelo botão: {e}")
        await query.edit_message_text(f"Erro ao remover usuário: {e}")

################################################################################################
#                                       FUNÇÕES AUXILIARES                                     #
################################################################################################

        

def main():
    try:
        # Inicializa o Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Handlers do painel administrativo
        application.add_handler(CommandHandler("painel_admin", painel_admin))  # Acessar painel
        application.add_handler(CallbackQueryHandler(listar_usuarios_painel, pattern="^listar_usuarios$"))  # Listar usuários
        application.add_handler(CallbackQueryHandler(remover_usuario_painel, pattern="^remover:"))  # Remover usuário

        # Outros handlers
        application.add_handler(CommandHandler("start", start))

        # Inicia o bot
        logger.info("Bot iniciado. Aguardando mensagens...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")    

if __name__ == "__main__":
    main()
