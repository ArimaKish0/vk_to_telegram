#! /usr/bin/python3

import os, configparser, telebot
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api, datetime, threading, re

pwd = os.environ['HOME']+'/.config/vk_to_telegram'
config = configparser.ConfigParser()
config.read(pwd+'/config')
bot_token = config.get('General', 'bot_token')
send_ids = config.get('General', 'user_ids')
send_ids = [x.strip("[] '") for x in send_ids.split(',')]
bot = telebot.TeleBot(bot_token)

def bot_send(msg):
    for i in send_ids:
        bot.send_message(i, msg)

def ParseBody(msg):
    if 'attachments' in msg.keys():
        attachments = []
        for i in msg['attachments']:
            print(i)
            print()
            if i['type'] == 'sticker':
                sticker = i['sticker']
                print(sticker)
                print()
                maxq = 0
                for j in sticker['images']:
                    if j['width']*j['height']>maxq:
                        maxq = j['width']*j['height']
                        url = j['url']
                attachments.append('sticker {}'.format(url))
            elif i['type'] == 'photo':
                maxq = 0
                for j in i['photo']['sizes']:
                    if j['width']*j['height']>maxq:
                        maxq = j['width']*j['height']
                        url = j['url']
                attachments.append('photo {}'.format(url))
            elif i['type'] == 'audio_message':
                attachments.append(i['audio_message']['link_ogg'])
            else:
                attachments.append(str(i))
        return attachments

def ParsePriv(msg, me, api):
    print(msg)
    print()
    print()
    user = api.users.get(user_ids=msg['from_id'])[0]
    content = ['Sent from "{} {}" message to "{} {}": '.format(user['first_name'], user['last_name'], me['first_name'], me['last_name']) + msg['text']]
    if 'attachments' in msg.keys():
        if msg['attachments']!=[]:
            content.append('Attachments: '+', '.join(ParseBody(msg)))
    print()
    print()
    return content

def ParseChat(msg, me, api):
    print(msg)
    user = api.users.get(user_ids=msg['from_id'])[0]
    content = ['In chat "{}" sent from "{} {}" message to "{} {}": '.format(msg['title'], user['first_name'], user['last_name'], me['first_name'], me['last_name']) + msg['text']]
    if 'attachments' in msg.keys():
        if msg['attachments']!=[]:
            content.append('Attachments: '+', '.join(ParseBody(msg)))
    return content

class LongPool(threading.Thread):

    def __init__(self, account):
        threading.Thread.__init__(self)
        self.paused = False
        self.token = account[0]
        self.chat_users = account[1]
        self.chats = account[2]

    def run(self):
        session = vk_api.VkApi(token=self.token, api_version='5.92')
        api = session.get_api()
        me = api.users.get()[0]
        while 1:
            long_pooll = VkLongPoll(session)
            try:
                for i in long_pooll.listen():
                    if self.paused:
                        continue
                    if i.type == VkEventType.MESSAGE_NEW:
                        msg = api.messages.getById(message_ids=(i.message_id))['items'][0]
                        if msg['out']:
                            continue
                        if 'chat_id' in msg.keys():
                            if msg['chat_id'] in self.chats:
                                content = ParseChat(msg, me, api)
                                for i in content:
                                    bot_send(i)
                        elif msg['from_id'] in self.chat_users:
                            content = ParsePriv(msg, me, api)
                            for i in content:
                                    bot_send(i)

            except Exception as exep:
                bot_send('Ohhh... there are some errors: '+str(exep))

    def stop(self):
        self.paused = True

    def resume(self):
        self.paused = False

@bot.message_handler(commands=['start'])
def handle_start(message):
    for i in threads:
        i.resume()
    for i in send_ids:
        bot.send_message(i, 'Bot have resumed')

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    for i in threads:
        i.stop()
    for i in send_ids:
        bot.send_message(i, 'Bot have stoped')
@bot.message_handler(commands=['kill'])
def kill(message):
    for i in send_ids:
        bot.send_message(i, 'Bot have been killed')
    *proc, = os.popen('ps axu | grep resender')
    pid = proc[0].split()[1]
    os.system('kill '+pid)

accounts = [i.strip("[]' ") for i in config.get('General', 'vk_users').split(',')]
check_configs = []
for name in accounts:
    check_configs.append([config.get(name, 'token'), [int(i.strip("[] '")) for i in config.get(name, 'chat_users').split(',')], [int(i.strip("[] '")) for i in config.get(name, 'chats').split(',')]])

global threads
threads = []
for i in check_configs:
    threads.append(LongPool(i))
    threads[-1].start()

while 1:
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        exit()
    except Exception as exep:
        bot_send('Ohhh... there are some errors: '+str(exep))

'''
{'audio_message': {'waveform': [13, 11, 10, 9, 17, 11, 12, 11, 9, 13, 10, 9, 9, 10, 12, 11, 11, 15, 14, 22, 20, 18, 16, 15, 11, 12, 11, 9, 15, 13, 8, 7, 6, 6, 6, 7, 9, 7, 12, 12, 18, 31, 26, 
19, 16, 10, 14, 11, 9, 14, 24, 21, 20, 22, 17, 13, 12, 7, 11, 14, 8, 9, 6, 18, 22, 20, 17, 20, 22, 13, 16, 8, 14, 9, 8, 9, 9, 12, 13, 11, 15, 17, 14], 'access_key': '90a1ffae6d3f54dcf8', 'ow$
er_id': 164572412, 'link_ogg': 'https://psv4.userapi.com/c853024//u164572412/audiomsg/d5/61b129a1a8.ogg', 'id': 485327287, 'link_mp3': 'https://psv4.userapi.com/c853024//u164572412/audiomsg/$
5/61b129a1a8.mp3', 'duration': 4}, 'type': 'audio_message'}
'''