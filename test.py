import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
import time
import random

def main():

    vk_session = vk_api.VkApi(login='jenya.sido@gmail.com', password='Htyfnf', app_id='2685278')
    print("BOT STARTED!")    
    vk_session.auth(token_only=True)
    longpoll = VkLongPoll(vk_session)
    vks = vk_session
    print("Ботик запущен")
    def send(peer_id, message):
        m = vks.method("messages.send", {"peer_id": peer_id, "random_id": 0, "message": message})
        return m
    
    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.text.lower():
                send(event.peer_id, "1. !photo {кол-во} {альбом}\n2. !music {кол-во} - загрузка музыки\n3. !video {кол-во} {альбом} {ссылка} - загрузка видео")
                print(event.text.lower())
                
        except Exception as s:
            print(f"Error: {s}")
   

while True:
    main()