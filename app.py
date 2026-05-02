from textual.app import App 
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from pathlib import Path
from file_picker import ImagePickerScreen
from chat_screen import ChatScreen
from login_screen import LoginScreen
from connection_screen import ConnectionScreen
import utils
import socket


class ChatApp(App):
    BINDINGS = [
        ("q", "quit", "Sair"),
        ("ctrl+c", "quit", "Sair"),
    ]
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
        "connection": ConnectionScreen,
        "login": LoginScreen,
        "chat": ChatScreen,
        "image_picker": ImagePickerScreen
    }

    def __init__(self):
        super().__init__()
        self.theme = "ansi-dark"

    def on_mount(self):
        self.push_screen("connection")

    def on_unmount(self):
        if utils.soc is not None:
            try:
                utils.soc.shutdown(socket.SHUT_RDWR)
            except:
                pass
    
            utils.soc.close()
            utils.soc = None

    def action_quit(self):

        if utils.soc is not None:
            try:
                utils.soc.shutdown(socket.SHUT_RDWR)
            except:
                pass

            utils.soc.close()
            utils.soc = None

        self.exit()

if __name__ == "__main__":
    ChatApp().run()
