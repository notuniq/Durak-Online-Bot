import api
import config
from api import logger
import time
import random
from api import servers
from colorama import init
init()


@logger.catch
def start():
    main = api.DurakClient(_type="main")
    
    for _ in range(100):
        server = random.choice(servers)
        logger.info(f"[INFO] Присоеденился к {server[0]+':'+str(server[1])}")
        main.connect(server)
        key2 = main.getSessionKey()
        main.verifySession(key2)
        main.auth(config.TOKEN)

        bot = api.DurakClient(_type="bot")
        bot.connect(server)
        key = bot.getSessionKey()
        bot.verifySession(key)
        token = ""
        while not token:
            try:
                token = bot.register()
            except:
                continue
        bot.auth(token)
        bot.sendFriendRequest()
        _id1 = ""
        while not _id1:
            _id1 = main.getMessagesUpdate()
        main.acceptFriendRequest(_id1)
        pwd = bot.createGame()
        bot.inviteToGame()
        _id = ""
        while not _id:
            _id = main.getInvites()
        main.join(_id, pwd)
        bot.ready()
        main.ready()
        bot.waitingFor()
        main.waitingFor()
        time.sleep(0.3)
        bot.leave(_id)
        time.sleep(0.4)
        main.leave(_id)
        main.deleteFriend(_id1)
        
        bot.sendFriendRequest()
        _id2 = ""
        while not _id2:
            _id2 = main.getMessagesUpdate()
        time.sleep(1.5)
        main.acceptFriendRequest(_id2)
        time.sleep(1.5)
        pwd = bot.createGame2()
        bot.inviteToGame()
        _id3 = ""
        while not _id3:
            _id3 = main.getInvites()
        main.join2(_id3, pwd)
        bot.ready()
        main.ready()
        bot.waitingFor()
        main.waitingFor()
        time.sleep(0.3)
        bot.leave2(_id3)
        time.sleep(0.4)
        main.leave2(_id3)
        main.deleteFriend2(_id2)
        bot.exit()
        time.sleep(1)
        
        bot.sendFriendRequest()
        _id4 = ""
        while not _id4:
            _id4 = main.getMessagesUpdate()
        time.sleep(1.5)
        main.acceptFriendRequest(_id4)
        time.sleep(1.5)
        pwd = bot.createGame3()
        bot.inviteToGame()
        _id5 = ""
        while not _id5:
            _id5 = main.getInvites()
        main.join3(_id5, pwd)
        bot.ready()
        main.ready()
        bot.waitingFor()
        main.waitingFor()
        time.sleep(0.3)
        bot.leave3(_id5)
        time.sleep(0.4)
        main.leave3(_id5)
        main.deleteFriend3(_id4)
        bot.exit()
        time.sleep(1)
start()