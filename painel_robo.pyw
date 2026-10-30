import sys
import os
import io
import re
import time
import gc
import random
import unicodedata
import difflib
import warnings
import threading
from datetime import datetime, timedelta

import pandas as pd
import pyautogui
import pyperclip
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Importa Playwright mantido por compatibilidade
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    PLAYWRIGHT_DISPONIVEL = False

# Importa keyboard para atalho universal de emergência, se disponível
try:
    import keyboard
    KEYBOARD_DISPONIVEL = True
except ImportError:
    KEYBOARD_DISPONIVEL = False

# Oculta avisos do openpyxl no terminal
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ==============================================================================
# CONFIGURAÇÃO EXTERNA (nada sensível fica no código)
# Copie config.exemplo.json para config.json e preencha com seus dados.
# ==============================================================================
def _carregar_config():
    import json
    pasta = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    cfg = {}
    caminho = os.path.join(pasta, "config.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    return cfg

CONFIG = _carregar_config()

# Bibliotecas de Autenticação do Google
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Configuração visual do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ==============================================================================
# IDENTIDADE VISUAL
# ==============================================================================
TEMA_ATUAL = "cockpit"
LAYOUT_ATUAL = "cockpit"
DENSIDADE_ATUAL = "confortavel"

COMPACTO = DENSIDADE_ATUAL == "compacto"
ALT_BOTAO = 32 if COMPACTO else 36
ALT_RODAPE = 36 if COMPACTO else 42
DASHBOARD = LAYOUT_ATUAL in ("dashboard", "cockpit")
ALT_LINHA = 24 if COMPACTO else (26 if DASHBOARD else 30)
RAIO_CARD = 6 if DASHBOARD else 12
RAIO_CTRL = 4 if DASHBOARD else 8
RAIO_BOTAO = 20 if LAYOUT_ATUAL == "cockpit" else RAIO_CTRL

TEMAS = {
    "violeta": dict(
        fundo="#0E0B1F", painel="#171333", painel_alt="#1F1A45", borda="#2F2966",
        texto="#ECE9FF", texto_suave="#A39BD0", destaque="#B49CFF",
        primario="#6D4AE0", primario_hover="#8061F0", sobre_primario="#FFFFFF", desab="#A495E6",
        hover="#2B2468", borda_sec="#5B47B5", borda_forte="#5A50A8", placeholder="#6F68A6",
        selecao="#2D2570", scroll="#3B3485",
        sucesso="#4ADE80", alerta="#FBBF24", aviso="#FB923C", erro="#FB7185", perigo="#F43F5E",
        perigo_fundo="#3A1426", perigo_hover="#55203A", perigo_texto="#FDA4AF", perigo_desab="#7D5A6B",
        aba_barra="#171333", aba_sel="#6D4AE0", aba_sel_hover="#8061F0", aba_nao_sel="#171333", aba_nao_hover="#1F1A45",
    ),
    "oceano": dict(
        fundo="#0A1720", painel="#102330", painel_alt="#162E3E", borda="#25435A",
        texto="#E4F1F7", texto_suave="#8FAEC0", destaque="#5EEAD4",
        primario="#0F8B8D", primario_hover="#13A3A5", sobre_primario="#FFFFFF", desab="#7FC9CA",
        hover="#1D3F54", borda_sec="#1E7C84", borda_forte="#3E6580", placeholder="#56788E",
        selecao="#174A5C", scroll="#2A4D63",
        sucesso="#4ADE80", alerta="#FBBF24", aviso="#FB923C", erro="#F87171", perigo="#F43F5E",
        perigo_fundo="#34161F", perigo_hover="#4F212E", perigo_texto="#FDA4AF", perigo_desab="#7A5B63",
        aba_barra="#102330", aba_sel="#0F8B8D", aba_sel_hover="#13A3A5", aba_nao_sel="#102330", aba_nao_hover="#162E3E",
    ),
    "cockpit": dict(
        fundo="#052A47", painel="#08334F", painel_alt="#0A3A5F", borda="#1B5683",
        texto="#EAF2FA", texto_suave="#9DB7D0", destaque="#22C7B8",
        primario="#EC1E79", primario_hover="#F2459A", sobre_primario="#FFFFFF", desab="#F4A3C6",
        hover="#12486F", borda_sec="#1E9AA0", borda_forte="#3A6B96", placeholder="#6F8DAE",
        selecao="#12486F", scroll="#1B5683",
        sucesso="#34D399", alerta="#FBBF24", aviso="#FB923C", erro="#FF6B6B", perigo="#FF6B6B",
        perigo_fundo="#3B1F33", perigo_hover="#55283F", perigo_texto="#FF8A8A", perigo_desab="#8A5C63",
        aba_barra="#08334F", aba_sel="#EC1E79", aba_sel_hover="#F2459A", aba_nao_sel="#08334F", aba_nao_hover="#0A3A5F",
        lateral_fundo="#003F6B", lateral_borda="#1B5683", lateral_texto="#B9CFE6", lateral_titulo="#FFFFFF",
        lateral_hover="#0F5185", lateral_ativo="#EC1E79",
        marca="#EC1E79",
    ),
    "dashboard": dict(
        fundo="#EEF1F6", painel="#FFFFFF", painel_alt="#F5F7FB", borda="#D5DCE8",
        texto="#18233A", texto_suave="#5B6B86", destaque="#2563EB",
        primario="#2563EB", primario_hover="#1D4ED8", sobre_primario="#FFFFFF", desab="#A9C0F5",
        hover="#E3E9F4", borda_sec="#9DB7EE", borda_forte="#9AA9C2", placeholder="#8C9AB3",
        selecao="#DBE7FF", scroll="#BCC8DC",
        sucesso="#15803D", alerta="#B45309", aviso="#C2410C", erro="#B91C1C", perigo="#DC2626",
        perigo_fundo="#FFFFFF", perigo_hover="#FEE2E2", perigo_texto="#B91C1C", perigo_desab="#D9A3A3",
        aba_barra="#E2E8F2", aba_sel="#FFFFFF", aba_sel_hover="#FFFFFF", aba_nao_sel="#E2E8F2", aba_nao_hover="#D3DCEA",
        lateral_fundo="#4B6A9B", lateral_borda="#6682B3", lateral_texto="#E6EDF8", lateral_titulo="#FFFFFF",
        lateral_hover="#5B7BB0", lateral_ativo="#2A5DDB",
    ),
    "claro": dict(
        fundo="#EDF1F7", painel="#FFFFFF", painel_alt="#F3F6FB", borda="#D3DCEA",
        texto="#18233A", texto_suave="#5B6B86", destaque="#2563EB",
        primario="#2563EB", primario_hover="#1D4ED8", sobre_primario="#FFFFFF", desab="#A9C0F5",
        hover="#E3EBF8", borda_sec="#9DB7EE", borda_forte="#9AA9C2", placeholder="#8C9AB3",
        selecao="#DBE7FF", scroll="#BCC8DC",
        sucesso="#15803D", alerta="#B45309", aviso="#C2410C", erro="#B91C1C", perigo="#DC2626",
        perigo_fundo="#FEE2E2", perigo_hover="#FECACA", perigo_texto="#B91C1C", perigo_desab="#D9A3A3",
        aba_barra="#E2E8F2", aba_sel="#FFFFFF", aba_sel_hover="#FFFFFF", aba_nao_sel="#E2E8F2", aba_nao_hover="#D3DCEA",
    ),
}
_t = TEMAS.get(TEMA_ATUAL, TEMAS["violeta"])

COR_FUNDO = _t["fundo"]
COR_PAINEL = _t["painel"]
COR_PAINEL_ALT = _t["painel_alt"]
COR_BORDA = _t["borda"]
COR_TEXTO = _t["texto"]
COR_TEXTO_SUAVE = _t["texto_suave"]
COR_DESTAQUE = _t["destaque"]
COR_PRIMARIO = _t["primario"]
COR_PRIMARIO_HOVER = _t["primario_hover"]
COR_SOBRE_PRIMARIO = _t["sobre_primario"]
COR_DESAB = _t["desab"]
COR_HOVER = _t["hover"]
COR_BORDA_SEC = _t["borda_sec"]
COR_BORDA_FORTE = _t["borda_forte"]
COR_PLACEHOLDER = _t["placeholder"]
COR_SELECAO = _t["selecao"]
COR_SCROLL = _t["scroll"]
COR_SUCESSO = _t["sucesso"]
COR_ALERTA = _t["alerta"]
COR_AVISO = _t["aviso"]
COR_ERRO = _t["erro"]
COR_PERIGO = _t["perigo"]
COR_PERIGO_FUNDO = _t["perigo_fundo"]
COR_PERIGO_HOVER = _t["perigo_hover"]
COR_PERIGO_TEXTO = _t["perigo_texto"]
COR_PERIGO_DESAB = _t["perigo_desab"]
COR_LAT_FUNDO = _t.get("lateral_fundo", COR_PAINEL)
COR_LAT_BORDA = _t.get("lateral_borda", COR_BORDA)
COR_LAT_TEXTO = _t.get("lateral_texto", COR_TEXTO_SUAVE)
COR_LAT_TITULO = _t.get("lateral_titulo", COR_TEXTO)
COR_LAT_HOVER = _t.get("lateral_hover", COR_HOVER)
COR_LAT_ATIVO = _t.get("lateral_ativo", COR_PRIMARIO)
COR_MARCA = _t.get("marca", COR_DESTAQUE)

FONTE_UI = "Segoe UI"
FONTE_MONO = "Consolas"

def filtrar_estilo(widget_cls, estilo):
    import inspect
    try:
        aceitos = set(inspect.signature(widget_cls.__init__).parameters)
    except (TypeError, ValueError):
        return estilo
    return {k: v for k, v in estilo.items() if k in aceitos}

ESTILO_CHECKBOX = dict(
    fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER, border_color=COR_DESTAQUE,
    checkmark_color=COR_SOBRE_PRIMARIO, text_color=COR_TEXTO, font=(FONTE_UI, 12),
    corner_radius=4, border_width=2, checkbox_width=18, checkbox_height=18,
)
ESTILO_RADIO = dict(
    fg_color=COR_DESTAQUE, hover_color=COR_PRIMARIO_HOVER, border_color=COR_BORDA_FORTE,
    text_color=COR_TEXTO, font=(FONTE_UI, 12), radio_button_width=18, radio_button_height=18,
    border_width_unchecked=2, border_width_checked=5,
)
ESTILO_ENTRY = dict(
    fg_color=COR_FUNDO, border_color=COR_BORDA, text_color=COR_TEXTO,
    placeholder_text_color=COR_PLACEHOLDER, font=(FONTE_MONO, 12),
    height=34, corner_radius=RAIO_CTRL, border_width=1,
)
ESTILO_BOTAO_PRIMARIO = dict(
    fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER, text_color=COR_SOBRE_PRIMARIO,
    text_color_disabled=COR_DESAB, border_width=1, border_color=COR_MARCA, corner_radius=RAIO_BOTAO,
)
ESTILO_BOTAO_SECUNDARIO = dict(
    fg_color=COR_PAINEL_ALT, hover_color=COR_HOVER, text_color=COR_DESTAQUE,
    text_color_disabled=COR_DESAB, border_width=1, border_color=COR_BORDA_SEC, corner_radius=RAIO_CTRL,
)
ESTILO_BOTAO_PERIGO = dict(
    fg_color=COR_PERIGO_FUNDO, hover_color=COR_PERIGO_HOVER, text_color=COR_PERIGO_TEXTO,
    text_color_disabled=COR_PERIGO_DESAB, border_width=1, border_color=COR_PERIGO, corner_radius=RAIO_BOTAO,
)
ESTILO_BOTAO_DISCRETO = dict(
    fg_color="transparent", hover_color=COR_PAINEL_ALT, text_color=COR_TEXTO_SUAVE,
    border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL,
)

ESTILO_CHECKBOX = filtrar_estilo(ctk.CTkCheckBox, ESTILO_CHECKBOX)
ESTILO_RADIO = filtrar_estilo(ctk.CTkRadioButton, ESTILO_RADIO)
ESTILO_ENTRY = filtrar_estilo(ctk.CTkEntry, ESTILO_ENTRY)
ESTILO_BOTAO_PRIMARIO = filtrar_estilo(ctk.CTkButton, ESTILO_BOTAO_PRIMARIO)
ESTILO_BOTAO_SECUNDARIO = filtrar_estilo(ctk.CTkButton, ESTILO_BOTAO_SECUNDARIO)
ESTILO_BOTAO_PERIGO = filtrar_estilo(ctk.CTkButton, ESTILO_BOTAO_PERIGO)
ESTILO_BOTAO_DISCRETO = filtrar_estilo(ctk.CTkButton, ESTILO_BOTAO_DISCRETO)

ESTILO_BOTAO_ATUALIZAR = filtrar_estilo(ctk.CTkButton, dict(
    fg_color="transparent", hover_color=COR_HOVER, text_color=COR_DESTAQUE, text_color_disabled=COR_DESAB,
    border_width=1, border_color=COR_DESTAQUE, corner_radius=RAIO_BOTAO,
))
ESTILO_SEGMENTADO = filtrar_estilo(ctk.CTkSegmentedButton, dict(
    height=24, font=(FONTE_UI, 11), corner_radius=RAIO_BOTAO, border_width=1,
    fg_color=COR_FUNDO, selected_color=COR_PRIMARIO, selected_hover_color=COR_PRIMARIO_HOVER,
    unselected_color=COR_FUNDO, unselected_hover_color=COR_HOVER, text_color=COR_TEXTO,
))

def categoria_status(status):
    if "Erro" in status or "❌" in status:
        return "erro"
    if "Pendente" in status:
        return "pendente"
    if "Enviando" in status or "Buscando" in status or "Executando" in status:
        return "andamento"
    if "Enviado" in status or "Concluído" in status or "Já Confirmado" in status:
        return "ok"
    return "outro"

def limpar_texto_log(texto):
    return "".join(c for c in texto if ord(c) < 0x2000).strip()

def aplicar_estilo_tabelas():
    style = ttk.Style()
    style.theme_use("clam")
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview", background=COR_PAINEL, foreground=COR_TEXTO, fieldbackground=COR_PAINEL,
                    rowheight=ALT_LINHA, borderwidth=0, relief="flat", font=(FONTE_MONO, 10))
    style.map("Treeview", background=[("selected", COR_SELECAO)], foreground=[("selected", COR_TEXTO)])
    style.configure("Treeview.Heading", background=COR_PAINEL_ALT, foreground=COR_DESTAQUE,
                    font=(FONTE_UI, 10, "bold"), relief="flat", borderwidth=0, padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", COR_HOVER)])
    style.configure("Vertical.TScrollbar", background=COR_SCROLL, troughcolor=COR_FUNDO, bordercolor=COR_FUNDO,
                    lightcolor=COR_SCROLL, darkcolor=COR_SCROLL, arrowcolor=COR_TEXTO_SUAVE, relief="flat")
    style.map("Vertical.TScrollbar", background=[("active", COR_PRIMARIO)])

pyautogui.FAILSAFE = True

# ==============================================================================
# CONFIGURAÇÕES COMPARTILHADAS DA AUTOMAÇÃO
# ==============================================================================

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
ID_PLANILHA = CONFIG.get("id_planilha") or os.environ.get("ID_PLANILHA", "")

ABAS_IGNORADAS_SISTEMA = [
    "MULTI", "INSTRUCOES", "INSTRUÇÕES", "LEIA-ME", "LEIAME",
    "BASE", "RESUMO", "DASHBOARD", "AJUDA", "CONFIG", "CONFIGURAÇÕES",
    "PACIENTES", "PACIENTE", "OBSERVACOES", "OBSERVAÇÕES",
    "LOG", "LOGS", "METRICAS", "MÉTRICAS"
]

# Grupos que o robô deve ignorar (definidos em config.json, chave "grupos_bloqueados")
GRUPOS_BLOQUEADOS = CONFIG.get("grupos_bloqueados", [])

TERMOS_INVALIDOS_PLANTAO = [
    "PENDENTE",
    "HOSPITALIZADO",
    "COBERTURA",
    "COBERTURA SOLICITADA"
]

# ==============================================================================
# FUNÇÕES DE TRATAMENTO, LIMPEZA E GOOGLE API
# ==============================================================================

def limpar_memoria():
    gc.collect()

def remover_acentos(texto):
    if not texto:
        return ""
    texto = str(texto).replace("'", "").replace("`", "").replace("’", "")
    texto_norm = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in texto_norm if unicodedata.category(c) != "Mn")
    return re.sub(r'[^A-ZA-Z0-9\s]', ' ', sem_acento).upper().strip()

def limpar_texto(texto):
    if texto is None or pd.isna(texto):
        return ""
    texto = str(texto).replace('\xa0', ' ').strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return "".join(c for c in texto if c.isalnum() or c in " -/()")

def normalizar_nome_busca(nome):
    if not nome:
        return ""
    nome_limpo = str(nome).replace('\xa0', ' ').strip()
    nome_base = nome_limpo.split("(")[0].strip()
    return remover_acentos(nome_base)

def eh_aba_ssa(nome_aba):
    aba_clean = limpar_texto(nome_aba).replace(" ", "")
    return aba_clean in ["SSADF", "SSA", "SSADFDF"] or aba_clean.startswith("SSADF")

def eh_aba_convenio_valida(nome_aba):
    aba_bruta = str(nome_aba).strip()
    if aba_bruta.startswith("_"):
        return False
    aba_clean = remover_acentos(aba_bruta)
    for ignorada in ABAS_IGNORADAS_SISTEMA:
        if ignorada in aba_clean:
            return False
    return True

def status_eh_ok(valor_status):
    if valor_status is None or pd.isna(valor_status):
        return False
    texto = unicodedata.normalize("NFD", str(valor_status).replace('\xa0', ' ').strip().upper())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto_limpo = "".join(c for c in texto if c.isalnum() or c == " ")
    
    status_validos = [
        "OK", "ATIVO", "SIM", "CONFIRMADO", "LIBERADO",
        "EM ANDAMENTO", "EM ATENDIMENTO", "CHECK-IN", "CHECKIN", "AGUARDANDO"
    ]
    return any(st in texto_limpo for st in status_validos)

def valor_eh_plantao_confirmado(valor):
    if valor is None or pd.isna(valor):
        return False
    val_str = remover_acentos(str(valor))
    if not val_str or val_str in ["NAN", "NONE", ""]:
        return False
    
    for termo in TERMOS_INVALIDOS_PLANTAO:
        if remover_acentos(termo) in val_str:
            return False
            
    return True

def grupo_esta_bloqueado(nome_grupo):
    if not nome_grupo:
        return True
    nome_norm = remover_acentos(nome_grupo)
    for bloqueado in GRUPOS_BLOQUEADOS:
        bloqueado_norm = remover_acentos(bloqueado)
        if bloqueado_norm in nome_norm or nome_norm == bloqueado_norm:
            return True
    return False

def contem_palavra_pendente(valor):
    if valor is None or pd.isna(valor):
        return False
    val_str = remover_acentos(str(valor))
    return "PENDENTE" in val_str

