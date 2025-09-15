import datetime
import time

import discord
from discord.ext import commands
import asyncio
import io


class DiscordBotController:
    def __init__(self, classe, json_manager=None):
        self.token = None
        self.json_manager = json_manager
        self.classe = classe
        self.tempo_ultimo_comando = None

        intents = discord.Intents.default()
        intents.message_content = True  # necessário para receber conteúdo da mensagem
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        @self.bot.event
        async def on_ready():
            print(f'Bot conectado como {self.bot.user}')

        @self.bot.command(name="bp")
        async def mover_bp(ctx, *, argumento=None):
            try:
                if self.classe != 'BK':
                    return

                if not argumento:
                    await ctx.send("⚠️ Uso correto: `!bp mover`")
                    return

                TEMPO_ESPERA = 600  # 10 minutos em segundos
                tempo_atual = time.time()

                if self.tempo_ultimo_comando is not None:
                    tempo_passado = tempo_atual - self.tempo_ultimo_comando
                    if tempo_passado < TEMPO_ESPERA:
                        restante = int(TEMPO_ESPERA - tempo_passado)
                        minutos = restante // 60
                        segundos = restante % 60
                        await ctx.send(f"⏳ Aguarde {minutos}m {segundos}s para executar novamente.")
                        return

                    # Atualiza o tempo do último comando
                self.tempo_ultimo_comando = tempo_atual

                argumento = argumento.strip().lower()

                if 'move' in argumento:
                    data = self.json_manager.read()
                    data["comando_discord"] = "mover_bp"
                    self.json_manager.write(data)
                    await ctx.send("✅ Comando enviado com sucesso.")
                else:
                    await ctx.send(f"❌ Comando inválido: `{argumento}`. Use `!bp mover`.")

            except Exception as e:
                await ctx.send(f"❌ Erro ao processar comando")
                print(f"[Erro DiscordBotController] ao executar !bp: {e}")

    def start(self):
        """Inicia o bot do Discord no loop principal"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.bot.start(self.token))

    async def enviar_mensagem(self, image, texto: str, channel_id: int):
        """Envia uma mensagem com ou sem imagem para o canal do Discord."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            print(f"[Erro] Canal ID {channel_id} não encontrado.")
            return

        try:
            if image is not None:
                await self._enviar_com_imagem(channel, image, texto)
            else:
                await self._enviar_somente_texto(channel, texto)
        except Exception as e:
            print(f"[Erro] Falha ao enviar mensagem para o Discord: {e}")

    async def _enviar_com_imagem(self, channel, image, texto):
        """Envia uma mensagem com imagem (usando buffer em memória)."""
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        arquivo = discord.File(img_buffer, filename="screenshot_bp.png")
        await channel.send(content=texto, file=arquivo)

    async def _enviar_somente_texto(self, channel, texto):
        """Envia uma mensagem de texto simples (sem imagem)."""
        await channel.send(content=texto)

    async def limpar_mensagens(self, channel_id):
        """Limpa apenas as mensagens enviadas pelo bot no canal"""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            print("Erro: Canal não encontrado.")
            return

        async for message in channel.history(limit=10):
            if not message.pinned and message.author == self.bot.user:
                await message.delete()

    import datetime

    async def limpar_mensagens_antigas(self, channel_id):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            print("Erro: Canal não encontrado.")
            return

        agora = datetime.datetime.now(datetime.timezone.utc)
        uma_hora_atras = agora - datetime.timedelta(hours=6)

        async for message in channel.history(limit=100):
            if (
                    not message.pinned
                    and message.author == self.bot.user
                    and message.created_at < uma_hora_atras
            ):
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Erro ao deletar mensagem: {e}")

    async def limpar_todas_mensagens(self, channel_id):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            print("Erro: Canal não encontrado.")
            return

        async for message in channel.history(limit=None):
            if not message.pinned:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Erro ao deletar mensagem: {e}")
