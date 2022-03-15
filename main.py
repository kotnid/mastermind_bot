from os import environ
from telebot.async_telebot import AsyncTeleBot
from telebot.types import  ReplyKeyboardMarkup
import asyncio
from pymongo import MongoClient
from uuid import uuid4
from random import choice , randint
from logging import info , basicConfig , INFO

# logging config 
basicConfig(level= INFO,
            format= '%(asctime)s %(levelname)s %(message)s',
            datefmt= '%Y-%m-%d %H:%M')

# telebot setup
botToken = environ['token']
bot = AsyncTeleBot(botToken,  parse_mode=None)

# mongodb client setup
client = MongoClient('mongodb+srv://tkt_bot_version1:{}@cluster0.tu30q.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'.format(environ['pw']))
db = client['mastermind_bot']
room_db = db['room']
stats_db = db['stats']

# check if account is created 
def check_ac(message):
    id = message.from_user.id
    myquery = {'_id' : id}
    if stats_db.count_documents(myquery) == 0 :
            data = {'_id' : id , 'win':0 , 'room': '' , 'name' : message.chat.first_name}
            info("User {} with id {} created account".format(message.chat.first_name , str(id)))
            stats_db.insert_one(data)

# check if user is in a room
def check_room(id):
    myquery = {'_id' : id}

    data = stats_db.find_one(myquery)
    if data['room'] != '':
        return data['room']
    else :
        return False

# check owner
def check_owner(room_num):
    myquery = {'_id' : room_num}
    data = room_db.find_one(myquery)

    return data['owner'][1]

# emoji to number
def em_to_num(arr):
    ans = []
    for em in arr:
        if em == '🟥': #red
            ans.append(1)
        elif em == '🟧': #orange
            ans.append(2)  
        elif em == '🟨': #yellow
            ans.append(3)
        elif em == '🟩': #green
            ans.append(4)
        elif em == '🟦': #blue
            ans.append(5)
        elif em == '🟪': #purple
            ans.append(6)
        elif em == '🟫': #brown
            ans.append(7)

    return ans

#number to emoji
def num_to_em(arr):
    ans = []

    for em in arr:
        if em == 1: #red
            ans.append('🟥')
        elif em == 2: #orange
            ans.append('🟧')  
        elif em == 3: #yellow
            ans.append('🟨')
        elif em == 4: #green
            ans.append('🟩')
        elif em == 5: #blue
            ans.append('🟦')
        elif em == 6: #purple
            ans.append('🟪')
        elif em == 7: #brown
            ans.append('🟫')
        elif em == 8:
            ans.append('⬛️')
        elif em == 9:
            ans.append('⬜️')
    return ans

# Information of the bot
@bot.message_handler(commands=['start','help'])
async def start(message):
    await bot.reply_to(message , ''' \
Mastermind Bot

The bot is made by kotnid , code available
https://github.com/kotnid/mastermind_bot

Command available:
        /help - show this message
        /open - open a room
        /join - join a room
        /kick - kick player in room
        /start_game - start a game
        /guess - guess a code pegs
        /end - end a game  
        /leave - leave a room
        /close - close a room
        /stats - show player stats
        /board - show leaderboard

If you have any problem , pls contact tkt0506
\ ''')




