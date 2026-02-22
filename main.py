#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storegame - Stability & Auto-Repair v1.21.4
Interface profissional com tratamento de erros
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
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Callable

# ==================== CONFIGURACAO DE LOG DE ERROS ====================
ERROR_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt")

def log_error(error_msg: str, trace: str = ""):
    """Registra erro em arquivo para debug"""
    try:
        with open(ERROR_LOG_FILE, 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Data: {datetime.now()}\n")
            f.write(f"Erro: {error_msg}\n")
            if trace:
                f.write(f"Traceback:\n{trace}\n")
            f.write(f"{'='*50}\n")
    except:
        pass

# ==================== SEGURANCA OFUSCADA ====================
AUTH_HASH = "8a7d5f9e3c2b1a4d6e8f0c9b7a5d3e1f2c4b6a8d0e2f4c6a8b0d2e4f6a8c0b2e4"
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)

# Verificar se esta na pasta correta
if not SCRIPT_DIR.endswith("Storegame"):
    log_error("Script executado fora da pasta Storegame", SCRIPT_DIR)
    print("ERRO: O script deve estar na pasta Storegame")
    sys.exit(1)

# Verificar assinatura
if hashlib.sha256(b"SamuelGamer2548").hexdigest() != AUTH_HASH:
    log_error("Assinatura invalida")
    print("ERRO: Assinatura invalida")
    sys.exit(1)

# ==================== CONFIGURACOES ====================
STOREGAME_PATH = os.environ.get('STOREGAME_PATH', SCRIPT_DIR)
SOUNDS_PATH = os.environ.get('STOREGAME_SOUNDS', f'{STOREGAME_PATH}/sounds')
CONFIG_PATH = os.environ.get('STOREGAME_CONFIG', f'{STOREGAME_PATH}/config')
DATABASE_FILE = f'{STOREGAME_PATH}/database.json'

# Resolucao R36S
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Cores do tema
COLORS = {
    "bg_dark": (0, 0, 40),
    "bg_card": (20, 20, 80),
    "bg_highlight": (40, 40, 120),
    "text_primary": (255, 255, 255),
    "text_secondary": (200, 200, 200),
    "gold": (255, 215, 0),
    "gold_dark": (204, 172, 0),
    "border": (255, 255, 255),
    "border_selected": (255, 215, 0),
    "shadow": (0, 0, 20)
}

# ==================== CLASSE DOWNLOADER ====================
class Downloader:
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
        except Exception as e:
            log_error(f"Erro ao listar jogos: {e}")
            return []
    
    def start_download(self, game_url: str, game_name: str, system_id: str,
                      callback: Optional[Callable] = None):
        self.active = True
        self.current_game = game_name
        self.progress = 0
        
        def download_thread():
            try:
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
            except Exception as e:
                log_error(f"Erro no download: {e}", traceback.format_exc())
                if callback:
                    callback(-1, f"Erro: {str(e)[:30]}")
            finally:
                self.active = False
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        return thread

# ==================== CLASSE AUDIO MANAGER (TOLERANTE A FALHAS) ====================
class AudioManager:
    def __init__(self, sounds_path: str):
        self.sounds_path = sounds_path
        self.music_files = []
        self.current_track = 0
        self.volume = 0.3
        self.enabled = True
        self.mixer_initialized = False
        
        # Tentar inicializar mixer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            log_error(f"Falha ao inicializar mixer: {e}")
            self.enabled = False
        
        # Carregar lista de musicas
        self._load_music_list()
        
        # Tentar tocar musica
        if self.enabled and self.mixer_initialized:
            self._play_current()
    
    def _load_music_list(self):
        try:
            if os.path.exists(self.sounds_path):
                self.music_files = [f for f in os.listdir(self.sounds_path) if f.endswith('.mp3')]
                self.music_files.sort()
        except Exception as e:
            log_error(f"Erro ao carregar lista de musicas: {e}")
    
    def _play_current(self):
        if not self.enabled or not self.mixer_initialized or not self.music_files:
            return
        
        try:
            music_path = os.path.join(self.sounds_path, self.music_files[self.current_track])
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)
            else:
                log_error(f"Arquivo de musica nao encontrado: {music_path}")
        except Exception as e:
            log_error(f"Erro ao tocar musica: {e}")
            # Continua sem som - nao fecha o programa

