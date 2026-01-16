"""
Script de automação de cliques com interface gráfica
Permite configurar múltiplos cliques, repetições e delays
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from pynput import mouse, keyboard
from pynput.mouse import Button


class ClickAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("Automação de Cliques")
        self.root.geometry("520x580")
        self.root.resizable(False, False)
        
        # Variáveis
        self.coordinates = []
        self.is_capturing = False
        self.is_running = False
        self.keyboard_listener = None
        
        # Configurações
        self.click_delay = tk.DoubleVar(value=1.0)
        self.loop_repetitions = tk.IntVar(value=1)
        self.total_repetitions = tk.IntVar(value=1)
        
        self.setup_ui()
        self.setup_listeners()
        
    def setup_ui(self):
        """Configura a interface gráfica"""
        # Frame principal com padding menor
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título compacto
        title_label = ttk.Label(main_frame, text="Automação de Cliques", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 8))
        
        # Container principal em duas colunas
        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Coluna esquerda
        left_col = ttk.Frame(container)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        # Coluna direita
        right_col = ttk.Frame(container)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        # === COLUNA ESQUERDA ===
        
        # Captura de Coordenadas
        capture_frame = ttk.LabelFrame(left_col, text="Captura", padding="6")
        capture_frame.pack(fill=tk.X, pady=(0, 6))
        
        ttk.Label(capture_frame, text="Pressione '0' para salvar", font=("Arial", 8)).pack(pady=(0, 4))
        
        capture_controls = ttk.Frame(capture_frame)
        capture_controls.pack(fill=tk.X)
        
        btn_capture = ttk.Button(capture_controls, text="Iniciar", command=self.toggle_capture, width=10)
        btn_capture.pack(side=tk.LEFT, padx=(0, 4))
        
        self.capture_status_label = ttk.Label(capture_controls, text="Parado", foreground="red", font=("Arial", 8))
        self.capture_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Coordenadas
        coords_frame = ttk.LabelFrame(left_col, text="Coordenadas", padding="6")
        coords_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        
        # Treeview compacto
        tree_frame = ttk.Frame(coords_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("#", "X", "Y")
        self.coords_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        self.coords_tree.heading("#", text="#")
        self.coords_tree.heading("X", text="X")
        self.coords_tree.heading("Y", text="Y")
        self.coords_tree.column("#", width=35, anchor=tk.CENTER)
        self.coords_tree.column("X", width=70, anchor=tk.CENTER)
        self.coords_tree.column("Y", width=70, anchor=tk.CENTER)
        self.coords_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.coords_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.coords_tree.configure(yscrollcommand=scrollbar.set)
        
        # Botões coordenadas
        coord_btn_frame = ttk.Frame(coords_frame)
        coord_btn_frame.pack(fill=tk.X, pady=(4, 0))
        
        ttk.Button(coord_btn_frame, text="Limpar", command=self.clear_coordinates, width=10).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(coord_btn_frame, text="Remover", command=self.remove_selected, width=10).pack(side=tk.LEFT)
        
        # Configurações
        config_frame = ttk.LabelFrame(left_col, text="Configurações", padding="6")
        config_frame.pack(fill=tk.X)
        
        # Delay
        delay_frame = ttk.Frame(config_frame)
        delay_frame.pack(fill=tk.X, pady=2)
        ttk.Label(delay_frame, text="Delay (s):", width=12, anchor=tk.W).pack(side=tk.LEFT)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0.1, to=60.0, increment=0.1, textvariable=self.click_delay, width=8)
        delay_spinbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Loop reps
        loop_frame = ttk.Frame(config_frame)
        loop_frame.pack(fill=tk.X, pady=2)
        ttk.Label(loop_frame, text="Rep. Loop:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        loop_spinbox = ttk.Spinbox(loop_frame, from_=1, to=1000, textvariable=self.loop_repetitions, width=8)
        loop_spinbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Total reps
        total_frame = ttk.Frame(config_frame)
        total_frame.pack(fill=tk.X, pady=2)
        ttk.Label(total_frame, text="Rep. Total:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        total_spinbox = ttk.Spinbox(total_frame, from_=1, to=1000, textvariable=self.total_repetitions, width=8)
        total_spinbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # === COLUNA DIREITA ===
        
        # Controles
        control_frame = ttk.LabelFrame(right_col, text="Controles", padding="6")
        control_frame.pack(fill=tk.X, pady=(0, 6))
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 4))
        
        self.btn_start = ttk.Button(btn_frame, text="▶ Iniciar", command=self.start_automation, width=12)
        self.btn_start.pack(fill=tk.X, pady=(0, 4))
        
        self.btn_stop = ttk.Button(btn_frame, text="⏹ Parar", command=self.stop_automation, state="disabled", width=12)
        self.btn_stop.pack(fill=tk.X)
        
        self.status_label = ttk.Label(control_frame, text="Status: Parado", foreground="red", font=("Arial", 9, "bold"))
        self.status_label.pack(pady=(4, 0))
        
        # Log
        log_frame = ttk.LabelFrame(right_col, text="Log", padding="6")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=30, font=("Consolas", 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_listeners(self):
        """Configura os listeners de mouse e teclado"""
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
        
    def on_key_press(self, key):
        """Callback quando uma tecla é pressionada"""
        try:
            if hasattr(key, 'char') and key.char == '0' and self.is_capturing:
                self.save_current_position()
        except AttributeError:
            pass
    
    def toggle_capture(self):
        """Alterna o modo de captura"""
        self.is_capturing = not self.is_capturing
        
        if self.is_capturing:
            self.capture_status_label.config(text="Capturando...", foreground="green")
            self.log("Captura ativada. Pressione '0' para salvar.")
        else:
            self.capture_status_label.config(text="Parado", foreground="red")
            self.log("Captura desativada.")
    
    def save_current_position(self):
        """Salva a posição atual do mouse"""
        try:
            mouse_controller = mouse.Controller()
            x, y = mouse_controller.position
            self.coordinates.append((x, y))
            self.update_coordinates_display()
            self.log(f"#{len(self.coordinates)}: ({x}, {y})")
        except Exception as e:
            self.log(f"Erro: {e}")
    
    def update_coordinates_display(self):
        """Atualiza a exibição das coordenadas"""
        for item in self.coords_tree.get_children():
            self.coords_tree.delete(item)
        
        for idx, (x, y) in enumerate(self.coordinates, 1):
            self.coords_tree.insert("", "end", values=(idx, x, y))
    
    def clear_coordinates(self):
        """Limpa todas as coordenadas"""
        if messagebox.askyesno("Confirmar", "Limpar todas as coordenadas?"):
            self.coordinates.clear()
            self.update_coordinates_display()
            self.log("Coordenadas limpas.")
    
    def remove_selected(self):
        """Remove a coordenada selecionada"""
        selected = self.coords_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma coordenada.")
            return
        
        item = selected[0]
        values = self.coords_tree.item(item, "values")
        idx = int(values[0]) - 1
        
        if 0 <= idx < len(self.coordinates):
            removed = self.coordinates.pop(idx)
            self.update_coordinates_display()
            self.log(f"Removido: ({removed[0]}, {removed[1]})")
    
    def log(self, message):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def start_automation(self):
        """Inicia a automação em thread separada"""
        if not self.coordinates:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma coordenada.")
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_label.config(text="Status: Executando...", foreground="green")
        
        thread = threading.Thread(target=self.run_automation, daemon=True)
        thread.start()
    
    def run_automation(self):
        """Executa a automação de cliques"""
        try:
            mouse_controller = mouse.Controller()
            click_delay = self.click_delay.get()
            loop_reps = self.loop_repetitions.get()
            total_reps = self.total_repetitions.get()
            
            self.log(f"Iniciando: {len(self.coordinates)} coords")
            self.log(f"Loop: {loop_reps}x | Total: {total_reps}x")
            
            for total_rep in range(1, total_reps + 1):
                if not self.is_running:
                    break
                
                self.log(f"--- Loop {total_rep}/{total_reps} ---")
                
                for loop_rep in range(1, loop_reps + 1):
                    if not self.is_running:
                        break
                    
                    self.log(f"Rep {loop_rep}/{loop_reps}")
                    
                    for idx, (x, y) in enumerate(self.coordinates, 1):
                        if not self.is_running:
                            break
                        
                        mouse_controller.position = (x, y)
                        time.sleep(0.1)
                        mouse_controller.click(Button.left, 1)
                        self.log(f"  Clique #{idx} ({x}, {y})")
                        
                        if idx < len(self.coordinates) or loop_rep < loop_reps:
                            time.sleep(click_delay)
                    
                    if loop_rep < loop_reps:
                        time.sleep(click_delay)
                
                if total_rep < total_reps:
                    time.sleep(click_delay)
            
            if self.is_running:
                self.log("Concluído!")
                self.root.after(0, self.automation_finished)
            else:
                self.log("Interrompido.")
                self.root.after(0, self.automation_stopped)
                
        except Exception as e:
            self.log(f"Erro: {e}")
            self.root.after(0, self.automation_error)
    
    def automation_finished(self):
        """Callback quando automação termina"""
        self.is_running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="Status: Concluído", foreground="blue")
    
    def automation_stopped(self):
        """Callback quando automação é parada"""
        self.is_running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="Status: Parado", foreground="red")
    
    def automation_error(self):
        """Callback quando ocorre erro"""
        self.is_running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="Status: Erro", foreground="red")
    
    def stop_automation(self):
        """Para a automação"""
        self.is_running = False
        self.log("Parando...")
    
    def on_closing(self):
        """Callback ao fechar a janela"""
        self.is_running = False
        self.is_capturing = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.root.destroy()


def main():
    """Função principal"""
    root = tk.Tk()
    app = ClickAutomation(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