# open a room for gaming
@bot.message_handler(commands=['open'])
async def open(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        await bot.reply_to(message , 'You already inside a room :/')
    else:
        room_num = str(uuid4()).replace('-','').upper()[0:4]
        owner = message.from_user.id
        name = message.chat.first_name

        data = {'_id':room_num , 'owner': [name , owner] , 'players' : [[name , owner , 0]] , 'picker' : [] , 'code' : []}
        room_db.insert_one(data)

        stats_db.update_one({'_id' : message.from_user.id } , {'$set' : {'room' : room_num}})

        info("User {} with id {} created room {}".format(message.chat.first_name , message.from_user.id , room_num))
        await bot.reply_to(message , f'Room {room_num} opened')

         

# join a room 
@bot.message_handler(commands=['join'])
async def join(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        await bot.reply_to(message , 'You alread inside a room :/')
    else:
        room_num = message.text.replace('/join ' , '')
        myquery = {'_id' : str(room_num)}
        if room_db.count_documents(myquery) == 1:
            stats_db.update_one({'_id' : message.from_user.id } , {'$set' : {'room' : room_num}})

            data = room_db.find_one(myquery)
            for player_list in data['players']:
                await bot.send_message(player_list[1] , '{} has joined the room {}'.format(message.chat.first_name , room_num))

            stats_db.update_one({'_id' : room_num } , {'$set' : {'room' : room_num}})

            data['players'].append([message.chat.first_name, message.from_user.id , 0])
            room_db.update_one({'_id' : room_num} , {'$set' : {'players' : data['players']}})
            await bot.reply_to(message , f'Room {room_num} joined')
            info("User {} with id {} join room {}".format(message.chat.first_name ,message.from_user.id , room_num))
        else:
            await bot.reply_to(message , 'Invalid room number :< ')
            

#kick player in room
@bot.message_handler(commands=['kick'])
async def kick(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)}
        data = room_db.find_one(myquery)

        if check_owner(data['_id']) == message.from_user.id:
            player = message.text.replace('/kick ','')

            if player == message.chat.first_name:
                await bot.reply_to(message , "Bruh u kick yourself which is illegal")

            else:
                for player_list in data['players']:
                    if player in player_list:
                        info("User {} with id {} removed player {} with id {} out of room {}".format(message.chat.first_name , message.from_user.id , player_list[0] , player_list[1] , data['_id']))
                        for player_list2 in data['players']:
                            await bot.send_message(player_list2[1] , '{} has been removed'.format(player))

                        data['players'].remove(player_list)
                        room_db.update_one({'_id' : data['_id']} , {'$set' : {'players' : data['players']}})

                        stats_db.update_one({'_id' : player_list[1]} , {'$set' : {'room' : ""}})

                        return ''

                await bot.reply_to(message , f'No player named {player}') 

        else:
            await bot.reply_to(message , 'You are not the owner of the room')

    else:
        await bot.reply_to(message , 'You are not inside a room')

# start the game
@bot.message_handler(commands=['start_game'])
async def start(message):
    check_ac(message)
    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)}
        data = room_db.find_one(myquery)

        if check_owner(data['_id']) == message.from_user.id:
            for player_list in data['players']:
                await bot.send_message(player_list[1] , 'Game start!')

            info("User {} with id {} start game in room {}".format(message.chat.first_name , message.from_user.id , data['_id'] ))

            name = message.text.replace("start_game " , "")

            if len(data['players']) == 1 or name == "bot" :
                await bot.reply_to(message , 'The code pegs will be maken by the bot')
                await bot.reply_to(message , "guess the code pegs like this : /guess 🟥 🟧 🟨 🟩 🟦 (black and white can't be used")

                code = []
                for i in range(5):
                    code.append(randint(1,7))

                room_db.update_one({'_id' : check_room(message.from_user.id)} , {'$set' : {'picker' : ['bot','id'] , 'code' : code}})

            elif name == "ran":
                picker = choice(data['players'])
                for player_list in data['players']:
                    await bot.send_message(player_list[1] , '{} is chosen to make the code pegs'.format(picker[0])) 
                await bot.send_message(picker[1] , 'Pls enter the code pegs')

                markup = ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Enter', 'Choose another one')
                bot.register_next_step_handler(bot.send_message(message.chat.id, 'Yes/no?', reply_markup=markup), code_next_step)

            else:
                picker = []

                for player_list in data['players']:
                    if name in player_list:
                        picker = player_list
                
                if picker == []:
                    picker = choice(data['players'])
                
                for player_list in data['players']:
                    await bot.send_message(player_list[1] , '{} is chosen to make the code pegs'.format(picker[0])) 
                await bot.send_message(picker[1] , 'Pls enter the code pegs')

                markup = ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('Enter', 'Choose another one')
                bot.register_next_step_handler(bot.send_message(message.chat.id, 'Yes/no?', reply_markup=markup), code_next_step)
                




        else:
            await bot.reply_to(message , 'You are not the owner of the room')

    else:
        await bot.reply_to(message , 'You are not inside a room')

