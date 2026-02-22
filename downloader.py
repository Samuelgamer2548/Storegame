#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storegame - Módulo de Download
"""

import os
import subprocess
import threading
import re

class Downloader:
    def __init__(self):
        self.download_path = "/roms"
        self.turbo_mode = self._check_aria2()
        self.active = False
        self.progress = 0
        self.status = ""
        self.current_game = ""
    
    def _check_aria2(self):
        try:
            subprocess.run(['aria2c', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def list_games(self, url):
        try:
            result = subprocess.run(
                ['curl', '-s', url],
                capture_output=True,
                text=True,
                timeout=15
            )
            games = re.findall(r'title="([^"]+\.zip)"', result.stdout)
            return sorted(list(set(games)))
        except:
            return []
    
    def start_download(self, game_url, game_name, system_id, callback=None):
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
