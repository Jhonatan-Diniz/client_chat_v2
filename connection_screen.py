from textual.app import App 
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from pathlib import Path
from file_picker import ImagePickerScreen
from chat_screen import *
import utils


class ConnectionScreen(Screen):
    CSS = """
    #connection_box {
        width: 50;
        height: auto;
        border: solid green;
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
                    Label("Conectar ao servidor", id="titulo"),
                    Input(value="127.0.0.1", placeholder="IP do servidor", id="host"),
                    Input(value="9000", placeholder="Porta", id="port"),
                    Button("Conectar", id="conectar", variant="primary"),
                    id="connection_box"
                )
            )
        )

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "conectar":
            self.conectar()

    def on_input_submitted(self, event: Input.Submitted):
        self.conectar()

    def conectar(self):
        host = self.query_one("#host", Input).value.strip()
        port_text = self.query_one("#port", Input).value.strip()

        if not host or not port_text:
            self.notify("Informe IP e porta.", severity="error")
            return

        try:
            port = int(port_text)
        except ValueError:
            self.notify("A porta precisa ser um número.", severity="error")
            return

        try:
            utils.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            utils.soc.connect((host, port))

        except OSError as e:
            self.notify(f"Erro ao conectar: {e}", severity="error")
            utils.soc = None
            return

        self.notify("Conectado ao servidor.")
        self.app.switch_screen("login")
