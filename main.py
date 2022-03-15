from os import environ
from telebot.async_telebot import AsyncTeleBot
import asyncio
from pymongo import MongoClient
from uuid import uuid4
from random import choice , randint

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
        data = {"_id" : id , "win":0 , "room": "" , "name" : message.chat.username}
        stats_db.insert_one(data)

# check if user is in a room
async def check_room(message):
    id = message.from_user.id
    myquery = {"_id" : id}

    data = stats_db.find(myquery)
    if data["room"] != "":
        return data["room"]
    else :
        return False

# check owner
async def check_owner(room_num):
    myquery = {"_id" : id}
    data = room_db.find(myquery)

    return data["owner"][1]



# open a room for gaming
@bot.message_handler(commands="open")
async def open(message):
    check_ac(message)
    if check_room(message) != False:
        await bot.reply(message , "You already inside a room :/")
    else:
        room_num = str(uuid4()).replace("-","").upper()[0:4]
        owner = message.from_user.id
        name = message.chat.username

        data = {"_id":room_num , "owner": [name , owner] , "players" : [[name , owner , 0]] , "picker" : [] , "code" : []}
        room_db.insert_one(data)

        stats_db.update_one({"_id" : id } , {"$set" : {"room" : room_num}})

        await bot.reply_to(message , f"Room {room_num} opened")

         

# join a room 
@bot.message_handler(commands="join")
async def join(message):
    check_ac(message)
    if check_room(message) != False:
        await bot.reply_to(message , "You alread join a room :/")
    else:
        room_num = message.chat.replace("/join " , "")
        myquery = {"_id" : room_num}

        if room_db.find(myquery) == 0:
            await bot.reply_to(message , "Invalid room number :< ")
        else:
            stats_db.update_one({"_id" : message.chat.id } , {"$set" : {"room" : room_num}})

            data = room_db.find(myquery)
            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "{} has joined the room {}".format(message.chat.username , room_num))

            stats_db.update_one({"_id" : room_num } , {"$set" : {"room" : room_num}})
            room_db.update_one({"_id" : room_num} , {"$set" : {"plauers" : data["players"].append([message.chat.username,message.from_user.id])}})
            await bot.reply_to(message , f"Room {room_num} joined")

#kick player in room
@bot.message_handler(commands="kick")
async def kick(message):
    check_ac(message)
    if check_room(message) != False:
        myquery = {"_id" : check_room(message)}
        data = room_db.find(myquery)

        if check_owner(data["_id"]) == message.from_user.id:
            player = message.text.replace("/kick ","")

            for player_list in data["players"]:
                if player in player_list:
                    data["players"] = data["players"].remove(player_list)

                    for player_list2 in data["players"]:
                        await bot.send_message(player_list2[1] , "{} has been removed {}".format(player))
                    return ""

            await bot.reply_to(message , f"No player named {player}") 

        else:
            await bot.reply_to(message , "You are not the owner of the room")

    else:
        await bot.reply_to(message , "You are not inside a room")

# start the game
@bot.message_handler(commands="start")
async def start(message):
    check_ac(message)
    if check_room(message) != False:
        myquery = {"_id" : check_room(message)}
        data = room_db.find(myquery)

        if check_owner(data["_id"]) == message.from_user.id:
            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "Game start!")

            if len(data["players"]) == 1:
                await bot.reply_to(message , "Due to only 1 player , the code pegs will be maken by the bot")

                code = []
                for i in range(5):
                    code.append(randint(1,7))

                room_db.update_one({"_id" : check_room(message)} , {"$set" : {"picker" : "bot" , "code" : code}})

            else:
                picker = choice(data["players"])
                for player_list in data["players"]:
                    await bot.send_message(player_list[1] , "{} is chosen to make the code pegs".format(picker[0])) 
                await bot.send_message(picker[1] , "Pls enter the code pegs")






        else:
            await bot.reply_to(message , "You are not the owner of the room")

    else:
        await bot.reply_to(message , "You are not inside a room")

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
    number = message.text.replace("/board " ,"")
    data = stats_db.find().sort("win" , -1).limit(int(number))
    
    await bot.reply_to(message , f"Here is the top {number} players")

    msg = ""
    for i in range(int(number)):
        msg += "{}. {} with {} wins".format(i , data[i]["name"] , data[i]["win"]) + "\n"

    await bot.reply_to(message , msg)


asyncio.run(bot.infinity_polling())