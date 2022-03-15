from os import environ
from telebot.async_telebot import AsyncTeleBot
from telebot.types import  ReplyKeyboardMarkup
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
async def check_room(id):
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

# emoji to number
async def em_to_num(arr):
    ans = []

    for em in arr:
        if em == "\ud83d\udfe5": #red
            ans.append(1)
        elif em == "\ud83d\udfe7": #orange
            ans.append(2)  
        elif em == "\ud83d\udfe8": #yellow
            ans.append(3)
        elif em == "\ud83d\udfe9": #green
            ans.append(4)
        elif em == "\ud83d\udfe6": #blue
            ans.append(5)
        elif em == "\ud83d\udfea": #purple
            ans.append(6)
        elif em == "\ud83d\udfeb": #brown
            ans.append(7)

    return ans

#number to emoji
async def num_to_em(arr):
    ans = []

    for em in arr:
        if em == 1: #red
            ans.append('\U0001F7E5')
        elif em == 2: #orange
            ans.append('\U0001F7E7')  
        elif em == 3: #yellow
            ans.append('\U0001F7E8')
        elif em == 4: #green
            ans.append('\U0001F7E9')
        elif em == 5: #blue
            ans.append('\U0001F7E6')
        elif em == 6: #purple
            ans.append('\U0001F7EA')
        elif em == 7: #brown
            ans.append('\U0001F7EB')
        elif em == 8:
            ans.append('\U00002B1B')
        elif em == 9:
            ans.append('\U00002B1C')
    return ans

# Information of the bot
@bot.message_handler(commands=["start","help"])
async def start(message):
    await bot.reply_to(
        "Mastermind Bot" + "\n \n" +
        "The bot is made by kotnid , code available : https://github.com/kotnid/mastermind_bot"
        "Command available: " + "\n" +
        "/help - show this message" + "\n" + 
        "/open - open a room" + "\n" +
        "/join - join a room" + "\n" +
        "/kick - kick player in room" + "\n" +
        "/start - start a game" + "\n" +
        "/guess - guess a code pegs" + "\n" +
        "/end - end a game" + "\n" + 
        "/leave - leave a room" + "\n" +
        "/close - close a room" + "\n" +
        "/stats - show player stats" + "\n" +
        "/board - show leaderboard" + "\n \n" +
        "If you have any problem , pls contact @tkt0506 ")




