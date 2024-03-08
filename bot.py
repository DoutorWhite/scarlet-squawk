import discord
import json
import os
import requests
import logging
from argparse import Namespace
#from redbot.core import commands


disable_restart = False

# Parte específica de cliente direto

def discord_client_setup():
    intents = discord.Intents.default()
    intents.message_content = True
    logging.basicConfig(level=logging.DEBUG)
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Conectado como {client.user}')

    @client.event
    async def on_message(message):
        author = message.author
        guild = message.guild
        
        if author == client.user or \
                not message.content.startswith(config.bot.prefix):
            return
        elif message.content[1:] == 'restart' and is_authorized(author):
            await do_command('restart', author, guild, send_discord_client(message))
        elif message.content[1:] == 'update' and is_authorized(author):
            await do_command('update', author, guild, send_discord_client(message))

    return client


def send_discord_client(message):
    async def _send_discord_client(*args, **kwargs):
        await message.channel.send(*args, **kwargs)
    return _send_discord_client


# Parte genérica, implementação do bot em si

def internal_setup():
    global config
    if(os.path.isfile('config.json')):
        with open('config.json') as file:
            config = json.load(file, object_hook=lambda converted_dict: Namespace(**converted_dict))
    else:
        raise Exception('Não é possível acessar o arquivo config.json, verifique se existe e é um arquivo legível.')
        sys.exit()

async def do_command(command, author, guild, send):
    traduz_operacao = {"restart": "reiniciar",
                       "update": "atualizar"}
    sucesso = {"restart": '```yml\nConexão efetuada com sucesso, o servidor deve reiniciar em breve.```',
               "update": '```yml\nConexão efetuada com sucesso, foi agendada uma atualização para o servidor.```'}
    falha_generica = '```yml\nAlgo deu errado durante a tentativa de conexão com o servidor remoto. Não se preocupe, não é culpa sua.\n```'
    falha = {"restart": falha_generica,
             "update": falha_generica}

    if post(command):
        await send(sucesso[command])
    else:
        await send(falha[command])


def is_authorized(author):
    whitelist = config.bot.whitelist

    for allowed_role in whitelist.roles:
        if allowed_role in [role.id for role in author.roles]:
            return True

    return author.id in whitelist.users


def post(command):
    try:
        url = '{}/instances/{}/{}'.format(config.watchdog.host, config.watchdog.instance, command)
        resp = requests.post(url, data={}, auth=(config.watchdog.instance, config.watchdog.token))
        print('CONEXÃO: POST efetuado com sucesso. Se o servidor não se comportou como esperado, verifique as configurações.')
        return True
    except Exception as e:
        print('ERRO DE CONEXÃO: {}'.format(e))
        return False

# parte específica de Cog

'''
class UpdateCog(commands.Cog, name="Update Cog"):

    def __init__(self, bot):
        raise NotImplementedError()
        self.bot = bot

    @commands.command(name='update')
    async def update(self, ctx):
        await self._do_command(ctx, 'update')

    @commands.command(name='restart')
    async def restart(self, ctx):
        await self._do_command(ctx, 'update')

    async def _do_command(self, ctx, cmd):
        if is_authorized():
            await do_command()
'''

def setup(bot):
    internal_setup()
    bot.add_cog(UpdateCog(bot))


def main():
    internal_setup()
    client = discord_client_setup()
    client.run(config.bot.token)


if __name__ == '__main__':
    main()
