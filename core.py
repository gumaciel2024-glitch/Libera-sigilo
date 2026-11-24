"""Regras e execução visual. Nenhuma integração interna com o SAJ."""
from __future__ import annotations
import json
import os
import re
import time
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
TARGETS = {
    'fluxo': '01 — Botão Fluxo de Trabalho',
    'pesquisar': '02 — Aba Pesquisar',
    'campo_processo': '03 — Rótulo Processo (ponto de clique no campo)',
    'consultar': '04 — Botão Consultar',
    'resultado_unico': '05 — Indicador Mostrando 1 de 1',
    'selecionar_processo': '06 — Caixa DESMARCADA da linha do resultado',
    'processo_marcado': '07 — Caixa MARCADA da linha do resultado',
    'pendencias': '08 — Título Pendências e Prazos do Processo',
    'autos': '10 — Título Visualização de Autos',
    'cadeado': 'Cadeado — botão habilitado',
    'remover_sigilo': 'Remover sigilo — opção do menu sem realce',
    'limpar': '16 — Limpar na Visualização de Autos',
    'campo_processo_autos': '17 — Processo vazio na Visualização de Autos',
}
BATCH_TARGETS = {'limpar', 'campo_processo_autos'}

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value or '').upper())
                   if unicodedata.category(c) != 'Mn').strip()

def digits(value):
    return re.sub(r'\D', '', str(value))

def query_number(processo):
    n = digits(processo)
    if len(n) != 20:
        raise ValueError('O processo deve conter 20 dígitos.')
    return n[:13]  # Campo com máscara: 0000000-00.0000. Sem Tab/Enter.

def read_sheet(path):
    from openpyxl import load_workbook
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(book.active.values)
        if not rows:
            raise ValueError('Planilha vazia.')
        if any(v is not None for row in rows for v in row[2:]):
            raise ValueError('Use somente duas colunas: processo e status.')
        first = [normalize(v) for v in rows[0][:2]]
        headers = {'PROCESSO', 'NUMERO DO PROCESSO', 'NUMERO PROCESSO'}
        start = 1 if first and first[0] in headers else 0
        result = []
        seen = set()
        for line, row in enumerate(rows[start:], start=start + 1):
            if not any(v is not None for v in row):
                continue
            original, status = (tuple(row) + (None, None))[:2]
            n = digits(original)
            error = ''
            if not isinstance(original, str) or len(n) != 20:
                error = 'Processo precisa ser Texto com 20 dígitos.'
            elif not re.fullmatch(r'[\d.\-\s]+', original):
                error = 'Processo contém caracteres inválidos.'
            elif normalize(status) != 'REMOVER SIGILO':
                error = 'Status deve ser REMOVER SIGILO.'
            elif n in seen:
                error = 'Processo repetido.'
            seen.add(n)
            result.append({'linha': line, 'processo': str(original or '').strip(),
                           'status': normalize(status), 'erro': error})
        # O prefixo consultado omite tribunal/origem; não executar colisões conhecidas.
        prefixes = {}
        for r in result:
            if not r['erro']:
                prefixes.setdefault(query_number(r['processo']), set()).add(digits(r['processo']))
        for r in result:
            if not r['erro'] and len(prefixes[query_number(r['processo'])]) > 1:
                r['erro'] = 'Prefixo de pesquisa coincide com outro processo da planilha.'
        if not result:
            raise ValueError('Não há processos na planilha.')
        return result
    finally:
        book.close()

class Journal:
    """Toda tentativa fica bloqueada até revisão manual, inclusive falhas."""
    def __init__(self, path):
        self.path = Path(path)

    def entries(self):
        if not self.path.exists():
            return []
        result = []
        for line in self.path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                result.append(json.loads(line))  # Corrupção impede execução silenciosa.
        return result

    def blocked(self):
        return {r['processo'] for r in self.entries()}

    def write(self, processo, state, phase, message=''):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {'data': time.strftime('%Y-%m-%d %H:%M:%S'), 'processo': digits(processo),
               'estado': state, 'etapa': phase, 'mensagem': message}
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())

def load_templates(config, keys, cv, np, base=BASE):
    """Leia caminhos Unicode com pathlib; OpenCV recebe bytes, não o caminho."""
    templates = {}
    for key in keys:
        item = config.get('targets', {}).get(key)
        if not item:
            raise ValueError('Calibre antes: ' + TARGETS.get(key, key))
        path = base / item['image']
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ValueError(
                'Imagem não encontrada ou sem acesso: ' + str(path) +
                '\nCapture novamente: ' + TARGETS.get(key, key)
            ) from exc
        try:
            image = cv.imdecode(np.frombuffer(data, dtype=np.uint8), cv.IMREAD_COLOR) if data else None
        except cv.error as exc:
            raise ValueError('Imagem inválida: ' + str(path)) from exc
        if image is None:
            raise ValueError('Imagem inválida: ' + str(path) +
                             '\nCapture novamente: ' + TARGETS.get(key, key))
        templates[key] = image
    return templates

class Stopped(RuntimeError):
    pass

