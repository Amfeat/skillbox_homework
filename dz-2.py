"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from typing import Optional

online_users = []   # список пользователей онлайн


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None
        self.wrong_count = 2  # счетчик неправильных попыток входа

    def data_received(self, data: bytes):

        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                user_login = decoded.replace("login:", "").replace("\r\n", "")
                if user_login in online_users: # проверка, свободен ли логин
                    print("Attempt to log in as another user ")
                    self.transport.write(
                        f"Логин {user_login} занят, попробуйте другой. осталось {self.wrong_count} попыток".encode()
                    )
                    self.wrong_count -= 1

                    if self.wrong_count < 0:   # отключаем пользователя после трех неудачных попыток зайти

                        self.transport.write("Вы отключены от сервера".encode())

                        self.transport.close()


                else:

                    self.login = user_login
                    online_users.append(user_login)

                    self.send_history()

                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
        else:
            self.send_message(decoded)

    def send_history(self):  # метод отправки истории

        self.transport.write('\n'.join(self.server.history).encode())

    def add_history(self, message):  # метод пополнения истории

        self.server.history.append(message)   # Закидываем сообщение в конец списка

        if len(self.server.history) > 10:  # ограничиваем длину истории
            del self.server.history[0]



    def send_message(self, message):

        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.add_history(format_string)  # сохраняем сообщение в историю


        for client in self.server.clients:

            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")
        print(process.clients)

    def connection_lost(self, exception):

        self.server.clients.remove(self)

        print(f"Соединение с {self.login} разорвано")



class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.history = []   # список истории сообщений сервера

    def create_protocol(self):
        return ClientProtocol(self)



    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")
        print(self.clients)

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
