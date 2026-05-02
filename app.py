from textual import Logger
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from pathlib import Path
import threading
import socket
import json
import os
import logging

from file_picker import ImagePickerScreen

logger = logging.getLogger("chat_app")

logging.basicConfig(
    filename="chat.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

meu_id = None
meu_nome = ""
HOST = "localhost"
PORT = 9000
CHAT_FOLDER = "chats"
CONTATOS_FILE = "contatos.json"

def carregar_contatos():
    with open(CONTATOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def carregar_chat(meu_id, contato_id):
    nome_arquivo = f"{meu_id}_{contato_id}.json"
    caminho = os.path.join(CHAT_FOLDER, nome_arquivo)

    if not os.path.exists(caminho):
        with open(caminho, "w") as f:
            json.dump([], f, indent=4)
        return []

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def save_msg(id, data):
    path = f"chats/{meu_id}_{id}.json"
    mensagens = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            mensagens = json.load(f)
    mensagens.append(data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(mensagens, f, indent=4, ensure_ascii=False)

def save_img(id, img_data) -> str:
    path_images = Path("images")
    path_images.mkdir(exist_ok=True)

    file_number = len(list(path_images.glob("*.jpg")))
    file_name = f"images/chat_file_{file_number+1}.jpg"
    file = Path(file_name)
    file.write_bytes(img_data)
    return file_name


def receive_data(soc, size):
    data = b""
    while len(data) < size:
        pack = soc.recv(size-len(data))
        if (not pack):
            return None
        data += pack
    return data


class LoginScreen(Screen):
    CSS = """
    #login_box {
        width: 50;
        height: auto;
        border: solid blue;
        padding: 1 2;
    }

    #titulo {
        text-align: center;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    Button {
        width: 100%;
    }
    """

    def compose(self):
        yield Header()

        yield Center(
            Middle(
                Vertical(
                    Label("Login do Chat", id="titulo"),
                    Input(placeholder="Nome do usuário", id="nome"),
                    Input(placeholder="Senha", password=True, id="senha"),
                    Button("Entrar", id="entrar", variant="primary"),
                    id="login_box"
                )
            )
        )

        yield Footer()
    def on_mount(self):
        self.login_andamento = False

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "entrar":
            self.fazer_login()

    def on_input_submitted(self, event: Input.Submitted):
        self.fazer_login()

    def fazer_login(self):
        if self.login_andamento:
            return
        self.login_andamento = True
        botao = self.query_one("#entrar", Button)
        botao.disabled = True

        try:
            nome = self.query_one("#nome", Input).value.strip()
            senha = self.query_one("#senha", Input).value.strip()
    
            nome_b = nome.encode("utf-8")
            senha_b = senha.encode("utf-8")
    
            soc.sendall(
                len(nome_b).to_bytes(8, "big") +
                nome_b +
                len(senha_b).to_bytes(8, "big") +
                senha_b
            )
    
            time_exist : bytes | None = receive_data(soc, 1)
            if time_exist == b"F" or not time_exist: 
                self.notify("Usuário ou senha inválidos.", severity="error")
                return
            if time_exist == b"A":
                self.notify("Usuário já está logado!")
                return
            id : bytes | None = receive_data(soc, 1) 
            if id is None: return
            global meu_id, meu_nome
            meu_id = int.from_bytes(id, "big")
            meu_nome = nome
            self.app.switch_screen("chat")
        finally:
            self.login_andamento = False
            botao.disabled = False


class ContatoItem(ListItem):
    def __init__(self, contato):
        super().__init__(Static(contato["nome"]))
        self.contato = contato


class ChatView(Static):
    contato_id = reactive(None)

    def atualizar_chat(self):
        if self.contato_id is None:
            self.update("Selecione um contato")
            return

        mensagens = carregar_chat(meu_id, self.contato_id)

        linhas = []

        for msg in mensagens:
            sender = msg["sender"]
            ext, content = msg["content"]

            if ext == ".txt":
                texto = content
            else:
                texto = f"[Imagem: {content}]"

            prefixo = "Você" if sender == meu_id else "Outro"
            linhas.append(f"{prefixo}: {texto}")

        self.update("\n".join(linhas))


class ChatScreen(Screen):
    def compose(self):
        contats = carregar_contatos()
        self.contatos = [c for c in contats if c["id_contato"] != meu_id]

        self.lista_contatos = ListView(id="contatos")
        self.chat_view = ChatView(id="chat")
        self.input_msg = Input(
            placeholder="Digite sua mensagem e pressione Enter...",
            id="input"
        )

        yield Header()
        yield Horizontal(
            self.lista_contatos,
            self.chat_view,
            id="main"
        )
        yield self.input_msg
        yield Footer()

    def on_mount(self):
        os.makedirs(CHAT_FOLDER, exist_ok=True)

        for c in self.contatos:
            self.lista_contatos.append(ContatoItem(c))

        self.recv_thread = threading.Thread(
            target=self.recv_msg,
            args=(),
            daemon=False
        )

        self.recv_thread.start()

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        contato_id = item.contato["id_contato"]

        self.chat_view.contato_id = contato_id
        self.chat_view.atualizar_chat()

    def on_input_submitted(self, event: Input.Submitted):
        texto = event.value.strip()

        if not texto:
            return

        if texto == "/img":
            self.app.push_screen(
                ImagePickerScreen(),
                callback=self.send_img
            )
            self.input_msg.value = ""
            return

        if self.chat_view.contato_id is None:
            self.notify("Selecione um contato antes de enviar.")
            return

        contato_id = self.chat_view.contato_id

        nova_msg = {
            "sender": meu_id,
            "receiver": contato_id,
            "content": [".txt", texto]
        }

        save_msg(contato_id, nova_msg)
        self.send_msg(nova_msg)
        self.input_msg.value = ""
        self.chat_view.atualizar_chat()

    def recv_msg(self):
        while True:
            msg_type : bytes | None = receive_data(soc, 1)
            if msg_type is None:break
            msg_sender : bytes | None = receive_data(soc, 1)
            if msg_sender is None: break
            msg_sender_id : int = int.from_bytes(msg_sender, "big")
            msg_size : bytes | None= receive_data(soc, 8)
            if msg_size is None:break
            size = int.from_bytes(msg_size, "big")
            msg : bytes | None = receive_data(soc, size)
            if (msg is None):break

            if msg_type == b"T":
                data = {
                    "sender": msg_sender_id,
                    "receiver": meu_id,
                    "content": ['.txt', msg.decode('utf-8')]
                }
                save_msg(msg_sender_id, data)
                self.app.call_from_thread(self.chat_view.atualizar_chat)
                continue

            logger.info(f"imagem e tal: {msg_type}")
            img_path = save_img(msg_sender_id, msg)
            data = {
                    "sender": msg_sender_id,
                    "receiver": meu_id,
                    "content": ['.jpg', img_path]
            }

            save_msg(msg_sender_id, data)
            self.app.call_from_thread(self.chat_view.atualizar_chat) 

    def send_msg(self, msg : dict):
        msg_encoded : bytes = msg["content"][1].encode("utf-8")
        soc.sendall(b"T" + msg["receiver"].to_bytes(1, "big") + len(msg_encoded).to_bytes(8, "big") + msg_encoded)

    def send_img(self, img_path):
        id_receiver = self.chat_view.contato_id
        if id_receiver is None:
            self.notify("Selecione um contato primeiro!")
            return
        img_data = b""
        try:
            with open(img_path, "rb") as file:
                img_data = file.read()
            logger.info("ENVIANDO IMAGEM")
            soc.sendall(
                b"I" + id_receiver.to_bytes(1, "big") +
                len(img_data).to_bytes(8, "big") +
                img_data
            )
            data = {
                "sender":meu_id,
                "receiver": id_receiver,
                "content":[".jpg", img_path]
            }
            save_msg(id_receiver, data)
            self.chat_view.atualizar_chat()

        except Exception as e:
            logger.debug(f"ERRO {e}")
            self.notify("ERROR AO ENVIAR A IMAGEM", severity="error")


class ChatApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
        layout: horizontal;
    }

    #contatos {
        width: 30%;
        border: solid green;
    }

    #chat {
        width: 70%;
        border: solid blue;
    }

    #input {
        height: 3;
        border: solid yellow;
    }
    """

    SCREENS = {
        "login": LoginScreen,
        "chat": ChatScreen,
        "image_picker": ImagePickerScreen
    }

    def __init__(self):
        super().__init__()
        self.theme = "ansi-dark"

    def on_mount(self):
        self.push_screen("login")


if __name__ == "__main__":
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect((HOST, PORT))
    ChatApp().run()