# guess the mastermind
@bot.message_handler(commands=['guess'])
async def guess(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)}
        data = room_db.find_one(myquery)


        if data['code'] == [] :
            await bot.reply_to(message , "Game haven't start yet or picker haven't decide yet")

        elif data['picker'][1]  == message.from_user.id :
            await bot.reply_to(message , 'You are the picker!')

        else:
            emojis = message.text.replace('/guess ' , '').split()
            input = em_to_num(emojis)
            
            info("User {} with id {} guess {}".format(message.chat.first_name , message.from_user.id  , input))

            if input == data['code'] :
                for player_list in data['players']:
                    await bot.send_message(player_list[1] , 'User {} with id {} won the game '.format(message.chat.first_name , message.from_user.id))
                    if message.from_user.id in player_list:
                        room_db.update_one({'_id' : check_room(message.from_user.id) , 'players' : player_list} , { '$set' : {'player.$' : [player_list[0] , player_list[1] , 0]}})
                
                stats_db.update_one({'_id' : message.from_user.id} , {'$inc' : {'win' : 1}})
                info("User {} with id {} won a game in room {}".format(message.chat.first_name , message.from_user.id ,data['_id']))
                
            else:

                if len(input) != 5:
                    await bot.reply_to(message , 'Invalid input')
                
                else:
                    output = []

                    for i in range(5):
                        if input[i] == data['code'][i]:
                            output.append(8)
                            input[i] = 0 
                            data['code'][i] = 0

                    for i in range(1 , 8):
                        if input.count(i) > data['code'].count(i):
                            output.extend(9 for x in range(data['code'].count(i)))
                        elif input.count(i) <= data['code'].count(i):
                            output.extend(9 for x in range(input.count(i)))
                    
                    emojis = num_to_em(output)
                    msg = 'Reaction : '

                    for emoji in emojis:
                        msg += emoji + ' '

                    emojis2 = num_to_em(input)
                    msg2 = 'Code entered : '

                    for emoji2 in emojis2:
                        msg2 += emoji2 + ' '

                    await bot.reply_to(message , msg2 + '\n' + msg )
                        
                    for player_list in data['players']:
                        if message.from_user.id in player_list:
                            info("User {} with id {} in round {} in room {} now ".format(message.chat.first_name , message.from_user.id , player_list[2]+2 , data['_id']))
                            if player_list[2] == 11 :
                                await bot.reply_to(message , 'Oof it is round 12 already so you lost')
                                stats_db.update_one({'_id' : data['picker'][1]} , {'$inc' : {'win' : 1}})
                                room_db.update_one({'_id' : check_room(message.from_user.id) , 'players' : player_list}, { '$set' : {'players.$' : [player_list[0] , player_list[1] , int(player_list[2])+1]}})

                            elif player_list[2] == 12:
                                await bot.reply_to(message , 'Pls wait until the game ended')

                            else:
                                room_db.update_one({'_id' : check_room(message.from_user.id) , 'players' : player_list}, { '$set' : {'players.$' : [player_list[0] , player_list[1] , int(player_list[2])+1]}})
                                await bot.reply_to(message , 'It is round {} now'.format(player_list[2]+2))
                                # add inline keyboard (option : guess , leave , stats)

    else:
        await bot.reply_to(message , 'You are not inside a room')

