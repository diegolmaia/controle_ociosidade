import time
import requests
import tkinter as tk
from tkinter import ttk
import threading
from pynput import mouse, keyboard
from datetime import datetime, timedelta
import socket
import os

# CONFIGURAÇÕES
SERVER_URL = "SEU_SERVER_AQUI"  # Exemplo: "http://seu-server.com"
IDLE_THRESHOLD = 10  #15m em segundos
COMPUTER_NAME = socket.gethostname()
CACHE_FILE = "motivos_cache.txt" # Arquivo para salvar os motivos localmente

class IdleMonitor:
    def __init__(self):
        self.last_activity = time.time()
        self.root = None
        self.is_popup_open = False
        # Motivos de emergência caso nunca tenha conseguido baixar nada
        self.default_reasons = ["Suporte Externo/Reunião", "Problema Técnico", "Troca de Turno",  "Intervalo", "Pausa Operacional", "Outros"]

    def reset_activity(self, *args):
        self.last_activity = time.time()

    def format_time(self, seconds):
        return str(timedelta(seconds=int(seconds)))

    def update_timer(self, label, start_ts):
        if self.is_popup_open and self.root:
            elapsed = time.time() - start_ts
            label.config(text=f"Tempo de Pausa: {self.format_time(elapsed)}")
            self.root.after(1000, self.update_timer, label, start_ts)

    def get_reasons_with_cache(self):
        """Tenta baixar da VPS, se falhar usa o arquivo local, se falhar usa a lista hardcoded"""
        try:
            # 1. Tenta baixar da VPS
            r = requests.get(f"{SERVER_URL}/api/reasons", timeout=3)
            if r.status_code == 200:
                data = r.json()
                online_reasons = [str(item[1]) if isinstance(item, list) else str(item) for item in data]
                
                # Salva no cache para a próxima vez
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(online_reasons))
                return online_reasons
        except Exception as e:
            print(f"Sem conexão com servidor: {e}")

        # 2. Se falhar, tenta ler o arquivo de cache local
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = f.read().splitlines()
                    if cache: return cache
            except:
                pass

        # 3. Se tudo falhar, usa os motivos padrão do código
        return self.default_reasons

    def show_popup(self, start_ts):
        self.is_popup_open = True
        self.root = tk.Tk()
        self.root.title("Alerta de Ociosidade")
        
        # Centralização e Estilo
        width, height = 400, 320
        sc_w, sc_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+{(sc_w-width)//2}+{(sc_h-height)//2}")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#ffffff")

        # Cabeçalho
        tk.Label(self.root, text="MONITORAMENTO DE ATIVIDADE", font=("Segoe UI", 8, "bold"), bg="#ffffff", fg="#94a3b8").pack(pady=(20,0))
        tk.Label(self.root, text="PAUSA DETECTADA", font=("Segoe UI", 16, "bold"), bg="#ffffff", fg="#ef4444").pack(pady=5)
        
        # Cronômetro HH:MM:SS
        lbl_timer = tk.Label(self.root, text="00:00:00", font=("Consolas", 15, "bold"), bg="#f8fafc", fg="#1e293b", padx=20, pady=10)
        lbl_timer.pack(pady=10)
        self.update_timer(lbl_timer, start_ts)

        tk.Label(self.root, text="Selecione o motivo da pausa:", font=("Segoe UI", 10), bg="#ffffff", fg="#64748b").pack(pady=5)
        
        # Carregando motivos (Online -> Cache -> Padrão)
        reasons = self.get_reasons_with_cache()
        combo = ttk.Combobox(self.root, values=reasons, state="readonly", width=35)
        combo.pack(pady=5)
        combo.current(0)

        def enviar():
            end_str = datetime.now().strftime("%H:%M:%S")
            start_str = datetime.fromtimestamp(start_ts).strftime("%H:%M:%S")
            
            payload = {
                "user": COMPUTER_NAME,
                "start": start_str,
                "end": end_str,
                "reason": combo.get()
            }
            
            try:
                requests.post(f"{SERVER_URL}/api/log", json=payload, timeout=3)
            except:
                # Se falhar o envio, podemos avisar o usuário ou tentar reenviar depois
                pass
            
            self.is_popup_open = False
            self.root.destroy()

        # Botão Estilizado
        btn = tk.Button(self.root, text="CONFIRMAR E RETORNAR", command=enviar, 
                       bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), 
                       padx=30, pady=12, border=0, cursor="hand2")
        btn.pack(pady=25)
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.mainloop()

    def check_idle(self):
        while True:
            diff = time.time() - self.last_activity
            if diff >= IDLE_THRESHOLD and not self.is_popup_open:
                start_ts = time.time() - diff
                self.show_popup(start_ts)
            time.sleep(1)

    def run(self):
        # Listeners para capturar movimentos
        mouse.Listener(on_move=self.reset_activity, on_click=self.reset_activity, on_scroll=self.reset_activity).start()
        keyboard.Listener(on_press=self.reset_activity).start()
        
        # Thread secundária para o relógio de ociosidade
        threading.Thread(target=self.check_idle, daemon=True).start()
        
        while True:
            time.sleep(10)

if __name__ == "__main__":
    monitor = IdleMonitor()
    monitor.run()