# ==============================================================================
# COMMAND CENTER WEB: REGRAS DE CASAMENTO (planilha x painel) E LEITURA DA TABELA
# ==============================================================================
def normalizar_para_comparar(texto):
    if texto is None:
        return ""
    t = unicodedata.normalize("NFD", str(texto).replace("'", "").replace("`", "").replace("’", ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").upper()
    return re.sub(r"[^A-Z0-9\s]", " ", t).strip()

PARTICULAS_NOME = {"DE", "DA", "DO", "DAS", "DOS", "E", "DI", "DU"}

JS_LER_TABELA = """
() => {
  const cab = Array.from(document.querySelectorAll('thead th')).map(th => (th.innerText || '').trim());
  const dados = Array.from(document.querySelectorAll('tbody tr')).map(tr =>
    Array.from(tr.querySelectorAll('td')).map(td => (td.innerText || '').trim()));
  return { cab: cab, dados: dados };
}
"""

JS_LINHAS_MARCADAS = """
() => Array.from(document.querySelectorAll('tbody tr'))
  .map((tr, i) => { const c = tr.querySelector('input[type="checkbox"]'); return (c && c.checked) ? i : -1; })
  .filter(i => i >= 0)
"""

def tokens_nome_paciente(nome):
    if nome is None:
        return []
    base = str(nome).replace('\xa0', ' ').split("(")[0]
    return [t for t in normalizar_para_comparar(base).split() if t not in PARTICULAS_NOME]

def nomes_compativeis(nome_planilha, nome_painel):
    a = tokens_nome_paciente(nome_planilha)
    b = tokens_nome_paciente(nome_painel)
    if len(a) < 1 or len(b) < 1:
        return False
    if a[0] == b[0]:
        intersecao = set(a) & set(b)
        return len(intersecao) >= min(len(a), len(b), 2)
    return False

def escolher_linha_paciente(nome_planilha, candidatos):
    compativeis = [c for c in candidatos if nomes_compativeis(nome_planilha, c["nome"])]
    if not compativeis:
        return None, "nao_encontrado"
    if len(compativeis) == 1:
        return compativeis[0], "ok"
    ref = tokens_nome_paciente(nome_planilha)
    exatos = [c for c in compativeis if tokens_nome_paciente(c["nome"]) == ref]
    if len(exatos) == 1:
        return exatos[0], "ok"
    return None, "ambiguo"

def turno_do_horario(hora):
    return "DIURNO" if 6 <= hora < 18 else "NOTURNO"

def turno_do_intervalo(ini, fim=None):
    """Turno do plantão pelo início e fim (horários quebrados).
    Diurno = dentro de 06h-19h (7-19 ou 6-18). Noturno = dentro de 18h-07h do dia seguinte (19-7 ou 18-6).
    Sem horário de fim, usa só a hora de início."""
    if ini is None:
        return None
    if fim is None or fim <= ini:
        return turno_do_horario(ini.hour)
    a = ini.hour + ini.minute / 60.0
    b = a + (fim - ini).total_seconds() / 3600.0
    diurno_ok = a >= 6 and b <= 19
    noturno_ok = (a >= 18 and b <= 31) or b <= 7
    if diurno_ok and noturno_ok:
        return turno_do_horario(ini.hour)  # cabe nos dois (ex.: 6h-7h, 18h-19h): desempata pelo início
    if diurno_ok:
        return "DIURNO"
    if noturno_ok:
        return "NOTURNO"
    meio = ((a + b) / 2.0) % 24  # atravessa as duas janelas: vale o ponto médio do plantão
    return "DIURNO" if 6.5 <= meio < 18.5 else "NOTURNO"

def normalizar_alerta(texto):
    t = normalizar_para_comparar(texto)
    if "NAO CONFIRMADO" in t:
        return "NAO_CONFIRMADO"
    if "CONFIRMADO" in t:
        return "CONFIRMADO"
    for chave in ("RECUSADO", "ATRASADO", "INICIADO"):
        if chave in t:
            return chave
    return "DESCONHECIDO"

def colunas_turno_data(colunas, turno, data_dt):
    turno_norm = normalizar_para_comparar(turno)
    candidatas = [c for c in colunas if turno_norm in normalizar_para_comparar(str(c))]
    if not candidatas:
        return []
    
    padrao_dia_mes = rf"(?<!\d)0?{data_dt.day}\s*[/\-.]\s*0?{data_dt.month}(?!\d)"
    do_dia = re.compile(padrao_dia_mes)
    
    com_data_do_dia = [c for c in candidatas if do_dia.search(str(c))]
    if com_data_do_dia:
        return com_data_do_dia
    
    return candidatas[:1]

def pontuar_item_filtro(alvo, candidato):
    ta = normalizar_para_comparar(alvo).split()
    tc = normalizar_para_comparar(candidato).split()
    if not ta or not tc:
        return None
    pontos = 0
    for t in ta:
        if t in tc:
            pontos += 2
        elif len(t) >= 2 and any(c.startswith(t) for c in tc):
            pontos += 1
        else:
            return None
    return pontos

def interpretar_tabela_command(dados_js):
    cab = [normalizar_para_comparar(c) for c in (dados_js or {}).get("cab", [])]

    def achar(prefixo):
        for i, c in enumerate(cab):
            if c.startswith(prefixo):
                return i
        return None

    i_pac = achar("PACIENTE")
    i_alerta = achar("STATUS DE ALERTA")
    i_hor = achar("HORARIO")

    linhas = []
    for idx, celulas in enumerate((dados_js or {}).get("dados", [])):
        if len(celulas) < 3:
            continue
        texto_linha = " ".join(celulas)
        nome_cel = celulas[i_pac] if (i_pac is not None and i_pac < len(celulas)) else celulas[1]
        nome = (nome_cel.split("\n")[0] if nome_cel else "").strip()
        alerta_txt = celulas[i_alerta] if (i_alerta is not None and i_alerta < len(celulas)) else texto_linha
        hor_txt = celulas[i_hor] if (i_hor is not None and i_hor < len(celulas)) else texto_linha
        m = re.search(r"(\d{2})/(\d{2})/(\d{4}),?\s*(\d{1,2}):(\d{2})", hor_txt)
        if m:
            data_br = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
            hh, mm = int(m.group(4)), int(m.group(5))
            turno = turno_do_horario(hh)
            hora = f"{hh:02d}:{mm:02d}"
        else:
            data_br, turno, hora = "", None, ""
        nome_chave = " ".join(normalizar_para_comparar(nome).split())
        linhas.append({
            "idx": idx, "nome": nome, "data": data_br, "hora": hora, "turno": turno,
            "alerta": normalizar_alerta(alerta_txt), "chave": f"{nome_chave}|{data_br} {hora}",
        })
    return linhas

# --- Command Center: leitura tolerante da API, token e log em arquivo -------------
import json
import base64

CC_PASTA_SCRIPT = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
CC_ARQ_LOG = os.path.join(CC_PASTA_SCRIPT, "command_center_log.txt")
CC_ARQ_TOKEN = os.path.join(CC_PASTA_SCRIPT, "api_token.txt")
CC_BASE_URL = CONFIG.get("api_base_url") or os.environ.get("API_BASE_URL", "")
CC_SITE_URL = CONFIG.get("site_url") or os.environ.get("SITE_URL", "")
CC_COOKIE_TOKEN = CONFIG.get("cookie_token", "token")

def cc_log(msg):
    try:
        with open(CC_ARQ_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def cc_token_inicial():
    token = os.environ.get("API_TOKEN", "").strip()
    if not token and os.path.exists(CC_ARQ_TOKEN):
        try:
            with open(CC_ARQ_TOKEN, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except Exception:
            token = ""
    return token

def cc_limpar_token(texto):
    t = (texto or "").strip().strip('"').strip("'")
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    if t.lower().startswith(CC_COOKIE_TOKEN.lower() + "="):
        t = t[len(CC_COOKIE_TOKEN) + 1:].strip()
    return t

def cc_token_expira_em(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        dados = json.loads(base64.urlsafe_b64decode(payload.encode()).decode("utf-8"))
        return datetime.fromtimestamp(int(dados["exp"]))
    except Exception:
        return None

def cc_obter_token_browser(timeout_login=240):
    if not PLAYWRIGHT_DISPONIVEL:
        return "", "Playwright não instalado (pip install playwright)."
    perfil = os.path.join(CC_PASTA_SCRIPT, "cc_perfil_browser")
    url_site = CC_SITE_URL
    js_storage = r"() => { const o = []; for (const st of [localStorage, sessionStorage]) { for (let i = 0; i < st.length; i++) { const v = st.getItem(st.key(i)); if (v && /^eyJ[\w-]+\.[\w-]+\.[\w-]+$/.test(v.trim())) o.push(v.trim()); } } return o; }"

    def valido(tok):
        exp = cc_token_expira_em(tok)
        return (not exp) or exp > datetime.now() + timedelta(minutes=5)

    def ler(ctx, page):
        for c in ctx.cookies():
            if c.get("name") == CC_COOKIE_TOKEN and c.get("value"):
                v = cc_limpar_token(c["value"])
                if valido(v):
                    return v
        try:
            for v in page.evaluate(js_storage):
                if valido(v):
                    return v
        except Exception:
            pass
        return ""

    ultimo_erro = "Não consegui abrir o navegador (Edge/Chrome)."
    for headless in (True, False):
        try:
            with sync_playwright() as pw:
                ctx = None
                for canal in ("msedge", "chrome", None):
                    try:
                        kw = dict(user_data_dir=perfil, headless=headless)
                        if canal:
                            kw["channel"] = canal
                        ctx = pw.chromium.launch_persistent_context(**kw)
                        break
                    except Exception as e:
                        cc_log(f"Browser canal={canal} headless={headless}: {str(e)[:150]}")
                        ctx = None
                if ctx is None:
                    continue
                try:
                    page = ctx.pages[0] if ctx.pages else ctx.new_page()
                    page.goto(url_site, wait_until="domcontentloaded", timeout=30000)
                    limite = time.time() + (10 if headless else timeout_login)
                    while time.time() < limite:
                        tok = ler(ctx, page)
                        if tok:
                            cc_log(f"Token obtido do navegador (headless={headless}).")
                            return tok, ""
                        page.wait_for_timeout(1000)
                    ultimo_erro = "Login não concluído a tempo no navegador."
                finally:
                    ctx.close()
        except Exception as e:
            cc_log(f"Falha Playwright headless={headless}: {e}")
            ultimo_erro = f"Falha ao usar o navegador: {str(e)[:80]}"
    return "", ultimo_erro

def cc_extrair_lista(corpo):
    if isinstance(corpo, list):
        return corpo
    if isinstance(corpo, dict):
        for chave in ("data", "items", "results", "rows", "content", "records", "services"):
            v = corpo.get(chave)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                achou = cc_extrair_lista(v)
                if achou:
                    return achou
    return []

def cc_buscar_valor(obj, chaves, profundidade=4):
    fila = [(obj, 0)]
    while fila:
        atual, nivel = fila.pop(0)
        if isinstance(atual, dict):
            for k, v in atual.items():
                if str(k).lower() in chaves and isinstance(v, (str, int, float)) and str(v).strip():
                    return str(v).strip()
            if nivel < profundidade:
                fila.extend((v, nivel + 1) for v in atual.values() if isinstance(v, (dict, list)))
        elif isinstance(atual, list) and nivel < profundidade:
            fila.extend((v, nivel + 1) for v in atual[:3])
    return ""

def cc_attrs(item):
    a = item.get("attributes")
    return a if isinstance(a, dict) else item

def cc_nome_paciente_api(item):
    for base in (cc_attrs(item), item):
        pes = base.get("person")
        if isinstance(pes, dict):
            for k in ("fullName", "full_name", "name"):
                if isinstance(pes.get(k), str) and pes[k].strip():
                    return pes[k].strip()
    for caminho in (("patient", "name"), ("patient", "fullName"), ("customer", "name"), ("beneficiary", "name")):
        v = item
        for c in caminho:
            v = v.get(c) if isinstance(v, dict) else None
        if isinstance(v, str) and v.strip():
            return v.strip()
    return cc_buscar_valor(item, {"patientname", "patient_name", "customername", "beneficiaryname"})

def cc_data_hora_api(item):
    a = cc_attrs(item)
    bruto = ""
    for k in ("timeFrom", "scheduledTime", "startTime", "timeStart", "start"):
        if isinstance(a.get(k), str) and a[k].strip():
            bruto = a[k].strip()
            break
    if not bruto:
        bruto = cc_buscar_valor(item, {"timefrom", "scheduledtime", "scheduled_time", "scheduledat", "scheduled_at",
                                       "startdatetime", "starttime", "datetime", "horario"})
    if not bruto:
        return None
    return _cc_parse_data_hora(bruto)

def cc_data_hora_fim_api(item):
    """Horário de término do plantão (timeTo etc.), ou None se a API não informar."""
    a = cc_attrs(item)
    bruto = ""
    for k in ("timeTo", "endTime", "timeEnd", "scheduledEndTime", "end"):
        if isinstance(a.get(k), str) and a[k].strip():
            bruto = a[k].strip()
            break
    if not bruto:
        bruto = cc_buscar_valor(item, {"timeto", "endtime", "timeend", "scheduledend", "scheduled_end", "enddatetime"})
    return _cc_parse_data_hora(bruto) if bruto else None

def _cc_parse_data_hora(bruto):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?", bruto)
    if m:
        ano, mes, dia, hh, mm, tz = m.groups()
        dt = datetime(int(ano), int(mes), int(dia), int(hh), int(mm))
        if tz:
            if tz == "Z":
                off = 0
            else:
                sinal = -1 if tz[0] == "-" else 1
                limpo = tz[1:].replace(":", "")
                off = sinal * (int(limpo[:2]) * 60 + int(limpo[2:]))
            dt = dt + timedelta(minutes=(-3 * 60) - off)
        return dt
    m = re.search(r"(\d{2})/(\d{2})/(\d{4}),?\s*(\d{1,2}):(\d{2})", bruto)
    if m:
        d, mo, an, hh, mm = m.groups()
        return datetime(int(an), int(mo), int(d), int(hh), int(mm))
    return None

_CHAVES_LOG_LIVRES = {"timefrom", "timeto", "statusid", "alertstatusid", "description", "type", "checkinat", "checkoutat"}

def cc_esquema(obj, chave=""):
    if isinstance(obj, dict):
        return {k: cc_esquema(v, str(k).lower()) for k, v in obj.items()}
    if isinstance(obj, list):
        return [cc_esquema(obj[0], chave)] if obj else []
    if isinstance(obj, str):
        return obj if chave in _CHAVES_LOG_LIVRES else "<texto>"
    return "<vazio>" if obj is None else f"<{type(obj).__name__}>"

CC_PAYLOADS_CONFIRMAR = [{"alertStatusId": "CONFIRMED"}]

def cc_resposta_confirma(res):
    try:
        corpo = res.json()
    except Exception:
        return True
    v = cc_buscar_valor(corpo, {"alertstatusid", "alertstatus"}, profundidade=5) if isinstance(corpo, (dict, list)) else ""
    return (cc_alerta_api(v) == "CONFIRMADO") if v else True

def cc_alerta_api(texto):
    t = normalizar_para_comparar(str(texto or "").replace("_", " "))
    if "NOT CONFIRMED" in t or "UNCONFIRMED" in t or "NAO CONFIRMADO" in t:
        return "NAO_CONFIRMADO"
    if "CONFIRMED" in t or "CONFIRMADO" in t:
        return "CONFIRMADO"
    return normalizar_alerta(t)

def cc_normalizar_plantoes(itens):
    plantoes = []
    descartados = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        p_id = item.get("id") or item.get("uuid") or cc_buscar_valor(item, {"id", "uuid", "serviceid"})
        nome = cc_nome_paciente_api(item)
        dt = cc_data_hora_api(item)
        if not (p_id and nome):
            descartados.append(item)
            continue
        alerta_bruto = cc_attrs(item).get("alertStatusId") or cc_buscar_valor(item, {"alertstatusid", "alertstatus", "alert_status"})
        dt_fim = cc_data_hora_fim_api(item)
        plantoes.append({
            "id": p_id, "nome": nome, "nome_norm": normalizar_para_comparar(nome),
            "turno": turno_do_intervalo(dt, dt_fim) if dt else None,
            "hora": dt.strftime("%H:%M") if dt else "",
            "hora_fim": dt_fim.strftime("%H:%M") if dt_fim else "",
            "dt_ini": dt, "dt_fim": dt_fim,
            "alerta": cc_alerta_api(alerta_bruto),
            "alerta_bruto": str(alerta_bruto or ""),
            "produto_id": cc_produto_api(item)[0], "produto_nome": cc_produto_api(item)[1],
            "resp_campo": cc_responsavel_api(item)[0], "resp_id": cc_responsavel_api(item)[1],
            "prof": cc_profissional_api(item),
            "prof_diag": cc_profissionais_diag(item),
            "nomes_reg": cc_nomes_no_registro(item),
            "textos_reg": cc_textos_registro(item),
            "todos_txt": cc_todos_textos(item),
        })
    if descartados:
        cc_log(f"AVISO: {len(descartados)} registro(s) da API descartado(s) por não ter id ou nome do paciente "
               f"(o robô não consegue localizar esses plantões). Estrutura do 1º descartado: "
               + json.dumps(cc_esquema(descartados[0]), ensure_ascii=False)[:1500])
    return plantoes

_RE_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

def cc_extrair_ids(texto, chave_link):
    texto = str(texto or "")
    if chave_link + "=" in texto:
        return re.findall(chave_link + r"=(" + _RE_UUID + ")", texto)
    return re.findall(_RE_UUID, texto)

_TITULOS_PROF = {"ENF", "ENFA", "ENFERMEIRA", "ENFERMEIRO", "ENFERMAGEM", "TEC", "TECNICO", "TECNICA", "TECENF",
                 "AUX", "AUXILIAR", "DR", "DRA"}
_CHAVES_PROF = ("collector", "professional", "caregiver", "provider", "nurse", "worker", "employee")

def cc_profissional_api(item):
    niveis = [item]
    for k in ("attributes", "data"):
        if isinstance(item.get(k), dict):
            niveis.append(item[k])
    achou_campo = False
    for nivel in niveis:
        for k, v in nivel.items():
            kl = str(k).lower().replace("_", "")
            if kl.endswith("id") or not any(kl.startswith(c) for c in _CHAVES_PROF):
                continue
            achou_campo = True
            if isinstance(v, list):
                v = v[0] if v else None
            if isinstance(v, dict):
                pes = v.get("person")
                direto = pes.get("fullName") if isinstance(pes, dict) else None
                v = direto or v.get("fullName") or cc_buscar_valor(v, {"name", "fullname", "full_name", "nome"}, profundidade=3)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return "" if achou_campo else None

_CC_SKIP_TOPO = {"person", "patient", "customer", "beneficiary", "monitoringresponsible", "responsible",
                 "product", "partner", "status", "alertstatus", "attributes", "data"}

def cc_nomes_no_registro(item):
    """Todos os nomes que aparecem no registro da API, fora paciente/responsável/produto/parceiro.
    Só serve para casar o profissional da planilha mesmo quando a API guarda o nome em outro campo."""
    nomes = []

    def varrer(v, prof=0):
        if prof > 6:
            return
        if isinstance(v, dict):
            for k, x in v.items():
                kl = str(k).lower().replace("_", "")
                if kl in ("fullname", "name", "nome") and isinstance(x, str) and x.strip():
                    nomes.append(x.strip())
                elif isinstance(x, (dict, list)):
                    varrer(x, prof + 1)
        elif isinstance(v, list):
            for x in v[:10]:
                varrer(x, prof + 1)

    if not isinstance(item, dict):
        return nomes
    niveis = [item] + [item[k] for k in ("attributes", "data") if isinstance(item.get(k), dict)]
    for nivel in niveis:
        for k, v in nivel.items():
            kl = str(k).lower().replace("_", "")
            if kl in _CC_SKIP_TOPO or not isinstance(v, (dict, list)):
                continue
            varrer(v)
    return list(dict.fromkeys(nomes))

def cc_textos_registro(item):
    """Todos os textos do registro da API fora paciente/responsável/produto/parceiro/status.
    Só serve para detectar 'escalista', 'coop' ou 'social saúde' mesmo fora do campo do nome."""
    textos = []

    def varrer(v, prof=0):
        if prof > 6:
            return
        if isinstance(v, dict):
            for x in v.values():
                varrer(x, prof + 1)
        elif isinstance(v, list):
            for x in v[:10]:
                varrer(x, prof + 1)
        elif isinstance(v, str) and v.strip():
            textos.append(v.strip())

    if not isinstance(item, dict):
        return ""
    niveis = [item] + [item[k] for k in ("attributes", "data") if isinstance(item.get(k), dict)]
    for nivel in niveis:
        for k, v in nivel.items():
            kl = str(k).lower().replace("_", "")
            if kl in _CC_SKIP_TOPO or kl.endswith("id"):
                continue
            if isinstance(v, (dict, list)) or kl.startswith(("professional", "collector", "caregiver", "nurse", "worker", "employee", "role", "profession")):
                varrer(v)
    return " | ".join(textos)[:2000]

def cc_todos_textos(item):
    """Todos os textos do registro da API, em qualquer campo (inclusive no nível de cima), exceto ids,
    datas e links. Serve para achar o profissional que assumiu o plantão (troca de profissional),
    quando a API guarda esse nome fora dos campos 'collector'/'professional'."""
    textos = []

    def varrer(v, chave="", prof=0):
        if prof > 8:
            return
        if isinstance(v, dict):
            for k, x in v.items():
                varrer(x, str(k).lower().replace("_", ""), prof + 1)
        elif isinstance(v, list):
            for x in v[:20]:
                varrer(x, chave, prof + 1)
        elif isinstance(v, str) and v.strip():
            if chave.endswith(("id", "at", "date", "url", "link", "email", "phone")) or chave.startswith(("time", "date")):
                return
            t = v.strip()
            if len(t) <= 80 and not t.lower().startswith(("http", "{", "[")):
                textos.append(t)

    if isinstance(item, dict):
        varrer(item)
    return list(dict.fromkeys(textos))

def cc_candidatos_prof(pl):
    """Nome do profissional lido pela API + qualquer outro nome do registro (para comparar com a planilha)."""
    nomes = [pl["prof"]] if pl.get("prof") else []
    nomes += [n for n in (pl.get("nomes_reg") or []) if n not in nomes]
    # Último recurso: textos do registro (campos de profissional/colaborador) que tenham cara de nome.
    for txt in str(pl.get("textos_reg") or "").split(" | "):
        txt = txt.strip()
        if txt and txt not in nomes and len(cc_tokens_profissional(txt)) >= 2 and len(txt) <= 80:
            nomes.append(txt)
    # Troca de profissional: o nome de quem assumiu pode estar em qualquer outro campo do registro.
    paciente_norm = cc_normalizar_nome(pl.get("nome"))
    for txt in (pl.get("todos_txt") or []):
        if txt in nomes or len(cc_tokens_profissional(txt)) < 2:
            continue
        tn = cc_normalizar_nome(txt)
        if tn == paciente_norm or "PLANTAO" in tn or "ENFERM" in tn or "HORAS" in tn:
            continue
        nomes.append(txt)
    return nomes

def cc_tem_pendente(valor):
    """True se o texto tem a palavra PENDENTE (maiúscula, minúscula ou com acento/hífen junto)."""
    if valor is None:
        return False
    try:
        if pd.isna(valor):
            return False
    except Exception:
        pass
    return "PENDENTE" in normalizar_para_comparar(str(valor).replace("\xa0", " "))

def cc_celula_sem_profissional(valor):
    """Regra do responsável: célula do plantão vazia ou com a palavra PENDENTE."""
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except Exception:
        pass
    t = normalizar_para_comparar(str(valor).replace("\xa0", " "))
    return t in ("", "NAN", "NONE") or "PENDENTE" in t

def cc_profissionais_diag(item):
    """Só para diagnóstico: lista 'campo=nome' de todos os campos de profissional do registro da API."""
    saida = []
    niveis = [item] + [item[k] for k in ("attributes", "data") if isinstance(item.get(k), dict)]
    for nivel in niveis:
        for k, v in nivel.items():
            kl = str(k).lower().replace("_", "")
            if kl.endswith("id") or not any(kl.startswith(c) for c in _CHAVES_PROF):
                continue
            if isinstance(v, list):
                v = v[0] if v else None
            if isinstance(v, dict):
                pes = v.get("person")
                direto = pes.get("fullName") if isinstance(pes, dict) else None
                v = direto or v.get("fullName") or cc_buscar_valor(v, {"name", "fullname", "full_name", "nome"}, profundidade=3)
            saida.append(f"{k}={v!r}")
    return saida

def cc_normalizar_nome(texto):
    """Normalização usada só na conferência de profissional do Command Center:
    ignora acento, caracteres invisíveis e espaços especiais (a normalizar_para_comparar das outras abas não muda)."""
    if texto is None:
        return ""
    t = str(texto)
    t = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff\u00ad]", "", t)
    t = re.sub(r"[\u00a0\u2007\u202f\u2009\u200a\u3000]", " ", t)
    t = t.replace("'", "").replace("`", "").replace("’", "").replace("‘", "").replace("´", "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").upper()
    t = t.replace("Ø", "O").replace("Æ", "AE").replace("Œ", "OE").replace("ß", "SS")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9\s]", " ", t)).strip()

def cc_tokens_profissional(nome):
    # Remove o que estiver entre parênteses (ex.: "(cobertura)"), partículas e tokens com número (ex.: "07h").
    texto = re.sub(r"\([^)]*\)", " ", str(nome or "").replace("\xa0", " "))
    toks = [t for t in cc_normalizar_nome(texto).split()
            if t not in PARTICULAS_NOME and not any(ch.isdigit() for ch in t)]
    while toks and toks[0] in _TITULOS_PROF:
        toks = toks[1:]
    return toks

def cc_profissionais_planilha(valor):
    partes = [x.strip() for x in re.split(r"[/;|+\n]+", str(valor or "")) if x.strip()]
    return partes or [str(valor or "")]

def _cc_token_igual(x, y):
    """Mesmo nome, inicial do nome, ou pequena diferença de digitação em nomes longos."""
    if x == y:
        return True
    if len(x) == 1 or len(y) == 1:
        return x[0] == y[0]
    if min(len(x), len(y)) >= 5 and abs(len(x) - len(y)) <= 1:
        return difflib.SequenceMatcher(None, x, y).ratio() >= 0.88
    return False

def cc_profissional_confere(nome_planilha, nome_painel):
    a, b = cc_tokens_profissional(nome_planilha), cc_tokens_profissional(nome_painel)
    if len(a) < 2 or len(b) < 2 or not _cc_token_igual(a[0], b[0]):
        return False
    if _cc_token_igual(a[1], b[1]):
        return True
    # Nome do meio omitido de um dos lados (ex.: "Edna Nobrega" x "Edna Maria Nobrega"):
    # os nomes que sobram do lado menor precisam aparecer, na mesma ordem, no lado maior.
    menor, maior = (a[1:], b[1:]) if len(a) <= len(b) else (b[1:], a[1:])
    it = iter(maior)
    return all(any(_cc_token_igual(t, m) for m in it) for t in menor)

def cc_rotulo_hora(pl):
    """'07:00-13:00' (ou só '07:00' se a API não informou o fim)."""
    return f"{pl.get('hora') or '?'}-{pl['hora_fim']}" if pl.get("hora_fim") else (pl.get("hora") or "?")

def cc_turno_ambiguo(pl):
    """True quando o plantão (horário quebrado) atravessa a divisa dos turnos: não cabe só no diurno
    nem só no noturno (ex.: 15h-21h, 04h-10h), então o turno calculado pode divergir do da planilha."""
    ini, fim = pl.get("dt_ini"), pl.get("dt_fim")
    if not ini or not fim or fim <= ini:
        return False
    a = ini.hour + ini.minute / 60.0
    b = a + (fim - ini).total_seconds() / 3600.0
    diurno_ok = a >= 6 and b <= 19
    noturno_ok = (a >= 18 and b <= 31) or b <= 7
    return diurno_ok == noturno_ok

def cc_plantao_quebrado(pl):
    """True para plantão de horário quebrado: não é o 12h padrão (07-19, 19-07, 06-18, 18-06) nem 24h.
    Esses plantões podem ter turno calculado diferente do da planilha, então o robô os aceita
    desde que o profissional da planilha confira com o do painel."""
    ini, fim = pl.get("dt_ini"), pl.get("dt_fim")
    if not ini:
        return False
    if (ini.hour, ini.minute) not in ((6, 0), (7, 0), (18, 0), (19, 0)):
        return True
    if fim and fim > ini:
        horas = (fim - ini).total_seconds() / 3600.0
        return abs(horas - 12) > 0.01 and abs(horas - 24) > 0.01
    return False

def cc_produto_eh_plantao(pl):
    """Sem nome de produto na API: aceita. Com nome: só se for plantão de enfermagem."""
    nome = normalizar_para_comparar(pl.get("produto_nome") or "")
    return (not nome) or any(k in nome for k in ("PLANTAO", "ENFERM"))

def cc_localizar_plantao(nome_planilha, turno, plantoes):
    candidatos = [p for p in plantoes if p["turno"] in (turno, None)]
    nome_norm = normalizar_para_comparar(nome_planilha)

    exatos = [p for p in candidatos if p["nome_norm"] == nome_norm]
    if exatos:
        return exatos, "ok"

    compat = [p for p in candidatos if nomes_compativeis(nome_planilha, p["nome"])]
    if compat:
        if len({p["nome_norm"] for p in compat}) == 1:
            return compat, "ok"
        ref = tokens_nome_paciente(nome_planilha)
        iguais = [p for p in compat if tokens_nome_paciente(p["nome"]) == ref]
        if iguais and len({p["nome_norm"] for p in iguais}) == 1:
            return iguais, "ok"
        # Desempate: o nome da planilha está inteiro dentro do nome do painel (ou o contrário),
        # ex.: "Gustavo Henrique Rodrigues" x "Gustavo Henrique Rodrigues Silva".
        # Outros pacientes que só dividem 2 nomes soltos (ex.: "Gustavo" e "Silva") não entram.
        set_ref = set(ref)
        contidos = [p for p in compat if set_ref and (set_ref <= set(tokens_nome_paciente(p["nome"])) or set(tokens_nome_paciente(p["nome"])) <= set_ref)]
        if contidos and len({p["nome_norm"] for p in contidos}) == 1:
            return contidos, "ok"
        return [], "ambiguo"

    outro = [p for p in plantoes if p["turno"] not in (turno, None) and nomes_compativeis(nome_planilha, p["nome"])]
    if outro:
        return [], "outro_turno"
    return [], "nao_encontrado"

def cc_nome_paciente_busca(item):
    """Nome do paciente num registro da busca /patients (mesma busca do filtro 'Paciente' do painel)."""
    if not isinstance(item, dict):
        return ""
    for base in (cc_attrs(item), item):
        if not isinstance(base, dict):
            continue
        for k in ("fullName", "full_name", "name"):
            if isinstance(base.get(k), str) and base[k].strip():
                return base[k].strip()
        pes = base.get("person")
        if isinstance(pes, dict):
            for k in ("fullName", "full_name", "name"):
                if isinstance(pes.get(k), str) and pes[k].strip():
                    return pes[k].strip()
    return cc_buscar_valor(item, {"fullname", "full_name", "name"})

def cc_termos_busca_paciente(nome):
    """Termos para digitar no filtro de paciente: nome inteiro, depois os 2 primeiros nomes, depois o primeiro."""
    base = " ".join(re.sub(r"\([^)]*\)", " ", str(nome or "").replace("\xa0", " ")).split())
    toks = base.split()
    termos = [base]
    if len(toks) > 2:
        termos.append(" ".join(toks[:2]))
    if len(toks) > 1:
        termos.append(toks[0])
    vistos, saida = set(), []
    for t in termos:
        if t and t.lower() not in vistos:
            vistos.add(t.lower())
            saida.append(t)
    return saida

def cc_produto_api(item):
    """Devolve (id, nome) do produto do plantão, se a API informar."""
    pid, nome = "", ""
    for base in (cc_attrs(item), item):
        if not isinstance(base, dict):
            continue
        prod = base.get("product")
        if isinstance(prod, dict):
            pa = prod.get("attributes") if isinstance(prod.get("attributes"), dict) else prod
            pid = pid or str(prod.get("id") or pa.get("id") or "")
            for k in ("name", "title", "description", "label"):
                if isinstance(pa.get(k), str) and pa[k].strip():
                    nome = nome or pa[k].strip()
                    break
        elif isinstance(prod, str) and prod.strip():
            nome = nome or prod.strip()
        if isinstance(base.get("productId"), str):
            pid = pid or base["productId"]
        for k in ("productName", "product_name", "productTitle"):
            if isinstance(base.get(k), str) and base[k].strip():
                nome = nome or base[k].strip()
    return pid, nome

def cc_usuario_do_token(token):
    """(id, nome) do usuário dono do token de login."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        dados = (json.loads(base64.urlsafe_b64decode(payload.encode()).decode("utf-8")).get("data")) or {}
        return str(dados.get("id") or ""), str(dados.get("name") or dados.get("email") or "")
    except Exception:
        return "", ""

def cc_responsavel_api(item):
    """(achou_campo, id) do responsável de monitoramento já gravado no plantão."""
    for base in (cc_attrs(item), item):
        if not isinstance(base, dict):
            continue
        if "monitoringResponsibleId" in base:
            return True, str(base.get("monitoringResponsibleId") or "")
        if "monitoringResponsible" in base:
            mr = base.get("monitoringResponsible")
            if isinstance(mr, dict):
                sub_attrs = mr.get("attributes") if isinstance(mr.get("attributes"), dict) else {}
                return True, str(mr.get("id") or sub_attrs.get("id") or "")
            return True, ""
    return False, ""

def cc_tem_cobertura(texto):
    return "COBERTURA" in normalizar_para_comparar(texto or "")

def cc_prof_protegido(texto):
    """Profissional COOP / escalista / Social Saúde: o responsável do plantão não deve ser alterado."""
    t = normalizar_para_comparar(texto or "")
    return bool(re.search(r"\bCOOP\b|\bCOOPERATIVA\b|ESCALISTA|SOCIAL\s*SAUDE", t))

def cc_sem_cobertura(texto):
    return re.sub(r"\(?\s*cobertura(\s+solicitada)?\s*\)?", " ", str(texto or ""), flags=re.I).strip()

def cc_valor_plantao_valido(valor, turno):
    """Regra do Command Center: DIURNO com 'cobertura' não confirma; NOTURNO confirma mesmo com a palavra."""
    if valor is None or pd.isna(valor):
        return False
    val = normalizar_para_comparar(str(valor))
    if not val or val in ("NAN", "NONE"):
        return False
    for termo in TERMOS_INVALIDOS_PLANTAO:
        t = normalizar_para_comparar(termo)
        if "COBERTURA" in t and turno == "NOTURNO":
            continue
        if t in val:
            return False
    if turno == "NOTURNO" and "COBERTURA" in val:
        return bool(normalizar_para_comparar(cc_sem_cobertura(valor)))
    return True

# ==============================================================================
# DISPARO DE MONITORAMENTO: REGRA DE PAD POR DIA PAR / ÍMPAR
# ==============================================================================
_TURNOS_PAD = {"DIURNO": "D", "DIURNOS": "D", "DIA": "D", "NOTURNO": "N", "NOTURNOS": "N", "NOITE": "N", "24H": "DN", "24": "DN"}
_PARIDADES_PAD = {"PAR": "PAR", "PARES": "PAR", "IMPAR": "IMPAR", "IMPARES": "IMPAR"}

def _regra_paridade_pad(texto):
    if texto is None:
        return None
    pares = []
    achou_paridade = False
    for segmento in re.split(r"[/;|+,\n]+", str(texto).upper()):
        acumulados = []
        paridade_pendente, paridade_usada = None, True
        for token in normalizar_para_comparar(segmento).split():
            if token in _TURNOS_PAD:
                if paridade_pendente is not None:
                    pares.append((_TURNOS_PAD[token], paridade_pendente))
                    paridade_usada = True
                else:
                    acumulados.append(_TURNOS_PAD[token])
            elif token in _PARIDADES_PAD:
                achou_paridade = True
                if acumulados:
                    pares.extend((t, _PARIDADES_PAD[token]) for t in acumulados)
                    acumulados = []
                else:
                    paridade_pendente, paridade_usada = _PARIDADES_PAD[token], False
        if paridade_pendente is not None and not paridade_usada:
            pares.append(("DN", paridade_pendente))
        pares.extend((t, None) for t in acumulados)
    return pares if achou_paridade else None

def interpretar_pad_paridade(pad_texto, status_texto, dia_noturno, dia_diurno):
    for texto in (pad_texto, status_texto):
        pares = _regra_paridade_pad(texto)
        if pares is None:
            continue
        ativo = {"N": False, "D": False}
        for turnos, paridade in pares:
            for turno in (("N", "D") if turnos == "DN" else (turnos,)):
                dia = dia_noturno if turno == "N" else dia_diurno
                if paridade is None or (paridade == "PAR") == (dia % 2 == 0):
                    ativo[turno] = True
        return {"noturno": ativo["N"], "diurno": ativo["D"], "texto": " ".join(str(texto).split())}
    return None

def obter_caminho_credenciais():
    pasta_script = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    for nome in ['credentials.json', 'credentials.json.json', 'credentials.json.txt', 'credentials']:
        caminho = os.path.join(pasta_script, nome)
        if os.path.exists(caminho):
            return caminho
    return None

def autenticar_google():
    creds = None
    pasta_script = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    caminho_token = os.path.join(pasta_script, 'token.json')
    
    if os.path.exists(caminho_token):
        creds = Credentials.from_authorized_user_file(caminho_token, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            caminho_creds = obter_caminho_credenciais()
            if not caminho_creds:
                raise FileNotFoundError("O arquivo 'credentials.json' não foi encontrado!")
            flow = InstalledAppFlow.from_client_secrets_file(caminho_creds, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(caminho_token, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def baixar_planilha_privada(creds, spreadsheet_id):
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=spreadsheet_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer

def normalizar_df(df_aba):
    if df_aba.empty:
        return df_aba

    idx_cabecalho = None
    for idx_linha in range(min(20, len(df_aba))):
        valores_linha = [str(x).replace('\xa0', ' ').strip().upper() for x in df_aba.iloc[idx_linha].values if pd.notna(x)]
        tem_paciente = any(any(k in cell for k in ["PACIENTE", "PACIENTES", "NOME", "GRUPO", "BENEFICIARIO"]) for cell in valores_linha)
        tem_status = any(any(k in cell for k in ["STATUS", "ATI", "ST", "SITUAÇÃO", "SITUACAO"]) for cell in valores_linha)
        
        if tem_paciente or tem_status:
            idx_cabecalho = idx_linha
            if tem_paciente and tem_status:
                break

    if idx_cabecalho is not None:
        novas_colunas = []
        for i, c in enumerate(df_aba.iloc[idx_cabecalho].values):
            nome_col = str(c).replace('\xa0', ' ').strip().upper() if pd.notna(c) else ""
            novas_colunas.append(f"{nome_col}_COL{i}" if nome_col else f"COL_{i}")
        
        df_aba.columns = novas_colunas
        df_aba = df_aba.iloc[idx_cabecalho + 1:].reset_index(drop=True)
    else:
        df_aba.columns = [f"COL_{i}" for i in range(len(df_aba.columns))]

    return df_aba

# ==============================================================================
# PAINEL PRINCIPAL UNIFICADO COM ABAS
# ==============================================================================

class PainelUnificado(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Painel Integrado de Automação de Disparos e Monitoramento Web")
        self.geometry("1200x860")

        self.abas_dict = {}
        self.creds = None

        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        self.configure(fg_color=COR_FUNDO)
        larg_pref, alt_pref = (1200, 720) if COMPACTO else (1200, 860)
        try:
            escala = self._get_window_scaling()
            alt_pref = min(alt_pref, int(self.winfo_screenheight() / escala) - 110)
            larg_pref = min(larg_pref, int(self.winfo_screenwidth() / escala) - 20)
        except Exception:
            pass
        self.geometry(f"{larg_pref}x{alt_pref}")
        self.minsize(900, 520)
        aplicar_estilo_tabelas()

        self._kpis = []

        if LAYOUT_ATUAL in ("lateral", "dashboard", "cockpit"):
            self._montar_layout_lateral()
        else:
            self._montar_layout_abas()

        self.setup_aba_monitoramento()
        self.setup_aba_cobrancas()
        self.setup_aba_command_center()

        self._iniciar_atualizacao_kpis()
        self.carregar_planilha_async()

    def ao_fechar(self):
        self.abas_dict.clear()
        limpar_memoria()
        self.destroy()

    def carregar_planilha_async(self):
        threading.Thread(target=self._carregar_planilha_worker, daemon=True).start()

    def _carregar_planilha_worker(self):
        try:
            self.creds = autenticar_google()
            buffer_excel = baixar_planilha_privada(self.creds, ID_PLANILHA)
            
            self.abas_dict.clear()
            limpar_memoria()

            self.abas_dict = pd.read_excel(buffer_excel, sheet_name=None, engine="openpyxl", header=None)
            buffer_excel.close()
            limpar_memoria()

            self.after(0, self._no_carregamento_sucesso)
        except Exception as e:
            self.after(0, lambda: self.lbl_status_planilha.configure(text=f"Erro ao conectar: {e}", text_color=COR_ERRO))

    def _no_carregamento_sucesso(self):
        self.lbl_status_planilha.configure(text="Planilha Conectada com Sucesso!", text_color=COR_SUCESSO)
        self.carregar_checkboxes_monitoramento()
        self.carregar_checkboxes_cobrancas()
        self.carregar_checkboxes_cc()

    def checar_interrupcao_usuario(self, pos_inicial, solicitar_parada_flag):
        if solicitar_parada_flag:
            return True, "Parada manual solicitada pelo operador."

        pos_atual = pyautogui.position()
        if abs(pos_atual.x - pos_inicial.x) > 15 or abs(pos_atual.y - pos_inicial.y) > 15:
            return True, "Movimentação do mouse detectada."

        if KEYBOARD_DISPONIVEL:
            if keyboard.is_pressed('esc') or keyboard.is_pressed('space'):
                return True, "Tecla de interrupção (ESC/Espaço) acionada."

        return False, ""

    def _montar_layout_abas(self):
        frame_top = ctk.CTkFrame(self, fg_color=COR_PAINEL, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CARD)
        frame_top.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkFrame(frame_top, width=4, height=1, fg_color=COR_DESTAQUE, corner_radius=2).pack(side="left", fill="y", padx=(12, 0), pady=12)

        bloco_titulo = ctk.CTkFrame(frame_top, fg_color="transparent")
        bloco_titulo.pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(bloco_titulo, text="Painel de Automação", font=(FONTE_UI, 18, "bold"), text_color=COR_TEXTO).pack(anchor="w")
        ctk.CTkLabel(bloco_titulo, text="Disparos, cobranças e atualização web", font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE).pack(anchor="w")

        ctk.CTkLabel(frame_top, text="Nome:", font=(FONTE_UI, 13, "bold"), text_color=COR_TEXTO_SUAVE).pack(side="left", padx=(30, 8), pady=10)
        self.ent_operador = ctk.CTkEntry(frame_top, placeholder_text="Digite seu nome (obrigatório)", width=280, **ESTILO_ENTRY)
        self.ent_operador.pack(side="left", padx=5, pady=10)

        self.lbl_status_planilha = ctk.CTkLabel(frame_top, text="Conectando ao Google Drive...", text_color=COR_ALERTA, font=(FONTE_MONO, 12, "bold"), fg_color=COR_FUNDO, corner_radius=RAIO_CTRL, height=34, wraplength=380)
        self.lbl_status_planilha.pack(side="right", padx=15)

        self.tabview = ctk.CTkTabview(self, **filtrar_estilo(ctk.CTkTabview, dict(
            fg_color=COR_FUNDO, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CARD,
            segmented_button_fg_color=_t["aba_barra"],
            segmented_button_selected_color=_t["aba_sel"],
            segmented_button_selected_hover_color=_t["aba_sel_hover"],
            segmented_button_unselected_color=_t["aba_nao_sel"],
            segmented_button_unselected_hover_color=_t["aba_nao_hover"],
            text_color=COR_TEXTO,
        )))
        try:
            self.tabview._segmented_button.configure(font=(FONTE_UI, 13, "bold"), height=36)
        except Exception:
            pass
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_monitoramento = self.tabview.add("Disparos de Monitoramento")
        self.tab_cobrancas = self.tabview.add("Confirmações e Cobranças")
        self.tab_command_center = self.tabview.add("Atualização Command Center")

    def _montar_layout_lateral(self):
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=12, pady=12)

        barra = ctk.CTkFrame(corpo, width=270, fg_color=COR_LAT_FUNDO, border_width=1, border_color=COR_LAT_BORDA, corner_radius=RAIO_CARD)
        barra.pack(side="left", fill="y", padx=(0, 10))
        barra.pack_propagate(False)

        ctk.CTkFrame(barra, width=36, height=4, fg_color=COR_DESTAQUE, corner_radius=2).pack(anchor="w", padx=20, pady=(22, 10))
        ctk.CTkLabel(barra, text="Painel de Automação", font=(FONTE_UI, 18, "bold"), text_color=COR_LAT_TITULO).pack(anchor="w", padx=20)
        ctk.CTkLabel(barra, text="Disparos, cobranças e atualização web", font=(FONTE_UI, 11), text_color=COR_LAT_TEXTO, anchor="w", wraplength=230).pack(anchor="w", padx=20, pady=(0, 18))

        self.lbl_status_planilha = ctk.CTkLabel(barra, text="Conectando ao Google Drive...", text_color=COR_ALERTA, font=(FONTE_MONO, 12, "bold"), fg_color=COR_FUNDO, corner_radius=RAIO_CTRL, height=34, wraplength=220)
        self.lbl_status_planilha.pack(side="bottom", fill="x", padx=16, pady=(6, 16))
        self.ent_operador = ctk.CTkEntry(barra, placeholder_text="Digite seu nome (obrigatório)", **{**ESTILO_ENTRY, "font": (FONTE_MONO, 11)})
        self.ent_operador.pack(side="bottom", fill="x", padx=16, pady=(4, 6))
        ctk.CTkLabel(barra, text="Nome:", font=(FONTE_UI, 13, "bold"), text_color=COR_LAT_TEXTO).pack(side="bottom", anchor="w", padx=20)

        area = ctk.CTkFrame(corpo, fg_color="transparent")
        area.pack(side="left", fill="both", expand=True)

        paginas = {}
        botoes = {}

        def mostrar(chave):
            for pagina in paginas.values():
                pagina.pack_forget()
            paginas[chave].pack(fill="both", expand=True)
            for k, botao in botoes.items():
                ativo = (k == chave)
                botao.configure(fg_color=COR_LAT_ATIVO if ativo else "transparent",
                                text_color=COR_SOBRE_PRIMARIO if ativo else COR_LAT_TEXTO)

        itens = (("mon", "Disparos de Monitoramento", "Disparos de monitoramento"),
                 ("cob", "Confirmações e Cobranças", "Confirmações e cobranças"),
                 ("cc", "Command Center", "Atualização Command Center"))
        for chave, rotulo, titulo in itens:
            paginas[chave] = ctk.CTkFrame(area, fg_color="transparent")
            if DASHBOARD:
                ctk.CTkLabel(paginas[chave], text=titulo, font=(FONTE_UI, 17, "bold"), text_color=COR_TEXTO, anchor="w").pack(fill="x", padx=8, pady=(0, 8))
            botoes[chave] = ctk.CTkButton(barra, text=rotulo, anchor="w", height=42, font=(FONTE_UI, 13, "bold"),
                                          corner_radius=RAIO_CTRL + 2, border_width=0, fg_color="transparent", hover_color=COR_LAT_HOVER,
                                          text_color=COR_LAT_TEXTO, command=lambda c=chave: mostrar(c))
            botoes[chave].pack(fill="x", padx=12, pady=3)

        self.tab_monitoramento = paginas["mon"]
        self.tab_cobrancas = paginas["cob"]
        self.tab_command_center = paginas["cc"]
        mostrar("mon")

    def _exigir_operador(self):
        if self.ent_operador.get().strip():
            return True
        messagebox.showwarning("Nome obrigatório", "Preencha o campo NOME antes de continuar.")
        try:
            self.ent_operador.configure(border_color=COR_PERIGO)
            self.ent_operador.focus_set()
            if not getattr(self, "_operador_bind", False):
                self.ent_operador.bind("<KeyRelease>", lambda e: self.ent_operador.configure(border_color=COR_BORDA), add="+")
                self._operador_bind = True
        except Exception:
            pass
        return False

    def _novo_card(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=COR_PAINEL, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CARD, **kwargs)

    def _cabecalho_secao(self, parent, numero, titulo, dica="", largura_dica=780):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(12, 2))
        ctk.CTkLabel(linha, text=str(numero), width=24, height=24, corner_radius=5, fg_color=COR_DESTAQUE, text_color=COR_FUNDO, font=(FONTE_MONO, 12, "bold")).pack(side="left")
        ctk.CTkLabel(linha, text=titulo, font=(FONTE_UI, 14, "bold"), text_color=COR_TEXTO).pack(side="left", padx=10)
        if dica and not COMPACTO:
            ctk.CTkLabel(parent, text=dica, font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE, anchor="w", wraplength=largura_dica).pack(fill="x", padx=14, pady=(0, 8))

    def _criar_painel_convenios(self, parent, titulo, dica, comando_toggle):
        card = self._novo_card(parent, width=280)
        card.pack(side="left", fill="y", padx=5, pady=5)
        self._cabecalho_secao(card, 1, titulo, dica, largura_dica=240)

        scroll = ctk.CTkScrollableFrame(card, width=250, **filtrar_estilo(ctk.CTkScrollableFrame, dict(fg_color=COR_FUNDO, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL,
                                        scrollbar_button_color=COR_SCROLL, scrollbar_button_hover_color=COR_PRIMARIO)))
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        ctk.CTkButton(card, text="Marcar/Desmarcar Todos", command=comando_toggle, height=32, font=(FONTE_UI, 12), **ESTILO_BOTAO_DISCRETO).pack(fill="x", padx=10, pady=(0, 12))
        return scroll

    def _montar_filtros(self, parent, variavel, comando, texto_todos):
        caixa = ctk.CTkFrame(parent, fg_color=COR_PAINEL_ALT, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
        caixa.pack(fill="x", padx=12, pady=(0, 6), ipady=3)
        opcoes = (
            (texto_todos, "1"),
            ("NÃO ENVIAR para pacientes específicos", "2"),
            ("ENVIAR APENAS para pacientes específicos", "3"),
        )
        for texto, valor in opcoes:
            ctk.CTkRadioButton(caixa, text=texto, variable=variavel, value=valor, command=comando, **ESTILO_RADIO).pack(anchor="w", padx=14, pady=5)

        entrada = ctk.CTkEntry(parent, placeholder_text="Opção 'Enviar para Todos' selecionada.", state="disabled", **ESTILO_ENTRY)
        entrada.pack(fill="x", padx=12, pady=(0, 6))
        return entrada

    def _criar_kpis(self, parent, atributo_tree, indice_status, rotulos):
        if LAYOUT_ATUAL == "cockpit":
            self._criar_cockpit(parent, atributo_tree, indice_status, rotulos)
            return
        if LAYOUT_ATUAL != "dashboard":
            return
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(0, 8))
        cores = {"total": COR_TEXTO, "ok": COR_SUCESSO, "pendente": COR_ALERTA, "erro": COR_ERRO}
        valores = {}
        for col, (chave, rotulo) in enumerate(rotulos):
            linha.grid_columnconfigure(col, weight=1, uniform="kpi")
            cartao = ctk.CTkFrame(linha, fg_color=COR_PAINEL_ALT, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
            cartao.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
            ctk.CTkLabel(cartao, text=rotulo, font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE, anchor="w").pack(anchor="w", padx=12, pady=(8, 0))
            lbl = ctk.CTkLabel(cartao, text="0", font=(FONTE_UI, 22, "bold"), text_color=cores[chave], anchor="w")
            lbl.pack(anchor="w", padx=12, pady=(0, 8))
            valores[chave] = lbl
        self._ref_tabela = linha
        self._kpis.append(dict(tipo="kpi", tree=atributo_tree, idx=indice_status, labels=valores))

    def _criar_cockpit(self, parent, atributo_tree, indice_status, rotulos):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(0, 8))
        linha.grid_columnconfigure(2, weight=1)
        self._ref_tabela = linha

        col_indicadores = ctk.CTkFrame(linha, fg_color="transparent")
        col_indicadores.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        cores = {"ok": COR_SUCESSO, "pendente": COR_ALERTA, "erro": COR_ERRO}
        valores = {}
        for chave, rotulo in rotulos[1:]:
            cartao = ctk.CTkFrame(col_indicadores, fg_color=COR_PAINEL_ALT, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
            cartao.pack(fill="both", expand=True, pady=(0, 4))
            ctk.CTkFrame(cartao, width=3, height=1, fg_color=cores[chave], corner_radius=0).pack(side="left", fill="y", padx=(1, 0), pady=1)
            ctk.CTkLabel(cartao, text=rotulo, width=86, font=(FONTE_MONO, 10), text_color=COR_TEXTO_SUAVE, anchor="w").pack(side="left", padx=(8, 0), pady=4)
            lbl = ctk.CTkLabel(cartao, text="0", width=34, font=(FONTE_MONO, 18, "bold"), text_color=cores[chave], anchor="e")
            lbl.pack(side="right", padx=(0, 10), pady=4)
            valores[chave] = lbl

        largura, altura = 150, 124
        cv = tk.Canvas(linha, width=largura, height=altura, bg=COR_PAINEL_ALT, highlightthickness=1, highlightbackground=COR_BORDA, bd=0)
        cv.grid(row=0, column=1, padx=(0, 8))
        segmentos = []
        for k in range(40):
            segmentos.append(cv.create_arc(33, 30, 117, 114, start=90 - k * 9 - 6, extent=6, style="arc", outline=COR_BORDA, width=8))
        txt_pct = cv.create_text(75, 66, text="0%", fill=COR_TEXTO, font=(FONTE_MONO, 18, "bold"))
        txt_sub = cv.create_text(75, 86, text="0 de 0", fill=COR_TEXTO_SUAVE, font=(FONTE_MONO, 9))
        cv.create_text(10, 7, anchor="nw", text="PROGRESSO", fill=COR_TEXTO_SUAVE, font=(FONTE_MONO, 8))
        cv.create_line(2, 14, 2, 2, 14, 2, fill=COR_MARCA, width=2)
        cv.create_line(largura - 2, altura - 14, largura - 2, altura - 2, largura - 14, altura - 2, fill=COR_MARCA, width=2)

        col_dir = ctk.CTkFrame(linha, fg_color="transparent")
        col_dir.grid(row=0, column=2, sticky="nsew")
        col_dir.grid_columnconfigure(0, weight=1)
        spark = tk.Canvas(col_dir, height=52, bg=COR_PAINEL_ALT, highlightthickness=1, highlightbackground=COR_BORDA, bd=0)
        spark.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        spark.create_text(10, 4, anchor="nw", text="ENVIOS A CADA 5 S", fill=COR_TEXTO_SUAVE, font=(FONTE_MONO, 8))
        linha_spark = spark.create_line(8, 44, 300, 44, fill=COR_DESTAQUE, width=2)

        log = tk.Text(col_dir, height=3, bg=COR_PAINEL_ALT, fg=COR_TEXTO_SUAVE, font=(FONTE_MONO, 10), relief="flat", bd=0,
                      highlightthickness=1, highlightbackground=COR_BORDA, wrap="none", padx=8, pady=3)
        log.grid(row=1, column=0, sticky="nsew")
        col_dir.grid_rowconfigure(1, weight=1)
        log.tag_configure("hora", foreground=COR_DESTAQUE)
        log.tag_configure("ok", foreground=COR_SUCESSO)
        log.tag_configure("erro", foreground=COR_ERRO)
        log.tag_configure("and", foreground=COR_ALERTA)
        log.tag_configure("pend", foreground=COR_TEXTO_SUAVE)
        log.insert("end", "aguardando envios...\n", "pend")
        log.configure(state="disabled")

        self._kpis.append(dict(tipo="cockpit", tree=atributo_tree, idx=indice_status, labels=valores,
                               gauge=cv, segs=segmentos, txt_pct=txt_pct, txt_sub=txt_sub, acesos=-1,
                               spark=spark, spark_line=linha_spark, hist=[], ultimo=0.0, log=log, snap={}))

    def _desenhar_spark(self, item):
        hist = item["hist"]
        deltas = [max(0, hist[n] - hist[n - 1]) for n in range(1, len(hist))]
        largura = max(item["spark"].winfo_width(), 120)
        topo, base = 18, 44
        if len(deltas) < 2:
            coords = [8, base, largura - 8, base]
        else:
            maximo = max(max(deltas), 1)
            passo = (largura - 16) / (len(deltas) - 1)
            coords = []
            for n, d in enumerate(deltas):
                coords += [8 + n * passo, base - (base - topo) * d / maximo]
        item["spark"].coords(item["spark_line"], *coords)

    def _atualizar_cockpit(self, item, total, contagem, snap, agora):
        feitos = total - contagem["pendente"] - contagem["andamento"]
        pct = int(round(100 * feitos / total)) if total else 0
        acesos = int(round(40 * pct / 100))
        cv = item["gauge"]
        if acesos != item["acesos"]:
            for k, seg in enumerate(item["segs"]):
                cv.itemconfigure(seg, outline=COR_MARCA if k < acesos else COR_BORDA)
            item["acesos"] = acesos
        cv.itemconfigure(item["txt_pct"], text=f"{pct}%")
        cv.itemconfigure(item["txt_sub"], text=f"{feitos} de {total}")

        if agora - item["ultimo"] >= 5:
            item["ultimo"] = agora
            item["hist"] = (item["hist"] + [feitos])[-25:]
            self._desenhar_spark(item)

        anterior = item["snap"]
        novos = [(status, paciente) for iid, (status, paciente) in snap.items()
                 if iid in anterior and anterior[iid][0] != status]
        item["snap"] = snap
        if novos:
            log = item["log"]
            log.configure(state="normal")
            for status, paciente in novos:
                categoria = categoria_status(status)
                tag = {"ok": "ok", "erro": "erro", "andamento": "and"}.get(categoria, "pend")
                log.insert("end", datetime.now().strftime("%H:%M:%S") + "  ", "hora")
                log.insert("end", f"{limpar_texto_log(status)} > {paciente}\n", tag)
            if int(log.index("end-1c").split(".")[0]) > 120:
                log.delete("1.0", "40.0")
            log.configure(state="disabled")
            log.see("end")

    def _iniciar_atualizacao_kpis(self):
        if not self._kpis:
            return

        def atualizar():
            try:
                agora = time.monotonic()
                for item in self._kpis:
                    tree = getattr(self, item["tree"], None)
                    if tree is None:
                        continue
                    contagem = {"erro": 0, "pendente": 0, "andamento": 0, "ok": 0, "outro": 0}
                    snap = {}
                    for filho in tree.get_children():
                        valores = tree.item(filho, "values")
                        status = str(valores[item["idx"]])
                        snap[filho] = (status, str(valores[1]))
                        contagem[categoria_status(status)] += 1
                    total = len(snap)
                    mostrar = {"total": total, "ok": contagem["ok"], "pendente": contagem["pendente"], "erro": contagem["erro"]}
                    for chave, valor in mostrar.items():
                        rotulo = item["labels"].get(chave)
                        if rotulo is not None and rotulo.cget("text") != str(valor):
                            rotulo.configure(text=str(valor))
                    if item["tipo"] == "cockpit":
                        self._atualizar_cockpit(item, total, contagem, snap, agora)
            except Exception:
                pass
            self.after(600, atualizar)

        atualizar()

    def _criar_legenda(self, parent, itens):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=14, pady=(0, 6))
        for texto, cor in itens:
            ctk.CTkLabel(linha, text="●", text_color=cor, font=(FONTE_UI, 12)).pack(side="left")
            ctk.CTkLabel(linha, text=texto, text_color=COR_TEXTO_SUAVE, font=(FONTE_UI, 11)).pack(side="left", padx=(3, 14))

    def _criar_tabela(self, parent, colunas):
        caixa = ctk.CTkFrame(parent, fg_color=COR_PAINEL, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
        opcoes_pack = dict(fill="both", expand=True, padx=12, pady=(0, 12))
        ref = getattr(self, "_ref_tabela", None)
        if ref is not None and ref.master is parent:
            opcoes_pack.update(side="bottom", before=ref)
        self._ref_tabela = None
        caixa.pack(**opcoes_pack)
        tree = ttk.Treeview(caixa, columns=colunas, show="headings", height=5)
        barra = ttk.Scrollbar(caixa, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y", padx=(0, 2), pady=2)
        tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        return tree

    def _criar_rodape(self, parent, texto_resumo, texto_disparar, comando_disparar, comando_parar):
        barra = ctk.CTkFrame(parent, fg_color=COR_PAINEL, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CARD)
        irmaos = parent.pack_slaves()
        opcoes_pack = dict(side="bottom", fill="x", padx=10, pady=(6, 4))
        if irmaos:
            opcoes_pack["before"] = irmaos[0]
        barra.pack(**opcoes_pack)

        lbl_resumo = ctk.CTkLabel(barra, text=texto_resumo, font=(FONTE_MONO, 13, "bold"), text_color=COR_DESTAQUE)
        lbl_resumo.pack(side="left", padx=18)

        btn_parar = ctk.CTkButton(barra, text="■ PARAR / PAUSAR", command=comando_parar, height=ALT_RODAPE, font=(FONTE_UI, 12, "bold"), state="disabled", **ESTILO_BOTAO_PERIGO)
        btn_parar.pack(side="right", padx=(5, 12), pady=10)

        btn_disparar = ctk.CTkButton(barra, text=texto_disparar, command=comando_disparar, height=ALT_RODAPE, font=(FONTE_UI, 13, "bold"), state="disabled", **ESTILO_BOTAO_PRIMARIO)
        btn_disparar.pack(side="right", padx=5, pady=10)
        return lbl_resumo, btn_parar, btn_disparar

    # ------------------------------------------------------------------
    # BOTÃO "ATUALIZAR PLANILHA" DAS ABAS MONITORAMENTO E COBRANÇAS
    # ------------------------------------------------------------------
    def _criar_barra_atualizar(self, parent, chave):
        barra = ctk.CTkFrame(parent, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(2, 2))
        btn = ctk.CTkButton(barra, text="🔄", width=34, height=26, font=(FONTE_UI, 13),
                            command=lambda: self.ab_atualizar_planilha(chave), **ESTILO_BOTAO_ATUALIZAR)
        btn.pack(side="left", padx=(0, 4), pady=0)
        lbl = ctk.CTkLabel(barra, text="", font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE, anchor="w")
        lbl.pack(side="left", padx=(2, 12))
        setattr(self, f"{chave}_btn_atualizar", btn)
        setattr(self, f"{chave}_lbl_atualizacao", lbl)
        setattr(self, f"_{chave}_atualizando", False)

    def ab_atualizar_planilha(self, chave):
        if getattr(self, f"{chave}_em_execucao", False):
            messagebox.showwarning("Atenção", "Aguarde ou pare a execução atual antes de atualizar a planilha.")
            return
        if getattr(self, f"_{chave}_atualizando", False):
            return
        setattr(self, f"_{chave}_atualizando", True)
        getattr(self, f"{chave}_btn_atualizar").configure(state="disabled", text="⏳")
        getattr(self, f"{chave}_lbl_atualizacao").configure(text="Baixando a planilha...", text_color=COR_ALERTA)
        threading.Thread(target=self._ab_atualizar_planilha_worker, args=(chave,), daemon=True).start()

    def _ab_atualizar_planilha_worker(self, chave):
        try:
            creds = self.creds
            if creds is None or not creds.valid:
                creds = autenticar_google()
            buffer_excel = baixar_planilha_privada(creds, ID_PLANILHA)
            novo = pd.read_excel(buffer_excel, sheet_name=None, engine="openpyxl", header=None)
            buffer_excel.close()
            limpar_memoria()
            self.after(0, self._ab_no_atualizacao, chave, novo, "")
        except Exception as e:
            self.after(0, self._ab_no_atualizacao, chave, None, str(e))

    def _ab_no_atualizacao(self, chave, novo, erro):
        setattr(self, f"_{chave}_atualizando", False)
        getattr(self, f"{chave}_btn_atualizar").configure(state="normal", text="🔄")
        lbl = getattr(self, f"{chave}_lbl_atualizacao")
        if novo is None:
            lbl.configure(text=f"Erro ao atualizar: {erro}", text_color=COR_ERRO)
            return

        self.abas_dict = novo

        # recarrega só a lista de convênios desta aba, mantendo o que estava desmarcado
        checks = getattr(self, f"{chave}_checkboxes_abas")
        desmarcadas = {aba for aba, var in checks.items() if var.get() == ""}
        if chave == "mon":
            self.carregar_checkboxes_monitoramento()
        else:
            self.carregar_checkboxes_cobrancas()
        for aba, var in getattr(self, f"{chave}_checkboxes_abas").items():
            if aba in desmarcadas:
                var.set("")

        hora = datetime.now().strftime("%H:%M:%S")
        tem_lista = len(getattr(self, f"{chave}_tree").get_children()) > 0
        aviso = " — clique no botão de carregar/buscar para recalcular a lista" if tem_lista else ""
        lbl.configure(text=f"Planilha atualizada às {hora}{aviso}", text_color=COR_SUCESSO)

    # ==========================================================================
    # LÓGICA DA ABA 1: DISPAROS DE MONITORAMENTO
    # ==========================================================================
    def setup_aba_monitoramento(self):
        self.mon_checkboxes_abas = {}
        self.mon_df_filtrado = pd.DataFrame()
        self.mon_em_execucao = False
        self.mon_solicitar_parada = False
        self.mon_indice_atual = 0

        frame_main = ctk.CTkFrame(self.tab_monitoramento, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=2, pady=2)

        self.mon_scroll_convenios = self._criar_painel_convenios(
            frame_main, "Convênios", "Marque os convênios que entram nesta rodada.", self.mon_toggle_todas_abas)

        frame_direita = self._novo_card(frame_main)
        frame_direita.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self._cabecalho_secao(frame_direita, 2, "Carregar Lista", "Carregue a lista dos pacientes que vão receber a mensagem de monitoramento.")

        self.mon_var_opcao_filtro = ctk.StringVar(value="1")
        self.mon_ent_filtro_nomes = ctk.CTkEntry(frame_direita)

        self._criar_barra_atualizar(frame_direita, "mon")

        self.mon_btn_processar = ctk.CTkButton(frame_direita, text="Carregar Lista Completa de Pacientes", command=self.mon_processar_lista, height=ALT_BOTAO, font=(FONTE_UI, 13, "bold"), **ESTILO_BOTAO_SECUNDARIO)
        self.mon_btn_processar.pack(fill="x", padx=12, pady=(4, 6))

        self._cabecalho_secao(frame_direita, 3, "Tabela de Monitoramento de Envio",
                              "Ao iniciar, você tem 5 segundos para clicar na janela do WhatsApp Desktop. Mover o mouse ou apertar ESC/Espaço pausa com segurança.")

        self._criar_kpis(frame_direita, "mon_tree", 4, (("total", "Total na lista"), ("ok", "Enviados"), ("pendente", "Pendentes"), ("erro", "Com erro")))
        self._criar_legenda(frame_direita, [("Pendente", COR_TEXTO_SUAVE), ("Enviando", COR_ALERTA), ("Enviado", COR_SUCESSO), ("Bloqueado", COR_AVISO), ("Fora do dia par/ímpar", COR_DESTAQUE), ("Erro", COR_ERRO)])
        self.mon_tree = self._criar_tabela(frame_direita, ("Convenio", "Paciente", "PAD", "Status", "StatusEnvio"))
        self.mon_tree.heading("Convenio", text="Convênio")
        self.mon_tree.heading("Paciente", text="Paciente / Grupo")
        self.mon_tree.heading("PAD", text="Tipo PAD")
        self.mon_tree.heading("Status", text="Status Planilha")
        self.mon_tree.heading("StatusEnvio", text="Status Disparo")

        self.mon_tree.column("Convenio", width=110)
        self.mon_tree.column("Paciente", width=220)
        self.mon_tree.column("PAD", width=80)
        self.mon_tree.column("Status", width=60)
        self.mon_tree.column("StatusEnvio", width=150)

        self.mon_tree.tag_configure("Pendente", foreground=COR_TEXTO_SUAVE)
        self.mon_tree.tag_configure("Enviando", foreground=COR_ALERTA, font=(FONTE_MONO, 10, "bold"))
        self.mon_tree.tag_configure("Enviado", foreground=COR_SUCESSO, font=(FONTE_MONO, 10, "bold"))
        self.mon_tree.tag_configure("Bloqueado", foreground=COR_AVISO)
        self.mon_tree.tag_configure("NaoEncontrado", foreground=COR_ERRO, font=(FONTE_MONO, 10, "bold"))
        self.mon_tree.tag_configure("Pulado", foreground=COR_DESTAQUE)

        self.mon_lbl_resumo, self.mon_btn_parar, self.mon_btn_disparar = self._criar_rodape(
            self.tab_monitoramento, "Total Carregados: 0", "▶ INICIAR DISPAROS NO WHATSAPP",
            self.mon_iniciar_disparos_thread, self.mon_parar_disparos)

    def carregar_checkboxes_monitoramento(self):
        for child in self.mon_scroll_convenios.winfo_children():
            child.destroy()

        self.mon_checkboxes_abas.clear()
        self.mon_abas_encontradas = []

        for nome_aba in self.abas_dict.keys():
            nome_aba_bruto = str(nome_aba).strip()
            if eh_aba_convenio_valida(nome_aba_bruto):
                self.mon_abas_encontradas.append(nome_aba_bruto)

        for aba in self.mon_abas_encontradas:
            var = ctk.StringVar(value=aba)
            chk = ctk.CTkCheckBox(self.mon_scroll_convenios, text=aba, variable=var, onvalue=aba, offvalue="", **ESTILO_CHECKBOX)
            chk.pack(anchor="w", padx=5, pady=3)
            self.mon_checkboxes_abas[aba] = var

    def mon_toggle_todas_abas(self):
        algum_desmarcado = any(v.get() == "" for v in self.mon_checkboxes_abas.values())
        for aba, var in self.mon_checkboxes_abas.items():
            var.set(aba if algum_desmarcado else "")

    def mon_atualizar_orientacao_filtro(self):
        opcao = self.mon_var_opcao_filtro.get()
        if opcao == "1":
            self.mon_ent_filtro_nomes.configure(state="disabled", placeholder_text="Opção 'Enviar para Todos' selecionada.")
            self.mon_ent_filtro_nomes.delete(0, "end")
        elif opcao == "2":
            self.mon_ent_filtro_nomes.configure(state="normal", placeholder_text="Digite os nomes que NÃO devem receber, separados por vírgula")
        elif opcao == "3":
            self.mon_ent_filtro_nomes.configure(state="normal", placeholder_text="Digite APENAS os nomes que devem receber, separados por vírgula")

    def mon_processar_lista(self):
        if self.mon_em_execucao:
            messagebox.showwarning("Atenção", "Aguarde a interrupção da execução atual antes de carregar uma nova lista.")
            return

        if not self._exigir_operador():
            return

        abas_selecionadas = [var.get() for var in self.mon_checkboxes_abas.values() if var.get() != ""]
        if not abas_selecionadas:
            messagebox.showwarning("Atenção", "Selecione ao menos um convênio na lista da esquerda.")
            return

        lista_dfs = []
        for nome_aba in abas_selecionadas:
            if nome_aba not in self.abas_dict:
                continue

            df_raw = self.abas_dict[nome_aba]
            if df_raw.empty or len(df_raw) < 2:
                continue

            is_ssa = eh_aba_ssa(nome_aba)
            df_aba = normalizar_df(df_raw.copy())

            col_grupo = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["PACIENTE", "PACIENTES", "NOME", "GRUPO", "BENEFICIARIO"])), None)
            if not col_grupo and len(df_aba.columns) > 0:
                col_grupo = df_aba.columns[0]

            col_status = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["STATUS", "ATI", "ST", "SITUAÇÃO", "SITUACAO"])), None)
            if not col_status and len(df_aba.columns) > 1:
                col_status = df_aba.columns[1]

            col_pad = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["PAD", "TIPO", "HORARIO", "HORÁRIO"])), None)

            if col_grupo and col_status:
                s_paciente = df_aba[col_grupo]
                s_status = df_aba[col_status]
                s_pad = df_aba[col_pad] if (col_pad and not is_ssa and col_pad in df_aba.columns) else ""

                temp_df = pd.DataFrame({
                    "Paciente": s_paciente,
                    "Status": s_status,
                    "PAD": s_pad,
                    "Convenio": nome_aba.strip()
                })
                
                temp_df = temp_df.dropna(subset=["Paciente"])
                lista_dfs.append(temp_df)

        if not lista_dfs:
            messagebox.showerror("Erro", "Não foi possível estruturar os dados dos convênios escolhidos.")
            return

        df = pd.concat(lista_dfs, ignore_index=True)
        df["Paciente"] = df["Paciente"].fillna("").astype(str).str.replace('\xa0', ' ').str.strip()
        df["Status"] = df["Status"].fillna("").astype(str).str.replace('\xa0', ' ').str.strip()

        df = df[(df["Paciente"] != "") & (df["Paciente"].str.lower() != "nan") & (~df["Paciente"].apply(grupo_esta_bloqueado))].copy()
        df_filtrado = df[df["Status"].apply(status_eh_ok)].copy()

        opcao = self.mon_var_opcao_filtro.get()
        nomes_input = self.mon_ent_filtro_nomes.get().strip()

        if opcao == "2" and nomes_input:
            lista_excluir = [remover_acentos(nome) for nome in nomes_input.split(",") if nome.strip()]
            df_filtrado = df_filtrado[~df_filtrado["Paciente"].apply(lambda p: any(ex in remover_acentos(p) for ex in lista_excluir))]
        elif opcao == "3" and nomes_input:
            lista_incluir = [remover_acentos(nome) for nome in nomes_input.split(",") if nome.strip()]
            df_filtrado = df_filtrado[df_filtrado["Paciente"].apply(lambda p: any(inc in remover_acentos(p) for inc in lista_incluir))]

        self.mon_df_filtrado = df_filtrado.reset_index(drop=True)
        self.mon_indice_atual = 0
        self.mon_solicitar_parada = False

        for row in self.mon_tree.get_children():
            self.mon_tree.delete(row)

        for _, row in self.mon_df_filtrado.iterrows():
            self.mon_tree.insert("", "end", values=(row["Convenio"], row["Paciente"], row["PAD"], row["Status"], "⏳ Pendente"), tags=("Pendente",))

        _hoje = datetime.now()
        _amanha = _hoje + timedelta(days=1)
        fora_do_dia = 0
        for _, _linha in self.mon_df_filtrado.iterrows():
            if eh_aba_ssa(str(_linha["Convenio"])):
                continue
            _regra = interpretar_pad_paridade(_linha["PAD"], _linha["Status"], _hoje.day, _amanha.day)
            if _regra is not None and not (_regra["noturno"] or _regra["diurno"]):
                fora_do_dia += 1
        texto_resumo = f"Total Carregados: {len(self.mon_df_filtrado)}"
        if fora_do_dia:
            texto_resumo += f"  |  fora do dia par/ímpar hoje: {fora_do_dia}"
        self.mon_lbl_resumo.configure(text=texto_resumo)

        del lista_dfs, df
        limpar_memoria()

        if len(self.mon_df_filtrado) > 0:
            self.mon_btn_disparar.configure(state="normal", text="▶ INICIAR DISPAROS NO WHATSAPP", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        else:
            self.mon_btn_disparar.configure(state="disabled")

    def mon_atualizar_status_linha(self, item_id, novo_status, tag_cor):
        valores = list(self.mon_tree.item(item_id, "values"))
        valores[4] = novo_status
        self.mon_tree.item(item_id, values=valores, tags=(tag_cor,))
        self.mon_tree.see(item_id)

    def mon_parar_disparos(self):
        if self.mon_em_execucao:
            self.mon_solicitar_parada = True
            self.mon_btn_parar.configure(state="disabled", text="■ PARANDO...")

    def mon_iniciar_disparos_thread(self):
        if self.mon_em_execucao:
            return

        if not self._exigir_operador():
            return

        pendentes = [i for i, child in enumerate(self.mon_tree.get_children()) if "⏳ Pendente" in str(self.mon_tree.item(child, "values")[4])]
        if not pendentes and self.mon_indice_atual >= len(self.mon_df_filtrado):
            messagebox.showinfo("Aviso", "Todos os pacientes pendentes foram processados!")
            return

        texto_msg = f"Serão enviadas mensagens para {len(pendentes)} pacientes pendentes.\n\nApós clicar em SIM, você terá 5 segundos para CLICAR na janela do WhatsApp Desktop.\n\n⚠ Qualquer movimento rápido de mouse ou tecla cancelará com segurança."
        if messagebox.askyesno("Confirmar Disparos", texto_msg):
            self.mon_em_execucao = True
            self.mon_solicitar_parada = False
            self.mon_btn_disparar.configure(state="disabled")
            self.mon_btn_processar.configure(state="disabled")
            self.mon_btn_parar.configure(state="normal", text="■ PARAR / PAUSAR")
            
            threading.Thread(target=self._mon_executar_disparos_worker, daemon=True).start()

    def _mon_finalizar_loop(self, motivo=""):
        self.mon_em_execucao = False
        self.mon_btn_disparar.configure(state="normal", text="▶ REINICIAR / CONTINUAR DISPAROS", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        self.mon_btn_processar.configure(state="normal")
        self.mon_btn_parar.configure(state="disabled", text="■ PARAR / PAUSAR")

        limpar_memoria()

        total = len(self.mon_tree.get_children())
        enviados = sum(1 for item_id in self.mon_tree.get_children() if "🟢 Enviado" in str(self.mon_tree.item(item_id, "values")[4]))
        erros = sum(1 for item_id in self.mon_tree.get_children() if "❌ Erro" in str(self.mon_tree.item(item_id, "values")[4]))
        bloqueados = sum(1 for item_id in self.mon_tree.get_children() if "⚠️ Bloqueado" in str(self.mon_tree.item(item_id, "values")[4]))
        pendentes = sum(1 for item_id in self.mon_tree.get_children() if "⏳ Pendente" in str(self.mon_tree.item(item_id, "values")[4]))
        pulados = sum(1 for item_id in self.mon_tree.get_children() if "⏭" in str(self.mon_tree.item(item_id, "values")[4]))

        resumo_msg = (
            f"📊 BALANÇO DE DISPAROS (MONITORAMENTO)\n\n"
            f"🔹 Total Processados: {total}\n"
            f"🟢 Enviados com Sucesso: {enviados}\n"
            f"⏭ Fora do dia par/ímpar (sem envio): {pulados}\n"
            f"⚠️ Bloqueados: {bloqueados}\n"
            f"❌ Com Erro: {erros}\n"
            f"⏳ Pendentes Restantes: {pendentes}\n\n"
        )

        if pendentes == 0 and erros == 0:
            resumo_msg += "🎉 EXCELENTE! Todos os pacientes receberam a mensagem com sucesso!"
        elif pendentes > 0:
            resumo_msg += f"⚠️ ATENÇÃO: Restam {pendentes} paciente(s) sem envio.\nClique em 'REINICIAR / CONTINUAR' para disparar para os faltantes."

        if motivo:
            resumo_msg = f"MOTIVO DA PAUSA: {motivo}\n\n" + resumo_msg

        messagebox.showinfo("Resumo da Automação", resumo_msg)

    def _mon_executar_disparos_worker(self):
        for i in range(5, 0, -1):
            if self.mon_solicitar_parada:
                break
            self.after(0, lambda sec=i: self.mon_btn_disparar.configure(text=f"CLIQUE NO WHATSAPP! ({sec}s)..."))
            time.sleep(1)

        if self.mon_solicitar_parada:
            self.after(0, self._mon_finalizar_loop, "Parado antes de iniciar.")
            return

        self.after(0, lambda: self.mon_btn_disparar.configure(text="ENVIANDO MENSAGENS..."))

        nome_operador = self.ent_operador.get().strip()
        cabecalho_nome = f"*Setor de Monitoramento - {nome_operador}:*" if nome_operador else "*Setor de Monitoramento:*"

        dt_hoje = datetime.now()
        dt_amanha = dt_hoje + timedelta(days=1)
        hoje = dt_hoje.strftime("%d/%m")
        amanha = dt_amanha.strftime("%d/%m")

        MENSAGEM_SSA = f"{cabecalho_nome}\n\n🔷 MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão de amanhã ({amanha})?\n➡️ Diurno e Noturno\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_PADRAO = f"{cabecalho_nome}\n\n🔷 MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão *Noturno de hoje ({hoje})?*\n🗓 Confirmado plantão *Diurno de amanhã ({amanha})?*\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_DIURNO = f"{cabecalho_nome}\n\n🔷 MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão *Diurno de amanhã ({amanha})?*\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_NOTURNO = f"{cabecalho_nome}\n\n🔷 MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão *Noturno de hoje ({hoje})?*\n\nAtenciosamente,\nSetor de Monitoramento"

        pyautogui.PAUSE = 0.1
        total = len(self.mon_tree.get_children())
        itens_tabela = self.mon_tree.get_children()
        pos_mouse_ref = pyautogui.position()
        motivo_interrupcao = ""

        for indice in range(self.mon_indice_atual, total):
            if self.mon_solicitar_parada:
                self.mon_indice_atual = indice
                motivo_interrupcao = "Interrupção solicitada pelo usuário."
                break

            item_id = itens_tabela[indice]
            valores_linha = self.mon_tree.item(item_id, "values")
            status_atual = str(valores_linha[4])

            if "⏳ Pendente" not in status_atual:
                continue

            self.mon_indice_atual = indice
            grupo = str(valores_linha[1]).replace('\xa0', ' ').strip()
            pad_valor = str(valores_linha[2]).replace('\xa0', ' ').strip().lower()
            convenio = str(valores_linha[0]).strip()
            nome_busca_norm = normalizar_nome_busca(grupo)

            if grupo_esta_bloqueado(grupo) or grupo_esta_bloqueado(nome_busca_norm):
                self.after(0, self.mon_atualizar_status_linha, item_id, "⚠ Bloqueado", "Bloqueado")
                continue

            regra_pad = None
            if not eh_aba_ssa(convenio):
                regra_pad = interpretar_pad_paridade(valores_linha[2], valores_linha[3], dt_hoje.day, dt_amanha.day)
                if regra_pad is not None and not (regra_pad["noturno"] or regra_pad["diurno"]):
                    self.after(0, self.mon_atualizar_status_linha, item_id, f"⏭ Fora do dia: {regra_pad['texto']}", "Pulado")
                    continue

            self.after(0, self.mon_atualizar_status_linha, item_id, "🟡 Enviando...", "Enviando")

            if eh_aba_ssa(convenio):
                mensagem_final = MENSAGEM_SSA
            elif regra_pad is not None:
                if regra_pad["noturno"] and regra_pad["diurno"]:
                    mensagem_final = MENSAGEM_PAD_PADRAO
                elif regra_pad["diurno"]:
                    mensagem_final = MENSAGEM_PAD_DIURNO
                else:
                    mensagem_final = MENSAGEM_PAD_NOTURNO
            else:
                if "24h" in pad_valor or "24 h" in pad_valor or "24" in pad_valor:
                    mensagem_final = MENSAGEM_PAD_PADRAO
                elif "diurno" in pad_valor or "dia" in pad_valor:
                    mensagem_final = MENSAGEM_PAD_DIURNO
                elif "noturno" in pad_valor or "noite" in pad_valor:
                    mensagem_final = MENSAGEM_PAD_NOTURNO
                else:
                    mensagem_final = MENSAGEM_PAD_PADRAO

            try:
                interrompido, razao = self.checar_interrupcao_usuario(pos_mouse_ref, self.mon_solicitar_parada)
                if interrompido:
                    self.mon_solicitar_parada = True
                    motivo_interrupcao = f"Interrompido em '{grupo}': {razao}"
                    self.after(0, self.mon_atualizar_status_linha, item_id, "⏳ Pendente", "Pendente")
                    break

                pyautogui.press('esc')
                time.sleep(0.15)
                pyautogui.press('esc')
                
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.4)
                
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')

                nome_bruto = grupo.split("(")[0].replace('\xa0', ' ').strip()
                nome_busca = remover_acentos(nome_bruto)

                pyperclip.copy(nome_busca)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1.5)

                pyautogui.press('down')
                time.sleep(0.3)
                pyautogui.press('enter')
                time.sleep(1.0)

                pyperclip.copy(mensagem_final)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.4)
                pyautogui.press('enter')
                time.sleep(0.8)

                self.after(0, self.mon_atualizar_status_linha, item_id, "🟢 Enviado", "Enviado")

            except Exception as e:
                self.after(0, self.mon_atualizar_status_linha, item_id, f"❌ Erro: {str(e)}", "NaoEncontrado")

            time.sleep(random.uniform(1.0, 1.8))

        self.after(0, self._mon_finalizar_loop, motivo_interrupcao)

    # ==========================================================================
    # LÓGICA DA ABA 2: CONFIRMAÇÕES E COBRANÇAS
    # ==========================================================================
    def setup_aba_cobrancas(self):
        self.cob_checkboxes_abas = {}
        self.cob_df_filtrado = pd.DataFrame()
        self.cob_em_execucao = False
        self.cob_solicitar_parada = False
        self.cob_indice_atual = 0

        frame_main = ctk.CTkFrame(self.tab_cobrancas, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=2, pady=2)

        self.cob_scroll_convenios = self._criar_painel_convenios(
            frame_main, "Convênios", "Marque os convênios onde buscar pendências.", self.cob_toggle_todas_abas)

        frame_direita = self._novo_card(frame_main)
        frame_direita.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self._cabecalho_secao(frame_direita, 2, "Busca de Pendências", "Busque os plantões ainda pendentes de confirmação (Noturno de hoje e Diurno de amanhã).")

        self.cob_var_opcao_filtro = ctk.StringVar(value="1")
        self.cob_ent_filtro_nomes = ctk.CTkEntry(frame_direita)

        self._criar_barra_atualizar(frame_direita, "cob")

        self.cob_btn_processar = ctk.CTkButton(
            frame_direita,
            text="Buscar Pendências de Confirmação/Cobrança",
            command=self.cob_processar_lista,
            height=ALT_BOTAO,
            font=(FONTE_UI, 13, "bold"),
            **ESTILO_BOTAO_SECUNDARIO
        )
        self.cob_btn_processar.pack(fill="x", padx=12, pady=(4, 6))

        self._cabecalho_secao(frame_direita, 3, "Tabela de Cobranças e Confirmações",
                              "Ao iniciar, você tem 5 segundos para clicar na janela do WhatsApp Desktop. Mover o mouse pausa com segurança.")

        self._criar_kpis(frame_direita, "cob_tree", 4, (("total", "Total na lista"), ("ok", "Enviados"), ("pendente", "Pendentes"), ("erro", "Com erro")))
        self._criar_legenda(frame_direita, [("Pendente", COR_TEXTO_SUAVE), ("Enviando", COR_ALERTA), ("Enviado", COR_SUCESSO), ("Bloqueado", COR_AVISO), ("Não lida (pulado)", COR_DESTAQUE), ("Erro", COR_ERRO)])
        self.cob_tree = self._criar_tabela(frame_direita, ("Convenio", "Paciente", "StatusNoturno", "StatusDiurno", "StatusEnvio"))
        self.cob_tree.heading("Convenio", text="Convênio")
        self.cob_tree.heading("Paciente", text="Paciente / Grupo")
        self.cob_tree.heading("StatusNoturno", text="Noturno (Hoje)")
        self.cob_tree.heading("StatusDiurno", text="Diurno (Amanhã)")
        self.cob_tree.heading("StatusEnvio", text="Status Disparo")

        self.cob_tree.column("Convenio", width=110)
        self.cob_tree.column("Paciente", width=220)
        self.cob_tree.column("StatusNoturno", width=110)
        self.cob_tree.column("StatusDiurno", width=110)
        self.cob_tree.column("StatusEnvio", width=150)

        self.cob_tree.tag_configure("Pendente", foreground=COR_TEXTO_SUAVE)
        self.cob_tree.tag_configure("Enviando", foreground=COR_ALERTA, font=(FONTE_MONO, 10, "bold"))
        self.cob_tree.tag_configure("Enviado", foreground=COR_SUCESSO, font=(FONTE_MONO, 10, "bold"))
        self.cob_tree.tag_configure("Bloqueado", foreground=COR_AVISO)
        self.cob_tree.tag_configure("Pulado", foreground=COR_DESTAQUE)
        self.cob_tree.tag_configure("NaoEncontrado", foreground=COR_ERRO, font=(FONTE_MONO, 10, "bold"))

        self.cob_lbl_resumo, self.cob_btn_parar, self.cob_btn_disparar = self._criar_rodape(
            self.tab_cobrancas, "Total Pendentes: 0", "▶ INICIAR COBRANÇAS NO WHATSAPP",
            self.cob_iniciar_disparos_thread, self.cob_parar_disparos)

    def carregar_checkboxes_cobrancas(self):
        for child in self.cob_scroll_convenios.winfo_children():
            child.destroy()

        self.cob_checkboxes_abas.clear()
        for aba in self.abas_dict.keys():
            aba_str = str(aba).strip()
            if eh_aba_convenio_valida(aba_str):
                var = ctk.StringVar(value=aba_str)
                chk = ctk.CTkCheckBox(self.cob_scroll_convenios, text=aba_str, variable=var, onvalue=aba_str, offvalue="", **ESTILO_CHECKBOX)
                chk.pack(anchor="w", padx=5, pady=3)
                self.cob_checkboxes_abas[aba_str] = var

    def cob_toggle_todas_abas(self):
        algum_desmarcado = any(v.get() == "" for v in self.cob_checkboxes_abas.values())
        for aba, var in self.cob_checkboxes_abas.items():
            var.set(aba if algum_desmarcado else "")

    def cob_atualizar_orientacao_filtro(self):
        opcao = self.cob_var_opcao_filtro.get()
        if opcao == "1":
            self.cob_ent_filtro_nomes.configure(state="disabled", placeholder_text="Opção 'Enviar para Todos' selecionada.")
            self.cob_ent_filtro_nomes.delete(0, "end")
        elif opcao == "2":
            self.cob_ent_filtro_nomes.configure(state="normal", placeholder_text="Digite os nomes que NÃO devem receber, separados por vírgula")
        elif opcao == "3":
            self.cob_ent_filtro_nomes.configure(state="normal", placeholder_text="Digite APENAS os nomes que devem receber, separados por vírgula")

    def cob_processar_lista(self):
        if self.cob_em_execucao:
            messagebox.showwarning("Atenção", "Aguarde a interrupção da execução atual antes de carregar uma nova lista.")
            return

        if not self._exigir_operador():
            return

        abas_selecionadas = [var.get() for var in self.cob_checkboxes_abas.values() if var.get() != ""]
        if not abas_selecionadas:
            messagebox.showwarning("Atenção", "Selecione ao menos um convênio na lista da esquerda.")
            return

        lista_cobrancas = []
        turnos_sem_coluna = []

        def eh_celula_pendente(val):
            # Exige explicitamente a palavra 'PENDENTE' na célula
            if val is None or pd.isna(val):
                return False
            return "PENDENTE" in normalizar_para_comparar(str(val).replace('\xa0', ' '))

        _re_qualquer_data = re.compile(r"(?<!\d)\d{1,2}\s*[/\-.]\s*\d{1,2}(?!\d)|\d{4}-\d{2}-\d{2}")

        def colunas_do_turno(colunas, turno, data_dt):
            turno_norm = normalizar_para_comparar(turno)
            candidatas = [c for c in colunas if turno_norm in normalizar_para_comparar(str(c))]
            if not candidatas:
                return []
            padroes = [
                rf"(?<!\d)0?{data_dt.day}\s*[/\-.]\s*0?{data_dt.month}(?!\d)",
                rf"(?<!\d){data_dt.year}-0?{data_dt.month}-0?{data_dt.day}(?!\d)",
            ]
            do_dia = [c for c in candidatas if any(re.search(pt, str(c)) for pt in padroes)]
            if do_dia:
                return do_dia
            # Cabecalho sem data (ex.: so "NOTURNO"): usa a primeira coluna do turno.
            sem_data = [c for c in candidatas if not _re_qualquer_data.search(str(c))]
            return sem_data[:1]

        hoje_dt = datetime.now()
        amanha_dt = hoje_dt + timedelta(days=1)

        str_hoje = hoje_dt.strftime("%d/%m")
        str_amanha = amanha_dt.strftime("%d/%m")

        for nome_aba in abas_selecionadas:
            if nome_aba not in self.abas_dict:
                continue

            df_raw = self.abas_dict[nome_aba]
            if df_raw.empty or len(df_raw) < 2:
                continue

            df_aba = normalizar_df(df_raw.copy())

            col_paciente = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["PACIENTE", "PACIENTES", "NOME", "GRUPO", "BENEFICIARIO"])), None)
            if not col_paciente and len(df_aba.columns) > 0:
                col_paciente = df_aba.columns[0]

            col_status = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["STATUS", "ATI", "ST", "SITUAÇÃO", "SITUACAO"])), None)
            if not col_status and len(df_aba.columns) > 1:
                col_status = df_aba.columns[1]

            colunas_validas = [
                c for c in df_aba.columns
                if not any(x in str(c).upper() for x in ["STATUS", "OBS", "SITUAÇÃO", "SITUACAO", "HISTORICO", "RESULTADO", "DISPARO"])
            ]

            cols_noturno = colunas_do_turno(colunas_validas, "NOTURNO", hoje_dt)
            cols_diurno = colunas_do_turno(colunas_validas, "DIURNO", amanha_dt)
            if not cols_noturno:
                turnos_sem_coluna.append(f"{nome_aba.strip()}: Noturno de {str_hoje}")
            if not cols_diurno:
                turnos_sem_coluna.append(f"{nome_aba.strip()}: Diurno de {str_amanha}")

            if col_paciente:
                for _, row in df_aba.iterrows():
                    if col_status and col_status in row:
                        val_status = row[col_status]
                        if not status_eh_ok(val_status) or "INATIV" in normalizar_para_comparar(val_status):
                            continue

                    paciente_nome = str(row[col_paciente]).replace('\xa0', ' ').strip()
                    if not paciente_nome or paciente_nome.lower() == "nan" or grupo_esta_bloqueado(paciente_nome):
                        continue

                    noturno_pendente = any(eh_celula_pendente(row[c]) for c in cols_noturno if c in row)
                    diurno_pendente = any(eh_celula_pendente(row[c]) for c in cols_diurno if c in row)

                    # Entra na lista SE E SOMENTE SE houver a palavra "PENDENTE" explicitamente
                    if noturno_pendente or diurno_pendente:
                        lista_cobrancas.append({
                            "Convenio": nome_aba.strip(),
                            "Paciente": paciente_nome,
                            "NoturnoPendente": noturno_pendente,
                            "DiurnoPendente": diurno_pendente,
                            "TxtNoturno": "PENDENTE" if noturno_pendente else "OK",
                            "TxtDiurno": "PENDENTE" if diurno_pendente else "OK"
                        })

        df_filtrado = pd.DataFrame(lista_cobrancas)

        if not df_filtrado.empty:
            opcao = self.cob_var_opcao_filtro.get()
            nomes_input = self.cob_ent_filtro_nomes.get().strip()

            if opcao == "2" and nomes_input:
                lista_excluir = [remover_acentos(nome) for nome in nomes_input.split(",") if nome.strip()]
                df_filtrado = df_filtrado[~df_filtrado["Paciente"].apply(lambda p: any(ex in remover_acentos(p) for ex in lista_excluir))]
            elif opcao == "3" and nomes_input:
                lista_incluir = [remover_acentos(nome) for nome in nomes_input.split(",") if nome.strip()]
                df_filtrado = df_filtrado[df_filtrado["Paciente"].apply(lambda p: any(inc in remover_acentos(p) for inc in lista_incluir))]

        self.cob_df_filtrado = df_filtrado.reset_index(drop=True)
        self.cob_indice_atual = 0
        self.cob_solicitar_parada = False

        for row in self.cob_tree.get_children():
            self.cob_tree.delete(row)

        for _, row in self.cob_df_filtrado.iterrows():
            self.cob_tree.insert("", "end", values=(row["Convenio"], row["Paciente"], row["TxtNoturno"], row["TxtDiurno"], "⏳ Pendente"), tags=("Pendente",))

        self.cob_lbl_resumo.configure(text=f"Total Pendentes: {len(self.cob_df_filtrado)}")

        limpar_memoria()

        if len(self.cob_df_filtrado) > 0:
            self.cob_btn_disparar.configure(state="normal", text="▶ INICIAR COBRANÇAS NO WHATSAPP", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        else:
            self.cob_btn_disparar.configure(state="disabled")

        if turnos_sem_coluna:
            messagebox.showwarning(
                "Coluna do dia não encontrada",
                "Não achei a coluna da data abaixo, então esse turno NÃO será cobrado:\n\n"
                + "\n".join(f"• {t}" for t in turnos_sem_coluna)
                + "\n\n(Noturno usa a coluna de hoje; Diurno usa a coluna de amanhã. Ex.: \"19/10 - Diurno\")"
            )

    def cob_atualizar_status_linha(self, item_id, novo_status, tag_cor):
        valores = list(self.cob_tree.item(item_id, "values"))
        valores[4] = novo_status
        self.cob_tree.item(item_id, values=valores, tags=(tag_cor,))
        self.cob_tree.see(item_id)

    def cob_parar_disparos(self):
        if self.cob_em_execucao:
            self.cob_solicitar_parada = True
            self.cob_btn_parar.configure(state="disabled", text="■ PARANDO...")

    def cob_iniciar_disparos_thread(self):
        if self.cob_em_execucao:
            return

        if not self._exigir_operador():
            return

        pendentes = [i for i, child in enumerate(self.cob_tree.get_children()) if "⏳ Pendente" in str(self.cob_tree.item(child, "values")[4])]
        if not pendentes and self.cob_indice_atual >= len(self.cob_df_filtrado):
            messagebox.showinfo("Aviso", "Todos os pacientes com pendência foram processados!")
            return

        texto_msg = f"Serão enviadas mensagens de cobrança/confirmação para {len(pendentes)} pacientes.\n\nApós clicar em SIM, você terá 5 segundos para CLICAR na janela do WhatsApp Desktop.\n\n⚠ Qualquer movimento rápido de mouse cancelará com segurança."
        if messagebox.askyesno("Confirmar Cobranças", texto_msg):
            self.cob_em_execucao = True
            self.cob_solicitar_parada = False
            self.cob_btn_disparar.configure(state="disabled")
            self.cob_btn_processar.configure(state="disabled")
            self.cob_btn_parar.configure(state="normal", text="■ PARAR / PAUSAR")

            threading.Thread(target=self._cob_executar_disparos_worker, daemon=True).start()

    def _cob_finalizar_loop(self, motivo=""):
        self.cob_em_execucao = False
        self.cob_btn_disparar.configure(state="normal", text="▶ REINICIAR / CONTINUAR COBRANÇAS", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        self.cob_btn_processar.configure(state="normal")
        self.cob_btn_parar.configure(state="disabled", text="■ PARAR / PAUSAR")

        limpar_memoria()

        total = len(self.cob_tree.get_children())
        enviados = sum(1 for item in self.cob_tree.get_children() if "🟢 Enviado" in str(self.cob_tree.item(item, "values")[4]))
        erros = sum(1 for item in self.cob_tree.get_children() if "❌ Erro" in str(self.cob_tree.item(item, "values")[4]))
        pendentes = sum(1 for item in self.cob_tree.get_children() if "⏳ Pendente" in str(self.cob_tree.item(item, "values")[4]))

        resumo_msg = (
            f"📊 BALANÇO DE COBRANÇAS / CONFIRMAÇÕES\n\n"
            f"🔹 Total Processados: {total}\n"
            f"🟢 Enviados com Sucesso: {enviados}\n"
            f"❌ Com Erro: {erros}\n"
            f"⏳ Pendentes Restantes: {pendentes}\n\n"
        )

        if motivo:
            resumo_msg = f"MOTIVO DA PAUSA: {motivo}\n\n" + resumo_msg

        messagebox.showinfo("Resumo da Automação", resumo_msg)

    def _cob_executar_disparos_worker(self):
        for i in range(5, 0, -1):
            if self.cob_solicitar_parada:
                break
            self.after(0, lambda sec=i: self.cob_btn_disparar.configure(text=f"CLIQUE NO WHATSAPP! ({sec}s)..."))
            time.sleep(1)

        if self.cob_solicitar_parada:
            self.after(0, self._cob_finalizar_loop, "Parado antes de iniciar.")
            return

        self.after(0, lambda: self.cob_btn_disparar.configure(text="ENVIANDO COBRANÇAS..."))

        nome_operador = self.ent_operador.get().strip()
        cabecalho_nome = f"*Setor de Monitoramento - {nome_operador}*" if nome_operador else "*Setor de Monitoramento*"

        pyautogui.PAUSE = 0.1
        total = len(self.cob_tree.get_children())
        itens_tabela = self.cob_tree.get_children()
        pos_mouse_ref = pyautogui.position()
        motivo_interrupcao = ""

        for indice in range(self.cob_indice_atual, total):
            if self.cob_solicitar_parada:
                self.cob_indice_atual = indice
                motivo_interrupcao = "Interrupção solicitada pelo usuário."
                break

            item_id = itens_tabela[indice]
            valores_linha = self.cob_tree.item(item_id, "values")
            status_atual = str(valores_linha[4])

            if "⏳ Pendente" not in status_atual:
                continue

            self.cob_indice_atual = indice
            dados_row = self.cob_df_filtrado.iloc[indice]

            grupo = dados_row["Paciente"]
            noturno_pendente = dados_row["NoturnoPendente"]
            diurno_pendente = dados_row["DiurnoPendente"]

            linhas_msg = [cabecalho_nome, ""]
            if noturno_pendente:
                linhas_msg.append("🟡 Pendente confirmação do Noturno Hoje. Plantão confirmado?")
            if diurno_pendente:
                linhas_msg.append("🟡 Pendente confirmação do Diurno Amanhã. Plantão confirmado?")

            mensagem_final = "\n".join(linhas_msg)
            nome_busca_norm = normalizar_nome_busca(grupo)

            if grupo_esta_bloqueado(grupo) or grupo_esta_bloqueado(nome_busca_norm):
                self.after(0, self.cob_atualizar_status_linha, item_id, "⚠ Bloqueado", "Bloqueado")
                continue

            self.after(0, self.cob_atualizar_status_linha, item_id, "🟡 Enviando...", "Enviando")

            try:
                interrompido, razao = self.checar_interrupcao_usuario(pos_mouse_ref, self.cob_solicitar_parada)
                if interrompido:
                    self.cob_solicitar_parada = True
                    motivo_interrupcao = f"Interrompido em '{grupo}': {razao}"
                    self.after(0, self.cob_atualizar_status_linha, item_id, "⏳ Pendente", "Pendente")
                    break

                pyautogui.press('esc')
                time.sleep(0.15)
                pyautogui.press('esc')

                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.4)

                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')

                nome_bruto = grupo.split("(")[0].replace('\xa0', ' ').strip()
                nome_busca = normalizar_para_comparar(nome_bruto)

                pyperclip.copy(nome_busca)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1.5)

                pyautogui.hotkey('ctrl', 'a')
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.2)
                conteudo_busca = pyperclip.paste().lower()

                if "não lida" in conteudo_busca or "unread" in conteudo_busca:
                    pyautogui.press('esc')
                    time.sleep(0.2)
                    pyautogui.press('esc')
                    self.after(0, self.cob_atualizar_status_linha, item_id, "📩 Não Lida (Pulado)", "Pulado")
                    continue

                pyautogui.press('down')
                time.sleep(0.3)
                pyautogui.press('enter')
                time.sleep(1.0)

                pyperclip.copy(mensagem_final)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.4)
                pyautogui.press('enter')
                time.sleep(0.8)

                self.after(0, self.cob_atualizar_status_linha, item_id, "🟢 Enviado", "Enviado")

            except Exception as e:
                self.after(0, self.cob_atualizar_status_linha, item_id, f"❌ Erro: {str(e)}", "NaoEncontrado")

            time.sleep(random.uniform(1.0, 1.8))

        self.after(0, self._cob_finalizar_loop, motivo_interrupcao)

    # ==========================================================================
    # LÓGICA DA ABA 3: ATUALIZAÇÃO VIA API (PLATAFORMA DE MONITORAMENTO)
    # ==========================================================================
    def setup_aba_command_center(self):
        self.cc_checkboxes_abas = {}
        self.cc_df_filtrado = pd.DataFrame()
        self.cc_em_execucao = False
        self.cc_solicitar_parada = False
        self.cc_indice_atual = 0
        self.cc_abas_dict = {}
        self.cc_itens_info = []
        self._cc_atualizando = False

        frame_main = ctk.CTkFrame(self.tab_command_center, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=2, pady=2)

        self.cc_scroll_convenios = self._criar_painel_convenios(
            frame_main, "Convênios / Parceiros", "Marque o convênio (parceiro) que será atualizado.", self.cc_toggle_todas_abas)

        frame_direita = self._novo_card(frame_main)
        frame_direita.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self._cabecalho_secao(frame_direita, 2, "Parâmetros do Command Center")
        self._cc_cab_param = frame_direita.pack_slaves()[-1]
        self._cc_params_visiveis = True

        f_config = ctk.CTkFrame(frame_direita, fg_color=COR_PAINEL_ALT, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
        f_config.pack(fill="x", padx=12, pady=(0, 2))
        self._cc_f_config = f_config
        f_config.grid_columnconfigure(3, weight=1)

        dt_hoje_str = datetime.now().strftime("%Y-%m-%d")
        fonte_rotulo = (FONTE_UI, 12, "bold")

        ctk.CTkLabel(f_config, text="Data (AAAA-MM-DD):", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=0, column=0, padx=(14, 10), pady=(8, 4), sticky="w")
        self.cc_ent_data = ctk.CTkEntry(f_config, width=150, **ESTILO_ENTRY)
        self.cc_ent_data.insert(0, dt_hoje_str)
        self.cc_ent_data.grid(row=0, column=1, padx=5, pady=(8, 4), sticky="w")

        self.cc_lbl_turno = ctk.CTkLabel(f_config, text="Turno:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE)
        self.cc_lbl_turno.grid(row=0, column=2, padx=(20, 10), pady=(12, 8), sticky="w")
        self.cc_cmb_turno = ctk.CTkOptionMenu(
            f_config, values=["Ambos", "Diurno", "Noturno"], **filtrar_estilo(ctk.CTkOptionMenu, dict(width=150, height=34, corner_radius=RAIO_CTRL,
            fg_color=COR_FUNDO, button_color=COR_PRIMARIO, button_hover_color=COR_PRIMARIO_HOVER,
            text_color=COR_TEXTO, font=(FONTE_MONO, 12), dropdown_font=(FONTE_MONO, 12),
            dropdown_fg_color=COR_PAINEL_ALT, dropdown_hover_color=COR_HOVER, dropdown_text_color=COR_TEXTO)))
        self.cc_cmb_turno.set("Ambos")
        self.cc_cmb_turno.grid(row=0, column=3, padx=5, pady=(12, 8), sticky="w")
        self.cc_lbl_turno.grid_remove()
        self.cc_cmb_turno.grid_remove()

        ctk.CTkLabel(f_config, text="Produto:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=1, column=0, padx=(14, 10), pady=4, sticky="w")
        self.cc_ent_produto = ctk.CTkEntry(f_config, width=280, **ESTILO_ENTRY)
        self.cc_ent_produto.insert(0, "PLANTÃO DE ENFERMAGEM 12 HORAS, PLANTÃO DE ENFERMAGEM 6 HORAS, PLANTÃO DE ENFERMAGEM 8 HORAS")
        self.cc_ent_produto.grid(row=1, column=1, columnspan=3, padx=(5, 14), pady=4, sticky="ew")

        ctk.CTkLabel(f_config, text="URL Painel / API:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=2, column=0, padx=(14, 10), pady=8, sticky="w")
        self.cc_ent_url = ctk.CTkEntry(f_config, placeholder_text="URL da API Command Center", width=550, **ESTILO_ENTRY)
        self.cc_ent_url.insert(0, CC_BASE_URL)
        self.cc_ent_url.grid(row=2, column=1, columnspan=3, padx=(5, 14), pady=8, sticky="ew")

        ctk.CTkLabel(f_config, text="Parceiro (opcional):", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=3, column=0, padx=(14, 10), pady=(8, 12), sticky="w")
        self.cc_ent_parceiro = ctk.CTkEntry(f_config, placeholder_text="Automático: usa o nome da aba do convênio", **ESTILO_ENTRY)
        self.cc_ent_parceiro.grid(row=3, column=1, columnspan=3, padx=(5, 14), pady=(8, 8), sticky="ew")

        ctk.CTkLabel(f_config, text="Token de acesso:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=4, column=0, padx=(14, 10), pady=(8, 12), sticky="w")
        self.cc_ent_token = ctk.CTkEntry(f_config, placeholder_text="Opcional: se vazio/expirado, o painel obtém sozinho pelo navegador", show="•", **ESTILO_ENTRY)
        _tok = cc_token_inicial()
        if _tok:
            self.cc_ent_token.insert(0, _tok)
        self.cc_ent_token.grid(row=4, column=1, columnspan=2, padx=(5, 5), pady=(8, 12), sticky="ew")
        self.cc_btn_log = ctk.CTkButton(f_config, text="Abrir log", width=90, height=34, font=(FONTE_UI, 12), command=self.cc_abrir_log, **ESTILO_BOTAO_DISCRETO)
        self.cc_btn_log.grid(row=4, column=3, padx=(5, 14), pady=(8, 12), sticky="e")

        ctk.CTkLabel(f_config, text="Filtros API (IDs):", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=5, column=0, padx=(14, 10), pady=(0, 12), sticky="w")
        f_ids = ctk.CTkFrame(f_config, fg_color="transparent")
        f_ids.grid(row=5, column=1, columnspan=3, padx=(5, 14), pady=(0, 12), sticky="ew")
        f_ids.grid_columnconfigure((0, 1), weight=1, uniform="ids")
        self.cc_ent_product_id = ctk.CTkEntry(f_ids, placeholder_text="productId(s) separados por vírgula (12h, 6h)", **ESTILO_ENTRY)
        self.cc_ent_product_id.insert(0, "60417fd7-b969-44a7-b4f2-c27c33794568")
        self.cc_ent_product_id.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.cc_ent_partner_id = ctk.CTkEntry(f_ids, placeholder_text="partnerId (opcional: só o convênio escolhido)", **ESTILO_ENTRY)
        self.cc_ent_partner_id.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        for _w in f_config.grid_slaves():
            if int(_w.grid_info().get("row", 0)) >= 2 and _w is not self.cc_btn_log:
                _w.grid_remove()
        self.cc_btn_log.grid(row=2, column=0, padx=(14, 6), pady=(4, 4), sticky="w")
        self.cc_lbl_usuario = ctk.CTkLabel(f_config, text="", font=(FONTE_UI, 12, "bold"), text_color=COR_TEXTO_SUAVE, anchor="w")
        self.cc_lbl_usuario.grid(row=2, column=1, columnspan=3, padx=(8, 14), pady=(4, 4), sticky="w")
        self.cc_var_resp = ctk.BooleanVar(value=True)
        self.cc_chk_resp = ctk.CTkCheckBox(f_config, text="Colocar o usuário logado como responsável nos plantões que continuarem NÃO confirmados no painel",
                                           variable=self.cc_var_resp, onvalue=True, offvalue=False, **ESTILO_CHECKBOX)
        self.cc_chk_resp.grid(row=3, column=0, columnspan=4, padx=14, pady=(0, 8), sticky="w")
        self._cc_mostrar_usuario(cc_limpar_token(cc_token_inicial()))

        f_barra_cc = ctk.CTkFrame(frame_direita, fg_color="transparent")
        f_barra_cc.pack(fill="x", padx=12, pady=(2, 2))
        self.cc_btn_atualizar = ctk.CTkButton(f_barra_cc, text="🔄", width=34, height=26, font=(FONTE_UI, 13),
                                              command=self.cc_atualizar_planilha, **ESTILO_BOTAO_ATUALIZAR)
        self.cc_btn_atualizar.pack(side="left", padx=(0, 4), pady=0)
        self.cc_btn_params = ctk.CTkButton(f_barra_cc, text="▾ Parâmetros", width=104, height=26, font=(FONTE_UI, 11),
                                           command=self.cc_alternar_parametros, **ESTILO_BOTAO_DISCRETO)
        self.cc_btn_params.pack(side="left", padx=(0, 6), pady=0)
        self._cc_barra = f_barra_cc
        self.cc_lbl_atualizacao = ctk.CTkLabel(f_barra_cc, text="", font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE, anchor="w")
        self.cc_seg_turno = ctk.CTkSegmentedButton(
            f_barra_cc, values=["Ambos", "Diurno", "Noturno"], command=self._cc_ao_mudar_visao, **ESTILO_SEGMENTADO)
        self.cc_seg_turno.set("Ambos")
        try:
            self.cc_seg_turno.configure(height=34, font=(FONTE_UI, 13, "bold"))
        except Exception:
            pass
        self.cc_seg_turno.pack(side="right", padx=(6, 0), pady=0)
        ctk.CTkLabel(f_barra_cc, text="TURNO A ENVIAR:", font=(FONTE_UI, 12, "bold"), text_color=COR_TEXTO).pack(side="right", padx=(0, 2))
        # o aviso ocupa só o espaço que sobrar: o seletor de turno nunca é empurrado para fora da barra
        self.cc_lbl_atualizacao.pack(side="left", fill="x", expand=True, padx=(2, 12))

        self.cc_btn_processar = ctk.CTkButton(frame_direita, text="Cruzar Planilha (Aba Selecionada) x Regras API", command=self.cc_processar_lista, height=30, font=(FONTE_UI, 13, "bold"), **ESTILO_BOTAO_SECUNDARIO)
        self.cc_btn_processar.pack(fill="x", padx=12, pady=(2, 2))

        self._cabecalho_secao(frame_direita, 3, "Fila de Confirmação Backend (API)")
        self._cc_cab_fila = frame_direita.pack_slaves()[-1]

        self._criar_kpis(frame_direita, "cc_tree", 5, (("total", "Total na fila"), ("ok", "Concluídos"), ("pendente", "Pendentes"), ("erro", "Com erro")))
        try:
            frame_direita.pack_slaves()[-1].pack_configure(pady=(0, 2))
        except Exception:
            pass
        if self._kpis and self._kpis[-1].get("tipo") == "cockpit":
            _it = self._kpis[-1]
            try:
                _cards = _it["labels"]["ok"].master.master
                for _c in _cards.winfo_children():
                    _c.pack_forget()
                    _c.pack(side="left", padx=(0, 8))
                _cards.grid_configure(sticky="w")
                _it["gauge"].grid_remove()
                _it["spark"].master.grid_remove()
            except Exception:
                pass
        self.cc_tree = self._criar_tabela(frame_direita, ("Convenio", "Paciente", "Turno", "ProfissionalPlanilha", "AcaoPrevista", "StatusExecucao"))
        self.cc_tree.heading("Convenio", text="Convênio / Aba")
        self.cc_tree.heading("Paciente", text="Paciente")
        self.cc_tree.heading("Turno", text="Turno")
        self.cc_tree.heading("ProfissionalPlanilha", text="Profissional Planilha")
        self.cc_tree.heading("AcaoPrevista", text="Ação API")
        self.cc_tree.heading("StatusExecucao", text="Status Execução")

        self.cc_tree.column("Convenio", width=110, stretch=False)
        self.cc_tree.column("Paciente", width=300, minwidth=200, stretch=False)
        self.cc_tree.column("Turno", width=70, stretch=False)
        self.cc_tree.column("ProfissionalPlanilha", width=230, stretch=False)
        self.cc_tree.column("AcaoPrevista", width=150, stretch=False)
        self.cc_tree["displaycolumns"] = ("Paciente", "ProfissionalPlanilha", "StatusExecucao")
        _st = ttk.Style()
        _st.configure("CC.Treeview", rowheight=ALT_LINHA + 6, font=(FONTE_MONO, 11))
        _st.configure("CC.Treeview.Heading", font=(FONTE_UI, 11, "bold"))
        self.cc_tree.configure(style="CC.Treeview", height=14)
        self.cc_tree.column("StatusExecucao", width=330, minwidth=280, stretch=True)

        self.cc_detalhes = {}
        self.cc_tree.bind("<Double-1>", self._cc_mostrar_detalhe)

        self.cc_tree.tag_configure("Confirmar", foreground=COR_SUCESSO)
        self.cc_tree.tag_configure("AtribuirResponsavel", foreground=COR_ALERTA)
        self.cc_tree.tag_configure("Pendente", foreground=COR_TEXTO_SUAVE)
        self.cc_tree.tag_configure("Executando", foreground=COR_ALERTA, font=(FONTE_MONO, 11, "bold"))
        self.cc_tree.tag_configure("Concluido", foreground=COR_SUCESSO, font=(FONTE_MONO, 11, "bold"))
        self.cc_tree.tag_configure("Erro", foreground=COR_ERRO, font=(FONTE_MONO, 11, "bold"))

        self.cc_lbl_resumo, self.cc_btn_parar, self.cc_btn_disparar = self._criar_rodape(
            self.tab_command_center, "Total Registros: 0", "▶ INICIAR CONFIRMAÇÕES",
            self.cc_iniciar_execucao_thread, self.cc_parar_disparos)
        self.cc_alternar_parametros(False)

    def carregar_checkboxes_cc(self):
        for child in self.cc_scroll_convenios.winfo_children():
            child.destroy()

        self.cc_checkboxes_abas.clear()
        for aba in getattr(self, 'mon_abas_encontradas', self.abas_dict.keys()):
            if eh_aba_convenio_valida(str(aba)):
                var = ctk.StringVar(value=aba)
                chk = ctk.CTkCheckBox(self.cc_scroll_convenios, text=aba, variable=var, onvalue=aba, offvalue="", **ESTILO_CHECKBOX)
                chk.pack(anchor="w", padx=5, pady=3)
                self.cc_checkboxes_abas[aba] = var

    def cc_toggle_todas_abas(self):
        algum_desmarcado = any(v.get() == "" for v in self.cc_checkboxes_abas.values())
        for aba, var in self.cc_checkboxes_abas.items():
            var.set(aba if algum_desmarcado else "")

    def _cc_interpretar_data(self, texto):
        texto = str(texto).strip()
        match_br = re.search(r'(\d{2})/(\d{2})/(\d{4})', texto)
        if match_br:
            dia, mes, ano = match_br.groups()
            dt = datetime(int(ano), int(mes), int(dia))
            return dt.strftime("%Y-%m-%d"), dt

        match_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', texto)
        if match_iso:
            ano, mes, dia = match_iso.groups()
            dt = datetime(int(ano), int(mes), int(dia))
            return dt.strftime("%Y-%m-%d"), dt

        return None

    def cc_processar_lista(self):
        if self.cc_em_execucao:
            messagebox.showwarning("Atenção", "Aguarde a interrupção da execução atual.")
            return

        if not self._exigir_operador():
            return

        abas_selecionadas = [var.get() for var in self.cc_checkboxes_abas.values() if var.get() != ""]
        if not abas_selecionadas:
            messagebox.showwarning("Atenção", "Selecione a aba do convênio na lista da esquerda (ex: PREVENT SENIOR).")
            return

        data_info = self._cc_interpretar_data(self.cc_ent_data.get())
        if not data_info:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato AAAA-MM-DD ou DD/MM/AAAA (ex: 2026-10-22).")
            return
        data_iso, data_dt = data_info

        turno_sel = self.cc_cmb_turno.get().strip().upper()
        turnos = ["DIURNO", "NOTURNO"] if turno_sel == "AMBOS" else [turno_sel]
        lista_resultados = []
        abas_sem_coluna = []
        fonte_abas = self._cc_fonte_abas()

        for nome_aba in abas_selecionadas:
            if nome_aba not in fonte_abas:
                continue

            df_raw = fonte_abas[nome_aba]
            if df_raw.empty or len(df_raw) < 2:
                continue

            df_aba = normalizar_df(df_raw.copy())

            col_paciente = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["PACIENTE", "PACIENTES", "NOME", "GRUPO", "BENEFICIARIO"])), None)
            if not col_paciente and len(df_aba.columns) > 0:
                col_paciente = df_aba.columns[0]

            col_status = next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["STATUS", "ATI", "ST", "SITUAÇÃO", "SITUACAO"])), None)
            if not col_status and len(df_aba.columns) > 1:
                col_status = df_aba.columns[1]

            colunas_por_turno = {t: colunas_turno_data(df_aba.columns, t, data_dt) for t in turnos}

            _cols_turno = {c for lista_c in colunas_por_turno.values() for c in lista_c}
            col_pad = next((c for c in df_aba.columns if "PAD" in str(c).upper() and c not in _cols_turno), None) \
                or next((c for c in df_aba.columns if any(k in str(c).upper() for k in ["TIPO", "HORARIO", "HORÁRIO"]) and c not in _cols_turno), None)

            if not col_paciente or not any(colunas_por_turno.values()):
                abas_sem_coluna.append(nome_aba)
                continue

            for _, row in df_aba.iterrows():
                if col_status and col_status in row:
                    val_st = row[col_status]
                    if not status_eh_ok(val_st) or "INATIV" in normalizar_para_comparar(val_st):
                        continue

                paciente_nome = str(row[col_paciente]).replace('\xa0', ' ').strip()
                if not paciente_nome or paciente_nome.lower() == "nan" or grupo_esta_bloqueado(paciente_nome):
                    continue

                pad_valor = ""
                if col_pad and col_pad in row and pd.notna(row[col_pad]):
                    pad_valor = " ".join(str(row[col_pad]).replace('\xa0', ' ').split())
                    if pad_valor.lower() in ("nan", "none"):
                        pad_valor = ""

                for turno in turnos:
                    prof_valor, bloqueado = "", False
                    col_usada = ""
                    celulas = []
                    for col_plantao in colunas_por_turno[turno]:
                        valor = str(row[col_plantao]).replace('\xa0', ' ').strip() if col_plantao in row else ""
                        celulas.append(valor)
                        if cc_tem_pendente(valor):
                            # PENDENTE = sem profissional confirmado: não procura nome em outra coluna, só responsável.
                            prof_valor, bloqueado, col_usada = "", False, ""
                            break
                        if turno == "DIURNO" and cc_tem_cobertura(valor):
                            prof_valor, bloqueado, col_usada = valor, True, col_plantao
                            break
                        if cc_valor_plantao_valido(valor, turno):
                            prof_valor, col_usada = valor, col_plantao
                            break

                    if not prof_valor:
                        # Regra do responsável: campo do plantão vazio ou com "PENDENTE" -> só colocar responsável.
                        if celulas:
                            if any(cc_tem_pendente(c) for c in celulas) or all(cc_celula_sem_profissional(c) for c in celulas):
                                _txt = "PENDENTE" if any("PENDENTE" in normalizar_para_comparar(c) for c in celulas) else "(vazio)"
                            else:
                                _txt = next((c for c in celulas if c), "(sem profissional)")[:40]
                            lista_resultados.append({
                                "Convenio": nome_aba.strip(),
                                "Paciente": paciente_nome,
                                "Turno": turno,
                                "Profissional": _txt,
                                "Acao": f"RESPONSÁVEL -> sem profissional / pendente ({turno})",
                                "TagAcao": "AtribuirResponsavel",
                                "IsPendente": True,
                                "Bloqueado": True,
                                "SemProf": True,
                                "PAD": pad_valor
                            })
                        continue

                    lista_resultados.append({
                        "Convenio": nome_aba.strip(),
                        "Paciente": paciente_nome,
                        "Turno": turno,
                        "Profissional": prof_valor,
                        "Acao": f"BLOQUEADO -> Cobertura ({turno})" if bloqueado else f"PATCH API -> Status Confirmado ({turno})",
                        "TagAcao": "Pendente" if bloqueado else "Confirmar",
                        "IsPendente": False,
                        "Bloqueado": bloqueado,
                        "SemProf": False,
                        "PAD": pad_valor,
                        "Coluna": re.sub(r"_COL\d+$", "", str(col_usada))
                    })

        self.cc_df_filtrado = pd.DataFrame(lista_resultados)
        self.cc_detalhes = {}
        self.cc_indice_atual = 0
        self.cc_solicitar_parada = False

        self._cc_limpar_tabela()

        for _, row in self.cc_df_filtrado.iterrows():
            iid = self.cc_tree.insert("", "end", values=(
                row["Convenio"], row["Paciente"], row["Turno"], row["Profissional"], row["Acao"],
                ("⛔ Sem profissional válido na planilha: só responsável" if row["SemProf"]
                 else "⛔ Cobertura no diurno: não confirmar") if row["Bloqueado"] else f"⏳ Pendente ({row['Turno']})"
            ), tags=(row["TagAcao"],))
            self.cc_itens_info.append((iid, str(row["Turno"]).strip().upper(), bool(row["Bloqueado"])))

        self.cc_btn_disparar.configure(text="▶ INICIAR CONFIRMAÇÕES", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        self._cc_aplicar_visualizacao()
        if self.cc_itens_info:
            self.cc_alternar_parametros(False)
        limpar_memoria()

        if abas_sem_coluna:
            messagebox.showwarning(
                "Coluna do dia não encontrada",
                f"Não achei a coluna de {data_dt.strftime('%d/%m')} ({' / '.join(t.title() for t in turnos)}) nesta(s) aba(s):\n\n"
                + "\n".join(f"• {a}" for a in abas_sem_coluna)
            )

    # ------------------------------------------------------------------
    # COMMAND CENTER: ATUALIZAR PLANILHA E ESCOLHER VISUALIZAÇÃO (DIURNO / NOTURNO / AMBOS)
    # ------------------------------------------------------------------
    def _cc_fonte_abas(self):
        return self.cc_abas_dict if self.cc_abas_dict else self.abas_dict

    def _cc_limpar_tabela(self):
        for iid, _, _ in self.cc_itens_info:
            try:
                self.cc_tree.delete(iid)
            except Exception:
                pass
        for row in self.cc_tree.get_children():
            self.cc_tree.delete(row)
        self.cc_itens_info = []

    def _cc_destacar_turno(self):
        """Escreve o turno escolhido no botão de iniciar (cores sempre as padrão do programa)."""
        try:
            modo = str(self.cc_seg_turno.get()).strip().upper()
            base = str(self.cc_btn_disparar.cget("text")).split(" — ")[0]
            self.cc_btn_disparar.configure(text=base if modo == "AMBOS" else f"{base} — {modo}",
                                           fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        except Exception:
            pass

    def _cc_ao_mudar_visao(self, valor=None):
        if self.cc_em_execucao:
            return
        self._cc_destacar_turno()
        self._cc_aplicar_visualizacao()

    def _cc_aplicar_visualizacao(self):
        """Mostra só os registros do turno escolhido (ou todos). Não recalcula nada nem mexe nos status."""
        self._cc_destacar_turno()
        if not self.cc_itens_info:
            return
        modo = str(self.cc_seg_turno.get()).strip().upper()
        pos = 0
        n_confirmaveis = n_bloqueados = 0
        for iid, turno, bloqueado in self.cc_itens_info:
            if modo == "AMBOS" or turno == modo:
                self.cc_tree.move(iid, "", pos)
                pos += 1
                if bloqueado:
                    n_bloqueados += 1
                else:
                    n_confirmaveis += 1
            else:
                self.cc_tree.detach(iid)

        sufixo = "" if modo == "AMBOS" else f" ({modo.title()})"
        self.cc_lbl_resumo.configure(
            text=f"Total Registros Confirmaveis{sufixo}: {n_confirmaveis}")
        self.cc_btn_disparar.configure(state="normal" if (n_confirmaveis > 0 or n_bloqueados > 0) else "disabled")

    def cc_atualizar_planilha(self):
        if self.cc_em_execucao:
            messagebox.showwarning("Atenção", "Aguarde ou pare a execução atual antes de atualizar a planilha.")
            return
        if self._cc_atualizando:
            return
        self._cc_atualizando = True
        self.cc_btn_atualizar.configure(state="disabled", text="⏳")
        self.cc_lbl_atualizacao.configure(text="Baixando a planilha...", text_color=COR_TEXTO_SUAVE)
        threading.Thread(target=self._cc_atualizar_planilha_worker, daemon=True).start()

    def _cc_atualizar_planilha_worker(self):
        try:
            creds = self.creds
            if creds is None or not creds.valid:
                creds = autenticar_google()
            buffer_excel = baixar_planilha_privada(creds, ID_PLANILHA)
            novo = pd.read_excel(buffer_excel, sheet_name=None, engine="openpyxl", header=None)
            buffer_excel.close()
            limpar_memoria()
            self.after(0, self._cc_no_atualizacao_sucesso, novo)
        except Exception as e:
            self.after(0, self._cc_no_atualizacao_erro, str(e))

    def _cc_no_atualizacao_erro(self, erro):
        self._cc_atualizando = False
        self.cc_btn_atualizar.configure(state="normal", text="🔄")
        self.cc_lbl_atualizacao.configure(text=f"Erro ao atualizar: {erro}", text_color=COR_ERRO)

    def _cc_no_atualizacao_sucesso(self, novo):
        self._cc_atualizando = False
        self.cc_btn_atualizar.configure(state="normal", text="🔄")
        self.cc_abas_dict = novo

        # recria a lista de convênios da aba, mantendo o que estava desmarcado
        desmarcadas = {aba for aba, var in self.cc_checkboxes_abas.items() if var.get() == ""}
        for child in self.cc_scroll_convenios.winfo_children():
            child.destroy()
        self.cc_checkboxes_abas.clear()
        for aba in novo.keys():
            nome = str(aba).strip()
            if eh_aba_convenio_valida(nome):
                var = ctk.StringVar(value="" if nome in desmarcadas else nome)
                chk = ctk.CTkCheckBox(self.cc_scroll_convenios, text=nome, variable=var, onvalue=nome, offvalue="", **ESTILO_CHECKBOX)
                chk.pack(anchor="w", padx=5, pady=3)
                self.cc_checkboxes_abas[nome] = var

        hora = datetime.now().strftime("%H:%M:%S")
        ja_executou = any("🟢" in str(self.cc_tree.item(iid, "values")[5]) for iid, _, _ in self.cc_itens_info)
        if self.cc_itens_info and not ja_executou:
            self.cc_lbl_atualizacao.configure(text=f"Planilha atualizada às {hora} (fila recalculada)", text_color=COR_TEXTO_SUAVE)
            self.cc_processar_lista()
        elif self.cc_itens_info:
            self.cc_lbl_atualizacao.configure(text=f"Planilha atualizada às {hora} (fila mantida)", text_color=COR_TEXTO_SUAVE)
        else:
            self.cc_lbl_atualizacao.configure(text=f"Planilha atualizada às {hora}", text_color=COR_TEXTO_SUAVE)

    def cc_alternar_parametros(self, mostrar=None):
        """Recolhe/expande o painel de parâmetros para dar mais altura à tabela da fila."""
        if mostrar is None:
            mostrar = not self._cc_params_visiveis
        if mostrar == self._cc_params_visiveis:
            return
        if mostrar:
            self._cc_cab_param.pack(fill="x", padx=12, pady=(12, 2), before=self._cc_barra)
            self._cc_f_config.pack(fill="x", padx=12, pady=(0, 2), before=self._cc_barra)
            self._cc_cab_fila.pack(fill="x", padx=12, pady=(12, 2), before=self.cc_tree.master)
        else:
            self._cc_cab_param.pack_forget()
            self._cc_f_config.pack_forget()
            self._cc_cab_fila.pack_forget()
        self._cc_params_visiveis = mostrar
        if mostrar:
            self.cc_btn_params.configure(text="▾ Parâmetros", width=104)
        else:
            texto_data = self.cc_ent_data.get().strip()
            try:
                info = self._cc_interpretar_data(texto_data)
                if info:
                    texto_data = info[1].strftime("%d/%m/%Y")
            except Exception:
                pass
            self.cc_btn_params.configure(text=f"▸ Parâmetros  ·  {texto_data}" if texto_data else "▸ Parâmetros", width=190)

    def cc_atualizar_status_linha(self, item_id, novo_status, tag_cor):
        valores = list(self.cc_tree.item(item_id, "values"))
        valores[5] = novo_status
        self.cc_tree.item(item_id, values=valores, tags=(tag_cor,))
        self.cc_tree.see(item_id)

    def _cc_definir_status(self, item_id, texto, tag):
        self.after(0, self.cc_atualizar_status_linha, item_id, texto, tag)

    def _cc_perguntar_turno(self, qtd):
        """Janela obrigatória antes dos envios: devolve 'DIURNO', 'NOTURNO', 'AMBOS' ou None (cancelado)."""
        escolha = {"v": None}
        win = ctk.CTkToplevel(self)
        win.title("Qual turno enviar?")
        win.geometry("430x330")
        win.resizable(False, False)
        try:
            win.configure(fg_color=COR_FUNDO)
        except Exception:
            pass
        try:
            win.transient(self)
        except Exception:
            pass

        def escolher(valor):
            escolha["v"] = valor
            win.destroy()

        ctk.CTkLabel(win, text="Qual turno você quer enviar agora?", font=(FONTE_UI, 15, "bold"), text_color=COR_TEXTO).pack(pady=(22, 4))
        ctk.CTkLabel(win, text="Só os registros do turno escolhido serão enviados.", font=(FONTE_UI, 11), text_color=COR_TEXTO_SUAVE).pack(pady=(0, 14))
        for rotulo, valor in (("Diurno", "DIURNO"), ("Noturno", "NOTURNO"), ("Ambos (Diurno e Noturno)", "AMBOS")):
            n = qtd[valor]
            ctk.CTkButton(win, text=f"{rotulo}   ({n} registro(s))", command=lambda v=valor: escolher(v), height=38,
                          font=(FONTE_UI, 13, "bold"), state="normal" if n else "disabled",
                          **ESTILO_BOTAO_SECUNDARIO).pack(fill="x", padx=34, pady=4)
        ctk.CTkButton(win, text="Cancelar", command=win.destroy, height=32, font=(FONTE_UI, 12), **ESTILO_BOTAO_DISCRETO).pack(pady=(10, 12))
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        try:
            win.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 430) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 330) // 3
            win.geometry(f"430x330+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            pass
        win.after(120, lambda: (win.lift(), win.focus_force()))
        try:
            win.grab_set()
        except Exception:
            pass
        self.wait_window(win)
        return escolha["v"]

    def _cc_mostrar_usuario(self, token):
        uid, nome = cc_usuario_do_token(token) if token else ("", "")
        if not nome:
            texto = "Usuário: será o do login feito no navegador"
        else:
            exp = cc_token_expira_em(token)
            texto = f"Rodando como: {nome}" + ("  (login expirado, será renovado)" if exp and exp < datetime.now() else "")
        try:
            self.cc_lbl_usuario.configure(text=texto)
        except Exception:
            pass

    def _cc_anexar_status(self, item_id, sufixo):
        try:
            valores = list(self.cc_tree.item(item_id, "values"))
            if sufixo not in str(valores[5]):
                valores[5] = f"{valores[5]}{sufixo}"
                self.cc_tree.item(item_id, values=valores)
        except Exception:
            pass

    def _cc_detalhe(self, item_id, texto):
        self.cc_detalhes[item_id] = texto

    def _cc_mostrar_detalhe(self, event=None):
        item_id = self.cc_tree.identify_row(event.y) if event is not None else ""
        if not item_id:
            sel = self.cc_tree.selection()
            item_id = sel[0] if sel else ""
        if not item_id:
            return
        v = self.cc_tree.item(item_id, "values")
        det = self.cc_detalhes.get(item_id) or "Sem detalhes adicionais para esta linha. Veja o log (botão 'Abrir log')."
        messagebox.showinfo("Detalhe do registro", f"{v[1]} ({v[2]})\n{v[5]}\n\n{det}")

    def cc_abrir_log(self):
        try:
            if not os.path.exists(CC_ARQ_LOG):
                messagebox.showinfo("Log", "Ainda não há log. Ele é criado na primeira execução.")
                return
            os.startfile(CC_ARQ_LOG)
        except Exception as e:
            messagebox.showwarning("Log", f"Não consegui abrir o log:\n{CC_ARQ_LOG}\n\n{e}")

    def cc_parar_disparos(self):
        if self.cc_em_execucao:
            self.cc_solicitar_parada = True
            self.cc_btn_parar.configure(state="disabled", text="■ PARANDO...")

    def cc_iniciar_execucao_thread(self):
        if self.cc_em_execucao:
            return

        if not self._exigir_operador():
            return

        # IMPORTANTE: usar TODAS as linhas na ordem do DataFrame (cc_itens_info), inclusive as ocultas pelo filtro
        # Diurno/Noturno. Com get_children() só as visíveis entravam, e o índice deixava de bater com
        # cc_df_filtrado.iloc[idx] -> o robô lia o paciente/profissional errado e só atribuía responsável.
        itens_tabela = [iid for iid, _, _ in self.cc_itens_info]
        modo_visao = str(self.cc_seg_turno.get()).strip().upper()
        def _na_visao(i):
            return modo_visao == "AMBOS" or str(self.cc_tree.item(itens_tabela[i], "values")[2]).strip().upper() == modo_visao
        pendentes = [i for i, child in enumerate(itens_tabela) if _na_visao(i) and any(m in str(self.cc_tree.item(child, "values")[5]) for m in ("⏳ Pendente", "❌"))]
        bloqueados = [i for i, child in enumerate(itens_tabela) if _na_visao(i) and "⛔" in str(self.cc_tree.item(child, "values")[5])]
        atribuir = bool(self.cc_var_resp.get())
        if not pendentes and not (bloqueados and atribuir):
            messagebox.showinfo("Aviso", "Todos os registros já foram executados!")
            return

        data_info = self._cc_interpretar_data(self.cc_ent_data.get())
        if not data_info:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato AAAA-MM-DD.")
            return
        data_iso = data_info[0]

        def _turno_da_linha(i):
            return str(self.cc_tree.item(itens_tabela[i], "values")[2]).strip().upper()
        conta = {"DIURNO": 0, "NOTURNO": 0}
        for i in pendentes + (bloqueados if atribuir else []):
            t = _turno_da_linha(i)
            if t in conta:
                conta[t] += 1
        conta["AMBOS"] = conta["DIURNO"] + conta["NOTURNO"]
        turno_escolhido = self._cc_perguntar_turno(conta)
        if not turno_escolhido:
            return
        if turno_escolhido != "AMBOS":
            pendentes = [i for i in pendentes if _turno_da_linha(i) == turno_escolhido]
            bloqueados = [i for i in bloqueados if _turno_da_linha(i) == turno_escolhido]
        rotulo_turno = {"DIURNO": "DIURNO", "NOTURNO": "NOTURNO", "AMBOS": "DIURNO e NOTURNO"}[turno_escolhido]
        cc_log(f"Turno escolhido para os envios: {turno_escolhido} | {len(pendentes)} pendente(s), {len(bloqueados)} bloqueado(s)")

        texto_msg = f"Iniciando atualização direta na API para {len(pendentes)} registro(s) pendente(s) do turno {rotulo_turno} na data {data_iso}."
        if atribuir:
            texto_msg += "\n\nDepois das confirmações, todo plantão que continuar NÃO confirmado no painel terá o usuário logado como responsável de monitoramento (exceto quando o profissional for COOP, escalista ou Social Saúde, ou quando já houver outro responsável)."
        texto_msg += "\n\nDeseja prosseguir?"
        if messagebox.askyesno("Confirmar Envio API", texto_msg):
            token = cc_limpar_token(self.cc_ent_token.get())
            expira = cc_token_expira_em(token) if token else None
            token_ok = bool(token) and not (expira and expira < datetime.now())
            if not token_ok and not PLAYWRIGHT_DISPONIVEL:
                messagebox.showwarning("Token", "Não há token válido e o Playwright não está instalado para obtê-lo sozinho.\n\nInstale com: pip install playwright\nou cole um token no campo 'Token'.")
                return
            cfg = {
                "url_api": self.cc_ent_url.get().strip() or CC_BASE_URL,
                "data_iso": data_iso,
                "token": token if token_ok else "",
                "atribuir_resp": atribuir,
                "produtos_nomes": self.cc_ent_produto.get().strip(),
                "product_id": self.cc_ent_product_id.get().strip(),
                "partner_id": self.cc_ent_partner_id.get().strip(),
            }
            self.cc_em_execucao = True
            self.cc_solicitar_parada = False
            self.cc_btn_disparar.configure(state="disabled")
            self.cc_btn_processar.configure(state="disabled")
            self.cc_btn_atualizar.configure(state="disabled")
            self.cc_seg_turno.configure(state="disabled")
            self.cc_btn_parar.configure(state="normal", text="■ PARAR / PAUSAR")

            self._cc_mostrar_usuario(token if token_ok else "")
            threading.Thread(target=self._cc_executar_api_worker, args=(cfg, itens_tabela, pendentes, bloqueados), daemon=True).start()

    def _cc_finalizar_loop(self, motivo=""):
        self.cc_em_execucao = False
        self.cc_btn_disparar.configure(state="normal", text="▶ REINICIAR / CONTINUAR ENVIOS API", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        self.cc_btn_processar.configure(state="normal")
        self.cc_btn_atualizar.configure(state="normal")
        self.cc_seg_turno.configure(state="normal")
        self.cc_btn_parar.configure(state="disabled", text="■ PARAR / PAUSAR")
        self._cc_destacar_turno()

        limpar_memoria()

        status_todos = [str(self.cc_tree.item(item, "values")[5]) for item in self.cc_tree.get_children()]
        total = len(status_todos)
        concluidos = sum(1 for st in status_todos if "🟢" in st)
        erros = sum(1 for st in status_todos if "❌" in st)
        pendentes = sum(1 for st in status_todos if "⏳" in st)
        bloqueados = sum(1 for st in status_todos if "⛔" in st)

        resumo_msg = (
            f"📊 BALANÇO DA ATUALIZAÇÃO VIA API\n\n"
            f"🔹 Total na Fila: {total}\n"
            f"🟢 Confirmados no Servidor: {concluidos}\n"
            f"❌ Com Erro na API: {erros}\n"
            f"⏳ Pendentes Restantes: {pendentes}\n"
            f"⛔ Só responsável (sem profissional/cobertura): {bloqueados}\n\n"
        )
        if getattr(self, "cc_info_atrib", ""):
            resumo_msg += self.cc_info_atrib + "\n\n"

        if motivo:
            resumo_msg = f"MOTIVO DA PAUSA: {motivo}\n\n" + resumo_msg

        messagebox.showinfo("Resumo da Automação API", resumo_msg)

    # ------------------------------------------------------------------
    # TRABALHADOR BACKEND VIA API HTTP (BUSCA DO ID + PATCH DE CONFIRMAÇÃO)
    # ------------------------------------------------------------------
    def _cc_renovar_token(self):
        self.after(0, lambda: self.cc_lbl_resumo.configure(text="Obtendo token... (se abrir o navegador, faça login)"))
        tok, erro = cc_obter_token_browser()
        if tok:
            def _preencher():
                self.cc_ent_token.delete(0, "end")
                self.cc_ent_token.insert(0, tok)
            self.after(0, _preencher)
            self.after(0, self._cc_mostrar_usuario, tok)
        else:
            cc_log(f"Não foi possível obter token: {erro}")
        self.after(0, lambda: self.cc_lbl_resumo.configure(text=f"Total Registros Confirmaveis: {len(self.cc_df_filtrado)}"))
        return tok, erro

    def _cc_enviar_patch(self, url, headers, cookies, estado, url_alt=None):
        ordem = [url, url_alt] if url_alt else [url]
        if estado.get("usar_alt") and url_alt:
            ordem = [url_alt, url]
        res, efetivo = None, False
        for pos, alvo in enumerate(ordem):
            res, efetivo = self._cc_patch_url(alvo, headers, cookies, estado)
            if efetivo and alvo == url_alt and not estado.get("usar_alt"):
                estado["usar_alt"] = True
                cc_log(f"URL alternativa funcionou (a principal deu 404): {url_alt}")
            if efetivo or res.status_code != 404 or pos == len(ordem) - 1:
                return res, efetivo
            cc_log(f"PATCH {alvo} -> HTTP 404 | corpo: {res.text[:300]} | tentando URL alternativa")
        return res, efetivo

    def _cc_consultar_um(self, base_url, pid, headers, cookies):
        try:
            res = requests.get(f"{base_url}/{pid}", headers=headers, cookies=cookies, timeout=15)
        except Exception as e:
            return None, "", f"sem conexão: {str(e)[:60]}"
        bruto = ""
        if res.status_code == 200:
            try:
                bruto = cc_buscar_valor(res.json(), {"alertstatusid", "alertstatus"}, profundidade=5)
            except Exception:
                pass
        return res.status_code, bruto, res.text[:200]

    def _cc_patch_url(self, url, headers, cookies, estado):
        candidatos = [estado["payload"]] if estado.get("payload") else CC_PAYLOADS_CONFIRMAR
        res = None
        for payload in candidatos:
            for tentativa in (1, 2):
                res = requests.patch(url, json=payload, headers=headers, cookies=cookies, timeout=15)
                if res.status_code in (401, 403) and tentativa == 1 and not estado["token_renovado"]:
                    estado["token_renovado"] = True
                    novo, _ = self._cc_renovar_token()
                    if novo:
                        cookies[CC_COOKIE_TOKEN] = novo
                        continue
                break
            if res.status_code in (401, 403):
                return res, False
            if res.status_code in (200, 201, 204) and cc_resposta_confirma(res):
                if not estado.get("payload"):
                    cc_log(f"Payload que funcionou: {json.dumps(payload)} | resposta: {res.text[:300]}")
                estado["payload"] = payload
                return res, True
            cc_log(f"PATCH {url} | payload {json.dumps(payload)} sem efeito (HTTP {res.status_code}): {res.text[:200]}")
        return res, False

    def _cc_buscar_paciente_filtro(self, nome_planilha, url_pacientes, headers, cookies):
        """Faz a mesma busca do filtro 'Paciente' do painel. Devolve ([(id, nome)], motivo)."""
        from urllib.parse import quote
        for termo in cc_termos_busca_paciente(nome_planilha):
            achados, vistos = [], set()
            for page in range(1, 4):
                url = f"{url_pacientes}?filter%5BfullName%5D={quote(termo)}&page%5Bnumber%5D={page}&page%5Bsize%5D=100"
                try:
                    res = requests.get(url, headers=headers, cookies=cookies, timeout=20)
                except Exception as e:
                    cc_log(f"Busca de paciente '{termo}': falha de conexão: {e}")
                    return [], "erro"
                cc_log(f"Busca de paciente '{termo}' página {page} -> HTTP {res.status_code}")
                if res.status_code != 200:
                    cc_log(f"Corpo da resposta: {res.text[:300]}")
                    return [], "erro"
                try:
                    corpo = res.json()
                except Exception:
                    cc_log(f"Busca de paciente: resposta não é JSON: {res.text[:300]}")
                    return [], "erro"
                itens = cc_extrair_lista(corpo)
                if page == 1 and itens and not getattr(self, "_cc_esquema_pac_logado", False):
                    self._cc_esquema_pac_logado = True
                    cc_log("Estrutura do 1º paciente da busca (sem dados pessoais): "
                           + json.dumps(cc_esquema(itens[0]), ensure_ascii=False)[:1500])
                novos = 0
                for it in itens:
                    if not isinstance(it, dict):
                        continue
                    pid = it.get("id") or it.get("uuid")
                    nome = cc_nome_paciente_busca(it)
                    if pid and nome and pid not in vistos:
                        vistos.add(pid)
                        achados.append({"id": pid, "nome": nome, "nome_norm": normalizar_para_comparar(nome), "turno": None})
                        novos += 1
                if len(itens) < 100 or not novos:
                    break
            alvos, motivo = cc_localizar_plantao(nome_planilha, None, achados)
            if alvos:
                return [(p["id"], p["nome"]) for p in alvos], "ok"
            if motivo == "ambiguo":
                return [], "ambiguo"
        return [], "nao_encontrado"

    def _cc_carregar_plantoes(self, base_url, data_iso, headers, cookies, filtros_extra=""):
        plantoes, ids_vistos = [], set()
        tamanho = 500
        for page in range(1, 31):
            url_get = f"{base_url}?filter%5Bdate%5D={data_iso}&page%5Bnumber%5D={page}&page%5Bsize%5D={tamanho}{filtros_extra}"
            try:
                res = requests.get(url_get, headers=headers, cookies=cookies, timeout=20)
            except Exception as e:
                cc_log(f"GET página {page}: falha de conexão: {e}")
                return plantoes, f"Sem conexão com a API ({str(e)[:60]})"

            cc_log(f"GET página {page} -> HTTP {res.status_code}")
            if res.status_code in (401, 403):
                return plantoes, f"Token recusado (HTTP {res.status_code}). Cole um token novo."
            if res.status_code != 200:
                cc_log(f"Corpo da resposta: {res.text[:400]}")
                return plantoes, f"API respondeu HTTP {res.status_code} na listagem."

            try:
                corpo = res.json()
            except Exception:
                cc_log(f"Resposta não é JSON: {res.text[:400]}")
                return plantoes, "A API não devolveu JSON (token inválido ou URL errada)."

            itens = cc_extrair_lista(corpo)
            if page == 1:
                chaves = list(corpo.keys()) if isinstance(corpo, dict) else "lista"
                cc_log(f"Estrutura da resposta (chaves): {chaves}")
                if itens:
                    cc_log("Estrutura do 1º registro (sem dados pessoais): " + json.dumps(cc_esquema(itens[0]), ensure_ascii=False)[:2500])
                else:
                    cc_log("Nenhum registro na 1ª página. Estrutura: " + json.dumps(cc_esquema(corpo), ensure_ascii=False)[:600])

            if not itens:
                break

            novos = 0
            for p in cc_normalizar_plantoes(itens):
                if p["id"] not in ids_vistos:
                    ids_vistos.add(p["id"])
                    plantoes.append(p)
                    novos += 1
            cc_log(f"  página {page}: {len(itens)} item(ns) recebidos, {novos} novo(s) (pedido: {tamanho} por página)")
            if novos == 0:
                break
        return plantoes, ""

    def _cc_executar_api_worker(self, cfg, itens_tabela, indices_pendentes, indices_bloqueados=()):
        base_url = (cfg.get("url_api") or CC_BASE_URL).rstrip("/")
        data_iso = cfg["data_iso"]
        raiz_servicos = base_url[:-len("/monitoring")] if base_url.endswith("/monitoring") else CC_BASE_URL[:-len("/monitoring")]
        raiz_cc = base_url.split("/services")[0] if "/services" in base_url else CC_BASE_URL.split("/services")[0]
        url_pacientes = f"{raiz_cc}/patients"
        motivo_interrupcao = ""
        self.cc_info_atrib = ""

        token = cfg.get("token", "")
        if not token:
            token, erro_tk = self._cc_renovar_token()
            if not token:
                self.after(0, self._cc_finalizar_loop, f"Não consegui obter o token automaticamente: {erro_tk}")
                return
        cookies = {CC_COOKIE_TOKEN: token}
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": CC_SITE_URL.rstrip("/"),
            "referer": CC_SITE_URL,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        cc_log("=" * 70)
        cc_log(f"Início da execução | data {data_iso} | {len(indices_pendentes)} pendente(s) | URL {base_url}")

        produtos = cc_extrair_ids(cfg.get("product_id", ""), "monProduct") or [""]
        partner = (cc_extrair_ids(cfg.get("partner_id", ""), "monPartner") or [""])[0]

        nomes_produto = [normalizar_para_comparar(x) for x in str(cfg.get("produtos_nomes", "")).split(",") if x.strip()]

        excluidos_api = {}  # plantões descartados só por causa do filtro de produto (ex.: horários quebrados)

        def carregar_todos(extra="", usar_parceiro=True, todos_produtos=False):
            parc = partner if usar_parceiro else ""
            if todos_produtos:
                # Busca de um paciente específico: lista TODOS os produtos dele (plantões de horário quebrado costumam
                # ter outro productId que o filtro de 12h deixa de fora). Mantém só plantão de enfermagem.
                filtros_t = (f"&filter%5BpartnerId%5D={parc}" if parc else "") + extra
                lista_t, erro_t = self._cc_carregar_plantoes(base_url, data_iso, headers, cookies, filtros_t)
                sel_t = [pl for pl in lista_t if cc_produto_eh_plantao(pl)]
                cc_log(f"Listagem sem filtro de produto: {len(sel_t)} de {len(lista_t)} plantão(ões) mantidos (plantão de enfermagem)")
                return sel_t, erro_t
            if nomes_produto:
                filtros_p = (f"&filter%5BpartnerId%5D={parc}" if parc else "") + extra
                cc_log(f"Listando todos os produtos e filtrando por nome: {nomes_produto} | filtros: {filtros_p or '(nenhum)'}")
                lista_p, erro_p = self._cc_carregar_plantoes(base_url, data_iso, headers, cookies, filtros_p)
                contagem = {}
                for pl in lista_p:
                    chave = (pl.get("produto_id") or "?", pl.get("produto_nome") or "?")
                    contagem[chave] = contagem.get(chave, 0) + 1
                cc_log("Produtos encontrados na listagem: " + "; ".join(f"{n} [{i}] x{q}" for (i, n), q in contagem.items()))
                if any(pl.get("produto_nome") for pl in lista_p):
                    sel = []
                    for pl in lista_p:
                        pn = normalizar_para_comparar(pl.get("produto_nome") or "")
                        if any(n == pn or n in pn for n in nomes_produto):
                            sel.append(pl)
                        else:
                            excluidos_api[pl["id"]] = pl
                    cc_log(f"Filtro por produto: {len(sel)} de {len(lista_p)} plantão(ões) mantidos")
                    if lista_p and not sel and not erro_p:
                        erro_p = "Nenhum plantão dos produtos selecionados. Produtos achados: " + ", ".join(sorted({n for (_, n) in contagem}))[:150]
                    return sel, erro_p
                cc_log("AVISO: não achei o nome do produto nos registros; usando apenas o productId.")
            todos, ids, erro = [], set(), ""
            for pid in produtos:
                filtros = (f"&filter%5BproductId%5D={pid}" if pid else "") + (f"&filter%5BpartnerId%5D={parc}" if parc else "") + extra
                cc_log(f"Listando produto {pid or '(todos)'} | filtros: {filtros or '(nenhum)'}")
                lista, e = self._cc_carregar_plantoes(base_url, data_iso, headers, cookies, filtros)
                cc_log(f"  -> {len(lista)} plantão(ões)")
                if e and not erro:
                    erro = e
                for pl in lista:
                    if pl["id"] not in ids:
                        ids.add(pl["id"])
                        todos.append(pl)
            return todos, erro

        plantoes_api, erro_carga = carregar_todos()
        if not plantoes_api and erro_carga.startswith("Token recusado"):
            novo, _ = self._cc_renovar_token()
            if novo and novo != cookies[CC_COOKIE_TOKEN]:
                cookies[CC_COOKIE_TOKEN] = novo
                plantoes_api, erro_carga = carregar_todos()
        if erro_carga and plantoes_api:
            motivo_interrupcao = f"Aviso na listagem de plantões (algum produto pode estar incompleto): {erro_carga}"
        cc_log(f"Plantões carregados da API: {len(plantoes_api)}")
        self.after(0, lambda n=len(plantoes_api): self.cc_lbl_resumo.configure(text=f"Mostrando 1 - {n} de {n} itens (500 por página)"))
        for p in plantoes_api[:5]:
            cc_log(f"  ex.: {p['nome_norm']} | {p['turno']} {cc_rotulo_hora(p)} | alerta {p['alerta']} | prof {p['prof']!r} | id {p['id']}")

        if not plantoes_api:
            motivo = erro_carga or f"A API não retornou plantões para {data_iso}. Veja o log para a resposta recebida."
            for idx in indices_pendentes:
                self._cc_definir_status(itens_tabela[idx], "❌ Erro: API sem dados", "Erro")
            self.after(0, self._cc_finalizar_loop, motivo)
            return

        mapa_pl = {pl["id"]: pl for pl in plantoes_api}
        nao_conf = {}
        estado_pac = {"param": None}
        buscados_pac = set()
        diag_filtro = {}  # motivo da busca por paciente, para aparecer no detalhe da linha

        def buscar_via_filtro_paciente(nome_planilha):
            """Paciente não veio na listagem geral: acha o id pelo filtro 'Paciente' e lista os plantões dele."""
            chave = normalizar_para_comparar(nome_planilha)
            if chave in buscados_pac:
                return False
            buscados_pac.add(chave)
            cands, mot = self._cc_buscar_paciente_filtro(nome_planilha, url_pacientes, headers, cookies)
            if not cands:
                cc_log(f"FILTRO PACIENTE: '{nome_planilha}' não encontrado na busca de pacientes ({mot})")
                diag_filtro[chave] = f"A busca de pacientes do painel não encontrou esse nome ({mot})."
                return False
            cc_log(f"FILTRO PACIENTE: '{nome_planilha}' -> {[(i, n) for i, n in cands]}")
            params = ["patientId"]  # confirmado pela chamada do próprio painel: filter[patientId]
            for param in params:
                achados = []
                for pid, _pn in cands:
                    lista, erro = carregar_todos(f"&filter%5B{param}%5D={pid}", usar_parceiro=False, todos_produtos=True)
                    cc_log(f"  filtro {param}={pid} -> {len(lista)} plantão(ões){(' | ' + erro) if erro else ''}")
                    achados.extend(lista)
                novos = 0
                for pl in achados:
                    if pl["id"] not in mapa_pl:
                        mapa_pl[pl["id"]] = pl
                        plantoes_api.append(pl)
                        novos += 1
                if novos:
                    estado_pac["param"] = param
                    cc_log(f"FILTRO PACIENTE: {novos} plantão(ões) novo(s) via filter[{param}] para '{nome_planilha}'")
                    return True
            cc_log(f"FILTRO PACIENTE: nenhum plantão novo para '{nome_planilha}' (parâmetros testados: {params})")
            diag_filtro[chave] = (f"O paciente foi achado no painel ({', '.join(n for _i, n in cands)}), "
                                  f"mas a API não devolveu plantão dele em {data_iso} (nos produtos do filtro).")
            return False

        sem_resp = {}
        cont = {"nao_localizado": 0}
        bloq_cob = {itens_tabela[i] for i in indices_bloqueados}

        def marcar(item_id, pls, forcar=False):
            lista = [pl for pl in (pls or []) if pl and (forcar or pl.get("alerta") != "CONFIRMADO")]
            if lista:
                atual = nao_conf.setdefault(item_id, [])
                for pl in lista:
                    if all(pl["id"] != x["id"] for x in atual):
                        atual.append(pl)
            elif pls:
                sem_resp.setdefault(item_id, "o plantão já está CONFIRMADO no painel (só coloco responsável em plantão não confirmado)")

        falhas_seguidas = 0
        estado_patch = {"token_renovado": False, "payload": None}
        ids_enviados = {}
        resp_patch = {}
        for idx in indices_pendentes:
            if self.cc_solicitar_parada:
                motivo_interrupcao = "Interrupção solicitada pelo usuário."
                break

            item_id = itens_tabela[idx]
            registro = self.cc_df_filtrado.iloc[idx].to_dict()
            nome_planilha, turno_planilha = registro["Paciente"], registro["Turno"]

            if cc_tem_pendente(registro.get("Profissional", "")):
                cc_log(f"SEM PROFISSIONAL (PENDENTE na planilha): '{nome_planilha}' [{turno_planilha}] -> {registro.get('Profissional')!r}")
                self._cc_definir_status(item_id, "⛔ Sem profissional válido na planilha: só responsável", "Pendente")
                bloq_cob.add(item_id)
                alv_p, _mp = cc_localizar_plantao(nome_planilha, turno_planilha, plantoes_api)
                marcar(item_id, alv_p)
                continue

            if turno_planilha == "DIURNO" and cc_tem_cobertura(registro.get("Profissional", "")):
                cc_log(f"BLOQUEADO (cobertura no diurno): '{nome_planilha}' -> {registro.get('Profissional')!r}")
                self._cc_definir_status(item_id, "⛔ Cobertura no diurno: não confirmar", "Pendente")
                bloq_cob.add(item_id)
                alv_b, _mb = cc_localizar_plantao(nome_planilha, turno_planilha, plantoes_api)
                marcar(item_id, alv_b)
                continue

            self._cc_definir_status(item_id, "🟡 Buscando ID...", "Executando")
            alvos, motivo = cc_localizar_plantao(nome_planilha, turno_planilha, plantoes_api)

            tentou_filtro = False
            if not alvos and motivo in ("nao_encontrado", "outro_turno"):
                tentou_filtro = True
                self._cc_definir_status(item_id, "🟡 Buscando no filtro de paciente...", "Executando")
                if buscar_via_filtro_paciente(nome_planilha):
                    alvos, motivo = cc_localizar_plantao(nome_planilha, turno_planilha, plantoes_api)

            if not alvos and motivo in ("nao_encontrado", "outro_turno") and excluidos_api:
                fora_pe = [p for p in excluidos_api.values()
                           if not (p.get("produto_nome") or "").strip()
                           or any(k in normalizar_para_comparar(p.get("produto_nome") or "") for k in ("PLANTAO", "ENFERM"))]
                alv_f, _mf = cc_localizar_plantao(nome_planilha, turno_planilha, fora_pe)
                if alv_f:
                    cc_log(f"PRODUTO FORA DO FILTRO ACEITO: '{nome_planilha}' [{turno_planilha}] -> "
                           f"{[(p['produto_nome'], p['hora'], p['id']) for p in alv_f]} (plantão de enfermagem de outra duração)")
                    for pl in alv_f:
                        if pl["id"] not in mapa_pl:
                            mapa_pl[pl["id"]] = pl
                            plantoes_api.append(pl)
                    alvos, motivo = alv_f, "ok"

            if not alvos and motivo in ("nao_encontrado", "outro_turno"):
                # Horário quebrado: a linha da planilha chegou aqui com profissional válido, então o plantão do paciente
                # é aceito mesmo que o turno calculado pelo horário não bata com o da planilha (ou que o produto
                # esteja fora do filtro). A conferência do profissional abaixo continua valendo.
                pool = [p for p in plantoes_api if p["turno"] not in (turno_planilha, None) and (cc_turno_ambiguo(p) or cc_plantao_quebrado(p))]
                pool += [p for p in excluidos_api.values()
                         if not (p.get("produto_nome") or "").strip()
                         or any(k in normalizar_para_comparar(p.get("produto_nome") or "") for k in ("PLANTAO", "ENFERM"))]
                copias = [dict(p, turno=None) for p in pool]
                alv_c, _mc = cc_localizar_plantao(nome_planilha, None, copias)
                ids_c = {c["id"] for c in alv_c}
                alv_q = [p for p in pool if p["id"] in ids_c]
                if alv_q:
                    cc_log(f"PLANTÃO QUEBRADO ACEITO: '{nome_planilha}' [{turno_planilha}] (profissional na planilha: {registro.get('Profissional')!r}) -> "
                           f"{[(p.get('produto_nome'), cc_rotulo_hora(p), p['turno'], p['id']) for p in alv_q]}")
                    for pl in alv_q:
                        if pl["id"] not in mapa_pl:
                            mapa_pl[pl["id"]] = pl
                            plantoes_api.append(pl)
                    alvos, motivo = alv_q, "ok"

            if not alvos:
                texto = {"ambiguo": "Erro: mais de um paciente com esse nome",
                         "outro_turno": "Erro: paciente só existe em outro turno"}.get(motivo, "Erro: ID não localizado")
                if motivo == "outro_turno":
                    pad_pl = str(registro.get("PAD", "") or "").strip()
                    outros = [p for p in plantoes_api if p["turno"] not in (turno_planilha, None) and nomes_compativeis(nome_planilha, p["nome"])]
                    achado = ", ".join(sorted({f"{p['turno']} {cc_rotulo_hora(p)}".strip() for p in outros}))
                    if pad_pl:
                        texto = f"Erro: {pad_pl}" if pad_pl.upper().startswith("PAD") else f"Erro: PAD planilha: {pad_pl}"
                    self._cc_detalhe(item_id, f"Você está confirmando o turno {turno_planilha}, mas o paciente só aparece no outro turno do painel.\n"
                                              f"PAD na planilha: {pad_pl or '(vazio)'}\nNo painel o paciente aparece em: {achado or '-'}")
                if motivo != "outro_turno":
                    tok_pl = set(tokens_nome_paciente(nome_planilha))
                    parecidos = sorted({f"{p['nome']} ({p['turno'] or '?'} {p['hora']})".strip() for p in plantoes_api
                                        if tok_pl & set(tokens_nome_paciente(p["nome"]))})[:8]
                    self._cc_detalhe(item_id, f"Nome na planilha: {nome_planilha} | Turno: {turno_planilha}\n"
                                              f"Plantões carregados da API para {data_iso}: {len(plantoes_api)} "
                                              f"({sum(1 for p in plantoes_api if p['turno'] == turno_planilha)} no turno {turno_planilha}).\n"
                                              + ("Nomes parecidos no painel:\n- " + "\n- ".join(parecidos) if parecidos
                                                 else "Nenhum nome parecido foi carregado da API. O plantão pode estar fora do filtro "
                                                      "de produto/parceiro, ou a API não trouxe o nome do paciente. Veja o log."))
                if tentou_filtro and item_id in self.cc_detalhes:
                    self.cc_detalhes[item_id] += ("\n\nTambém busquei pelo filtro de Paciente do painel: "
                                                  + diag_filtro.get(normalizar_para_comparar(nome_planilha), "não achei plantão para este nome.")
                                                  + f"\nFiltro de convênio (partnerId) na listagem geral: {partner or 'vazio'}."
                                                  + "\nVeja o log (FILTRO PACIENTE).")
                fora_todos = [p for p in excluidos_api.values() if nomes_compativeis(nome_planilha, p["nome"])]
                fora_q = [p for p in fora_todos if p["turno"] in (turno_planilha, None)]
                if fora_todos and motivo != "ambiguo":
                    prods_q = "; ".join(sorted({f"{p.get('produto_nome') or '?'} | {cc_rotulo_hora(p)} | turno {p['turno'] or '?'}" for p in fora_todos}))
                    texto = "Erro: produto fora do filtro" if fora_q else "Erro: fora do filtro e em outro turno"
                    self.cc_detalhes[item_id] = (self.cc_detalhes.get(item_id, "") + "\n\n" if item_id in self.cc_detalhes else "") + \
                        f"O paciente existe no painel, mas o plantão foi descartado pelo filtro de Produtos (turno da planilha: {turno_planilha}):\n- " + prods_q.replace("; ", "\n- ") + \
                        "\nInclua esse produto no campo 'Produtos' (Parâmetros) ou confira o turno do horário."
                    cc_log(f"PRODUTO FORA DO FILTRO: '{nome_planilha}' [{turno_planilha}] -> {prods_q}")
                cont["nao_localizado"] += 1
                sem_resp[item_id] = {"ambiguo": "há mais de um paciente com esse nome no painel",
                                     "outro_turno": "o paciente só tem plantão no outro turno do painel"
                                     }.get(motivo, "o plantão não foi localizado no painel (sem plantão, não há onde colocar responsável)")
                cc_log(f"FALHA ({motivo}): '{nome_planilha}' [{turno_planilha}] | PAD planilha: {registro.get('PAD', '')!r}")
                self._cc_definir_status(item_id, f"❌ {texto}", "Erro")
                continue

            if turno_planilha == "DIURNO" and any(cc_tem_cobertura(pl["prof"] or "") for pl in alvos):
                cc_log(f"BLOQUEADO (cobertura no painel, diurno): '{nome_planilha}' | painel: {[pl['prof'] for pl in alvos]}")
                self._cc_definir_status(item_id, "⛔ Cobertura no painel (diurno): não confirmar", "Pendente")
                bloq_cob.add(item_id)
                marcar(item_id, alvos)
                continue

            if all(pl["alerta"] == "CONFIRMADO" for pl in alvos):
                partes_c = cc_profissionais_planilha(cc_sem_cobertura(registro.get("Profissional", "")))
                diverge = not any(any(cc_profissional_confere(x, n) for x in partes_c for n in cc_candidatos_prof(pl)) for pl in alvos)
                aviso = ""
                if diverge and any(cc_candidatos_prof(pl) for pl in alvos):
                    aviso = " ⚠ profissional da planilha difere do painel"
                    self._cc_detalhe(item_id, f"O plantão já está CONFIRMADO no painel, então não precisei enviar nada.\n"
                                              f"Mas o profissional da planilha difere do painel:\n"
                                              f"Planilha: {registro.get('Profissional')!r}\n"
                                              f"Painel: {', '.join(repr(pl['prof']) for pl in alvos)}\n"
                                              f"Campos de profissional na API: {' | '.join('; '.join(pl.get('prof_diag') or []) for pl in alvos)}")
                cc_log(f"JÁ CONFIRMADO (sem enviar): '{nome_planilha}' [{turno_planilha}] ids {[pl['id'] for pl in alvos]}"
                       + (f" | profissional difere: planilha {registro.get('Profissional')!r} x painel {[pl['prof'] for pl in alvos]} | campos: {[pl.get('prof_diag') for pl in alvos]}" if aviso else ""))
                self._cc_definir_status(item_id, f"🟢 Concluído (já confirmado - {turno_planilha}){aviso}", "Concluido")
                continue

            partes_prof = cc_profissionais_planilha(cc_sem_cobertura(registro.get("Profissional", "")))
            if not any(len(cc_tokens_profissional(x)) >= 2 for x in partes_prof):
                cc_log(f"PROFISSIONAL INCOMPLETO na planilha: '{nome_planilha}' [{turno_planilha}] -> {registro.get('Profissional')!r}")
                self._cc_definir_status(item_id, "❌ Erro: profissional incompleto na planilha", "Erro")
                marcar(item_id, alvos)
                continue
            if all(not cc_candidatos_prof(pl) for pl in alvos):
                cc_log(f"CAMPO PROFISSIONAL NÃO ENCONTRADO na API para '{nome_planilha}' (veja o exemplo bruto no início do log)")
                self._cc_definir_status(item_id, "❌ Erro: campo do profissional não achado na API", "Erro")
                marcar(item_id, alvos)
                continue
            confere = [pl for pl in alvos if any(cc_profissional_confere(x, n) for x in partes_prof for n in cc_candidatos_prof(pl))]
            if not confere:
                if all(not pl["prof"] for pl in alvos):
                    texto = "Erro: sem profissional no painel"
                else:
                    texto = "Erro: profissional não confere"
                cc_log(f"{texto.upper()}: '{nome_planilha}' [{turno_planilha}] | planilha: {registro.get('Profissional')!r} (tokens {[cc_tokens_profissional(x) for x in partes_prof]}) | painel: {[pl['prof'] for pl in alvos]} | candidatos comparados: {[[(n, cc_tokens_profissional(n)) for n in cc_candidatos_prof(pl)] for pl in alvos]}")
                self._cc_detalhe(item_id, f"Aba / coluna da planilha lida: {registro.get('Convenio')} / {registro.get('Coluna')}\n"
                                          f"Profissional na planilha: {registro.get('Profissional')!r}\n"
                                          f"Profissional no painel: {', '.join(repr(pl['prof']) for pl in alvos)}\n"
                                          f"Campos de profissional na API: {' | '.join('; '.join(pl.get('prof_diag') or []) for pl in alvos)}\n"
                                          f"Nomes encontrados no registro da API: {' | '.join('; '.join(pl.get('nomes_reg') or []) for pl in alvos)}\n"
                                          f"Outros textos no registro da API: {' | '.join('; '.join(pl.get('todos_txt') or []) for pl in alvos)}\n"
                                          "Se os dois são a mesma pessoa, me envie essa linha do log para ajustar a regra. "
                                          "Se forem pessoas diferentes (ex.: troca de profissional), o robô recusou de propósito.")
                self._cc_definir_status(item_id, f"❌ {texto}", "Erro")
                marcar(item_id, alvos)
                continue
            if len(confere) < len(alvos):
                cc_log(f"'{nome_planilha}' [{turno_planilha}]: {len(confere)} de {len(alvos)} registros têm o profissional da planilha; os demais foram ignorados.")
            alvos = confere
            n_dup = len(alvos)
            if n_dup > 1:
                ja_conf_d = [pl for pl in alvos if pl["alerta"] == "CONFIRMADO"]
                alvos = ja_conf_d[:1] if ja_conf_d else [pl for pl in alvos if pl["alerta"] != "CONFIRMADO"][:1]
                cc_log(f"DUPLICIDADE: '{nome_planilha}' [{turno_planilha}] tem {n_dup} atendimentos do mesmo profissional; "
                       f"{'já havia 1 confirmado' if ja_conf_d else 'confirmando apenas 1'} -> id {[pl['id'] for pl in alvos]} | todos: {[(pl['id'], pl['hora'], pl['alerta']) for pl in confere]}")

            a_enviar = [pl for pl in alvos if pl["alerta"] != "CONFIRMADO"]
            if not a_enviar:
                cc_log(f"JÁ CONFIRMADO: '{nome_planilha}' [{turno_planilha}] ids {[pl['id'] for pl in alvos]}")
                self._cc_definir_status(item_id, f"🟢 Concluído (já confirmado - {turno_planilha}{f', {n_dup} duplicados' if n_dup > 1 else ''})", "Concluido")
                continue

            self._cc_definir_status(item_id, "🟡 Enviando API...", "Executando")
            enviados, erro_txt, parar, detalhe = 0, "", False, ""
            try:
                for plantao in a_enviar:
                    res, efetivo = self._cc_enviar_patch(f"{raiz_servicos}/{plantao['id']}/alert-status", headers, cookies, estado_patch,
                                                         url_alt=f"{base_url}/{plantao['id']}/alert-status")
                    cc_log(f"PATCH '{nome_planilha}' [{turno_planilha}] {cc_rotulo_hora(plantao)} id {plantao['id']} -> HTTP {res.status_code} efetivo={efetivo}")
                    if efetivo:
                        enviados += 1
                        resp_patch[plantao["id"]] = f"HTTP {res.status_code} | {res.text[:200]}"
                        continue
                    detalhe = f"{res.request.method} {res.url}\nHTTP {res.status_code}\nResposta do servidor: {res.text[:500] or '(vazia)'}"
                    if res.status_code in (401, 403):
                        erro_txt, parar = f"Erro HTTP {res.status_code} (token)", True
                    elif res.status_code in (200, 201, 204):
                        erro_txt = "Erro: API não confirmou (resposta sem CONFIRMED)"
                    else:
                        cc_log(f"Corpo: {res.text[:300]}")
                        erro_txt = f"Erro HTTP {res.status_code}" + (" (ID/endpoint não existe)" if res.status_code == 404 else "")
                    break
            except Exception as e:
                cc_log(f"PATCH exceção: {e}")
                erro_txt = f"Erro Conexão: {str(e)[:20]}"
                detalhe = f"Exceção ao enviar PATCH: {e}"
            if erro_txt:
                marcar(item_id, [pl for pl in a_enviar if pl["id"] not in resp_patch])
            if erro_txt and detalhe:
                self._cc_detalhe(item_id, detalhe)

            if not erro_txt:
                falhas_seguidas = 0
                sufixo = f" - duplicado: confirmado 1 de {n_dup}" if n_dup > 1 else ""
                self._cc_definir_status(item_id, f"🟢 Concluído ({turno_planilha}){sufixo}", "Concluido")
                ids_enviados[item_id] = [pl["id"] for pl in a_enviar]
            else:
                falhas_seguidas += 1
                parcial = f" [{enviados}/{len(a_enviar)}]" if enviados else ""
                self._cc_definir_status(item_id, f"❌ {erro_txt}{parcial}", "Erro")
                if parar:
                    motivo_interrupcao = "Token recusado pela API mesmo após renovar. Faça login no navegador do painel e continue."
                    break

            if falhas_seguidas >= 5:
                motivo_interrupcao = "5 falhas seguidas no envio. Verifique conexão/token e continue."
                break
            time.sleep(0.3)

        if ids_enviados:
            a_conferir = dict(ids_enviados)
            problemas_por_item = {}
            erro_lista = ""
            conferiu = False
            for espera in (1.5, 3.0, 5.0):
                if not a_conferir:
                    break
                time.sleep(espera)
                conferidos, erro_conf = carregar_todos()
                if not conferidos:
                    erro_lista = erro_conf or "listagem veio vazia"
                    cc_log(f"Verificação final: não consegui listar ({erro_lista}).")
                    continue
                conferiu, erro_lista = True, ""
                por_id = {pl["id"]: pl for pl in conferidos}
                for item_id, ids in list(a_conferir.items()):
                    probs = []
                    for i in ids:
                        pl = por_id.get(i)
                        if pl is None:
                            probs.append((i, "ausente", ""))
                        elif pl["alerta"] != "CONFIRMADO":
                            probs.append((i, "status", pl.get("alerta_bruto") or pl["alerta"] or "vazio"))
                    if probs:
                        problemas_por_item[item_id] = probs
                    else:
                        a_conferir.pop(item_id, None)
                        problemas_por_item.pop(item_id, None)

            if not conferiu:
                cc_log(f"Verificação final NÃO executada: {erro_lista}")
                motivo_interrupcao = motivo_interrupcao or f"Não consegui conferir no servidor se as confirmações valeram: {erro_lista}"
            else:
                for item_id, probs in problemas_por_item.items():
                    if item_id not in a_conferir:
                        continue
                    linhas, curto, tudo_ok, pids_nao = [], "", True, []
                    for pid, tipo, valor in probs:
                        if tipo == "status":
                            tudo_ok = False
                            pids_nao.append(pid)
                            linhas.append(f"ID {pid}: o servidor aceitou o PATCH ({resp_patch.get(pid, '-')}), mas a listagem ainda mostra o status '{valor}'.")
                            curto = curto or f"status atual = {valor}"
                        else:
                            http, bruto, trecho = self._cc_consultar_um(base_url, pid, headers, cookies)
                            if http == 200 and cc_alerta_api(bruto) == "CONFIRMADO":
                                continue
                            tudo_ok = False
                            pids_nao.append(pid)
                            linhas.append(f"ID {pid}: não apareceu na listagem de conferência; consulta direta GET {base_url}/{pid} -> HTTP {http} {('| status ' + bruto) if bruto else ''} | {trecho}")
                            curto = curto or (f"ID fora da listagem (GET {http})" if http else "ID fora da listagem")
                    if tudo_ok:
                        continue
                    cc_log(f"VERIFICAÇÃO: servidor não confirmou | " + " || ".join(linhas))
                    self._cc_detalhe(item_id, "\n\n".join(linhas))
                    self._cc_definir_status(item_id, f"❌ Servidor não confirmou: {curto}", "Erro")
                    marcar(item_id, [mapa_pl[p] for p in pids_nao if p in mapa_pl], forcar=True)
                cc_log("Verificação final no servidor concluída.")

        def status_atual_painel(pid):
            http, bruto, _t = self._cc_consultar_um(base_url, pid, headers, cookies)
            return cc_alerta_api(bruto) if (http == 200 and bruto) else None

        # ---- CONFERÊNCIA FINAL: o status lido no início pode ter mudado durante a execução
        if nao_conf and not self.cc_solicitar_parada:
            for item_id in list(nao_conf.keys()):
                pls = nao_conf[item_id]
                for pl in pls:
                    st = status_atual_painel(pl["id"])
                    if st:
                        if st != pl.get("alerta"):
                            cc_log(f"STATUS ATUALIZADO no painel: '{pl['nome']}' id {pl['id']}: {pl.get('alerta')} -> {st}")
                        pl["alerta"] = st
                        pl["alerta_conferido"] = True
                if pls and all(pl.get("alerta") == "CONFIRMADO" for pl in pls):
                    nao_conf.pop(item_id, None)
                    if item_id in bloq_cob:
                        sem_resp[item_id] = "o plantão está CONFIRMADO no painel (conferido ao final da execução)"
                    else:
                        cc_log(f"CONFERÊNCIA FINAL: plantão(ões) {[pl['id'] for pl in pls]} já CONFIRMADO(s) no painel; linha atualizada para Concluído e responsável NÃO atribuído.")
                        self._cc_definir_status(item_id, "🟢 Concluído (confirmado no painel - conferido ao final)", "Concluido")
                        _det_ant = self.cc_detalhes.get(item_id, "")
                        self.cc_detalhes[item_id] = (_det_ant + "\n\n" if _det_ant else "") + "Ao final da execução o painel já mostrava este plantão como CONFIRMADO, então a linha deixou de ser erro."

        # ---- ATRIBUIÇÃO DO RESPONSÁVEL NOS PLANTÕES NÃO CONFIRMADOS
        if cfg.get("atribuir_resp") and not self.cc_solicitar_parada:
            amostra_falha = ""
            for idx in indices_bloqueados:
                registro_b = self.cc_df_filtrado.iloc[idx].to_dict()
                alv_b, motivo_b = cc_localizar_plantao(registro_b["Paciente"], registro_b["Turno"], plantoes_api)
                if not alv_b and motivo_b in ("nao_encontrado", "outro_turno"):
                    if buscar_via_filtro_paciente(registro_b["Paciente"]):
                        alv_b, motivo_b = cc_localizar_plantao(registro_b["Paciente"], registro_b["Turno"], plantoes_api)
                if alv_b:
                    marcar(itens_tabela[idx], alv_b)
                else:
                    cc_log(f"Sem plantão localizado para atribuir responsável: '{registro_b['Paciente']}' [{registro_b['Turno']}] ({motivo_b})")
                    cont["nao_localizado"] += 1
                    if bool(registro_b.get("SemProf")):
                        self._cc_definir_status(itens_tabela[idx], "ℹ Sem plantão no painel para este turno", "Pendente")
                        _tok_b = set(tokens_nome_paciente(registro_b["Paciente"]))
                        _par_b = sorted({f"{pl_['nome']} ({pl_['turno'] or '?'} {pl_['hora']})".strip() for pl_ in plantoes_api
                                         if _tok_b & set(tokens_nome_paciente(pl_["nome"]))})[:8]
                        self._cc_detalhe(itens_tabela[idx],
                                         f"Planilha: {registro_b['Paciente']} | turno {registro_b['Turno']} | campo do plantão vazio/pendente.\n"
                                         f"Não achei plantão deste paciente neste turno no painel (motivo: {motivo_b}).\n"
                                         + ("Nomes parecidos no painel:\n- " + "\n- ".join(_par_b) if _par_b
                                            else "Nenhum nome parecido foi carregado da API. Veja o log (FILTRO PACIENTE)."))

            if nao_conf:
                uid, unome = cc_usuario_do_token(cookies.get(CC_COOKIE_TOKEN, ""))
                if not uid:
                    cc_log("Atribuição de responsável NÃO executada: não consegui ler o usuário no token.")
                    self.cc_info_atrib = "👤 Responsável: não consegui identificar o usuário logado (veja o log)."
                else:
                    primeiro_nome = (unome.split() or ["você"])[0].title()
                    cc_log(f"Atribuindo responsável {unome} ({uid}) em {len(nao_conf)} registro(s) não confirmado(s)")
                    t_ok = t_ja = t_outro = t_falha = t_prot = 0
                    idx_por_item = {itens_tabela[i]: i for i in range(len(itens_tabela))}
                    for item_id, pls in nao_conf.items():
                        ok_n = ja_n = outro_n = falha_n = prot_n = 0
                        ids_atrib = []
                        falhas_txt = []
                        outros_txt = []
                        i_linha = idx_por_item.get(item_id)
                        prof_planilha = str(self.cc_df_filtrado.iloc[i_linha].to_dict().get("Profissional", "")) if i_linha is not None else ""
                        for pl in pls:
                            if (cc_prof_protegido(prof_planilha) or cc_prof_protegido(pl.get("prof") or "")
                                    or any(cc_prof_protegido(n) for n in (pl.get("nomes_reg") or []))
                                    or cc_prof_protegido(pl.get("textos_reg") or "")):
                                prot_n += 1
                                cc_log(f"Responsável MANTIDO (coop/escalista/social saúde): '{pl['nome']}' id {pl['id']} | planilha: {prof_planilha!r} | painel: {pl.get('prof')!r}")
                                continue
                            if pl.get("resp_campo") and pl.get("resp_id") == uid:
                                ja_n += 1
                                continue
                            if pl.get("resp_campo") and pl.get("resp_id"):
                                outro_n += 1
                                outros_txt.append(str(pl["resp_id"]))
                                cc_log(f"Responsável NÃO alterado (já é {pl['resp_id']}): '{pl['nome']}' id {pl['id']}")
                                continue
                            try:
                                res_r = requests.patch(f"{raiz_servicos}/{pl['id']}/monitoring-responsible",
                                                       json={"monitoringResponsibleId": uid}, headers=headers, cookies=cookies, timeout=15)
                                cc_log(f"Responsável '{pl['nome']}' id {pl['id']} -> HTTP {res_r.status_code} | {res_r.text[:200]}")
                                if res_r.status_code in (200, 201, 204):
                                    ok_n += 1
                                    if pl.get("alerta_conferido"):
                                        ids_atrib.append(pl["id"])
                                else:
                                    falha_n += 1
                                    falhas_txt.append(f"HTTP {res_r.status_code}: {res_r.text[:160]}")
                            except Exception as e:
                                cc_log(f"Responsável exceção em id {pl['id']}: {e}")
                                falha_n += 1
                                falhas_txt.append(f"exceção: {e}")
                        t_ok, t_ja, t_outro, t_falha, t_prot = t_ok + ok_n, t_ja + ja_n, t_outro + outro_n, t_falha + falha_n, t_prot + prot_n
                        if falhas_txt and not amostra_falha:
                            amostra_falha = falhas_txt[0]
                        if falha_n:
                            suf = " → falha ao atribuir: " + (falhas_txt[0][:90] if falhas_txt else "veja o log")
                        elif ok_n or ja_n:
                            suf = f" → resp.: {primeiro_nome}"
                        elif prot_n:
                            suf = " → responsável mantido (coop/escalista/social saúde)"
                        else:
                            suf = " → já tem outro responsável"
                        if ids_atrib:
                            viraram = [pid for pid in ids_atrib if status_atual_painel(pid) == "CONFIRMADO"]
                            if viraram:
                                cc_log(f"ATENÇÃO: depois de atribuir o responsável, o painel passou a CONFIRMADO: ids {viraram} (estavam não confirmados antes)")
                                suf += " ⚠ painel passou a Confirmado após atribuir o responsável"
                        self.after(0, self._cc_anexar_status, item_id, suf)
                        _det_ant = self.cc_detalhes.get(item_id, "")
                        _extra = ""
                        if falhas_txt:
                            _extra += "\nResposta do servidor ao atribuir: " + " | ".join(falhas_txt)
                        if outros_txt:
                            _extra += "\nResponsável já existente no plantão (id): " + ", ".join(outros_txt)
                        self.cc_detalhes[item_id] = (_det_ant + "\n\n" if _det_ant else "") + "Responsável:" + suf.replace(" →", "") + _extra
                    self.cc_info_atrib = (f"👤 Responsável {unome}: atribuído em {t_ok} plantão(ões)"
                                          + (f", já era seu em {t_ja}" if t_ja else "")
                                          + (f", {t_outro} já tinham outro responsável (não alterados)" if t_outro else "")
                                          + (f", {t_prot} mantidos por serem coop/escalista/social saúde" if t_prot else "")
                                          + (f", {t_falha} falha(s)" if t_falha else "") + ".")

            if not nao_conf:
                self.cc_info_atrib = ("👤 Responsável: nenhum plantão não confirmado foi encontrado para atribuir"
                                      f" (plantões não localizados no painel: {cont['nao_localizado']}).")
            else:
                if cont["nao_localizado"]:
                    self.cc_info_atrib += f" Plantões não localizados no painel: {cont['nao_localizado']}."
                if amostra_falha:
                    self.cc_info_atrib += f"\nResposta do servidor ao atribuir: {amostra_falha[:200]}"

            for item_id, motivo_sr in sem_resp.items():
                if item_id not in nao_conf and item_id in bloq_cob:
                    self.after(0, self._cc_anexar_status, item_id, f" → responsável não atribuído: {motivo_sr}")
                    _det_ant = self.cc_detalhes.get(item_id, "")
                    self.cc_detalhes[item_id] = (_det_ant + "\n\n" if _det_ant else "") + f"Responsável não atribuído: {motivo_sr}."

        cc_log(f"Fim da execução. Motivo de pausa: {motivo_interrupcao or '-'}")
        self.after(0, self._cc_finalizar_loop, motivo_interrupcao)

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    app = PainelUnificado()
    app.mainloop()