# end the game
@bot.message_handler(commands=['end'])
async def end(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        if check_owner(check_room(message.from_user.id)) == message.from_user.id:
            myquery = {'_id' : check_room(message.from_user.id)}
            data = room_db.find_one(myquery)
            players_data = []
            for player_list in data['players']:
                await bot.send_message(player_list[1] , 'Owner has ended the game')
                players_data.append([player_list[0] , player_list[1] , 0])   

            room_db.update_one({'_id' : data['_id']} , { '$set' : {'players' : players_data , 'code' : [] , 'picker' : []}})
            info("User {} with id {} ended a game in room {}".format(message.chat.first_name , message.from_user.id , data['_id']))

        else:
           await bot.reply_to(message , 'You are not the owner of the room') 

    else:
        await bot.reply_to(message , 'You are not inside a room')

# leave the room
@bot.message_handler(commands=['leave'])
async def leave(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = {'_id' : check_room(message.from_user.id)}
        data = room_db.find_one(myquery)
        player_data = []
        room_num = data["_id"]

        for player_list in data['players']:
            await bot.send_message(player_list[1] , f'Player {message.chat.first_name} has left the room')

            if message.chat.first_name in player_list :
                player_data = player_list

        data['players'].remove(player_data)
        room_db.update_one({'_id' : data['_id']} , {'$set' : {'players' : data['players']}})
        stats_db.update_one({'_id' : message.from_user.id} , {'$set' : {'room' : ''}})
        info("User {} with id {} left the room {}".format(message.chat.first_name , message.from_user.id , data['_id']))

        if len(data['players']) == 0:
            room_db.delete_one({'_id' : room_num})
            info("Room {} closed".format(room_num))

        elif check_owner(room_num) == message.from_user.id:
            myquery = {'_id' : data['_id']}
            data = room_db.find_one(myquery)

            picker = choice(data['players'])
            print(picker)
            for player_list in data['players']:
                await bot.send_message(player_list[1] , 'Player {} has become new owner'.format(picker[0]))
            
            room_db.update_one({'_id' : data['_id']} , {'$set' : {'owner' : [picker[0] , picker[1]]}})
            info('Player {} has become new owner in room {}'.format(picker[0] , room_num))
    else:
        await bot.reply_to(message , 'You are not inside a room')


# close the room
@bot.message_handler(commands=['close'])
async def close(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        if check_owner(check_room(message.from_user.id)) == message.from_user.id:
            myquery = {'_id' : check_room(message.from_user.id)}
            data = room_db.find_one(myquery)
            room_num = data['_id']

            for player_list in data['players']:
                await bot.send_message(player_list[1] , 'Owner has close the room')

                stats_db.update_one({'_id' : player_list[1]} , {'$set' : {'room' : ''}})

            info("User {} with id {} close the room {}".format(message.chat.first_name , message.from_user.id , data['_id']))
            room_db.delete_one({'_id' : room_num})
            
        else:
           await bot.reply_to(message , 'You are not the owner of the room') 

    else:
        await bot.reply_to(message , 'You are not inside a room')

# show room information
@bot.message_handler(commands=['room'])
async def room(message):
    check_ac(message)

    if check_room(message.from_user.id) != False:
        myquery = check_room(message.from_user.id)
        data = room_db.find_one(myquery)

        players = ""
        for player_list in data['players']:
            players += str(player_list[0]) + ' in round ' + str(player_list[2])+'\n'

        if len(data['picker']) == 0:
            picker = "None"
        else:
            picker = data['picker'][0]

        info("User {} with id {} check the stats of room {}".format(message.chat.first_name , message.from_user.id , data['_id']))
        await bot.reply_to(message , 'Room {} stats'.format(data['_id']) + '\n' + 'owner : {} '.format(data['owner'][0]) + '\n' + 'picker : {} '.format(picker) + '\n' + 'players : ' + '\n'+ players)
    else:
        await bot.reply_to(message , 'You are not inside a room')    

# show player stats
@bot.message_handler(commands=['stats'])
async def stats(message):
    check_ac(message)

    myquery = {'_id' : message.from_user.id}
    data = stats_db.find_one(myquery)
    await bot.reply_to(message , 'Player {} stats'.format(data['name']) + '\n' + 'wins : {}'.format(data['win']) + '\n' + 'Current room : {}'.format(data['room']))
    info("User {} with id {} check the stats".format(message.chat.first_name , message.from_user.id))

# show the leaderboard
@bot.message_handler(commands=['board'])
async def board(message):
    check_ac(message)

    number = message.text.replace('/board ' ,'')
    data = stats_db.find().sort('win' , -1).limit(int(number))
    
    msg =  f'Here is the top {number} players'+'\n'+'\n'
    for i in range(int(number)):
        msg += '{}. {} with {} wins'.format(i+1 , data[i]['name'] , data[i]['win']) + '\n'

    info('User {} with id {} check the leaderboard'.format(str(message.chat.first_name) , str(message.from_user.id)))
    await bot.reply_to(message , msg)


# Receive the option chosen by player
def code_next_step(message):
    if message.text == 'Enter':
        bot.register_next_step_handler(bot.reply_to(message , 'Ok then type the code by using the sticker'), code_next_step2)

    else :
        myquery = {'_id' : check_room(message.from_user.id)}
        data = room_db.find_one(myquery)
        picker = choice(data['players'])

        markup = ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Enter', 'Choose another one')
        bot.register_next_step_handler(bot.send_message(picker[1], 'Yes/no?', reply_markup=markup), code_next_step)




# Receive the code pegs made by player
def code_next_step2(message):
    code = message.text.split()
    input = em_to_num(code)

    if len(input) != 5:
        bot.register_next_step_handler(bot.reply_to(message , 'Invalid input , please try again'), code_next_step2)
    else:
        room_num = check_room(message.from_user.id)

        myquery = {'_id' : room_num}
        data = room_db.find_one(myquery)

        room_db.update_one({'_id' : room_num} , {'$set' : {'code' : input}})

        for player_list in data['players']:
            bot.reply_to(player_list[1] , 'Player {} has submitted the code pegs , the game start now ~ '.format(message.chat.first_name))


asyncio.run(bot.infinity_polling())