from textual import Logger
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from pathlib import Path
from file_picker import ImagePickerScreen
import utils
from utils import save_img, save_msg, receive_data, carregar_chat
import threading
import socket
import os
import logging

class ChatScreen(Screen):
    def compose(self):
        contats = utils.carregar_contatos()
        self.contatos = [c for c in contats if c["id_contato"] != utils.meu_id]

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
        os.makedirs(utils.CHAT_FOLDER, exist_ok=True)

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
            "sender": utils.meu_id,
            "receiver": contato_id,
            "content": [".txt", texto]
        }

        save_msg(utils.meu_id, contato_id, nova_msg)
        self.send_msg(nova_msg)
        self.input_msg.value = ""
        self.chat_view.atualizar_chat()

    def recv_msg(self):
        while True:
            soc = utils.soc
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
                    "receiver": utils.meu_id,
                    "content": ['.txt', msg.decode('utf-8')]
                }
                save_msg(utils.meu_id, msg_sender_id, data)
                self.app.call_from_thread(self.chat_view.atualizar_chat)
                continue

            img_path = save_img(msg_sender_id, msg)
            data = {
                    "sender": msg_sender_id,
                    "receiver": utils.meu_id,
                    "content": ['.jpg', img_path]
            }

            save_msg(utils.meu_id, msg_sender_id, data)
            self.app.call_from_thread(self.chat_view.atualizar_chat) 

    def send_msg(self, msg : dict):
        msg_encoded : bytes = msg["content"][1].encode("utf-8")
        if utils.soc is None:
            self.notify("Você precisa estar conectado para enviar uma mensagem")
            self.switch_screen("connection")
            return
        utils.soc.sendall(b"T" + msg["receiver"].to_bytes(1, "big") + len(msg_encoded).to_bytes(8, "big") + msg_encoded)

    def send_img(self, img_path):
        id_receiver = self.chat_view.contato_id
        if id_receiver is None:
            self.notify("Selecione um contato primeiro!")
            return
        img_data = b""
        try:
            with open(img_path, "rb") as file:
                img_data = file.read()
            if utils.soc is None:
                self.notify("Você precisa estar conectado para enviar uma imagem")
                self.switch_screen("connection")
                return
            utils.soc.sendall(
                b"I" + id_receiver.to_bytes(1, "big") +
                len(img_data).to_bytes(8, "big") +
                img_data
            )
            data = {
                "sender":utils.meu_id,
                "receiver": id_receiver,
                "content":[".jpg", img_path]
            }
            save_msg(utils.meu_id, id_receiver, data)
            self.chat_view.atualizar_chat()

        except Exception as e:
            self.notify("ERROR AO ENVIAR A IMAGEM", severity="error")


class ChatView(Static):
    contato_id = reactive(None)

    def atualizar_chat(self):
        if self.contato_id is None:
            self.update("Selecione um contato")
            return

        mensagens = carregar_chat(utils.meu_id, self.contato_id)

        linhas = []

        for msg in mensagens:
            sender = msg["sender"]
            ext, content = msg["content"]

            if ext == ".txt":
                texto = content
            else:
                texto = f"[Imagem: {content}]"

            prefixo = "Você" if sender == utils.meu_id else msg["sender"]
            linhas.append(f"{prefixo}: {texto}")

        self.update("\n".join(linhas))

class ContatoItem(ListItem):
    def __init__(self, contato):
        super().__init__(Static(contato["nome"]))
        self.contato = contato