# open a room for gaming
@bot.message_handler(commands=["open"])
async def open(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
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
@bot.message_handler(commands=["join"])
async def join(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        await bot.reply_to(message , "You alread join a room :/")
    else:
        room_num = message.chat.replace("/join " , "")
        myquery = {"_id" : room_num}

        if room_db.find(myquery) == 0:
            await bot.reply_to(message , "Invalid room number :< ")
        else:
            stats_db.update_one({"_id" : message.from_user.id } , {"$set" : {"room" : room_num}})

            data = room_db.find(myquery)
            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "{} has joined the room {}".format(message.chat.username , room_num))

            stats_db.update_one({"_id" : room_num } , {"$set" : {"room" : room_num}})
            room_db.update_one({"_id" : room_num} , {"$set" : {"players" : data["players"].append([message.chat.username , message.from_user.id , 0])}})
            await bot.reply_to(message , f"Room {room_num} joined")

#kick player in room
@bot.message_handler(commands=["kick"])
async def kick(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        myquery = {"_id" : check_room(message.from_user.id)}
        data = room_db.find(myquery)

        if check_owner(data["_id"]) == message.from_user.id:
            player = message.text.replace("/kick ","")

            for player_list in data["players"]:
                if player in player_list:
                    room_db.update_one({"_id" : data["_id"]} , {"$set" : {"players" : data["players"].remove(player_list)}})

                    for player_list2 in data["players"]:
                        await bot.send_message(player_list2[1] , "{} has been removed {}".format(player))
                    return ""

            await bot.reply_to(message , f"No player named {player}") 

        else:
            await bot.reply_to(message , "You are not the owner of the room")

    else:
        await bot.reply_to(message , "You are not inside a room")

# start the game
@bot.message_handler(commands=["start"])
async def start(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        myquery = {"_id" : check_room(message.from_user.id)}
        data = room_db.find(myquery)

        if check_owner(data["_id"]) == message.from_user.id:
            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "Game start!")

            if len(data["players"]) == 1:
                await bot.reply_to(message , "Due to only 1 player , the code pegs will be maken by the bot")

                code = []
                for i in range(5):
                    code.append(randint(1,7))

                room_db.update_one({"_id" : check_room(message.from_user.id)} , {"$set" : {"picker" : ["bot","id"] , "code" : code}})

            else:
                picker = choice(data["players"])
                for player_list in data["players"]:
                    await bot.send_message(player_list[1] , "{} is chosen to make the code pegs".format(picker[0])) 
                await bot.send_message(picker[1] , "Pls enter the code pegs")

                markup = ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Enter', 'Choose another one')
                bot.register_next_step_handler(bot.send_message(message.chat.id, "Yes/no?", reply_markup=markup), code_next_step)




        else:
            await bot.reply_to(message , "You are not the owner of the room")

    else:
        await bot.reply_to(message , "You are not inside a room")

# guess the mastermind
@bot.message_handler(commands=["guess"])
async def guess(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = {"_id" : check_room(message.from_user.id)}
        data = room_db.find(myquery)

        if data["picker"][1]  == message.from_user.id :
            await bot.reply_to(message , "You are the picker!")

        elif data["code"] == "":
            await bot.reply_to(message , "Game haven't start yet or picker haven't decide yet")

        else:
            emojis = message.text.replace("/guess " , "").split()
            input = em_to_num(emojis)
            
            if input == data["code"] :
                for player_list in data["players"]:
                    await bot.send_message(player_list[1] , "Player {} won the game".format(message.chat.username))
                    if message.from_user.id in player_list:
                        room_db.update_one({"_id" : check_room(message.from_user.id) , "players" : player_list} , { "$set" : {"player.$" : [player_list[0] , player_list[1] , 0]}})
                
                stats_db.update_one({"_id" : message.from_user.id} , {"$inc" : {"win" : 1}})
                
            else:

                if len(input) != 5:
                    await bot.reply_to(message , "Invalid input")
                
                else:
                    output = []

                    for i in range(5):
                        if input[i] == data["code"][i]:
                            output.append(8)
                            input[i] = 0 
                            data["code"][i] = 0
                    
                    for i in range(1 , 7):
                        if input.count(i) > data["code"][i].count(i):
                            output.extend(9 for i in range(data["code"][i].count(i)))
                        elif input.count(i) <= data["code"][i].count(i):
                            output.extend(9 for i in range(input.count(i)))
                        
                    emojis = num_to_em(output)
                    msg = "Reaction : "

                    for emoji in emojis:
                        msg += emoji + "\n"

                    emojis2 = num_to_em(input)
                    msg2 = "Code entered : "

                    for emoji2 in emojis2:
                        msg2 += emoji2 + "\n"

                    await bot.reply_to(message , msg2 + "\n" + msg )
                        
                    for player_list in data["players"]:
                        if message.from_user.id in player_list:
                            if player_list[2] == 12 :
                                await bot.reply_to(message , "Oof it is round 12 already so you lost")
                                stats_db.update_one({"_id" : data["picker"][1]} , {"$inc" : {"win" : 1}})
                                room_db.update_one({"_id" : check_room(message.from_user.id) , "players" : player_list}, { "$set" : {"player.$" : [player_list[0] , player_list[1] , int(player_list[2])+1]}})

                            elif player_list[2] == 13:
                                await bot.reply_to(message , "Pls wait until the game ended")

                            else:
                                room_db.update_one({"_id" : check_room(message.from_user.id) , "players" : player_list}, { "$set" : {"player.$" : [player_list[0] , player_list[1] , int(player_list[2])+1]}})
                                await bot.reply_to(message , f"It is round {player_list[2]} now")
                                # add inline keyboard (option : guess , leave , stats)

    else:
        await bot.reply_to(message , "You are not inside a room")

# end the game
@bot.message_handler(commands=["end"])
async def end(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        if check_owner(check_room(message.from_user.id)) == message.from_user.id:
            myquery = {"_id" : check_room(message.from_user.id)}
            data = room_db.find(myquery)

            players_data = []
            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "Owner has ended the game")

                stats_db.update_one({"_id" : player_list[1]} , {"$set" : {"room" : ""}})
                players_data.append([player_list[0] , player_list[1] , 0])   

            room_db.update_one({"_id" : data["_id"]} , {"players" : players_data})

        else:
           await bot.reply_to(message , "You are not the owner of the room") 

    else:
        await bot.reply_to(message , "You are not inside a room")

# leave the room
@bot.message_handler(commands=["leave"])
async def leave(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = {"_id" : check_room(message.from_user.id)}
        data = room_db.find(myquery)
        player_data = []

        for player_list in data["players"]:
            await bot.send_message(player_list[1] , f"Player {message.chat.username} has left the room")

            if message.chat.username in player_list :
                player_data = player_list

        room_db.update_one({"_id" : data["_id"]} , {"$set" : {"players" : data["players"].remove(player_data)}})
        stats_db.update_one({"_id" : message.from_user.id} , {"$set" : {"room" : ""}})

    else:
        await bot.reply_to(message , "You are not inside a room")


# close the room
@bot.message_handler(commands=["close"])
async def close(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        if check_owner(check_room(message.from_user.id)) == message.from_user.id:
            myquery = {"_id" : check_room(message.from_user.id)}
            data = room_db.find(myquery)

            for player_list in data["players"]:
                await bot.send_message(player_list[1] , "Owner has closen the room")

                stats_db.update_one({"_id" : player_list[1]} , {"$set" : {"room" : ""}})

            room_db.delete_one({"_id" : check_room(message.from_user.id)})

        else:
           await bot.reply_to(message , "You are not the owner of the room") 

    else:
        await bot.reply_to(message , "You are not inside a room")

# show room information
@bot.message_handler(commands=["room"])
async def room(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = check_room(message.from_user.id)
        data = room_db.find(myquery)

        players = []
        for player_list in data["player"]:
            players.append(player_list[0] + " in round " + player_list[2])

        await bot.reply_to(message , "Room {} stats".format(data["_id"]) + "\n" + "owner : ".format(data["owner"]) + "\n" + "picker : ".format(data["picker"][0]) + "\n" + "players : " + players)
    else:
        await bot.reply_to(message , "You are not inside a room")    

# show player stats
@bot.message_handler(commands=["stats"])
async def stats(message):
    check_ac(message)

    myquery = {"_id" : message.from_user.id}
    data = stats_db.find(myquery)

    await bot.reply_to(message , "Player {} stats".format(data["name"]) + "\n" + "wins : {}".format(data["win"]) + "\n" + "Current room : {}".format(data["room"]))

# show the leaderboard
@bot.message_handler(commands=["board"])
async def board(message):
    check_ac(message)

    number = message.text.replace("/board " ,"")
    data = stats_db.find().sort("win" , -1).limit(int(number))
    
    await bot.reply_to(message , f"Here is the top {number} players")

    msg = ""
    for i in range(int(number)):
        msg += "{}. {} with {} wins".format(i , data[i]["name"] , data[i]["win"]) + "\n"

    await bot.reply_to(message , msg)


# Receive the option chosen by player
def code_next_step(message):
    if message.text == "Enter":
        bot.register_next_step_handler(bot.reply_to(message , "Ok then type the code by using the sticker"), code_next_step2)

    else :
        myquery = {"_id" : check_room(message.from_user.id)}
        data = room_db.find(myquery)
        picker = choice(data["players"])

        markup = ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Enter', 'Choose another one')
        bot.register_next_step_handler(bot.send_message(picker[1], "Yes/no?", reply_markup=markup), code_next_step)




# Receive the code pegs made by player
def code_next_step2(message):
    code = message.text.split()
    input = em_to_num(code)

    if len(input) != 5:
        bot.register_next_step_handler(bot.reply_to(message , "Invalid input , please try again"), code_next_step2)
    else:
        room_num = check_room(message.from_user.id)

        myquery = {"_id" : room_num}
        data = room_db.find(myquery)

        room_db.update_one({"_id" : room_num} , {"$set" : {"code" : input}})

        for player_list in data["players"]:
            bot.reply_to(player_list[1] , "Player {} has submitted the code pegs , the game start now ~ ".format(message.chat.username))


asyncio.run(bot.infinity_polling())