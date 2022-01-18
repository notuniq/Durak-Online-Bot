import socket
import config
import hashlib
from datetime import datetime
from loguru import logger
import base64
from faker import Faker
from python_rucaptcha import ImageCaptcha
import requests
import utils
import random
import sys
from termcolor import colored

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkApi, longpoll
from vk_api.utils import get_random_id


vk_session = VkApi(token = config.VKTOKEN)
longpoll = VkLongPoll(vk_session)
vks = vk_session
vk = vk_session.get_api()
print("LOGS: [INFO] VK Announce Start!")

logger.remove()
logger.add(sys.stderr, format="LOGS: {message}", level=config.level)

servers = utils.getServers()

class DurakClient:
    def __init__(self, _type):
        self.faker = Faker()
        self._type = _type


    def connect(self, server):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(server)


    def getSessionKey(self):
        currTime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"
        self.sock.sendall(utils.marshal(
            {
                "tz": "+02:00",
                "t": currTime,
                "p": 10,
                "pl": "iphone",
                "l": "ru",
                "d": "iPhone10,4",
                "ios": "14.4",
                "v": "1.9.1.2",
                "n": "durak.ios",
                "command": "c"
            }
        ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        key = utils.unMarshal(data)[0]["key"]
        return key
    

    def verifySession(self, key):
        verifData = base64.b64encode(hashlib.md5((key+config.SIGN_KEY).encode()).digest()).decode()
        self.sock.sendall(
            utils.marshal(
                {
                    "hash": verifData,
                    "command": "sign"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        logger.info(f"[{self._type.upper()}] Сессия работает")
    
    @logger.catch
    def register(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command":"get_captcha"
                }
            ).encode()
        )
        data1 = utils.unMarshal(self.sock.recv(4096).decode())
        logger.debug(data1)
        data2 = utils.unMarshal(self.sock.recv(4096).decode())
        logger.debug(data2)
        captcha = ""
        url = data1[0].get("url") or data2[0].get("url")
        if url:
            logger.info(f"[{self._type.upper()}] Solving captcha...")
            if config.HUMAN_CAPTCHA_SOLVE:
                vk.messages.send(user_id=config.VK_USER_ID, message=f"Пройдите капчу! {url}", random_id=get_random_id())
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.text.lower()[:8] == "!captcha":
                        captcha = event.text.lower()[8:].split()[0]
                        break
                # vk.messages.send(user_id=config.VK_USER_ID, message='Успешно!', random_id=get_random_id())
            else:
                answer = ImageCaptcha.ImageCaptcha(service_type="rucaptcha", rucaptcha_key=config.RUCAPTCHA_KEY).captcha_handler(captcha_link=url)
                captcha = answer.get("captchaSolve")
                captchaId = answer.get("taskId")

        name = self.faker.first_name()
        self.sock.sendall(
            utils.marshal(
                {
                    "name": name,
                    "captcha": captcha,
                    "command": "register"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        if captcha:
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        data = utils.unMarshal(data)
        if data[0].get("command") == "set_token":
            token = data[0]["token"]
            logger.info(f"[{self._type.upper()}] Зарегистрирован аккаунт: {name}")
            return token
        if not config.HUMAN_CAPTCHA_SOLVE:
            r = requests.get("http://rucaptcha.com/res.php", params={
                "key":config.RUCAPTCHA_KEY,
                "action":"reportbad",
                "id":captchaId,
                })
        logger.info(f"[{self._type.upper()}] Вы не смогли решить капчу :(")
        vk.messages.send(user_id=config.VK_USER_ID, message=f"[{self._type.upper()}] Вы не смогли решить капчу :(", random_id=get_random_id())
        return ""
    

    def auth(self, token):
        self.sock.sendall(
            utils.marshal(
                {
                    "token": token,
                    "command": "auth"
                }
            ).encode()
        )
        for _ in range(3):
            data = self.sock.recv(4096)
            try:
                logger.debug(data.decode())
            except UnicodeDecodeError:
                logger.debug(data)
        logger.info(f"[{self._type.upper()}] Авторизация прошла успешно")
    

    def createGame(self) -> int:
        pwd = str(random.randint(1000, 9999))
        self.sock.sendall(
            utils.marshal(
                {
                    "sw": False,
                    "bet": config.bet1,
                    "deck": 24,
                    "password": pwd,
                    "players": 2,
                    "fast": False,
                    "ch": False,
                    "nb": True,
                    "command": "create"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Игра была создана")
        return pwd
        


    def sendFriendRequest(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "name": config.NAME,
                    "command": "users_find"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)

        self.sock.sendall(
            utils.marshal(
                {
                    "id": config.USER_ID,
                    "command": "friend_request"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.info(f"[{self._type.upper()}] Запрос дружбы отправлен")
        logger.debug(data)

    
    def inviteToGame(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "user_id": config.USER_ID,
                    "command": "invite_to_game"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        logger.info(f"[{self._type.upper()}] Пригласил в игру")
    

    def ready(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "ready"
                }
            ).encode()
        )
        '''for _ in range(2):
            data = self.sock.recv(4096).decode()
            messages = utils.unMarshal(data)
            logger.debug(messages)'''
        logger.info(f"[{self._type.upper()}] Нажал Готов")
    

    def exit(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "surrender"
                }
            ).encode()
        )
        data = self.sock.recv(4096).decode()
        logger.debug(data)
        logger.info(f"[{self._type.upper()}] Игра оконченна")
    

    def getMessagesUpdate(self):
        try:
            messages = utils.unMarshal(self.sock.recv(1024).decode())
            logger.debug(messages)
            for message in messages:
                if message.get("user"):
                    _id = message["user"]["id"]
                    return _id
        except UnicodeDecodeError:
            print(colored('LOGS: [ВАЖНО] Не смог обновить данные. (не обращайте внимания)', 'red'))

        return ""
    

    def acceptFriendRequest(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "friend_accept"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Принял в друзья")
    

    def getInvites(self):
        data = utils.unMarshal(self.sock.recv(4096).decode())
        logger.debug(data)
        if data[0].get("command") == "invite_to_game":
            gameId = data[0]["game_id"]
            return gameId
        return ""
    


    def join(self, _id, pwd):
        self.sock.sendall(
            utils.marshal(
                {
                    "password": pwd,
                    "id": _id,
                    "command": "join"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Вошел в игру")
        
        
    def leave(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "leave"
                }
            ).encode()
        )
        for _ in range(3):
            data = utils.unMarshal(self.sock.recv(4096).decode())
            logger.debug(data)
            for i in data:
                if isinstance(i, dict): 
                    if i.get("k") == "points":
                        points = i["v"]
        logger.info(f"[{self._type.upper()}] ДЕНЕГ: {points}")
        
    def deleteFriend(self, _id):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id,
                    "command": "friend_delete"
                }
            ).encode()
        )
        for _ in range(3):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Друг был удалён")
        
    def waitingFor(self):
        while True:
            messages = utils.unMarshal(self.sock.recv(4096).decode())
            logger.debug(messages)
            for message in messages:
                if message.get("command") == "hand":
                    self.cards: list = message["cards"]
                elif message.get("command") == "turn":
                    self.trump = message["trump"]
                elif message.get("command") in ("mode", "end_turn", "t"):
                    return
    
    

    def _pass(self):
        self.sock.sendall(
            utils.marshal(
                {
                    "command": "pass"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Пас")
        
        #=============================================[2]===============================================================#
    def join2(self, _id3, pwd):
        self.sock.sendall(
            utils.marshal(
                {
                    "password": pwd,
                    "id": _id3,
                    "command": "join"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Вошел в игру")        


        
    def leave2(self, _id3):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id3,
                    "command": "leave"
                }
            ).encode()
        )
        for _ in range(3):
            data = utils.unMarshal(self.sock.recv(4096).decode())
            logger.debug(data)
            for i in data:
                if isinstance(i, dict): 
                    if i.get("k") == "points":
                        points = i["v"]
        logger.info(f"[{self._type.upper()}] ДЕНЕГ: {points}")
    


    
    def deleteFriend2(self, _id2):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id2,
                    "command": "friend_delete"
                }
            ).encode()
        )
        for _ in range(3):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Друг был удалён")
        
    def createGame2(self) -> int:
        pwd = str(random.randint(1000, 9999))
        self.sock.sendall(
            utils.marshal(
                {
                    "sw": False,
                    "bet": config.bet2,
                    "deck": 24,
                    "password": pwd,
                    "players": 2,
                    "fast": False,
                    "ch": False,
                    "nb": True,
                    "command": "create"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Доп. игра была создана")
        return pwd
        
        #=============================================[3]===============================================================#
        
    def join3(self, _id5, pwd):
        self.sock.sendall(
            utils.marshal(
                {
                    "password": pwd,
                    "id": _id5,
                    "command": "join"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Вошел в игру")        


        
    def leave3(self, _id5):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id5,
                    "command": "leave"
                }
            ).encode()
        )
        for _ in range(3):
            data = utils.unMarshal(self.sock.recv(4096).decode())
            logger.debug(data)
            for i in data:
                if isinstance(i, dict): 
                    if i.get("k") == "points":
                        points = i["v"]
        logger.info(f"[{self._type.upper()}] ДЕНЕГ: {points}")
    


    
    def deleteFriend3(self, _id4):
        self.sock.sendall(
            utils.marshal(
                {
                    "id": _id4,
                    "command": "friend_delete"
                }
            ).encode()
        )
        for _ in range(3):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Друг был удалён")
        
    def createGame3(self) -> int:
        pwd = str(random.randint(1000, 9999))
        self.sock.sendall(
            utils.marshal(
                {
                    "sw": False,
                    "bet": config.bet3,
                    "deck": 24,
                    "password": pwd,
                    "players": 2,
                    "fast": False,
                    "ch": False,
                    "nb": True,
                    "command": "create"
                }
            ).encode()
        )
        for _ in range(2):
            data = self.sock.recv(4096).decode()
            logger.debug(data)
        logger.info(f"[{self._type.upper()}] Доп. игра была создана")
        return pwd
    




