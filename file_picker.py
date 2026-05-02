from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Static, Input, Label, Button
from textual.reactive import reactive
from textual.screen import Screen
from textual.containers import Horizontal, Vertical, Center, Middle
from pathlib import Path

class ImagePickerScreen(Screen):
    CSS = """
    #file-list {
        height: 1fr;
        border: solid blue;
    }

    #current-path {
        height: 3;
        border: solid green;
        padding: 1;
    }
    """

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def __init__(self, start_path="."):
        super().__init__()
        self.current_path = Path(start_path).resolve()

    def compose(self):
        self.path_label = Static(id="current-path")
        self.file_list = ListView(id="file-list")

        yield Header()
        yield Vertical(
            self.path_label,
            self.file_list,
        )
        yield Footer()

    def on_mount(self):
        self.load_directory()

    def load_directory(self):
        self.file_list.clear()
        self.path_label.update(f"Diretório atual: {self.current_path}")

        if self.current_path.parent != self.current_path:
            item = ListItem(Static(".."))
            item.path = self.current_path.parent
            item.is_back = True
            self.file_list.append(item)

        items = sorted(
            self.current_path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        )

        for path in items:
            if path.is_dir():
                label = f"📁 {path.name}"
                item = ListItem(Static(label))
                item.path = path
                item.is_back = False
                self.file_list.append(item)

            elif path.suffix.lower() in self.IMAGE_EXTENSIONS:
                label = f"🖼️ {path.name}"
                item = ListItem(Static(label))
                item.path = path
                item.is_back = False
                self.file_list.append(item)

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item

        if getattr(item, "is_back", False):
            self.current_path = self.current_path.parent
            self.load_directory()
            return

        path = getattr(item, "path", None)

        if path is None:
            return

        if path.is_dir():
            self.current_path = path
            self.load_directory()
            return

        if path.is_file():
            self.dismiss(str(path))
