#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storegame - Módulo de Download Turbo
Gerencia downloads com aria2c/curl
"""

import os
import subprocess
import threading
import re
import json
from typing import Dict, List, Optional, Callable

class DownloadManager:
    """Gerenciador de downloads com suporte a multi-threading"""
    
    def __init__(self, config_path: str = None):
        self.download_path = "/roms"
        self.active_downloads = {}
        self.completed = []
        self.failed = []
        self.max_connections = 10
        self.turbo_mode = self._check_aria2()
        
        # Carregar config se existir
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.max_connections = config.get('max_connections', 10)
                self.download_path = config.get('download_path', '/roms')
    
    def _check_aria2(self) -> bool:
        """Verifica disponibilidade do aria2c"""
        try:
            subprocess.run(['aria2c', '--version'], 
                          capture_output=True, check=True)
            return True
        except:
            return False
    
    def list_games(self, url: str) -> List[str]:
        """Lista jogos disponiveis em uma URL"""
        try:
            result = subprocess.run(
                ['curl', '-s', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Extrair nomes dos arquivos .zip
            games = re.findall(r'title="([^"]+\.zip)"', result.stdout)
            games = sorted(list(set(games)))  # Remover duplicatas
            
            return games
        except Exception as e:
            print(f"Erro ao listar jogos: {e}")
            return []
    
    def download_game(self, game_url: str, game_name: str, system_id: str,
                     callback: Optional[Callable] = None) -> threading.Thread:
        """Inicia download em thread separada"""
        
        def download_task():
            system_dir = f"{self.download_path}/{system_id}"
            os.makedirs(system_dir, exist_ok=True)
            
            zip_path = f"{system_dir}/{game_name}"
            
            if callback:
                callback(0, "Iniciando download...")
            
            if self.turbo_mode:
                # Modo Turbo com aria2c
                cmd = [
                    'aria2c', 
                    '-x', str(self.max_connections),
                    '-s', str(self.max_connections),
                    '-j', str(self.max_connections),
                    '--check-certificate=false',
                    '--console-log-level=error',
                    '--summary-interval=1',
                    '--human-readable=true',
                    '--file-allocation=none',
                    '--allow-overwrite=true',
                    '--auto-file-renaming=false',
                    '--connect-timeout=30',
                    '--max-tries=5',
                    '--retry-wait=5',
                    '--dir', system_dir,
                    '--out', game_name,
                    '--referer=https://myrient.erista.me/',
                    game_url
                ]
            else:
                # Fallback para curl
                cmd = ['curl', '-L', '--connect-timeout', '30', 
                       '-o', zip_path, game_url]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Monitorar progresso
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                
                if callback and line:
                    # Extrair porcentagem
                    percent_match = re.search(r'(\d+)%', line)
                    if percent_match:
                        percent = int(percent_match.group(1))
                        
                        # Extrair velocidade
                        speed_match = re.search(r'([\d.]+)([KM])B/s', line)
                        if speed_match:
                            speed = f"{speed_match.group(1)}{speed_match.group(2)}B/s"
                        else:
                            speed = "??"
                        
                        callback(percent, f"Baixando... {speed}")
            
            success = process.poll() == 0
            
            if success:
                if callback:
                    callback(90, "Extraindo arquivo...")
                
                # Extrair arquivo
                extract_cmd = ['7z', 'x', zip_path, f"-o{system_dir}", 
                              '-mmt=on', '-y']
                subprocess.run(extract_cmd, capture_output=True)
                
                # Remover zip
                os.remove(zip_path)
                
                if callback:
                    callback(100, "Download concluido!")
                    self.completed.append(game_name)
            else:
                if callback:
                    callback(-1, "Falha no download")
                self.failed.append(game_name)
        
        thread = threading.Thread(target=download_task)
        thread.daemon = True
        thread.start()
        return thread
    
    def cancel_download(self, game_name: str) -> bool:
        """Cancela um download em andamento"""
        # Implementar se necessario
        return True
    
    def get_stats(self) -> Dict:
        """Retorna estatisticas de download"""
        return {
            'active': len(self.active_downloads),
            'completed': len(self.completed),
            'failed': len(self.failed),
            'turbo_mode': self.turbo_mode
        }

# Exportar classe principal
__all__ = ['DownloadManager']