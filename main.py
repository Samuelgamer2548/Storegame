#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storegame - Ultimate Python GUI v1.21.2
Interface profissional estilo PortMaster para R36S
Autor: SamuelGamer2548 (Protegido)
"""

import os
import sys
import json
import pygame
import random
import subprocess
import threading
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable

# ==================== SEGURANCA ====================
AUTH_HASH = "8a7d5f9e3c2b1a4d6e8f0c9b7a5d3e1f2c4b6a8d0e2f4c6a8b0d2e4f6a8c0b2e4"
if hashlib.sha256(b"SamuelGamer2548").hexdigest() != AUTH_HASH:
    print("ERRO: Assinatura invalida")
    sys.exit(1)

# ==================== CONFIGURACOES ====================
STOREGAME_PATH = os.environ.get('STOREGAME_PATH', '/roms/tools/Storegame')
SOUNDS_PATH = os.environ.get('STOREGAME_SOUNDS', f'{STOREGAME_PATH}/sounds')
CONFIG_PATH = os.environ.get('STOREGAME_CONFIG', f'{STOREGAME_PATH}/config')
CACHE_PATH = os.environ.get('STOREGAME_CACHE', f'{STOREGAME_PATH}/cache')
DATABASE_FILE = f'{STOREGAME_PATH}/database.json'
SCRIPT_DIR = os.environ.get('STOREGAME_SCRIPT_DIR', '/roms/tools')

# Resolucao R36S
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60  # Mais suave

# Cores do tema Ultimate (Azul escuro #000033 + Dourado)
COLORS = {
    "bg_dark": (0, 0, 51),        # #000033
    "bg_card": (20, 20, 80),       # Azul medio
    "bg_highlight": (40, 40, 120),  # Azul claro
    "text_primary": (255, 255, 255), # Branco
    "text_secondary": (200, 200, 200), # Cinza claro
    "gold": (255, 215, 0),          # Dourado
    "gold_dark": (204, 172, 0),     # Dourado escuro
    "border": (255, 255, 255),      # Branco
    "border_selected": (255, 215, 0), # Dourado
    "shadow": (0, 0, 25)            # Sombra
}

# ==================== CLASSE DOWNLOADER ====================
class Downloader:
    """Gerenciador de downloads com Modo Turbo"""
    
    def __init__(self):
        self.download_path = "/roms"
        self.turbo_mode = self._check_aria2()
        self.active = False
        self.progress = 0
        self.status = ""
        self.current_game = ""
    
    def _check_aria2(self) -> bool:
        try:
            subprocess.run(['aria2c', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def list_games(self, url: str) -> List[str]:
        try:
            result = subprocess.run(
                ['curl', '-s', url],
                capture_output=True,
                text=True,
                timeout=15
            )
            import re
            games = re.findall(r'title="([^"]+\.zip)"', result.stdout)
            return sorted(list(set(games)))
        except:
            return []
    
    def start_download(self, game_url: str, game_name: str, system_id: str,
                      callback: Optional[Callable] = None):
        self.active = True
        self.current_game = game_name
        self.progress = 0
        
        def download_thread():
            system_dir = f"{self.download_path}/{system_id}"
            os.makedirs(system_dir, exist_ok=True)
            zip_path = f"{system_dir}/{game_name}"
            
            if callback:
                callback(0, "Iniciando...")
            
            if self.turbo_mode:
                cmd = [
                    'aria2c', '-x', '10', '-s', '10', '-j', '10',
                    '--check-certificate=false',
                    '--console-log-level=error',
                    '--summary-interval=1',
                    '--human-readable=true',
                    '--file-allocation=none',
                    '--allow-overwrite=true',
                    '--auto-file-renaming=false',
                    '--dir', system_dir,
                    '--out', game_name,
                    game_url
                ]
            else:
                cmd = ['curl', '-L', '-o', zip_path, game_url]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
            
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if callback and line:
                    import re
                    percent_match = re.search(r'(\d+)%', line)
                    if percent_match:
                        percent = int(percent_match.group(1))
                        self.progress = percent
                        callback(percent, f"Baixando... {percent}%")
            
            success = process.poll() == 0
            
            if success:
                if callback:
                    callback(95, "Extraindo...")
                subprocess.run(['7z', 'x', zip_path, f"-o{system_dir}", '-mmt=on', '-y'],
                             capture_output=True)
                os.remove(zip_path)
                if callback:
                    callback(100, "Concluido!")
            else:
                if callback:
                    callback(-1, "Falha no download")
            
            self.active = False
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        return thread

# ==================== CLASSE AUDIO MANAGER ====================
class AudioManager:
    def __init__(self, sounds_path: str):
        self.sounds_path = sounds_path
        self.music_files = []
        self.current_track = 0
        self.volume = 0.3
        self.enabled = True
        self._load_music_list()
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._play_current()
        except:
            self.enabled = False
    
    def _load_music_list(self):
        if os.path.exists(self.sounds_path):
            self.music_files = [f for f in os.listdir(self.sounds_path) if f.endswith('.mp3')]
            self.music_files.sort()
    
    def _play_current(self):
        if not self.enabled or not self.music_files:
            return
        music_path = os.path.join(self.sounds_path, self.music_files[self.current_track])
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
        except:
            pass
    
    def next_track(self):
        if self.music_files:
            self.current_track = (self.current_track + 1) % len(self.music_files)
            pygame.mixer.music.stop()
            self._play_current()
    
    def prev_track(self):
        if self.music_files:
            self.current_track = (self.current_track - 1) % len(self.music_files)
            pygame.mixer.music.stop()
            self._play_current()
    
    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

# ==================== CLASSE GUI PRINCIPAL ====================
class StoregameGUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Storegame Ultimate")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.fonts = self._load_fonts()
        
        # Carregar database
        self.systems = self._load_database()
        self.selected_index = 0
        self.menu_stack = ["main"]
        self.current_games = []
        self.game_selected = 0
        self.animation_offset = 0
        self.animation_dir = 1
        
        # Componentes
        self.downloader = Downloader()
        self.audio = AudioManager(SOUNDS_PATH)
        
        # Estado da interface
        self.download_progress = 0
        self.download_status = ""
        self.show_download = False
        
        # Iniciar musica
        self.audio._play_current()
        
        # Criar superficies estaticas
        self._create_static_surfaces()
    
    def _load_fonts(self):
        return {
            'large': pygame.font.Font(None, 48),
            'medium': pygame.font.Font(None, 32),
            'small': pygame.font.Font(None, 24),
            'tiny': pygame.font.Font(None, 18)
        }
    
    def _load_database(self) -> List[Dict]:
        try:
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('systems', [])
        except:
            return self._get_default_systems()
    
    def _get_default_systems(self) -> List[Dict]:
        return [
            {"id": "NES", "name": "Nintendo Entertainment System", "icon": "NES",
             "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20Entertainment%20System%20(Headered)/"},
            {"id": "SNES", "name": "Super Nintendo", "icon": "SNES",
             "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/"},
            {"id": "N64", "name": "Nintendo 64", "icon": "N64",
             "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%2064%20(BigEndian)/"},
            {"id": "PSX", "name": "PlayStation", "icon": "PSX",
             "url": "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/"}
        ]
    
    def _create_static_surfaces(self):
        # Logo principal
        self.logo_surf = self.fonts['large'].render("STOREGAME", True, COLORS["gold"])
        
        # Versao
        self.version_surf = self.fonts['tiny'].render("v1.21.2 Ultimate", True, COLORS["text_secondary"])
        
        # Barra de titulo
        bar_width = SCREEN_WIDTH - 40
        self.title_bar = pygame.Surface((bar_width, 40))
        self.title_bar.fill(COLORS["gold"])
        
        # Barra de rodape
        self.footer_text = self.fonts['tiny'].render("(A) SELECIONAR    (B) VOLTAR    (START) SAIR", 
                                                     True, COLORS["gold"])
    
    def draw_background(self):
        self.screen.fill(COLORS["bg_dark"])
        
        # Efeito de gradiente sutil (linhas horizontais)
        for i in range(0, SCREEN_HEIGHT, 4):
            alpha = 10 + (i * 20 // SCREEN_HEIGHT)
            color = (0, 0, 51 + alpha)
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))
    
    def draw_top_bar(self):
        # Barra superior
        pygame.draw.rect(self.screen, COLORS["gold"], (0, 0, SCREEN_WIDTH, 4))
        pygame.draw.rect(self.screen, COLORS["bg_highlight"], (0, 4, SCREEN_WIDTH, 40))
        
        # Logo
        logo_x = 20
        logo_y = 12
        self.screen.blit(self.logo_surf, (logo_x, logo_y))
        
        # Versao
        self.screen.blit(self.version_surf, (SCREEN_WIDTH - 100, 20))
        
        # Linha dourada inferior
        pygame.draw.line(self.screen, COLORS["gold"], (0, 45), (SCREEN_WIDTH, 45), 2)
    
    def draw_bottom_bar(self):
        # Barra inferior
        pygame.draw.rect(self.screen, COLORS["bg_highlight"], (0, SCREEN_HEIGHT-35, SCREEN_WIDTH, 35))
        
        # Texto de comandos
        footer_x = (SCREEN_WIDTH - self.footer_text.get_width()) // 2
        footer_y = SCREEN_HEIGHT - 25
        self.screen.blit(self.footer_text, (footer_x, footer_y))
        
        # Linha dourada superior
        pygame.draw.line(self.screen, COLORS["gold"], (0, SCREEN_HEIGHT-36), (SCREEN_WIDTH, SCREEN_HEIGHT-36), 2)
    
    def draw_card(self, x: int, y: int, width: int, height: int, 
                  title: str, subtitle: str = "", selected: bool = False):
        """Desenha card com efeito de selecao"""
        
        # Sombra
        shadow_rect = pygame.Rect(x+3, y+3, width, height)
        pygame.draw.rect(self.screen, COLORS["shadow"], shadow_rect, border_radius=8)
        
        # Card principal
        card_rect = pygame.Rect(x, y, width, height)
        if selected:
            bg_color = COLORS["bg_highlight"]
            border_color = COLORS["gold"]
            # Efeito de brilho
            pygame.draw.rect(self.screen, COLORS["gold_dark"], card_rect, 3, border_radius=8)
        else:
            bg_color = COLORS["bg_card"]
            border_color = COLORS["border"]
        
        pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, card_rect, 2, border_radius=8)
        
        # Titulo
        title_surf = self.fonts['small'].render(title, True, COLORS["text_primary"])
        title_rect = title_surf.get_rect(center=(x + width//2, y + height//2 - 10))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitulo (ID)
        if subtitle:
            sub_surf = self.fonts['tiny'].render(subtitle, True, COLORS["text_secondary"])
            sub_rect = sub_surf.get_rect(center=(x + width//2, y + height//2 + 15))
            self.screen.blit(sub_surf, sub_rect)
    
    def draw_main_menu(self):
        self.draw_background()
        self.draw_top_bar()
        self.draw_bottom_bar()
        
        # Grade de sistemas
        card_width = 180
        card_height = 90
        cols = 3
        spacing = 20
        start_x = (SCREEN_WIDTH - (cols * (card_width + spacing))) // 2
        start_y = 80
        
        # Animacao do seletor
        self.animation_offset += self.animation_dir * 0.5
        if self.animation_offset > 5 or self.animation_offset < -5:
            self.animation_dir *= -1
        
        for i, system in enumerate(self.systems):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_width + spacing)
            y = start_y + row * (card_height + spacing)
            
            selected = (i == self.selected_index)
            
            # Efeito de animacao no card selecionado
            if selected:
                x += int(self.animation_offset)
            
            self.draw_card(x, y, card_width, card_height, 
                          system['name'][:18], system['id'], selected)
    
    def draw_game_list(self):
        self.draw_background()
        self.draw_top_bar()
        self.draw_bottom_bar()
        
        system = self.systems[self.selected_index]
        
        # Titulo da tela
        title = f"{system['name']} - Jogos Disponiveis"
        title_surf = self.fonts['medium'].render(title, True, COLORS["gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 60))
        self.screen.blit(title_surf, title_rect)
        
        # Lista de jogos
        if self.current_games:
            start_y = 100
            for i, game in enumerate(self.current_games[:12]):
                y = start_y + i * 28
                
                # Fundo do item
                if i == self.game_selected:
                    pygame.draw.rect(self.screen, COLORS["bg_highlight"], 
                                    (50, y-2, SCREEN_WIDTH-100, 28))
                    
                    # Indicador dourado
                    pygame.draw.rect(self.screen, COLORS["gold"], 
                                    (45, y-2, 3, 28))
                
                # Nome do jogo (truncado)
                display_name = game
                if len(display_name) > 50:
                    display_name = display_name[:47] + "..."
                
                game_surf = self.fonts['small'].render(display_name, True, COLORS["text_primary"])
                self.screen.blit(game_surf, (60, y))
            
            # Indicador de mais jogos
            if len(self.current_games) > 12:
                more_text = f"... e mais {len(self.current_games)-12} jogos"
                more_surf = self.fonts['tiny'].render(more_text, True, COLORS["text_secondary"])
                self.screen.blit(more_surf, (60, start_y + 12*28 + 10))
        else:
            # Loading
            loading = self.fonts['medium'].render("Carregando lista de jogos...", 
                                                 True, COLORS["text_secondary"])
            loading_rect = loading.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(loading, loading_rect)
    
    def draw_download_progress(self):
        if not self.show_download:
            return
        
        # Fundo semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(COLORS["bg_dark"])
        self.screen.blit(overlay, (0, 0))
        
        # Janela de progresso
        window_width = 400
        window_height = 150
        window_x = (SCREEN_WIDTH - window_width) // 2
        window_y = (SCREEN_HEIGHT - window_height) // 2
        
        pygame.draw.rect(self.screen, COLORS["bg_highlight"], 
                        (window_x, window_y, window_width, window_height))
        pygame.draw.rect(self.screen, COLORS["gold"], 
                        (window_x, window_y, window_width, window_height), 3)
        
        # Nome do jogo
        game_name = self.downloader.current_game
        if len(game_name) > 30:
            game_name = game_name[:27] + "..."
        
        name_surf = self.fonts['small'].render(game_name, True, COLORS["text_primary"])
        name_rect = name_surf.get_rect(center=(SCREEN_WIDTH//2, window_y + 30))
        self.screen.blit(name_surf, name_rect)
        
        # Barra de progresso
        bar_width = 300
        bar_height = 20
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = window_y + 70
        
        pygame.draw.rect(self.screen, COLORS["bg_dark"], 
                        (bar_x, bar_y, bar_width, bar_height))
        
        if self.downloader.progress > 0:
            fill_width = int(bar_width * self.downloader.progress / 100)
            pygame.draw.rect(self.screen, COLORS["gold"], 
                            (bar_x, bar_y, fill_width, bar_height))
        
        pygame.draw.rect(self.screen, COLORS["border"], 
                        (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Porcentagem
        percent_surf = self.fonts['medium'].render(f"{self.downloader.progress}%", 
                                                   True, COLORS["gold"])
        percent_rect = percent_surf.get_rect(center=(SCREEN_WIDTH//2, bar_y + 30))
        self.screen.blit(percent_surf, percent_rect)
        
        # Status
        status_surf = self.fonts['tiny'].render(self.downloader.status, 
                                                True, COLORS["text_secondary"])
        status_rect = status_surf.get_rect(center=(SCREEN_WIDTH//2, bar_y + 50))
        self.screen.blit(status_surf, status_rect)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if self.menu_stack[-1] == "main":
                        self.selected_index = max(0, self.selected_index - 1)
                    else:
                        self.game_selected = max(0, self.game_selected - 1)
                
                elif event.key == pygame.K_DOWN:
                    if self.menu_stack[-1] == "main":
                        self.selected_index = min(len(self.systems)-1, self.selected_index + 1)
                    else:
                        max_index = len(self.current_games) - 1
                        self.game_selected = min(max_index, self.game_selected + 1)
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                    if self.menu_stack[-1] == "main":
                        # Selecionar sistema
                        system = self.systems[self.selected_index]
                        self.menu_stack.append("games")
                        self.game_selected = 0
                        self.current_games = []
                        
                        def load_games():
                            self.current_games = self.downloader.list_games(system['url'])
                        
                        thread = threading.Thread(target=load_games)
                        thread.daemon = True
                        thread.start()
                    else:
                        # Baixar jogo
                        if self.current_games:
                            game = self.current_games[self.game_selected]
                            system = self.systems[self.selected_index]
                            
                            def progress_callback(percent, status):
                                self.downloader.progress = percent
                                self.downloader.status = status
                            
                            game_url = system['url'] + game
                            self.downloader.start_download(
                                game_url, game, system['id'], progress_callback
                            )
                            self.show_download = True
                
                elif event.key == pygame.K_b or event.key == pygame.K_ESCAPE:
                    if self.menu_stack[-1] == "games":
                        self.menu_stack.pop()
                        self.show_download = False
                    else:
                        self.running = False
                
                elif event.key == pygame.K_HOME or event.key == pygame.K_END:
                    self.running = False
                
                elif event.key == pygame.K_n:
                    self.audio.next_track()
                elif event.key == pygame.K_p:
                    self.audio.prev_track()
    
    def run(self):
        while self.running:
            self.handle_events()
            
            if self.menu_stack[-1] == "main":
                self.draw_main_menu()
            else:
                self.draw_game_list()
            
            if self.show_download:
                self.draw_download_progress()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

# ==================== PONTO DE ENTRADA ====================
if __name__ == "__main__":
    gui = StoregameGUI()
    gui.run()
    sys.exit(0)

### END OF STOREGAME v1.21.2 ULTIMATE ###
