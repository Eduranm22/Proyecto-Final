import discord
import random
import json
from discord.ext import commands
from utils.story_engine import get_story_node, make_choice
from utils.save import update_user_progress
from utils.eco_engine import start_session, handle_answer, load_eco_data
import utils.eco_engine as eco_engine
from utils.trivia import start_trivia_session, get_current_question, answer_question
from utils.challenge import assign_challenge, claim_challenge, get_balance
from utils.currency import get_balance, update_currency

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command()
async def cuento(ctx):
    user_id = ctx.author.id
    node_id, node = get_story_node(user_id)

    intro_msg = (
        " **Bienvenidos a *Ecos de la Tierra***\n"
        "Un juego de rol interactivo sobre el clima en el que tus decisiones dan forma al futuro.\n\n"
        " Usa `!escoger [numero]` para tomar decisiones.\n"
        " Usa `!reinciar` para empezar de nuevo.\n"
        " Tu progreso se guarda automáticamente.\n"
        " Te esperan múltiples historias. ¡Explóralos todos!\n"
        "━━━━━━━━━━━━━━━\n"
    )

    story_text = f"**{node['text']}**\n"
    for i, choice in enumerate(node["choices"]):
        story_text += f"{i+1}. {choice['option']}\n"

    await ctx.send(intro_msg + story_text)


@bot.command()
async def escoger(ctx, choice_index: int):
    user_id = ctx.author.id
    new_id, new_node, error = make_choice(user_id, choice_index - 1)
    if error:
        await ctx.send(error)
    else:
        msg = f"**{new_node['text']}**\n"

        # Detectar si es un nodo final
        if not new_node["choices"]:
            reward = 0
            text_lower = new_node["text"].lower()

            if "(final verdadero)" in text_lower:
                reward = 60
                await ctx.send("Has alcanzado el **final verdadero**. ¡Increíble trabajo!")
            elif "(final bueno)" in text_lower:
                reward = 20
                await ctx.send("Has alcanzado un **final bueno**. ¡Buen trabajo!")
            elif "(final malo)" in text_lower:
                reward = -10
                await ctx.send("Has alcanzado un **final malo**. Intenta otro camino.")
            elif "(final neutral)" in text_lower:
                reward = 0
                await ctx.send("Has alcanzado un **final neutral**.")

            if reward != 0:
                new_balance = update_currency(user_id, reward)
                await ctx.send(f"Has ganado {reward} monedas. Tu saldo actual es {new_balance} eco-monedas.")
            else:
                await ctx.send("No se han ganado ni perdido monedas en este final.")

        else:
            for i, choice in enumerate(new_node["choices"]):
                msg += f"{i+1}. {choice['option']}\n"

        await ctx.send(msg)

@bot.command(name="reiniciar")
async def reiniciar(ctx):
    user_id = ctx.author.id

    with open("story/story_data.json", "r", encoding="utf-8") as f:
        stories = json.load(f)
    story_ids = list(stories.keys())

    random_story = random.choice(story_ids)

    update_user_progress(user_id, random_story, "start")

    await ctx.send(f"¡Tu aventura ha sido reiniciada! Ahora estás comenzando la historia **{random_story}** desde el principio. Escribe !story para comenzar tu nueva aventura.")

@bot.command(name="eco")
async def eco_start(ctx):
    question = eco_engine.start_session(ctx.author.id)
    await ctx.send(f"Iniciando calculadora de huella ecológica.\n{question}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = eco_engine.load_eco_data()
    user_data = data.get(str(message.author.id))
    if user_data and "step" in user_data:
        next_question, error = eco_engine.handle_answer(message.author.id, message.content)
        if error:
            await message.channel.send(error)
        elif next_question:
            await message.channel.send(next_question)
        else:
            pass

        return

    await bot.process_commands(message)

@bot.command(name="trivia")
async def trivia(ctx):
    user_id = ctx.author.id
    question = start_trivia_session(user_id)
    if not question:
        await ctx.send("No hay suficientes preguntas.")
        return

    options = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    await ctx.send(f"Trivia:\n**{question['question']}**\n{options}\nResponde con `!responder <número>`.")

@bot.command(name="responder")
async def responder(ctx, respuesta: int):
    user_id = ctx.author.id
    result = answer_question(user_id, respuesta)
    if result is None:
        await ctx.send("No tienes una sesión activa. Usa `!trivia` para comenzar.")
        return

    correct, correct_answer, finished, score = result
    msg = "¡Correcto!" if correct else f"Incorrecto. La respuesta era: **{correct_answer}**"
    await ctx.send(msg)

    if finished:
        await ctx.send(
            f"Fin de la sesión. Aciertos total de todos los tiempos: {score['correct']} / {score['total']}"
        )
    else:
        question = get_current_question(user_id)
        options = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
        await ctx.send(f"Siguiente pregunta:\n**{question['question']}**\n{options}")

@bot.command(name="reto_diario")
async def reto_diario(ctx):
    challenge, msg = assign_challenge(ctx.author.id, "daily")
    if challenge:
        await ctx.send(f"Reto diario asignado:\n**{challenge}**\n¡Usa `!reclamar_diario` cuando lo completes!")
    else:
        await ctx.send(msg)

@bot.command(name="reto_horario")
async def reto_horario(ctx):
    challenge, msg = assign_challenge(ctx.author.id, "hourly")
    if challenge:
        await ctx.send(f"Reto por hora asignado:\n**{challenge}**\n¡Usa `!reclamar_horario` cuando lo completes!")
    else:
        await ctx.send(msg)

@bot.command(name="reclamar_diario")
async def reclamar_diario(ctx):
    result = claim_challenge(ctx.author.id, "daily")
    await ctx.send(result)

@bot.command(name="reclamar_horario")
async def reclamar_horario(ctx):
    result = claim_challenge(ctx.author.id, "hourly")
    await ctx.send(result)

@bot.command(name="eco_monedas")
async def eco_monedas(ctx):
    coins = get_balance(ctx.author.id)
    await ctx.send(f"💰 Tienes {coins} eco-coins.")

@bot.command(name="ayuda")
async def ayuda(ctx):
    help_text = """
**Lista de comandos disponibles:**

**Historias interactivas:**
!cuento - Inicia una historia.
!escoger <opción> - Elige una opción en la historia.
!reiniciar - Reinicia la historia actual.

**Trivia:**
!trivia - Comienza una trivia.
!responder <opción> - Responde a la pregunta actual.

**Eco-calculadora:**
!eco - Evalúa tu impacto ecológico.

**Retos:**
!reto_diario - Recibe un reto ecológico diario.
!reclamar_diario - Reclama recompensa por el reto diario.
!reto_horario - Recibe un reto ecológico por hora.
!reclamar_horario - Reclama recompensa por el reto horario.

**Eco-monedas:**
!eco_monedas - Consulta cuántas eco-coins tienes.

**Ayuda:**
!ayuda - Muestra esta lista de comandos.
    """
    await ctx.send(help_text)


bot.run("TOKEN")
