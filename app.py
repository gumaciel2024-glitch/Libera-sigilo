"""SAJ — Remoção de sigilo de decisões, versão 0.1. Interface local para Windows."""
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core import BASE, TARGETS, BATCH_TARGETS, Journal, Visual, Autos, Runner, read_sheet, digits, load_templates

CONFIG = BASE / 'calibracao.json'

class App:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.running = False
        self.calibrating = False
        self.records = []
        self.config = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {'targets': {}}
        self.journal = Journal(BASE / 'dados' / 'historico.jsonl')
        self.path = tk.StringVar()
        self.release = tk.BooleanVar(value=False)
        root.title('SAJ | Remoção de sigilo de decisões — 0.3')
        root.geometry('1080x750')
        ttk.Label(root, text='Remoção de sigilo de decisões', font=('Segoe UI', 18, 'bold')).pack(anchor='w', padx=18, pady=15)
        ttk.Label(root, text='Mouse, teclado e imagens | Comece na tela inicial do SAJ maximizado.').pack(anchor='w', padx=18)
        row = ttk.Frame(root); row.pack(fill='x', padx=18, pady=15)
        ttk.Entry(row, textvariable=self.path).pack(side='left', fill='x', expand=True)
        ttk.Button(row, text='Selecionar .xlsx', command=self.select).pack(side='left', padx=5)
        ttk.Button(row, text='Conferir planilha', command=self.load).pack(side='left')
        self.table = ttk.Treeview(root, columns=('linha', 'processo', 'status', 'resultado'), show='headings', selectmode='browse')
        for key, label, width in [('linha', 'Linha', 55), ('processo', 'Processo', 250), ('status', 'Status', 100), ('resultado', 'Validação / execução', 580)]:
            self.table.heading(key, text=label); self.table.column(key, width=width)
        self.table.pack(fill='both', expand=True, padx=18)
        row = ttk.Frame(root); row.pack(fill='x', padx=18, pady=12)
        ttk.Button(row, text='Calibrar imagens', command=self.calibrate).pack(side='left')
        ttk.Button(row, text='Abrir histórico', command=self.history).pack(side='left', padx=8)
        ttk.Checkbutton(row, text='Remover sigilo (desmarcado = ensaio até abrir o menu)', variable=self.release).pack(side='left', padx=8)
        row = ttk.Frame(root); row.pack(fill='x', padx=18)
        ttk.Button(row, text='Executar selecionado', command=lambda: self.start(False)).pack(side='left')
        ttk.Button(row, text='Executar lote pendente', command=lambda: self.start(True)).pack(side='left', padx=8)
        ttk.Button(row, text='PARAR', command=self.stop.set).pack(side='left')
        ttk.Label(root, text='Emergência: mouse no canto superior esquerdo. Mantenha o SAJ em primeiro plano durante a execução.').pack(anchor='w', padx=18, pady=10)
        self.log = tk.Text(root, height=10, state='disabled', font=('Consolas', 10))
        self.log.pack(fill='x', padx=18, pady=(0, 15))
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def busy(self):
        return self.running or self.calibrating

    def select(self):
        if self.busy(): return
        p = filedialog.askopenfilename(filetypes=[('Planilha Excel', '*.xlsx')])
        if p: self.path.set(p)

    def load(self):
        if self.busy(): return
        try:
            records = read_sheet(self.path.get())
            blocked = self.journal.blocked()
            self.table.delete(*self.table.get_children())
            self.records = records
            for i, r in enumerate(records):
                state = r['erro'] or ('Já tentado — revisar histórico' if digits(r['processo']) in blocked else 'Pronto')
                self.table.insert('', 'end', iid=str(i), values=(r['linha'], r['processo'], r['status'], state))
            self.say(f'{len(records)} linhas carregadas; somente status REMOVER SIGILO é elegível.')
        except Exception as exc:
            messagebox.showerror('Planilha', str(exc))

    def say(self, text): self.events.put(('log', text))

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'log':
                    self.log.configure(state='normal'); self.log.insert('end', data + '\n'); self.log.see('end'); self.log.configure(state='disabled')
                elif kind == 'row': self.table.set(str(data[0]), 'resultado', data[1])
                elif kind == 'done':
                    self.running = False
                    self.root.deiconify()
                    self.say(data)
        except queue.Empty: pass
        self.root.after(100, self.poll)

    def history(self):
        if self.busy(): return
        folder = BASE / 'dados'; folder.mkdir(exist_ok=True)
        if os.name == 'nt': os.startfile(str(folder))
        else: messagebox.showinfo('Histórico', str(folder))

    def calibrate(self):
        if self.busy(): return
        win = tk.Toplevel(self.root); win.title('Calibração visual'); win.geometry('800x720'); win.grab_set()
        ttk.Label(win, text='Abra manualmente cada etapa no SAJ, depois capture a referência correspondente.\nRecorte somente elementos fixos; evite números de processo e datas.\nCaixas: recorte a caixa e sua borda. Capture marcada e desmarcada separadamente.\nApós o recorte, clique no ponto que receberá o clique (pode ficar fora do recorte).', wraplength=760).pack(padx=15, pady=15)
        for key, label in TARGETS.items():
            row = ttk.Frame(win); row.pack(fill='x', padx=15, pady=3)
            status = tk.StringVar(value='✓' if key in self.config['targets'] else '—')
            ttk.Label(row, textvariable=status, width=3).pack(side='left')
            ttk.Label(row, text=label).pack(side='left')
            ttk.Button(row, text='Capturar', command=lambda k=key, s=status: self.capture(win, k, s)).pack(side='right')
        ttk.Label(win, text='Limpar e Processo vazio são usados no lote. Capture Limpar e o campo Processo vazio na Visualização de Autos.\nO indicador “Mostrando 1 de 1” deve ser recortado inteiro.\nPendências: capture somente o título. Remover sigilo: capture a opção inteira.\nMantenha resolução, escala do Windows e tamanho dos painéis após calibrar.', wraplength=760).pack(pady=15)

    def capture(self, win, key, status):
        if self.busy(): return
        try:
            import pyautogui as pg
            from PIL import ImageTk
        except ImportError as exc:
            messagebox.showerror('Dependências', str(exc)); return
        self.calibrating = True
        win.grab_release(); win.withdraw(); self.root.withdraw()
        def restore():
            self.calibrating = False
            self.root.deiconify(); win.deiconify(); win.grab_set()
        def photo():
            try:
                image = pg.screenshot()
                overlay = tk.Toplevel(self.root); overlay.overrideredirect(True)
                overlay.geometry(f'{image.width}x{image.height}+0+0'); overlay.attributes('-topmost', True)
                canvas = tk.Canvas(overlay, highlightthickness=0, cursor='crosshair'); canvas.pack(fill='both', expand=True)
                canvas.picture = ImageTk.PhotoImage(image)
                canvas.create_image(0, 0, image=canvas.picture, anchor='nw')
                note = canvas.create_text(20, 20, anchor='nw', fill='red', font=('Segoe UI', 15, 'bold'), text='Arraste para recortar a referência. Esc cancela.')
                state = {}
                def cancel(event=None): overlay.destroy(); restore()
                def down(event):
                    if 'box' in state:
                        save(event); return
                    state['start'] = (event.x, event.y)
                    state['rect'] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)
                def drag(event):
                    if 'box' not in state and 'start' in state:
                        canvas.coords(state['rect'], *state['start'], event.x, event.y)
                def up(event):
                    if 'box' in state or 'start' not in state: return
                    x1, x2 = sorted((state['start'][0], event.x)); y1, y2 = sorted((state['start'][1], event.y))
                    if x2-x1 < 6 or y2-y1 < 6:
                        state.pop('start', None); return
                    state['box'] = (x1, y1, x2, y2)
                    canvas.itemconfigure(note, text='Agora clique no ponto de ação. Para título/indicador, clique no centro do recorte.')
                def save(event):
                    try:
                        x1, y1, x2, y2 = state['box']
                        resolution = [image.width, image.height]
                        if self.config.get('resolution', resolution) != resolution:
                            raise ValueError('Resolução diferente da calibração anterior. Restaure a resolução original.')
                        folder = BASE / 'imagens'; folder.mkdir(exist_ok=True)
                        relative = f'imagens/{key}.png'; image.crop(state['box']).save(BASE / relative)
                        # Região estreita mantém caixas genéricas vinculadas à posição calibrada.
                        margin = 3 if key in {'selecionar_processo', 'processo_marcado'} else 16
                        left, top = max(0, x1-margin), max(0, y1-margin)
                        right, bottom = min(image.width, x2+margin), min(image.height, y2+margin)
                        if key == 'remover_sigilo':
                            top, bottom = 0, image.height
                        self.config['resolution'] = resolution
                        self.config['targets'][key] = {'image': relative, 'region': [left, top, right-left, bottom-top], 'offset': [event.x-x1, event.y-y1], 'confidence': .97}
                        temp = CONFIG.with_suffix('.tmp'); temp.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding='utf-8'); temp.replace(CONFIG)
                        status.set('✓'); self.say('Calibrado: ' + TARGETS[key])
                    except Exception as exc: messagebox.showerror('Calibração', str(exc), parent=overlay)
                    finally: cancel()
                canvas.bind('<ButtonPress-1>', down); canvas.bind('<B1-Motion>', drag); canvas.bind('<ButtonRelease-1>', up)
                overlay.bind('<Escape>', cancel); overlay.grab_set(); overlay.focus_force()
            except Exception as exc:
                restore(); messagebox.showerror('Captura', str(exc))
        self.root.after(4000, photo)

    def start(self, batch):
        if self.busy(): return
        if os.name != 'nt':
            messagebox.showerror('Windows', 'Esta automação foi preparada para Windows.'); return
        try:
            import pyautogui
            import cv2
            import numpy
            blocked = self.journal.blocked()
            ids = list(self.table.get_children()) if batch else list(self.table.selection())
            ids = [i for i in ids if not self.records[int(i)]['erro'] and digits(self.records[int(i)]['processo']) not in blocked and self.table.set(i, 'resultado') == 'Pronto']
            if not ids: raise ValueError('Selecione uma linha pronta, ou carregue uma planilha com processos pendentes.')
            release = self.release.get()
            if batch and not release: raise ValueError('Faça o ensaio individual. Para lote, marque Remover sigilo.')
            needed = set(TARGETS) - (BATCH_TARGETS if len(ids) == 1 else set())
            missing = [TARGETS[k] for k in TARGETS if k in needed and k not in self.config['targets']]
            if missing: raise ValueError('Calibre antes:\n' + '\n'.join(missing))
            templates = load_templates(self.config, needed, cv2, numpy)
            if list(pyautogui.size()) != self.config['resolution']: raise ValueError('Resolução diferente da calibração.')
        except Exception as exc:
            messagebox.showerror('Preparação', str(exc)); return
        self.running = True; self.stop.clear()
        records = [dict(self.records[int(i)]) for i in ids]
        config = json.loads(json.dumps(self.config))
        self.root.iconify()
        def work():
            try:
                visual = Visual(config, self.stop, self.say, templates=templates)
                self.say('Início em 5 segundos. Volte à tela inicial do SAJ.')
                visual.wait(5)
                runner = Runner(visual, Autos(visual), self.journal, self.say, lambda i, text: self.events.put(('row', (ids[i], text))))
                runner.run(records, release=release)
                message = 'Execução encerrada. Confira os resultados no SAJ.'
            except Exception as exc:
                self.say('Interrompido: ' + str(exc)); message = 'Execução interrompida:\n' + str(exc)
            self.events.put(('done', message))
        threading.Thread(target=work, daemon=True).start()

    def close(self):
        if self.running:
            self.stop.set()
            return
        if not self.calibrating: self.root.destroy()

if __name__ == '__main__':
    # Coordenadas da captura e do mouse em pixels físicos no Windows.
    if os.name == 'nt':
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    # Trava do Windows, liberada pelo sistema ao encerrar ou cair.
    root = tk.Tk()
    lock = None
    try:
        if os.name == 'nt':
            import msvcrt
            lock = (BASE / '.instancia-sigilo.lock').open('a+b')
            lock.seek(0, 2)
            if lock.tell() == 0:
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        App(root)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror('Não foi possível iniciar', str(exc) + '\nVerifique se outra instância já está aberta.')
        root.destroy()
    finally:
        if lock: lock.close()
