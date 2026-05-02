from textual.app import App 
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from pathlib import Path
from file_picker import ImagePickerScreen
from chat_screen import *
import utils
from utils import save_img, save_msg, receive_data, carregar_chat

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
        if utils.soc is None:
            self.notify("Você ainda não está conectado ao servidor", severity="error")
            self.app.switch_screen("connection")
            return
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
    
            utils.soc.sendall(
                len(nome_b).to_bytes(8, "big") +
                nome_b +
                len(senha_b).to_bytes(8, "big") +
                senha_b
            )
    
            time_exist : bytes | None = receive_data(utils.soc, 1)
            if time_exist == b"F" or not time_exist: 
                self.notify("Usuário ou senha inválidos.", severity="error")
                return
            if time_exist == b"A":
                self.notify("Usuário já está logado!")
                return
            id : bytes | None = receive_data(utils.soc, 1) 
            if id is None: return
            utils.meu_id = int.from_bytes(id, "big")
            utils.meu_nome = nome
            self.app.switch_screen("chat")
        finally:
            self.login_andamento = False
            botao.disabled = False