class Visual:
    def __init__(self, config, stop, log, templates=None):
        import pyautogui
        import cv2
        import numpy
        self.pg, self.cv, self.np = pyautogui, cv2, numpy
        self.pg.FAILSAFE = True
        self.pg.PAUSE = .15
        self.config, self.stop, self.log = config, stop, log
        self.expected_window = None
        self.templates = templates if templates is not None else load_templates(config, set(config['targets']).intersection(TARGETS), cv2, numpy)

    def foreground(self):
        import ctypes
        from ctypes import wintypes
        get_window = ctypes.windll.user32.GetForegroundWindow
        get_window.restype = wintypes.HWND
        window = get_window()
        if not window:
            raise RuntimeError('Nenhuma janela ativa.')
        return window

    def check(self):
        if self.stop.is_set():
            raise Stopped('Parada solicitada; confira o SAJ antes de retomar.')
        self.pg.failSafeCheck()
        if self.expected_window and self.foreground() != self.expected_window:
            raise Stopped('A janela de autos perdeu o foco.')
        if list(self.pg.size()) != self.config['resolution']:
            raise RuntimeError('Resolução mudou. Recalibre as imagens.')

    def wait(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.check()
            self.stop.wait(min(.1, max(0, end - time.monotonic())))

    def find(self, key):
        self.check()
        item = self.config['targets'][key]
        template = self.templates[key]
        region = (0, 0, *self.pg.size()) if key == 'pendencias' else item['region']
        x, y, w, h = region
        shot = self.np.array(self.pg.screenshot(region=(x, y, w, h)))
        shot = self.cv.cvtColor(shot, self.cv.COLOR_RGB2BGR)
        if shot.shape[0] < template.shape[0] or shot.shape[1] < template.shape[1]:
            raise RuntimeError('Região inválida: ' + key)
        # SQDIFF evita a falsa certeza de CCOEFF com recortes de cor uniforme.
        scores = self.cv.matchTemplate(shot, template, self.cv.TM_SQDIFF_NORMED)
        matches = []
        for _ in range(2):
            best, _, loc, _ = self.cv.minMaxLoc(scores)
            if best > 1 - item.get('confidence', .97):
                break
            matches.append((x + loc[0], y + loc[1]))
            th, tw = template.shape[:2]
            lx, ly = loc
            scores[max(0, ly-th+1):ly+th, max(0, lx-tw+1):lx+tw] = 1
        if len(matches) > 1:
            raise RuntimeError('Mais de uma correspondência visual: ' + key)
        return matches[0] if matches else None

    def dismiss_pending(self):
        if self.find('pendencias') is None:
            return False
        self.log('Pendências reconhecidas. Pressionando Enter para fechar.')
        self.check()
        self.pg.press('enter')
        self.wait(.5)
        self.until_absent('pendencias', pending=False)
        self.log('Pendências fechadas. Continuando a execução.')
        return True

    def locate(self, key, timeout=25, pending=True):
        self.log('Aguardando imagem: ' + TARGETS[key])
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if pending:
                self.dismiss_pending()
            point = self.find(key)
            if point:
                return point
            self.wait(.3)
        raise RuntimeError('Não localizado: ' + TARGETS[key])

    def click_point(self, key, point):
        self.check()
        dx, dy = self.config['targets'][key]['offset']
        self.pg.click(point[0] + dx, point[1] + dy)
        self.wait(1)

    def click(self, key, pending=True):
        self.click_point(key, self.locate(key, pending=pending))

    def until_absent(self, key, timeout=25, pending=True):
        end = time.monotonic() + timeout
        misses = 0
        while time.monotonic() < end:
            if pending:
                self.dismiss_pending()
            misses = 0 if self.find(key) else misses + 1
            if misses >= 3:
                return
            self.wait(.4)
        raise RuntimeError('A janela permaneceu aberta: ' + TARGETS[key])

class Autos:
    """Read the document hierarchy exposed by Windows UI Automation."""

    def __init__(self, visual):
        from pywinauto import Desktop

        self.visual = visual
        self.desktop = Desktop(backend='uia')

    def load(self, processo):
        visual = self.visual
        end = time.monotonic() + 25
        while time.monotonic() < end:
            visual.dismiss_pending()
            window = visual.foreground()
            root = self.process_root(window, processo)
            if root is not None and root.children(control_type='TreeItem'):
                visual.expected_window = window
                visual.check()
                return window
            visual.wait(.4)
        raise Stopped(
            'O SAJ não expôs uma árvore de documentos com o número completo esperado.'
        )

    def process_root(self, window, processo):
        expected = digits(processo)
        dialog = self.desktop.window(handle=window).wrapper_object()
        candidates = []
        for tree in dialog.descendants(control_type='Tree'):
            for node in tree.children(control_type='TreeItem'):
                label = node.window_text().strip()
                if re.fullmatch(r'[0-9.\- ]+', label) and digits(label) == expected:
                    candidates.append(node)
        if len(candidates) > 1:
            raise Stopped('Mais de uma árvore contém o número completo do processo.')
        return candidates[0] if candidates else None

    def decisions(self, window, processo):
        self.visual.check()
        root = self.process_root(window, processo)
        if root is None:
            raise Stopped('O número completo do processo deixou de aparecer na árvore.')
        children = root.children(control_type='TreeItem')
        if not children:
            raise Stopped('A árvore do processo ainda não apresenta documentos.')
        sections = [node for node in children if normalize(node.window_text()) == 'PECAS SIGILOSAS']
        if len(sections) > 1:
            raise Stopped('Mais de uma seção Peças sigilosas foi encontrada.')
        public_count = sum(normalize(node.window_text()) == 'DECISAO' for node in children)
        if not sections:
            return [], public_count

        section = sections[0]
        if not section.is_expanded():
            self.visual.check()
            section.expand()
            # The SAJ can open a separate pending dialog while expanding the section.
            self.visual.expected_window = None
            try:
                self.visual.dismiss_pending()
            finally:
                self.visual.expected_window = window
            self.visual.check()
            if not section.is_expanded():
                raise Stopped('Não foi possível abrir Peças sigilosas.')
        items = section.children(control_type='TreeItem')
        if not items:
            raise Stopped('Peças sigilosas está visível, mas sua lista não pôde ser lida.')
        decisions = [node for node in items if normalize(node.window_text()) == 'DECISAO']
        return decisions, public_count

    def verify_removal(self, window, processo, before):
        end = time.monotonic() + 15
        while time.monotonic() < end:
            decisions, public_count = self.decisions(window, processo)
            if not decisions and public_count == before + 1:
                return
            self.visual.wait(.4)
        raise Stopped('Remoção sem confirmação na árvore dos autos. Confira o histórico e o SAJ.')


class Runner:
    def __init__(self, visual, autos, journal, log, update):
        self.v, self.autos = visual, autos
        self.journal, self.log, self.update = journal, log, update

    def run(self, records, release):
        phase = 'preparação'
        for index, r in enumerate(records):
            p = r['processo']
            if r['erro'] or digits(p) in self.journal.blocked():
                raise RuntimeError('Processo inválido ou já tentado: ' + p)
            phase = 'início'
            self.journal.write(p, 'iniciado', phase)
            try:
                def step(name):
                    nonlocal phase
                    phase = name
                    self.log(f'{p} — {name}')
                    self.update(index, name)
                if index == 0:
                    step('abrir Fluxo de Trabalho')
                    self.v.click('fluxo')
                    self.v.click('pesquisar')
                    step('consultar processo')
                    self.v.click('campo_processo')
                    self.v.check()
                    self.v.pg.hotkey('ctrl', 'a')
                    self.v.pg.write(query_number(p), interval=.12)
                    self.v.wait(1)
                    self.v.click('consultar')
                    step('aguardar resultado único da pesquisa — imagem 05')
                    self.v.locate('resultado_unico')
                    step('clicar na caixa do processo — imagem 06')
                    self.v.click('selecionar_processo')
                    step('confirmar caixa marcada — imagem 07')
                    self.v.locate('processo_marcado')
                    step('abrir autos com F12')
                    self.v.check()
                    self.v.pg.press('f12')
                    self.v.locate('autos')
                else:
                    step('limpar autos para o próximo processo — imagem 16')
                    self.v.click('limpar')
                    step('aguardar campo Processo vazio nos autos — imagem 17')
                    self.v.click('campo_processo_autos')
                    self.v.check()
                    self.v.pg.hotkey('ctrl', 'a')
                    self.v.pg.write(query_number(p), interval=.12)
                    self.v.expected_window = None
                    step('aguardar visualização de autos')
                    self.v.locate('autos')
                step('conferir número completo e localizar decisão sigilosa')
                window = self.autos.load(p)
                decisions, public_count = self.autos.decisions(window, p)
                if not decisions:
                    self.journal.write(p, 'sem_decisao', phase)
                    self.update(index, 'Sem decisão sigilosa')
                    continue
                if len(decisions) > 1:
                    raise Stopped('Há mais de uma decisão sigilosa neste processo.')

                step('selecionar decisão e abrir menu do cadeado')
                self.v.check()
                decisions[0].select()
                selected, current_count = self.autos.decisions(window, p)
                if len(selected) != 1 or current_count != public_count or not selected[0].is_selected():
                    raise Stopped('A seleção da decisão sigilosa não pôde ser conferida.')
                self.v.click('cadeado', pending=False)
                self.v.locate('remover_sigilo', pending=False)
                if not release:
                    self.journal.write(p, 'ensaio', phase)
                    self.update(index, 'Ensaio — menu aberto')
                    return

                step('acionar Remover sigilo')
                self.journal.write(p, 'remocao_solicitada', phase)
                self.v.click('remover_sigilo', pending=False)
                self.v.until_absent('remover_sigilo', pending=False)
                step('verificar remoção na árvore dos autos')
                self.autos.verify_removal(window, p, public_count)
                self.journal.write(p, 'remocao_conferida', phase)
                self.update(index, 'Remoção conferida automaticamente')
            except Exception as exc:
                self.journal.write(p, 'interrompido', phase, str(exc))
                self.update(index, 'Interrompido — conferir SAJ')
                raise
