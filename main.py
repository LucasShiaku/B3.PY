import datetime
import json
import os
from collections import defaultdict
from enum import Enum

from prettytable.prettytable import PrettyTable

DATABASE_FILE = "db.data"


class MainMenuOption(Enum):
    EXIT = 0
    USER_LOGIN = 1
    USER_SIGNUP = 2


main_menu = """
Digite a opção desejada:
0 - Sair
1 - Fazer login
2 - Cadastre-se 
"""


class UserMenuOption(Enum):
    LOGOUT = 0
    CREATE_ROUTE = 1
    LIST_ROUTES = 2
    VIEW_MESSAGES = 3


user_menu = """
Digite a opção desejada:
0 - Logout
1 - Cadastrar rota
2 - Visualizar rotas
3 - Mensagens
"""


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


class DatetimeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            if key in {"time"}:
                ret[key] = datetime.datetime.fromisoformat(value)
            else:
                ret[key] = value
        return ret


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def wait_key_to_continue():
    input("Pressione Enter para continuar")


def get_input(msg, cast=None, default=None):
    while True:
        try:
            inputed_text = input(msg)
            if inputed_text == "" and default is not None:
                return default
            return cast(inputed_text) if cast is not None else inputed_text
        except (ValueError, KeyboardInterrupt):
            continue


def user_signup():
    clear_console()
    username = get_input("Digite o username: ")
    mail = get_input("Digite o email do usuário: ")
    password = get_input("Digite a senha do usuário: ")

    if db["users"].get(username):
        print(f"Usuário já cadastrado com o username {username}")
    else:
        db["users"][username] = {"mail": mail, "password": password}
        print("Usuário cadastrado com sucesso!")

    wait_key_to_continue()


def user_login():
    clear_console()
    username = get_input("Digite o username: ")
    password = get_input("Digite a senha: ")

    if db["users"].get(username):
        if password == db["users"][username]["password"]:
            return username
        else:
            print("Senha inválida.")
    else:
        print("Usuário usuário não cadastrado.")

    wait_key_to_continue()
    return None


def create_route(user):
    clear_console()
    route_start = get_input("Digite o ponto de partida da rota: ")
    route_end = get_input("Digite o ponto final da rota: ")
    route_type = get_input("Digite se você oferece carona ou quer carona: ")

    route = {
        "start": route_start,
        "end": route_end,
        "user": user,
        "id": len(db["routes"]) + 1,
        "type": route_type
    }
    db["routes"].append(route)
    print("Rota criada com sucesso!")
    wait_key_to_continue()


def list_routes(user):
    clear_console()
    route_table = PrettyTable(("ID", "Usuário", "Inicio", "Fim", "Carona"))

    for route in db["routes"]:
        route_table.add_row((route["id"], route["user"], route["start"], route["end"], route["type"]))

    print("Listando rotas:")
    print(route_table.get_string())

    route_id = get_input(
        "Digite o ID da routa desejada para enviar mensagem ao usuário da rota "
        "(0 para voltar): ",
        int,
    )

    if route_id:
        for r in db["routes"]:
            if route_id == r["id"]:
                route = r
                break
        else:
            route = None

        if route is None:
            print("Rota inválida.")
            wait_key_to_continue()
            return

        msg = get_input(f"Digite a mensagem para o usuário {route['user']}: ")
        db["msgs"].append(
            {
                "from": user,
                "to": route["user"],
                "msg": msg,
                "time": datetime.datetime.now(),
            }
        )
        print("Mensagem enviada com sucesso!")
        wait_key_to_continue()


def view_messages(user):
    user_msgs = list(filter(lambda x: user == x["to"] or user == x["from"], db["msgs"]))
    user_msgs.sort(key=lambda x: x["time"], reverse=True)

    conversations = list()

    for msg in user_msgs:
        if {msg["to"], msg["from"]} not in conversations:
            conversations.append({msg["to"], msg["from"]})

    conversations_msg = defaultdict(list)

    chats = PrettyTable(("ID", "Convesando com", "Última mensagem"))

    for conversation in conversations:
        for msg in user_msgs:
            if {msg["to"], msg["from"]} == conversation:
                conversations_msg[tuple(conversation)].append(msg)
        conversation = tuple(conversation)
        conversations_msg[conversation].sort(key=lambda x: x["time"])

        chats.add_row(
            (
                len(chats.rows) + 1,
                conversation[0] if conversation[0] != user else conversation[1],
                conversations_msg[conversation][-1]["time"].strftime("%H:%M %d/%m/%Y"),
            )
        )

    print("Listando conversas:")
    print(chats.get_string())

    chat_id = get_input("Digite o ID da conversa que seja visualizar: ", int)

    if chat_id:
        if chat_id > len(chats.rows):
            print("Convesa inválida.")
            wait_key_to_continue()
            return

        user_chat = chats.rows[chat_id - 1][1]

        chat_msgs = conversations_msg[tuple({user, user_chat})]

        clear_console()
        print(f"Conversa com {user_chat}")
        for msg in chat_msgs:
            print(
                f"{msg['from']} ({msg['time'].strftime('%H:%M %d/%m/%Y')}): {msg['msg']}"
            )
        resp = get_input("Deseja responder (s/n)?")

        if resp == "s":
            response = get_input("Digite a resposta: ")

            db["msgs"].append(
                {
                    "from": user,
                    "to": user_chat,
                    "msg": response,
                    "time": datetime.datetime.now(),
                }
            )
            print("Mensagem enviada com sucesso!")
            wait_key_to_continue()


def user_menu_loop(user):
    while True:
        clear_console()
        op = UserMenuOption(get_input(user_menu, int))

        match op:
            case UserMenuOption.LOGOUT:
                break
            case UserMenuOption.CREATE_ROUTE:
                create_route(user)
            case UserMenuOption.LIST_ROUTES:
                list_routes(user)
            case UserMenuOption.VIEW_MESSAGES:
                view_messages(user)


def main_menu_loop():
    while True:
        clear_console()
        op = MainMenuOption(get_input(main_menu, int))

        match op:
            case MainMenuOption.EXIT:
                break
            case MainMenuOption.USER_LOGIN:
                user = user_login()
                if user is not None:
                    user_menu_loop(user)
            case MainMenuOption.USER_SIGNUP:
                user_signup()


if __name__ == "__main__":
    if os.path.isfile(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            db = json.loads(f.read(), cls=DatetimeDecoder)
    else:
        db = dict()
        db["users"] = dict()
        db["msgs"] = list()
        db["routes"] = list()

    try:
        main_menu_loop()
    finally:
        with open(DATABASE_FILE, "w") as f:
            f.write(json.dumps(db, cls=DatetimeEncoder))
