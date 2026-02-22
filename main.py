#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storegame - Professional GUI Architecture v1.21.1
Motor grafico Pygame para R36S
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
from typing import List, Dict, Optional, Tuple

# ==================== SEGURANCA - ASSINATURA ====================
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

# Resolucao R36S
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 30

# Cores (tema profissional)
COLORS = {
    "bg_dark": (10, 25, 40),
    "bg_card": (20, 35, 55),
    "bg_highlight": (30, 45, 65),
    "text_primary": (220, 240, 255),
    "text_secondary": (160, 180, 200),
    "accent_cyan": (0, 200, 255),
    "accent_green": (100, 255, 150),
    "border": (255, 255, 255),
    "border_selected": (0, 200, 255)
}

# ==================== CLASSE DOWNLOADER ====================
class Downloader:
    """Gerenciador de downloads com Modo Turbo (aria2c)"""
    
    def __init__(self):
        self.download_path = "/roms"
        self.turbo_mode = self._check_aria2()
        self.active_downloads = {}
        self.download_threads = []
    
    def _check_aria2(self) -> bool:
        """Verifica se aria2c esta disponivel"""
        try:
            subprocess.run(['aria2c', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def list_games(self, system_url: str) -> List[str]:
        """Baixa lista de jogos do sistema"""
        try:
            result = subprocess.run(
                ['curl', '-s', system_url],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            import re
            games = re.findall(r'title="([^"]+\.zip)"', result.stdout)
            return sorted(games)
        except Exception as e:
            print(f"Erro ao listar jogos: {e}")
            return []
    
    def download_game(self, game_url: str, game_name: str, system_dir: str, 
                     callback=None) -> bool:
        """Download com progresso via callback"""
        
        def download_thread():
            os.makedirs(system_dir, exist_ok=True)
            
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
                cmd = ['curl', '-L', '-o', f"{system_dir}/{game_name}", game_url]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output and callback:
                    # Extrair porcentagem
                    import re
                    match = re.search(r'(\d+)%', output)
                    if match:
                        callback(int(match.group(1)))
            
            success = process.poll() == 0
            
            if success:
                # Extrair arquivo
                zip_file = f"{system_dir}/{game_name}"
                subprocess.run([
                    '7z', 'x', zip_file, f"-o{system_dir}", '-mmt=on', '-y'
                ], capture_output=True)
                os.remove(zip_file)
            
            return success
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        self.download_threads.append(thread)
        return True

# ==================== CLASSE AUDIO MANAGER ====================
class AudioManager:
    """Gerenciador de audio com pygame.mixer"""
    
    def __init__(self, sounds_path: str):
        self.sounds_path = sounds_path
        self.music_files = []
        self.current_track = 0
        self.volume = 0.3
        self.enabled = True
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._load_music_list()
        except Exception as e:
            print(f"Erro ao iniciar audio: {e}")
            self.enabled = False
    
    def _load_music_list(self):
        """Carrega lista de musicas MP3"""
        if os.path.exists(self.sounds_path):
            self.music_files = [
                f for f in os.listdir(self.sounds_path) 
                if f.endswith('.mp3')
            ]
            self.music_files.sort()
    
    def play(self, track_index: int = -1):
        """Toca musica especifica ou randomica"""
        if not self.enabled or not self.music_files:
            return
        
        if track_index >= 0 and track_index < len(self.music_files):
            self.current_track = track_index
        else:
            self.current_track = random.randint(0, len(self.music_files) - 1)
        
        music_path = os.path.join(self.sounds_path, self.music_files[self.current_track])
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)  # Loop infinito
        except Exception as e:
            print(f"Erro ao tocar musica: {e}")
    
    def next_track(self):
        """Proxima musica"""
        if self.music_files:
            self.current_track = (self.current_track + 1) % len(self.music_files)
            self.play(self.current_track)
    
    def prev_track(self):
        """Musica anterior"""
        if self.music_files:
            self.current_track = (self.current_track - 1) % len(self.music_files)
            self.play(self.current_track)
    
    def set_volume(self, volume: float):
        """Ajusta volume (0.0 a 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def stop(self):
        """Para a musica"""
        pygame.mixer.music.stop()

# ==================== CLASSE GUI ====================
class StoregameGUI:
    """Interface grafica principal"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Storegame v1.21.1")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Carregar database
        self.systems = self._load_database()
        self.selected_index = 0
        self.menu_stack = ["main"]
        self.current_games = []
        
        # Inicializar componentes
        self.downloader = Downloader()
        self.audio = AudioManager(SOUNDS_PATH)
        
        # Fontes
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Estado da interface
        self.download_progress = 0
        self.download_status = ""
        self.show_progress = False
        
        # Iniciar musica
        self.audio.play()
        
        # Criar superficie para cache
        self.create_cached_surfaces()
    
    def _load_database(self) -> List[Dict]:
        """Carrega database de sistemas"""
        try:
            with open(DATABASE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('systems', [])
        except Exception as e:
            print(f"Erro ao carregar database: {e}")
            return []
    
    def create_cached_surfaces(self):
        """Cria superficies que serao reutilizadas"""
        self.logo_surf = self.font_large.render("STOREGAME", True, COLORS["accent_cyan"])
        self.version_surf = self.font_tiny.render("v1.21.1 - Python Core", True, COLORS["text_secondary"])
        
        # Instrucoes
        instr_text = "▲/▼ Navegar | A Selecionar | B Voltar | Start Sair"
        self.instr_surf = self.font_tiny.render(instr_text, True, COLORS["border"])
    
    def draw_background(self):
        """Desenha fundo gradiente"""
        self.screen.fill(COLORS["bg_dark"])
        
        # Linha sutil no topo
        pygame.draw.line(self.screen, COLORS["border"], (0, 80), (SCREEN_WIDTH, 80), 1)
        
        # Linha sutil no rodape
        pygame.draw.line(self.screen, COLORS["border"], (0, SCREEN_HEIGHT-40), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT-40), 1)
    
    def draw_main_menu(self):
        """Desenha menu principal com cards em grade"""
        self.draw_background()
        
        # Logo
        logo_rect = self.logo_surf.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(self.logo_surf, logo_rect)
        self.screen.blit(self.version_surf, (SCREEN_WIDTH-100, 65))
        
        # Grade de sistemas
        card_width = 180
        card_height = 80
        cols = 3
        spacing = 20
        start_x = (SCREEN_WIDTH - (cols * (card_width + spacing))) // 2
        start_y = 120
        
        for i, system in enumerate(self.systems):
            row = i // cols
            col = i % cols
            x = start_x + col * (card_width + spacing)
            y = start_y + row * (card_height + spacing)
            
            selected = (i == self.selected_index)
            
            # Cor do card
            if selected:
                bg_color = COLORS["bg_highlight"]
                border_color = COLORS["border_selected"]
            else:
                bg_color = COLORS["bg_card"]
                border_color = COLORS["border"]
            
            # Desenhar card
            pygame.draw.rect(self.screen, bg_color, (x, y, card_width, card_height))
            pygame.draw.rect(self.screen, border_color, (x, y, card_width, card_height), 2)
            
            # Nome do sistema
            name = system.get('name', 'Unknown')
            if len(name) > 18:
                name = name[:15] + "..."
            
            name_surf = self.font_small.render(name, True, COLORS["text_primary"])
            name_rect = name_surf.get_rect(center=(x + card_width//2, y + card_height//2 - 10))
            self.screen.blit(name_surf, name_rect)
            
            # ID do sistema
            id_surf = self.font_tiny.render(system.get('id', ''), True, COLORS["text_secondary"])
            id_rect = id_surf.get_rect(center=(x + card_width//2, y + card_height//2 + 15))
            self.screen.blit(id_surf, id_rect)
        
        # Instrucoes
        instr_rect = self.instr_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-20))
        self.screen.blit(self.instr_surf, instr_rect)
    
    def draw_game_list(self):
        """Desenha lista de jogos"""
        self.draw_background()
        
        # Titulo do sistema
        system = self.systems[self.selected_index]
        title = f"{system['name']} - Jogos Disponiveis"
        title_surf = self.font_medium.render(title, True, COLORS["accent_cyan"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.screen.blit(title_surf, title_rect)
        
        # Instrucao
        back_surf = self.font_tiny.render("A: Baixar | B: Voltar", True, COLORS["border"])
        back_rect = back_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-20))
        self.screen.blit(back_surf, back_rect)
        
        # Lista de jogos
        if self.current_games:
            start_y = 80
            for i, game in enumerate(self.current_games[:10]):
                y = start_y + i * 35
                
                # Indicador de selecao
                if i == self.selected_index:
                    pygame.draw.rect(self.screen, COLORS["bg_highlight"], 
                                    (50, y-5, SCREEN_WIDTH-100, 30))
                
                # Nome do jogo
                game_name = game
                if len(game_name) > 50:
                    game_name = game_name[:47] + "..."
                
                game_surf = self.font_small.render(game_name, True, COLORS["text_primary"])
                self.screen.blit(game_surf, (60, y))
            
            if len(self.current_games) > 10:
                more_surf = self.font_tiny.render(f"... e mais {len(self.current_games)-10} jogos", 
                                                  True, COLORS["text_secondary"])
                self.screen.blit(more_surf, (60, start_y + 10*35))
        else:
            loading_surf = self.font_medium.render("Carregando lista de jogos...", True, COLORS["text_secondary"])
            loading_rect = loading_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(loading_surf, loading_rect)
    
    def draw_progress_bar(self, progress: int, status: str):
        """Desenha barra de progresso durante download"""
        bar_width = 400
        bar_height = 30
        x = (SCREEN_WIDTH - bar_width) // 2
        y = SCREEN_HEIGHT - 100
        
        # Fundo da barra
        pygame.draw.rect(self.screen, COLORS["bg_card"], (x, y, bar_width, bar_height))
        
        # Progresso
        fill_width = int(bar_width * progress / 100)
        pygame.draw.rect(self.screen, COLORS["accent_cyan"], (x, y, fill_width, bar_height))
        
        # Borda
        pygame.draw.rect(self.screen, COLORS["border"], (x, y, bar_width, bar_height), 2)
        
        # Porcentagem
        percent_surf = self.font_medium.render(f"{progress}%", True, COLORS["text_primary"])
        percent_rect = percent_surf.get_rect(center=(SCREEN_WIDTH//2, y + bar_height//2))
        self.screen.blit(percent_surf, percent_rect)
        
        # Status
        if status:
            status_surf = self.font_tiny.render(status, True, COLORS["text_secondary"])
            status_rect = status_surf.get_rect(center=(SCREEN_WIDTH//2, y - 20))
            self.screen.blit(status_surf, status_rect)
    
    def handle_events(self):
        """Processa eventos do controle"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    if self.menu_stack[-1] == "main":
                        self.selected_index = min(len(self.systems)-1, self.selected_index + 1)
                    else:
                        self.selected_index = min(len(self.current_games)-1, self.selected_index + 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_a:
                    if self.menu_stack[-1] == "main":
                        # Selecionar sistema
                        system = self.systems[self.selected_index]
                        self.menu_stack.append("games")
                        self.selected_index = 0
                        self.current_games = []
                        
                        # Carregar lista de jogos em background
                        def load_games():
                            url = system['url']
                            self.current_games = self.downloader.list_games(url)
                        
                        thread = threading.Thread(target=load_games)
                        thread.daemon = True
                        thread.start()
                    else:
                        # Baixar jogo selecionado
                        if self.current_games:
                            game = self.current_games[self.selected_index]
                            system = self.systems[self.selected_index]
                            
                            def progress_callback(percent):
                                self.download_progress = percent
                                self.download_status = f"Baixando {game[:30]}..."
                            
                            system_dir = f"/roms/{system['id']}"
                            game_url = system['url'] + game
                            
                            self.downloader.download_game(
                                game_url, game, system_dir, progress_callback
                            )
                            self.show_progress = True
                
                elif event.key == pygame.K_b or event.key == pygame.K_ESCAPE:
                    # Voltar
                    if len(self.menu_stack) > 1:
                        self.menu_stack.pop()
                        self.selected_index = 0
                        self.show_progress = False
                    else:
                        self.running = False
                
                elif event.key == pygame.K_HOME or event.key == pygame.K_END:
                    self.running = False
                
                elif event.key == pygame.K_n:
                    # Proxima musica
                    self.audio.next_track()
                elif event.key == pygame.K_p:
                    # Musica anterior
                    self.audio.prev_track()
    
    def run(self):
        """Loop principal"""
        while self.running:
            self.handle_events()
            
            if self.menu_stack[-1] == "main":
                self.draw_main_menu()
            else:
                self.draw_game_list()
            
            if self.show_progress:
                self.draw_progress_bar(self.download_progress, self.download_status)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.audio.stop()
        pygame.quit()

# ==================== PONTO DE ENTRADA ====================
if __name__ == "__main__":
    gui = StoregameGUI()
    gui.run()
    sys.exit(0)