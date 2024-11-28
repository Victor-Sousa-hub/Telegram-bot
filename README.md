# Telegram Torrent Bot

Um bot para Telegram que permite aos usuários buscar, baixar e acessar torrents diretamente pelo Telegram. O bot integra o cliente **qBittorrent** para gerenciar downloads, além de fornecer funcionalidades como listar arquivos disponíveis e enviar torrents concluídos para o chat.

---

## **Funcionalidades**
- **Buscar torrents**: Pesquise torrents utilizando a API do YTS.
- **Adicionar torrents**: Adicione torrents diretamente no cliente qBittorrent.
- **Gerenciar downloads**:
  - Listar downloads ativos.
  - Pausar downloads.
  - Receber notificação de downloads concluídos.
- **Acessar arquivos concluídos**: Envie arquivos baixados diretamente para o chat do usuário.
- **Limpeza de cache**: Remove magnet links antigos do cache a cada 10 minutos.

---

## **Pré-requisitos**
- Python 3.8 ou superior.
- Cliente **qBittorrent** configurado com acesso Web (host, username e senha).
- Uma conta de bot criada no Telegram (Token gerado pelo BotFather).
- Biblioteca **`python-telegram-bot`** instalada.

---

## **Instalação**

1. **Clone o Repositório**
   ```bash
   git clone https://github.com/seu_usuario/seu_repositorio.git
   cd seu_repositorio
Crie o Ambiente Virtual

```bash

python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

Instale as Dependências

```bash
pip install -r requirements.txt
```
Configuração do Bot

Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:

```makefile
TELEGRAM_TOKEN=seu_token_aqui
```

Substitua seu_token_aqui pelo token do seu bot do Telegram.
Configure o Cliente qBittorrent

Certifique-se de que o qBittorrent WebUI está habilitado.
Configure o host, username e senha no código, na seção:

```python
qb = Client(host='http://127.0.0.1:8080', username='admin', password='adminadmin')
```
Uso

Comandos Disponíveis
/start: Inicia o bot e exibe informações básicas.
/buscar <termo>: Busca torrents usando a API do YTS.
/torrent <magnet_link>: Adiciona um torrent pelo link magnet.
/downloads: Lista os downloads ativos no cliente qBittorrent.
/pausar <nome_do_torrent>: Pausa um download ativo.
/arquivos: Lista os arquivos baixados disponíveis no histórico.
/listar_concluidos: Envia para o chat todos os downloads concluídos.
Estrutura do Projeto

```bash

.
├── main.py               # Código principal do bot
├── requirements.txt      # Dependências do projeto
├── .env                  # Token do bot (não enviado ao GitHub)
├── historico.db          # Banco de dados SQLite (gerado automaticamente)
├── README.md             # Documentação do projeto
```
Como Funciona
O usuário executa um comando como /buscar Breaking Bad.
O bot responde com botões que representam torrents encontrados.
O usuário seleciona o botão correspondente, e o bot adiciona o torrent ao qBittorrent.
Quando o download é concluído, o bot envia o arquivo diretamente para o chat.
Contribuindo
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

Licença
Este projeto está sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.

Autores
Victor Sousa - Victor-Sousa-hub
