#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Storegame GUI v1.15 - Interface Python com SDL2 para R36S
Compativel com PortMaster
"""

import os
import sys
import subprocess
import time
import curses
import signal

# Configuracoes
GAMEDIR = os.environ.get('GAMEDIR', '/roms/ports/gamestore')
DOWNLOAD_LOCATION = os.environ.get('DOWNLOAD_LOCATION', '/roms')
AUDIO_ENABLED = os.environ.get('AUDIO_ENABLED', '1') == '1'

# Caminhos
SOUNDS_DIR = os.path.join(GAMEDIR, 'sounds')
MUSIC_DIR = os.path.join(GAMEDIR, 'music')
CONFIG_DIR = os.path.join(GAMEDIR, 'config')

# Cores para curses
class Colors:
    def init_colors(self):
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Cyan
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)      # Red
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Yellow
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Green
        curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Blue

# Mapeamento de sistemas
SYSTEMS = {
    'PTBR': 'ROMs Traduzidas [BR]',
    'NES': 'Nintendo Entertainment System',
    'SNES': 'Super Nintendo',
    'N64': 'Nintendo 64',
    'GB': 'Game Boy',
    'GBC': 'Game Boy Color',
    'GBA': 'Game Boy Advance',
    'NDS': 'Nintendo DS',
    'PSX': 'PlayStation',
    'PSP': 'PlayStation Portable',
    'GAMEGEAR': 'Game Gear',
    'GENESIS': 'Genesis / Mega Drive',
    'MASTERSYSTEM': 'Master System',
    'SATURN': 'Saturn',
    'DREAMCAST': 'Dreamcast',
    'NEOGEO': 'Neo Geo',
    'TURBOGRAFX': 'TurboGrafx-16',
    'MSX': 'MSX',
    'MSX2': 'MSX2',
    'J2ME': 'Java Mobile',
    'SEGACD': 'Sega CD',
    'PICO8': 'PICO-8',
    'WSWAN': 'WonderSwan Color'
}

SYSTEM_URLS = {
    'NES': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20Entertainment%20System%20(Headered)/',
    'SNES': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/',
    'N64': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%2064%20(BigEndian)/',
    'GB': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy/',
    'GBC': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy%20Color/',
    'GBA': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy%20Advance/',
    'NDS': 'https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20DS%20(Decrypted)/',
    'PSX': 'https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/',
    'PSP': 'https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%20Portable/',
    'GAMEGEAR': 'https://myrient.erista.me/files/No-Intro/Sega%20-%20Game%20Gear/',
    'GENESIS': 'https://myrient.erista.me/files/No-Intro/Sega%20-%20Mega%20Drive%20-%20Genesis/',
    'MASTERSYSTEM': 'https://myrient.erista.me/files/No-Intro/Sega%20-%20Master%20System%20-%20Mark%20III/',
    'SATURN': 'https://myrient.erista.me/files/Redump/Sega%20-%20Saturn/',
    'DREAMCAST': 'https://myrient.erista.me/files/Redump/Sega%20-%20Dreamcast/',
    'NEOGEO': 'https://myrient.erista.me/files/Redump/SNK%20-%20Neo%20Geo%20CD/',
    'TURBOGRAFX': 'https://myrient.erista.me/files/No-Intro/NEC%20-%20PC%20Engine%20-%20TurboGrafx-16/',
    'MSX': 'https://myrient.erista.me/files/No-Intro/Microsoft%20-%20MSX/',
    'MSX2': 'https://myrient.erista.me/files/No-Intro/Microsoft%20-%20MSX2/',
    'J2ME': 'https://myrient.erista.me/files/No-Intro/Mobile%20-%20Java%202%20Micro%20Edition/',
    'SEGACD': 'https://myrient.erista.me/files/Redump/Sega%20-%20Mega-CD%20-%20Sega%20CD/',
    'PICO8': 'https://myrient.erista.me/files/No-Intro/Lexaloffle%20-%20PICO-8/',
    'WSWAN': 'https://myrient.erista.me/files/No-Intro/Bandai%20-%20WonderSwan%20Color/'
}

def play_sound(sound_name):
    """Toca um efeito sonoro"""
    if not AUDIO_ENABLED:
        return
    sound_file = os.path.join(SOUNDS_DIR, f'{sound_name}.ogg')
    if os.path.exists(sound_file):
        subprocess.Popen(['ffplay', '-nodisp', '-autoexit', sound_file],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def draw_box(stdscr, y, x, height, width, title='', color_pair=1):
    """Desenha uma caixa com bordas"""
    stdscr.attron(curses.color_pair(color_pair))
    # Bordas horizontais
    stdscr.addch(y, x, curses.ACS_ULCORNER)
    for i in range(width - 2):
        stdscr.addch(y, x + i + 1, curses.ACS_HLINE)
    stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
    
    for i in range(height - 2):
        stdscr.addch(y + i + 1, x, curses.ACS_VLINE)
        stdscr.addch(y + i + 1, x + width - 1, curses.ACS_VLINE)
    
    stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
    for i in range(width - 2):
        stdscr.addch(y + height - 1, x + i + 1, curses.ACS_HLINE)
    stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
    
    if title:
        title = f' {title} '
        title_x = x + (width - len(title)) // 2
        stdscr.addstr(y, title_x, title, curses.color_pair(1) | curses.A_BOLD)
    
    stdscr.attroff(curses.color_pair(color_pair))

def main_menu(stdscr):
    """Menu principal"""
    colors = Colors()
    colors.init_colors()
    
    menu_items = [
        ('[1] JOGOS TRADUZIDOS [BR]', 'ptbr'),
        ('[2] SISTEMAS NINTENDO', 'nintendo'),
        ('[3] SONY', 'sony'),
        ('[4] SEGA', 'sega'),
        ('[5] OUTROS SISTEMAS', 'outros'),
        ('[6] CONFIGURAR AUDIO', 'audio'),
        ('[0] SAIR', 'sair')
    ]
    
    current_idx = 0
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Título
        title = f'STOREGAME v1.15 - R36S'
        title_x = (max_x - len(title)) // 2
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, title_x, title)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        # Desenhar caixa do menu
        box_y = 5
        box_x = (max_x - 40) // 2
        draw_box(stdscr, box_y, box_x, len(menu_items) + 2, 40, 'MENU PRINCIPAL', 2)
        
        # Menu items
        for i, (item, _) in enumerate(menu_items):
            y = box_y + i + 1
            x = box_x + 2
            
            if i == current_idx:
                stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(y, x, '> ')
                stdscr.addstr(y, x + 2, item.ljust(34))
                stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, '  ' + item.ljust(34))
        
        stdscr.refresh()
        
        # Input handling
        key = stdscr.getch()
        
        if key == ord('q') or key == ord('Q') or key == ord('0'):
            play_sound('click')
            return 'sair'
        elif key == curses.KEY_UP or key == ord('k'):
            current_idx = (current_idx - 1) % len(menu_items)
            play_sound('click')
        elif key == curses.KEY_DOWN or key == ord('j'):
            current_idx = (current_idx + 1) % len(menu_items)
            play_sound('click')
        elif key == ord('\n') or key == ord(' '):
            play_sound('collect')
            return menu_items[current_idx][1]

def system_menu(stdscr, system_group, title):
    """Menu de sistemas por grupo"""
    colors = Colors()
    colors.init_colors()
    
    if system_group == 'nintendo':
        systems = ['NES', 'SNES', 'N64', 'GB', 'GBC', 'GBA', 'NDS']
    elif system_group == 'sony':
        systems = ['PSX', 'PSP']
    elif system_group == 'sega':
        systems = ['GAMEGEAR', 'GENESIS', 'MASTERSYSTEM', 'SATURN', 'DREAMCAST', 'SEGACD']
    else:  # outros
        systems = ['NEOGEO', 'TURBOGRAFX', 'MSX', 'MSX2', 'J2ME', 'PICO8', 'WSWAN']
    
    current_idx = 0
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Título
        title_x = (max_x - len(title)) // 2
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, title_x, title)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        # Desenhar caixa do menu
        box_y = 5
        box_x = (max_x - 40) // 2
        draw_box(stdscr, box_y, box_x, len(systems) + 2, 40, 'SISTEMAS', 2)
        
        # Menu items
        for i, sys_key in enumerate(systems):
            y = box_y + i + 1
            x = box_x + 2
            sys_name = SYSTEMS.get(sys_key, sys_key)
            item = f'[{i+1}] {sys_name[:34]}'
            
            if i == current_idx:
                stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(y, x, '> ')
                stdscr.addstr(y, x + 2, item.ljust(34))
                stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, '  ' + item.ljust(34))
        
        # Opcao voltar
        y = box_y + len(systems) + 1
        stdscr.addstr(y, box_x + 2, '[0] VOLTAR')
        
        stdscr.refresh()
        
        # Input handling
        key = stdscr.getch()
        
        if key == ord('0') or key == ord('q') or key == ord('Q'):
            play_sound('click')
            return None
        elif key == curses.KEY_UP or key == ord('k'):
            current_idx = (current_idx - 1) % len(systems)
            play_sound('click')
        elif key == curses.KEY_DOWN or key == ord('j'):
            current_idx = (current_idx + 1) % len(systems)
            play_sound('click')
        elif key == ord('\n') or key == ord(' '):
            play_sound('collect')
            return systems[current_idx]

def audio_config(stdscr):
    """Configuracao de audio"""
    colors = Colors()
    colors.init_colors()
    
    config_file = os.path.join(CONFIG_DIR, 'config')
    current_status = 'LIGADO' if AUDIO_ENABLED else 'DESLIGADO'
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Título
        title = 'CONFIGURACAO DE AUDIO'
        title_x = (max_x - len(title)) // 2
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(3, title_x, title)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        # Desenhar caixa
        box_y = 6
        box_x = (max_x - 40) // 2
        draw_box(stdscr, box_y, box_x, 5, 40, '', 2)
        
        # Status
        status_text = f'AUDIO: {current_status}'
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(box_y + 1, box_x + 2, status_text.center(36))
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        # Opcoes
        stdscr.addstr(box_y + 2, box_x + 2, '[1] ATIVAR AUDIO'.ljust(36))
        stdscr.addstr(box_y + 3, box_x + 2, '[2] DESATIVAR AUDIO'.ljust(36))
        stdscr.addstr(box_y + 4, box_x + 2, '[0] VOLTAR'.ljust(36))
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == ord('1'):
            play_sound('collect')
            with open(config_file, 'w') as f:
                f.write('AUDIO_ENABLED=1\n')
            # Reiniciar musica
            os.environ['AUDIO_ENABLED'] = '1'
            return
        elif key == ord('2'):
            play_sound('collect')
            with open(config_file, 'w') as f:
                f.write('AUDIO_ENABLED=0\n')
            # Parar musica
            os.environ['AUDIO_ENABLED'] = '0'
            subprocess.run(['pkill', '-f', 'ffplay.*sweden'])
            return
        elif key == ord('0') or key == ord('q'):
            play_sound('click')
            return

def main(stdscr):
    """Funcao principal"""
    # Configurar curses
    curses.curs_set(0)
    stdscr.keypad(1)
    curses.mousemask(0)
    
    while True:
        choice = main_menu(stdscr)
        
        if choice == 'sair':
            break
        elif choice == 'audio':
            audio_config(stdscr)
        elif choice == 'ptbr':
            # TODO: Implementar PT-BR
            pass
        else:
            system = system_menu(stdscr, choice, SYSTEMS.get(choice, ''))
            if system:
                # TODO: Listar e baixar jogos
                pass

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    sys.exit(0)
