from os import environ
from telebot.async_telebot import AsyncTeleBot
import asyncio
from pymongo import MongoClient
from uuid import uuid4

# telebot setup
botToken = environ['token']
bot = AsyncTeleBot(botToken,  parse_mode="Markdown")

# mongodb client setup
client = MongoClient("mongodb+srv://tkt_bot_version1:{}@cluster0.tu30q.mongodb.net/myFirstDatabase?retryWrites=true&w=majority".format(environ['pw']))
db = client["mastermind_bot"]
room_db = db["room"]
stats_db = db["stats"]

# check if account is created 
async def check_ac(message):
    id = message.from_user.id
    myquery = {"_id" : id}

    if stats_db.count_document(myquery) == 0 :
        data = {"_id" : id , "win":0 , "room": ""}
        stats_db.insert_one(data)

# check if user is in a room
async def check_room(message):
    id = message.from_user.id
    myquery = {"_id" : id}

    data = stats_db.find(myquery)
    if data["room"] != "":
        return True
    else :
        return False



# open a room for gaming
@bot.message_handler(commands="open")
async def open(message):
    check_ac(message)
    if check_room(message):
        await bot.reply(message , "You already inside a room :/")
    else:
        room_num = str(uuid4()).replace("-","").upper()[0:4]
        owner = message.from_user.id

        data = {"_id":room_num , "owner": owner , "players" : [id]}
        room_db.insert_one(data)

        stats_db.update_one({"_id" : id } , {"$set" : {"room" : room_num}})

        await bot.reply_to(message , f"Room {room_num} opened")

         

# join a room 
@bot.message_handler(commands="join")
async def join(message):
    check_ac(message)
    if check_room(message):
        await bot.reply(message , "You alread join a room :/")
    else:
        room_num = message.chat.replace("/join " , "")
        myquery = {"_id" : room_num}

        if room_db.find(myquery) == 0:
            await bot.reply_to(message , "Invalid room number :< ")
        else:
            stats_db.update_one({"_id" : message.chat.id } , {"$set" : {"room" : room_num}})

            data = room_db.find(myquery)
            for id in data["players"]:
                await bot.reply_to(id , "{} has joined the room {}".format(message.chat.username , room_num))
            stats_db.update_one({"_id" : room_num } , {"$set" : {"room" : room_num}})

            await bot.reply_to(message , f"Room {room_num} joined")

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