# ==================== CLASSE GUI PRINCIPAL ====================
class StoregameGUI:
    def __init__(self):
        try:
            pygame.init()
            pygame.display.set_caption("Storegame v1.21.4")
            
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.clock = pygame.time.Clock()
            self.running = True  # So muda com botao de sair
            self.fonts = self._load_fonts()
            
            # Carregar database
            self.systems = self._load_database()
            self.selected_index = 0
            self.menu_stack = ["main"]
            self.current_games = []
            self.game_selected = 0
            
            # Downloader
            self.downloader = Downloader()
            self.audio = AudioManager(SOUNDS_PATH)
            
            # Estado do download
            self.show_download = False
            self.download_progress = 0
            self.download_status = ""
            
            # Criar superficies estaticas
            self._create_static_surfaces()
            
        except Exception as e:
            log_error(f"Erro na inicializacao da GUI: {e}", traceback.format_exc())
            raise
    
    def _load_fonts(self):
        fonts = {}
        try:
            fonts['large'] = pygame.font.Font(None, 48)
            fonts['medium'] = pygame.font.Font(None, 32)
            fonts['small'] = pygame.font.Font(None, 24)
            fonts['tiny'] = pygame.font.Font(None, 18)
        except Exception as e:
            log_error(f"Erro ao carregar fontes: {e}")
            # Fallback para fonte padrao
            fonts['large'] = pygame.font.Font(None, 48)
            fonts['medium'] = pygame.font.Font(None, 32)
            fonts['small'] = pygame.font.Font(None, 24)
            fonts['tiny'] = pygame.font.Font(None, 18)
        return fonts
    
    def _load_database(self) -> List[Dict]:
        try:
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('systems', [])
        except Exception as e:
            log_error(f"Erro ao carregar database: {e}", traceback.format_exc())
            return self._get_default_systems()
    
    def _get_default_systems(self) -> List[Dict]:
        return [
            {"id": "NES", "name": "Nintendo Entertainment System", "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20Entertainment%20System%20(Headered)/"},
            {"id": "SNES", "name": "Super Nintendo", "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/"},
            {"id": "N64", "name": "Nintendo 64", "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%2064%20(BigEndian)/"},
            {"id": "PSX", "name": "PlayStation", "url": "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/"}
        ]
    
    def _create_static_surfaces(self):
        try:
            self.logo_surf = self.fonts['large'].render("STOREGAME", True, COLORS["gold"])
            self.version_surf = self.fonts['tiny'].render("v1.21.4 Stability", True, COLORS["text_secondary"])
            self.footer_text = self.fonts['tiny'].render("(A) SELECIONAR    (B) VOLTAR    (START) SAIR", 
                                                         True, COLORS["gold"])
        except Exception as e:
            log_error(f"Erro ao criar superficies: {e}")
    
    def draw_background(self):
        try:
            self.screen.fill(COLORS["bg_dark"])
            # Efeito de gradiente
            for i in range(0, SCREEN_HEIGHT, 4):
                color = (0, 0, 40 + i // 10)
                pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))
        except Exception as e:
            log_error(f"Erro ao desenhar background: {e}")
    
    def draw_top_bar(self):
        try:
            pygame.draw.rect(self.screen, COLORS["gold"], (0, 0, SCREEN_WIDTH, 4))
            pygame.draw.rect(self.screen, COLORS["bg_highlight"], (0, 4, SCREEN_WIDTH, 40))
            self.screen.blit(self.logo_surf, (20, 12))
            self.screen.blit(self.version_surf, (SCREEN_WIDTH - 100, 20))
            pygame.draw.line(self.screen, COLORS["gold"], (0, 45), (SCREEN_WIDTH, 45), 2)
        except Exception as e:
            log_error(f"Erro ao desenhar top bar: {e}")
    
    def draw_bottom_bar(self):
        try:
            pygame.draw.rect(self.screen, COLORS["bg_highlight"], (0, SCREEN_HEIGHT-35, SCREEN_WIDTH, 35))
            footer_x = (SCREEN_WIDTH - self.footer_text.get_width()) // 2
            self.screen.blit(self.footer_text, (footer_x, SCREEN_HEIGHT-25))
            pygame.draw.line(self.screen, COLORS["gold"], (0, SCREEN_HEIGHT-36), (SCREEN_WIDTH, SCREEN_HEIGHT-36), 2)
        except Exception as e:
            log_error(f"Erro ao desenhar bottom bar: {e}")
    
    def draw_card(self, x: int, y: int, width: int, height: int, 
                  title: str, subtitle: str = "", selected: bool = False):
        try:
            # Sombra
            pygame.draw.rect(self.screen, COLORS["shadow"], (x+3, y+3, width, height), border_radius=8)
            
            # Card
            card_rect = pygame.Rect(x, y, width, height)
            if selected:
                bg_color = COLORS["bg_highlight"]
                border_color = COLORS["gold"]
                pygame.draw.rect(self.screen, COLORS["gold_dark"], card_rect, 3, border_radius=8)
            else:
                bg_color = COLORS["bg_card"]
                border_color = COLORS["border"]
            
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, card_rect, 2, border_radius=8)
            
            # Texto
            title_surf = self.fonts['small'].render(title, True, COLORS["text_primary"])
            title_rect = title_surf.get_rect(center=(x + width//2, y + height//2 - 10))
            self.screen.blit(title_surf, title_rect)
            
            if subtitle:
                sub_surf = self.fonts['tiny'].render(subtitle, True, COLORS["text_secondary"])
                sub_rect = sub_surf.get_rect(center=(x + width//2, y + height//2 + 15))
                self.screen.blit(sub_surf, sub_rect)
        except Exception as e:
            log_error(f"Erro ao desenhar card: {e}")
    
    def draw_main_menu(self):
        try:
            self.draw_background()
            self.draw_top_bar()
            self.draw_bottom_bar()
            
            # Grade 3x3
            card_width, card_height = 180, 90
            cols = 3
            spacing = 20
            start_x = (SCREEN_WIDTH - (cols * (card_width + spacing))) // 2
            start_y = 80
            
            for i, system in enumerate(self.systems):
                if i >= 9: break
                row = i // cols
                col = i % cols
                x = start_x + col * (card_width + spacing)
                y = start_y + row * (card_height + spacing)
                
                self.draw_card(x, y, card_width, card_height, 
                              system['name'][:18], system['id'], 
                              selected=(i == self.selected_index))
        except Exception as e:
            log_error(f"Erro ao desenhar menu principal: {e}")
    
    def draw_game_list(self):
        try:
            self.draw_background()
            self.draw_top_bar()
            self.draw_bottom_bar()
            
            system = self.systems[self.selected_index]
            
            # Titulo
            title = f"{system['name']} - Jogos"
            title_surf = self.fonts['medium'].render(title, True, COLORS["gold"])
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 60))
            self.screen.blit(title_surf, title_rect)
            
            # Lista
            if self.current_games:
                start_y = 100
                for i, game in enumerate(self.current_games[:12]):
                    y = start_y + i * 28
                    
                    if i == self.game_selected:
                        pygame.draw.rect(self.screen, COLORS["bg_highlight"], 
                                        (50, y-2, SCREEN_WIDTH-100, 28))
                        pygame.draw.rect(self.screen, COLORS["gold"], (45, y-2, 3, 28))
                    
                    display_name = game if len(game) <= 50 else game[:47] + "..."
                    game_surf = self.fonts['small'].render(display_name, True, COLORS["text_primary"])
                    self.screen.blit(game_surf, (60, y))
            else:
                loading = self.fonts['medium'].render("Carregando...", True, COLORS["text_secondary"])
                loading_rect = loading.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(loading, loading_rect)
        except Exception as e:
            log_error(f"Erro ao desenhar lista de jogos: {e}")
    
    def draw_download_progress(self):
        if not self.show_download:
            return
        
        try:
            # Fundo escuro
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(COLORS["bg_dark"])
            self.screen.blit(overlay, (0, 0))
            
            # Janela
            win_w, win_h = 400, 150
            win_x = (SCREEN_WIDTH - win_w) // 2
            win_y = (SCREEN_HEIGHT - win_h) // 2
            
            pygame.draw.rect(self.screen, COLORS["bg_highlight"], 
                            (win_x, win_y, win_w, win_h))
            pygame.draw.rect(self.screen, COLORS["gold"], 
                            (win_x, win_y, win_w, win_h), 3)
            
            # Nome do jogo
            game_name = self.downloader.current_game
            if len(game_name) > 30:
                game_name = game_name[:27] + "..."
            name_surf = self.fonts['small'].render(game_name, True, COLORS["text_primary"])
            name_rect = name_surf.get_rect(center=(SCREEN_WIDTH//2, win_y + 30))
            self.screen.blit(name_surf, name_rect)
            
            # Barra de progresso
            bar_w, bar_h = 300, 20
            bar_x = (SCREEN_WIDTH - bar_w) // 2
            bar_y = win_y + 70
            
            pygame.draw.rect(self.screen, COLORS["bg_dark"], (bar_x, bar_y, bar_w, bar_h))
            
            if self.downloader.progress > 0:
                fill_w = int(bar_w * self.downloader.progress / 100)
                pygame.draw.rect(self.screen, COLORS["gold"], (bar_x, bar_y, fill_w, bar_h))
            
            pygame.draw.rect(self.screen, COLORS["border"], (bar_x, bar_y, bar_w, bar_h), 2)
            
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
        except Exception as e:
            log_error(f"Erro ao desenhar progresso: {e}")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # ===== NAVEGACAO CORRIGIDA PARA R36S =====
                if self.menu_stack[-1] == "main":
                    # Menu principal
                    if event.key == pygame.K_UP:
                        self.selected_index = max(0, self.selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = min(len(self.systems)-1, self.selected_index + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                        # Botao A - Selecionar sistema
                        system = self.systems[self.selected_index]
                        self.menu_stack.append("games")
                        self.game_selected = 0
                        self.current_games = []
                        
                        def load_games():
                            try:
                                self.current_games = self.downloader.list_games(system['url'])
                            except Exception as e:
                                log_error(f"Erro ao carregar jogos: {e}")
                        
                        thread = threading.Thread(target=load_games)
                        thread.daemon = True
                        thread.start()
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                        # Botao B - Sair
                        self.running = False
                    elif event.key == pygame.K_HOME or event.key == pygame.K_END:
                        # Start - Sair
                        self.running = False
                
                elif self.menu_stack[-1] == "games":
                    # Lista de jogos
                    if event.key == pygame.K_UP:
                        self.game_selected = max(0, self.game_selected - 1)
                    elif event.key == pygame.K_DOWN:
                        max_index = len(self.current_games) - 1
                        self.game_selected = min(max_index, self.game_selected + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                        # Botao A - Baixar jogo
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
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                        # Botao B - Voltar ao menu principal
                        self.menu_stack.pop()
                        self.show_download = False
                    elif event.key == pygame.K_HOME or event.key == pygame.K_END:
                        # Start - Sair
                        self.running = False
    
    def run(self):
        try:
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
        except Exception as e:
            log_error(f"Erro no loop principal: {e}", traceback.format_exc())
        finally:
            try:
                pygame.quit()
            except:
                pass

# ==================== PONTO DE ENTRADA COM TRATAMENTO DE ERROS ====================
if __name__ == "__main__":
    try:
        gui = StoregameGUI()
        gui.run()
        sys.exit(0)
    except Exception as e:
        log_error(f"Erro fatal: {e}", traceback.format_exc())
        print(f"Erro fatal. Verifique {ERROR_LOG_FILE}")
        sys.exit(1)

### END OF STOREGAME v1.21.4 STABILITY ###
