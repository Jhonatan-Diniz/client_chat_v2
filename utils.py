from pathlib import Path
import json
import os
import logging
import socket

soc : socket.socket | None = None

CHAT_FOLDER = "chats"

logger = logging.getLogger("chat_app")

logging.basicConfig(
    filename="chat.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

meu_id = None
meu_nome = ""
CHAT_FOLDER = "chats"
CONTATOS_FILE = "contatos.json"


def carregar_contatos():
    with open("contatos.json", "r", encoding="utf-8") as f:
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


def save_msg(meu_id, id, data):
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
