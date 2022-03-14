from os import environ
from telebot.async_telebot import AsyncTeleBot
import asyncio

botToken = environ['token']
bot = AsyncTeleBot(botToken,  parse_mode="Markdown")

# open a room for gaming
@bot.message_handler(commands="open")
async def open(message):
    pass

# join a room 
@bot.message_handler(commands="join")
async def join(message):
    pass

# start the game
@bot.message_handler(commands="start")
async def start(message):
    pass

# guess the mastermind
@bot.message_handler(commands="guess")
async def guess(message):
    pass

# end the game
@bot.message_handler(commands="end")
async def end(message):
    pass

# leave the room
@bot.message_handler(commands="leave")
async def leave(message):
    pass

# close the room
@bot.message_handler(commands="close")
async def close(message):
    pass

# show room information
@bot.message_handler(commands="room")
async def room(message):
    pass

# show player stats
@bot.message_handler(commands="stats")
async def stats(message):
    pass

# show the leaderboard
@bot.message_handler(commands="board")
async def board(message):
    pass

asyncio.run(bot.infinity_polling())