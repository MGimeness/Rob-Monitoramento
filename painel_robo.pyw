import sys
import os
import io
import re
import time
import gc
import random
import unicodedata
import warnings
import threading
from datetime import datetime, timedelta

import pandas as pd
import pyautogui
import pyperclip
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

# Importa Playwright para a automação web da Aba 3 (Atualização Web Command Center)
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
ID_PLANILHA = "1B8hf71jUN2YNyvb3aJ-i_qoXoYmVXoss"

ABAS_IGNORADAS_SISTEMA = [
    "MULTI", "INSTRUCOES", "INSTRUÇÕES", "LEIA-ME", "LEIAME",
    "BASE", "RESUMO", "DASHBOARD", "AJUDA", "CONFIG", "CONFIGURAÇÕES",
    "PACIENTES", "PACIENTE", "OBSERVACOES", "OBSERVAÇÕES",
    "LOG", "LOGS", "METRICAS", "MÉTRICAS"
]

GRUPOS_BLOQUEADOS = [
    "ISA LAB - ASSISTE & TD",
    "ISA LAB",
    "OPS/LOG CARE",
    "LOG CARE",
    "EQUIPE SUPORTE",
    "ATB E PROCEDIMENTOS"
]

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
    if "ISA LAB" in nome_norm or "ISA LAB - ASSISTE & TD" in nome_norm:
        return True
    for bloqueado in GRUPOS_BLOQUEADOS:
        bloqueado_norm = remover_acentos(bloqueado)
        if bloqueado_norm in nome_norm or nome_norm == bloqueado_norm:
            return True
    return False

def contem_palavra_pendente(valor):
    if valor is None or pd.isna(valor):
        return True
    val_str = remover_acentos(str(valor))
    for termo in TERMOS_INVALIDOS_PLANTAO:
        if remover_acentos(termo) in val_str:
            return True
    return val_str in ["", "NAN", "NONE"]

# ==============================================================================
# COMMAND CENTER WEB: REGRAS DE CASAMENTO (planilha x painel) E LEITURA DA TABELA
# ==============================================================================
def normalizar_para_comparar(texto):
    """Maiúsculas, sem acentos e sem pontuação (funciona com texto em minúsculas, ao contrário de remover_acentos)."""
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
    """Nome em palavras maiúsculas, sem acentos, sem '(...)' e sem partículas (DE, DA, DOS...)."""
    if nome is None:
        return []
    base = str(nome).replace('\xa0', ' ').split("(")[0]
    return [t for t in normalizar_para_comparar(base).split() if t not in PARTICULAS_NOME]


def nomes_compativeis(nome_planilha, nome_painel):
    """O painel traz o nome completo; a planilha pode trazer só os primeiros nomes (mínimo 2).
    Compara as palavras na ordem: o nome menor precisa ser o começo do maior."""
    a = tokens_nome_paciente(nome_planilha)
    b = tokens_nome_paciente(nome_painel)
    if len(a) < 2 or len(b) < 2:
        return False
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def escolher_linha_paciente(nome_planilha, candidatos):
    """Escolhe a linha do painel para o paciente. Retorna (linha, motivo): 'ok', 'nao_encontrado' ou 'ambiguo'."""
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
    """07:00 / 08:10 -> DIURNO; 19:00 -> NOTURNO."""
    return "DIURNO" if 6 <= hora < 18 else "NOTURNO"


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
    """Colunas da planilha do turno (DIURNO/NOTURNO) e do dia escolhido. Ex.: '19/10 - NOTURNO'.
    Se a planilha tiver colunas com data, só vale a do dia; se não tiver data nenhuma, usa a primeira do turno."""
    turno_norm = normalizar_para_comparar(turno)
    candidatas = [c for c in colunas if turno_norm in normalizar_para_comparar(str(c))]
    if not candidatas:
        return []
    
    # Procura dia e mês na string da coluna (ex: "19/10" ou "19-10" ou "19/10/2026")
    padrao_dia_mes = rf"(?<!\d)0?{data_dt.day}\s*[/\-.]\s*0?{data_dt.month}(?!\d)"
    do_dia = re.compile(padrao_dia_mes)
    
    com_data_do_dia = [c for c in candidatas if do_dia.search(str(c))]
    if com_data_do_dia:
        return com_data_do_dia
    
    # Se não houver data explícita com o dia filtrado, retorna candidatas gerais do turno
    return candidatas[:1]


def pontuar_item_filtro(alvo, candidato):
    """Pontua o quanto um item da lista de filtros corresponde ao nome procurado (None = não corresponde)."""
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
    """Transforma a tabela lida da página em uma lista de linhas com nome, data, hora, turno e alerta."""
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


# ==============================================================================
# DISPARO DE MONITORAMENTO: REGRA DE PAD POR DIA PAR / ÍMPAR
# ==============================================================================
_TURNOS_PAD = {"DIURNO": "D", "DIURNOS": "D", "DIA": "D", "NOTURNO": "N", "NOTURNOS": "N", "NOITE": "N", "24H": "DN", "24": "DN"}
_PARIDADES_PAD = {"PAR": "PAR", "PARES": "PAR", "IMPAR": "IMPAR", "IMPARES": "IMPAR"}


def _regra_paridade_pad(texto):
    """Lê textos como 'DIURNO - ÍMPAR', 'NOTURNO - PAR / DIURNO - ÍMPAR', '24H - PAR'.
    Retorna None se não houver PAR/ÍMPAR; senão uma lista de (turno, paridade), onde turno é 'D', 'N' ou 'DN'
    e paridade é 'PAR', 'IMPAR' ou None (o turno vale todos os dias)."""
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
            pares.append(("DN", paridade_pendente))  # só 'PAR'/'ÍMPAR', sem turno: vale para os dois
        pares.extend((t, None) for t in acumulados)
    return pares if achou_paridade else None


def interpretar_pad_paridade(pad_texto, status_texto, dia_noturno, dia_diurno):
    """Decide quais plantões do paciente caem em um dia que combina com o PAD escrito na planilha.
    O noturno é de HOJE e o diurno é de AMANHÃ, então cada um usa a paridade do seu próprio dia.
    Procura primeiro na coluna PAD e, se não houver PAR/ÍMPAR lá, na coluna Status.
    Retorna None quando não há regra de par/ímpar (vale a lógica antiga) ou {'noturno', 'diurno', 'texto'}."""
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
        self.tab_command_center = self.tabview.add("Atualização Web Command Center")

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
                 ("cc", "Command Center Web", "Atualização web Command Center"))
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
        """Trava: sem o nome no campo NOME nenhuma ação continua."""
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

        # Coluna 1: indicadores
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

        # Coluna 2: medidor circular feito de 40 marcas
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

        # Coluna 3: gráfico de envios recentes + registro de eventos
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

        MENSAGEM_SSA = f"{cabecalho_nome}\n\n🔷ATENÇÃO – MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão de amanhã ({amanha})\n➡️Diurno e Noturno \n➡️Caso tenha necessidade de cobertura sinalizar com antecedência. \n\n⚠️ Importante\nO pagamento será realizado somente com:\n📱 Uso correto do aplicativo.\n📎 Evidências anexadas,\n💳 Dados bancários conferidos e atualizados.\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_PADRAO = f"{cabecalho_nome}\n\n🔷ATENÇÃO – MONITORAMENTO DIÁRIO 🔷\n\n🗓️ Confirmado plantão *Noturno de hoje ({hoje})?*\n🗓 Confirmado plantão *Diurno de amanhã ({amanha})?*\n\n*➡️ Se o atendimento confirmado for uma cobertura, sinalize imediatamente.*\n*➡Caso tenha necessidade de cobertura sinalizar com antecedência.*\n\n⚠ Importante\nO pagamento será realizado somente com:\n📱 Uso correto do aplicativo.\n📎 Folhas de produtividade e evolução.\n💳 Dados bancários conferidos e atualizados.\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_DIURNO = f"{cabecalho_nome}\n\n🔷ATENÇÃO – MONITORAMENTO DIÁRIO 🔷\n\n🗓 Confirmado plantão *Diurno de amanhã ({amanha})?*\n\n*➡ Se o atendimento confirmado for uma cobertura, sinalize imediatamente.*\n*➡Caso tenha necessidade de cobertura sinalizar com antecedência.*\n\n⚠ Importante\nO pagamento será realizado somente com:\n📱 Uso correto do aplicativo.\n📎 Folhas de produtividade e evolução.\n💳 Dados bancários conferidos e atualizados.\n\nAtenciosamente,\nSetor de Monitoramento"
        MENSAGEM_PAD_NOTURNO = f"{cabecalho_nome}\n\n🔷ATENÇÃO – MONITORAMENTO DIÁRIO 🔷\n\n🗓️ Confirmado plantão *Noturno de hoje ({hoje})?*\n\n*➡ Se o atendimento confirmado for uma cobertura, sinalize imediatamente.*\n*➡Caso tenha necessidade de cobertura sinalizar com antecedência.*\n\n⚠ Importante\nO pagamento será realizado somente com:\n📱 Uso correto do aplicativo.\n📎 Folhas de produtividade e evolução.\n💳 Dados bancários conferidos e atualizados.\n\nAtenciosamente,\nSetor de Monitoramento"

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
            if pd.isna(val) or val is None:
                return False
            texto = remover_acentos(str(val))
            return "PENDENTE" in texto

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

            cols_noturno = colunas_turno_data(colunas_validas, "NOTURNO", hoje_dt)
            cols_diurno = colunas_turno_data(colunas_validas, "DIURNO", amanha_dt)
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

                    if noturno_pendente or diurno_pendente:
                        lista_cobrancas.append({
                            "Convenio": nome_aba.strip(),
                            "Paciente": paciente_nome,
                            "NoturnoPendente": noturno_pendente,
                            "DiurnoPendente": diurno_pendente,
                            "TxtNoturno": "PENDENTE" if noturno_pendente else ("OK" if cols_noturno else "—"),
                            "TxtDiurno": "PENDENTE" if diurno_pendente else ("OK" if cols_diurno else "—")
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
                nome_busca = remover_acentos(nome_bruto)

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
    # LÓGICA DA ABA 3: ATUALIZAÇÃO WEB COMMAND CENTER
    # ==========================================================================
    def setup_aba_command_center(self):
        self.cc_checkboxes_abas = {}
        self.cc_df_filtrado = pd.DataFrame()
        self.cc_em_execucao = False
        self.cc_solicitar_parada = False
        self.cc_indice_atual = 0

        frame_main = ctk.CTkFrame(self.tab_command_center, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=2, pady=2)

        self.cc_scroll_convenios = self._criar_painel_convenios(
            frame_main, "Convênios / Parceiros", "Marque o convênio (parceiro) que será atualizado.", self.cc_toggle_todas_abas)

        frame_direita = self._novo_card(frame_main)
        frame_direita.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self._cabecalho_secao(frame_direita, 2, "Parâmetros do Command Center", "Confira data, turno (Ambos confirma Diurno e Noturno), produto e endereço do painel antes de cruzar a planilha.")

        f_config = ctk.CTkFrame(frame_direita, fg_color=COR_PAINEL_ALT, border_width=1, border_color=COR_BORDA, corner_radius=RAIO_CTRL)
        f_config.pack(fill="x", padx=12, pady=(0, 6))
        f_config.grid_columnconfigure(3, weight=1)

        dt_hoje_str = datetime.now().strftime("%Y-%m-%d")
        fonte_rotulo = (FONTE_UI, 12, "bold")

        ctk.CTkLabel(f_config, text="Data (AAAA-MM-DD):", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=0, column=0, padx=(14, 10), pady=(12, 8), sticky="w")
        self.cc_ent_data = ctk.CTkEntry(f_config, width=150, **ESTILO_ENTRY)
        self.cc_ent_data.insert(0, dt_hoje_str)
        self.cc_ent_data.grid(row=0, column=1, padx=5, pady=(12, 8), sticky="w")

        ctk.CTkLabel(f_config, text="Turno:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=0, column=2, padx=(20, 10), pady=(12, 8), sticky="w")
        self.cc_cmb_turno = ctk.CTkOptionMenu(
            f_config, values=["Ambos", "Diurno", "Noturno"], **filtrar_estilo(ctk.CTkOptionMenu, dict(width=150, height=34, corner_radius=RAIO_CTRL,
            fg_color=COR_FUNDO, button_color=COR_PRIMARIO, button_hover_color=COR_PRIMARIO_HOVER,
            text_color=COR_TEXTO, font=(FONTE_MONO, 12), dropdown_font=(FONTE_MONO, 12),
            dropdown_fg_color=COR_PAINEL_ALT, dropdown_hover_color=COR_HOVER, dropdown_text_color=COR_TEXTO)))
        self.cc_cmb_turno.set("Ambos")
        self.cc_cmb_turno.grid(row=0, column=3, padx=5, pady=(12, 8), sticky="w")

        ctk.CTkLabel(f_config, text="Produto:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=1, column=0, padx=(14, 10), pady=8, sticky="w")
        self.cc_ent_produto = ctk.CTkEntry(f_config, width=280, **ESTILO_ENTRY)
        self.cc_ent_produto.insert(0, "PLANTÃO DE ENFERMAGEM 12 HORAS")
        self.cc_ent_produto.grid(row=1, column=1, columnspan=3, padx=(5, 14), pady=8, sticky="ew")

        ctk.CTkLabel(f_config, text="URL Painel:", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=2, column=0, padx=(14, 10), pady=8, sticky="w")
        self.cc_ent_url = ctk.CTkEntry(f_config, placeholder_text="URL do Command Center", width=550, **ESTILO_ENTRY)
        self.cc_ent_url.insert(0, f"https://command-center.isalab.com.br/monitoramento?monDate={dt_hoje_str}&monPageSize=200")
        self.cc_ent_url.grid(row=2, column=1, columnspan=3, padx=(5, 14), pady=8, sticky="ew")

        ctk.CTkLabel(f_config, text="Parceiro (opcional):", font=fonte_rotulo, text_color=COR_TEXTO_SUAVE).grid(row=3, column=0, padx=(14, 10), pady=(8, 12), sticky="w")
        self.cc_ent_parceiro = ctk.CTkEntry(f_config, placeholder_text="Automático: usa o nome da aba do convênio (preencha só se o nome no painel for diferente)", **ESTILO_ENTRY)
        self.cc_ent_parceiro.grid(row=3, column=1, columnspan=3, padx=(5, 14), pady=(8, 12), sticky="ew")

        self.cc_btn_processar = ctk.CTkButton(frame_direita, text="Cruzar Planilha (Aba Selecionada) x Regras Web", command=self.cc_processar_lista, height=ALT_BOTAO, font=(FONTE_UI, 13, "bold"), **ESTILO_BOTAO_SECUNDARIO)
        self.cc_btn_processar.pack(fill="x", padx=12, pady=(4, 6))

        self._cabecalho_secao(frame_direita, 3, "Fila de Confirmação Web",
                              "O navegador abre sozinho. Se pedir login, entre manualmente: a sessão fica salva para as próximas vezes.")

        self._criar_kpis(frame_direita, "cc_tree", 5, (("total", "Total na fila"), ("ok", "Concluídos"), ("pendente", "Pendentes"), ("erro", "Com erro")))
        self._criar_legenda(frame_direita, [("Pendente", COR_TEXTO_SUAVE), ("Executando", COR_ALERTA), ("Concluído", COR_SUCESSO), ("Erro", COR_ERRO)])
        self.cc_tree = self._criar_tabela(frame_direita, ("Convenio", "Paciente", "Turno", "ProfissionalPlanilha", "AcaoPrevista", "StatusExecucao"))
        self.cc_tree.heading("Convenio", text="Convênio / Aba")
        self.cc_tree.heading("Paciente", text="Paciente")
        self.cc_tree.heading("Turno", text="Turno")
        self.cc_tree.heading("ProfissionalPlanilha", text="Profissional Planilha")
        self.cc_tree.heading("AcaoPrevista", text="Ação Web")
        self.cc_tree.heading("StatusExecucao", text="Status Execução")

        self.cc_tree.column("Convenio", width=110)
        self.cc_tree.column("Paciente", width=180)
        self.cc_tree.column("Turno", width=70)
        self.cc_tree.column("ProfissionalPlanilha", width=160)
        self.cc_tree.column("AcaoPrevista", width=200)
        self.cc_tree.column("StatusExecucao", width=130)

        self.cc_tree.tag_configure("Confirmar", foreground=COR_SUCESSO)
        self.cc_tree.tag_configure("AtribuirResponsavel", foreground=COR_ALERTA)
        self.cc_tree.tag_configure("Pendente", foreground=COR_TEXTO_SUAVE)
        self.cc_tree.tag_configure("Executando", foreground=COR_ALERTA, font=(FONTE_MONO, 10, "bold"))
        self.cc_tree.tag_configure("Concluido", foreground=COR_SUCESSO, font=(FONTE_MONO, 10, "bold"))
        self.cc_tree.tag_configure("Erro", foreground=COR_ERRO, font=(FONTE_MONO, 10, "bold"))

        self.cc_lbl_resumo, self.cc_btn_parar, self.cc_btn_disparar = self._criar_rodape(
            self.tab_command_center, "Total Registros: 0", "▶ EXECUTAR ATUALIZAÇÃO NO COMMAND CENTER WEB",
            self.cc_iniciar_execucao_thread, self.cc_parar_disparos)

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
        """Aceita AAAA-MM-DD ou DD/MM/AAAA. Retorna (iso, datetime) ou None."""
        texto = str(texto).strip()
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(texto, formato)
                return dt.strftime("%Y-%m-%d"), dt
            except ValueError:
                continue
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
            messagebox.showwarning("Atenção", "Data inválida. Use o formato AAAA-MM-DD (ex: 2026-10-16).")
            return
        data_iso, data_dt = data_info

        turno_sel = self.cc_cmb_turno.get().strip().upper()
        turnos = ["DIURNO", "NOTURNO"] if turno_sel == "AMBOS" else [turno_sel]
        lista_resultados = []
        abas_sem_coluna = []

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

            colunas_por_turno = {t: colunas_turno_data(df_aba.columns, t, data_dt) for t in turnos}

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

                for turno in turnos:
                    prof_valor = ""
                    for col_plantao in colunas_por_turno[turno]:
                        valor = str(row[col_plantao]).replace('\xa0', ' ').strip() if col_plantao in row else ""
                        if valor_eh_plantao_confirmado(valor):
                            prof_valor = valor
                            break

                    if not prof_valor:
                        continue

                    lista_resultados.append({
                        "Convenio": nome_aba.strip(),
                        "Paciente": paciente_nome,
                        "Turno": turno,
                        "Profissional": prof_valor,
                        "Acao": "Mudar Status de Alerta -> Confirmado",
                        "TagAcao": "Confirmar",
                        "IsPendente": False
                    })

        self.cc_df_filtrado = pd.DataFrame(lista_resultados)
        self.cc_indice_atual = 0
        self.cc_solicitar_parada = False

        for row in self.cc_tree.get_children():
            self.cc_tree.delete(row)

        for _, row in self.cc_df_filtrado.iterrows():
            self.cc_tree.insert("", "end", values=(
                row["Convenio"], row["Paciente"], row["Turno"], row["Profissional"], row["Acao"], "⏳ Pendente"
            ), tags=(row["TagAcao"],))

        self.cc_lbl_resumo.configure(text=f"Total Registros Confirmaveis: {len(self.cc_df_filtrado)}")
        limpar_memoria()

        if len(self.cc_df_filtrado) > 0:
            self.cc_btn_disparar.configure(state="normal", text="▶ EXECUTAR ATUALIZAÇÃO NO COMMAND CENTER WEB", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        else:
            self.cc_btn_disparar.configure(state="disabled")

        if abas_sem_coluna:
            messagebox.showwarning(
                "Coluna do dia não encontrada",
                f"Não achei a coluna de {data_dt.strftime('%d/%m')} ({' / '.join(t.title() for t in turnos)}) nesta(s) aba(s):\n\n"
                + "\n".join(f"• {a}" for a in abas_sem_coluna)
                + "\n\nConfira se existe uma coluna com o nome no formato \"19/10 - Diurno\" para a data escolhida."
            )

    def cc_atualizar_status_linha(self, item_id, novo_status, tag_cor):
        valores = list(self.cc_tree.item(item_id, "values"))
        valores[5] = novo_status
        self.cc_tree.item(item_id, values=valores, tags=(tag_cor,))
        self.cc_tree.see(item_id)

    def cc_parar_disparos(self):
        if self.cc_em_execucao:
            self.cc_solicitar_parada = True
            self.cc_btn_parar.configure(state="disabled", text="■ PARANDO...")

    def cc_iniciar_execucao_thread(self):
        if self.cc_em_execucao:
            return

        if not self._exigir_operador():
            return

        if not PLAYWRIGHT_DISPONIVEL:
            messagebox.showerror("Biblioteca Ausente", "A biblioteca Playwright não está instalada.\nInstale executando: pip install playwright && playwright install")
            return

        itens_tabela = list(self.cc_tree.get_children())
        pendentes = [i for i, child in enumerate(itens_tabela) if "⏳ Pendente" in str(self.cc_tree.item(child, "values")[5])]
        if not pendentes:
            messagebox.showinfo("Aviso", "Todos os registros já foram executados!")
            return

        data_info = self._cc_interpretar_data(self.cc_ent_data.get())
        if not data_info:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato AAAA-MM-DD (ex: 2026-10-16).")
            return
        data_iso = data_info[0]

        convenios = list(dict.fromkeys(self.cc_df_filtrado.iloc[i]["Convenio"] for i in pendentes))
        parceiro_manual = self.cc_ent_parceiro.get().strip()
        produto = self.cc_ent_produto.get().strip()

        texto_msg = (
            f"🚀 EXECUTANDO NAVEGAÇÃO AUTOMÁTICA WEB (PLAYWRIGHT)\n\n"
            f"1. Abrir o painel na data {data_iso}\n"
            f"2. Filtros -> Produto ('{produto}') -> Parceiro ('{parceiro_manual or ' / '.join(convenios)}')\n"
            f"3. Achar cada paciente no plantão certo (Diurno 07h / Noturno 19h). O nome pode estar completo no painel e só com os 2 primeiros nomes na planilha.\n"
            f"4. Marcar as linhas -> Atualizar Status -> Confirmado.\n\n"
            f"{len(pendentes)} registro(s) na fila. Deseja iniciar?"
        )

        if messagebox.askyesno("Confirmar Execução Web", texto_msg):
            cfg = {
                "url": self._cc_url_com_data(self.cc_ent_url.get().strip(), data_iso),
                "data_iso": data_iso,
                "produto": produto,
                "parceiro_manual": parceiro_manual,
            }
            self.cc_em_execucao = True
            self.cc_solicitar_parada = False
            self.cc_btn_disparar.configure(state="disabled")
            self.cc_btn_processar.configure(state="disabled")
            self.cc_btn_parar.configure(state="normal", text="■ PARAR / PAUSAR")

            threading.Thread(target=self._cc_executar_playwright_worker, args=(cfg, itens_tabela, pendentes), daemon=True).start()

    def _cc_finalizar_loop(self, motivo=""):
        self.cc_em_execucao = False
        self.cc_btn_disparar.configure(state="normal", text="▶ REINICIAR / CONTINUAR ATUALIZAÇÃO WEB", fg_color=COR_PRIMARIO, hover_color=COR_PRIMARIO_HOVER)
        self.cc_btn_processar.configure(state="normal")
        self.cc_btn_parar.configure(state="disabled", text="■ PARAR / PAUSAR")

        limpar_memoria()

        status_todos = [str(self.cc_tree.item(item, "values")[5]) for item in self.cc_tree.get_children()]
        total = len(status_todos)
        concluidos = sum(1 for st in status_todos if "🟢" in st)
        erros = sum(1 for st in status_todos if "❌" in st)
        alertas = sum(1 for st in status_todos if "⚠" in st)
        pendentes = sum(1 for st in status_todos if "⏳" in st)

        resumo_msg = (
            f"📊 BALANÇO DA ATUALIZAÇÃO WEB COMMAND CENTER\n\n"
            f"🔹 Total na Fila: {total}\n"
            f"🟢 Confirmados no Painel: {concluidos}\n"
            f"❌ Com Erro / Não Localizados: {erros}\n"
            f"⚠️ Alerta diferente de 'Não confirmado' (não alterados): {alertas}\n"
            f"⏳ Pendentes Restantes: {pendentes}\n\n"
        )

        if motivo:
            resumo_msg = f"MOTIVO DA PAUSA: {motivo}\n\n" + resumo_msg

        messagebox.showinfo("Resumo da Automação Web", resumo_msg)

    # ------------------------------------------------------------------
    # COMMAND CENTER WEB: apoio à navegação (Playwright)
    # ------------------------------------------------------------------
    def _cc_url_com_data(self, url, data_iso):
        if re.search(r"monDate=\d{4}-\d{2}-\d{2}", url):
            return re.sub(r"monDate=\d{4}-\d{2}-\d{2}", f"monDate={data_iso}", url)
        separador = "&" if "?" in url else "?"
        return f"{url}{separador}monDate={data_iso}"

    def _cc_pasta_script(self):
        return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    def _cc_salvar_debug(self, page, nome):
        try:
            pasta = os.path.join(self._cc_pasta_script(), "debug_command_center")
            os.makedirs(pasta, exist_ok=True)
            carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
            page.screenshot(path=os.path.join(pasta, f"{carimbo}_{nome}.png"))
        except Exception:
            pass

    def _cc_definir_status(self, item_id, texto, tag):
        self.after(0, self.cc_atualizar_status_linha, item_id, texto, tag)
        if tag != "Executando":
            self._cc_finalizados.add(item_id)

    @staticmethod
    def _cc_visivel(localizador, ms=1500):
        try:
            localizador.wait_for(state="visible", timeout=ms)
            return True
        except Exception:
            return False

    def _cc_abrir_filtros(self, page):
        candidatos = [
            page.get_by_role("button", name=re.compile(r"Filtros", re.I)).first,
            page.locator("button, .v-btn").filter(has_text=re.compile(r"^\s*Filtros\s*$", re.I)).first,
            page.locator(".mdi-filter-outline, i.v-icon").first,
        ]
        for cand in candidatos:
            if self._cc_visivel(cand, 2500):
                cand.click(force=True)
                time.sleep(1.5)
                return
        raise RuntimeError("Botão 'Filtros' não encontrado na página")

    def _cc_fechar_filtros(self, page):
        try:
            page.locator(".v-navigation-drawer").get_by_role("button", name=re.compile(r"^\s*Fechar\s*$", re.I)).first.click(timeout=3000)
        except Exception:
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
        time.sleep(2.0)

    def _cc_itens_da_lista(self, page, espera_max=12.0):
        inicio = time.time()
        textos = []
        while time.time() - inicio < espera_max:
            textos = [t.strip() for t in page.locator(".v-overlay-container .v-list-item").all_inner_texts()]
            carregando = any("CARREGANDO" in normalizar_para_comparar(t) for t in textos)
            if textos and not carregando:
                return textos
            time.sleep(0.5)
        return [t for t in textos if "CARREGANDO" not in normalizar_para_comparar(t)]

    def _cc_selecionar_filtro(self, page, rotulo, termos_busca, alvo_item):
        gaveta = page.locator(".v-navigation-drawer")
        campo = gaveta.locator(".v-field").filter(has_text=re.compile(rotulo, re.I)).first
        campo.wait_for(state="visible", timeout=10000)

        for termo in termos_busca:
            campo.click(force=True)
            time.sleep(0.8)
            caixa = page.locator(".v-overlay-container input").last
            if not self._cc_visivel(caixa, 1500):
                caixa = campo.locator("input").first
            caixa.click(force=True)
            caixa.fill("")
            time.sleep(0.2)
            caixa.press_sequentially(termo, delay=50)
            time.sleep(1.2)

            textos = self._cc_itens_da_lista(page)
            melhor, melhor_pontos = None, None
            for i, texto in enumerate(textos):
                pontos = pontuar_item_filtro(alvo_item, texto)
                if pontos is None:
                    continue
                if melhor is None or pontos > melhor_pontos or (pontos == melhor_pontos and len(texto) < len(textos[melhor])):
                    melhor, melhor_pontos = i, pontos

            if melhor is not None:
                page.locator(".v-overlay-container .v-list-item").nth(melhor).click(force=True)
                time.sleep(1.2)
                try:
                    gaveta.get_by_text(re.compile(rf"^\s*{rotulo}\s*$", re.I)).first.click(force=True, timeout=2000)
                except Exception:
                    pass
                time.sleep(0.8)
                return textos[melhor]
        return None

    def _cc_ler_tabela(self, page):
        return interpretar_tabela_command(page.evaluate(JS_LER_TABELA))

    def _cc_ler_tabela_estavel(self, page, espera_max=15.0):
        inicio = time.time()
        ultimo, linhas = -1, []
        while time.time() - inicio < espera_max:
            linhas = self._cc_ler_tabela(page)
            if linhas and len(linhas) == ultimo:
                return linhas
            ultimo = len(linhas)
            time.sleep(1.2)
        return linhas

    def _cc_marcar_linhas(self, page, indices):
        for idx in indices:
            linha = page.locator("tbody tr").nth(idx)
            linha.scroll_into_view_if_needed()
            caixa = linha.locator("input[type='checkbox']").first
            try:
                if not caixa.is_checked():
                    caixa.click(force=True, timeout=4000)
            except Exception:
                linha.locator(".v-selection-control, .v-checkbox-btn, td").first.click(force=True)
            time.sleep(0.25)
        return sorted(page.evaluate(JS_LINHAS_MARCADAS))

    def _cc_atualizar_status_confirmado(self, page):
        botao = page.get_by_role("button", name=re.compile(r"Atualizar Status", re.I)).first
        botao.wait_for(state="visible", timeout=8000)
        botao.click(force=True)
        time.sleep(1.0)

        dialogo = page.locator(".v-overlay--active .v-card, .v-dialog .v-card").filter(has_text=re.compile(r"novo status", re.I)).last
        dialogo.wait_for(state="visible", timeout=8000)
        dialogo.locator(".v-field").first.click(force=True)
        time.sleep(0.8)

        itens = page.locator(".v-overlay-container .v-list-item")
        textos = itens.all_inner_texts()
        alvo = next((i for i, t in enumerate(textos) if normalizar_para_comparar(t) == "CONFIRMADO"), None)
        if alvo is None:
            raise RuntimeError("Opção 'Confirmado' não encontrada no modal")
        itens.nth(alvo).click(force=True)
        time.sleep(0.6)

        dialogo.get_by_role("button", name=re.compile(r"^\s*Confirmar\s*$", re.I)).first.click(force=True)
        dialogo.wait_for(state="hidden", timeout=20000)
        time.sleep(2.0)

    def _cc_limpar_selecao(self, page):
        try:
            texto_barra = page.get_by_text(re.compile(r"\d+\s+itens?\s+selecionad", re.I)).first
            recipiente = texto_barra.locator("xpath=ancestor::*[.//button][1]")
            recipiente.locator("button").last.click(force=True, timeout=4000)
            time.sleep(1.0)
        except Exception:
            pass
        return not page.evaluate(JS_LINHAS_MARCADAS)

    def _cc_confirmar_lote(self, page, lote):
        resultados = {}
        mapa = {l["chave"]: l for l in self._cc_ler_tabela_estavel(page)}

        selecionar = []
        for item_id, rec, linha in lote:
            atual = mapa.get(linha["chave"])
            if atual is None:
                resultados[item_id] = ("❌ Erro: linha sumiu da tabela", "Erro")
            elif atual["alerta"] != "NAO_CONFIRMADO":
                resultados[item_id] = ("🟢 Já Confirmado", "Concluido")
            else:
                selecionar.append((item_id, rec, atual))

        if not selecionar:
            return resultados

        indices = sorted(a["idx"] for _, _, a in selecionar)
        marcadas = self._cc_marcar_linhas(page, indices)
        if marcadas != indices:
            self._cc_limpar_selecao(page)
            raise RuntimeError(f"Seleção divergente: esperado {len(indices)} linha(s), marcadas {len(marcadas)}")

        self._cc_atualizar_status_confirmado(page)

        mapa_depois = {l["chave"]: l for l in self._cc_ler_tabela_estavel(page)}
        for item_id, rec, linha in selecionar:
            depois = mapa_depois.get(linha["chave"])
            if depois is not None and depois["alerta"] == "CONFIRMADO":
                resultados[item_id] = (f"🟢 Concluído ({rec['Turno']})", "Concluido")
            else:
                resultados[item_id] = ("❌ Erro: não confirmou no painel", "Erro")

        if not self._cc_limpar_selecao(page):
            raise RuntimeError("Não foi possível limpar a seleção da tabela")
        return resultados

    def _cc_processar_grupo(self, page, grupo, data_br):
        for _, item_id, _ in grupo:
            self._cc_definir_status(item_id, "🟡 Buscando...", "Executando")

        linhas = self._cc_ler_tabela_estavel(page)
        if not linhas:
            for _, item_id, _ in grupo:
                self._cc_definir_status(item_id, "❌ Erro: tabela vazia", "Erro")
            return

        usados = set()
        plano = []
        for _, item_id, rec in grupo:
            candidatos = [l for l in linhas if l["turno"] == rec["Turno"] and l["data"] in ("", data_br) and l["chave"] not in usados]
            linha, motivo = escolher_linha_paciente(rec["Paciente"], candidatos)

            if linha is None:
                if motivo == "ambiguo":
                    self._cc_definir_status(item_id, "❌ Erro: nome ambíguo", "Erro")
                else:
                    self._cc_definir_status(item_id, f"❌ Erro: não achei no {rec['Turno'].lower()}", "Erro")
                continue

            usados.add(linha["chave"])
            if linha["alerta"] == "CONFIRMADO":
                self._cc_definir_status(item_id, "🟢 Já Confirmado", "Concluido")
            elif linha["alerta"] == "INICIADO":
                self._cc_definir_status(item_id, "🟢 Já Iniciado", "Concluido")
            elif linha["alerta"] == "NAO_CONFIRMADO":
                plano.append((item_id, rec, linha))
            else:
                self._cc_definir_status(item_id, f"⚠ Alerta: {linha['alerta'].title()}", "AtribuirResponsavel")

        tamanho_lote = getattr(self, "_cc_tamanho_lote", 8)
        for ini in range(0, len(plano), tamanho_lote):
            if self.cc_solicitar_parada:
                break
            lote = plano[ini:ini + tamanho_lote]
            try:
                resultados = self._cc_confirmar_lote(page, lote)
                for item_id, (texto, tag) in resultados.items():
                    self._cc_definir_status(item_id, texto, tag)
            except Exception as e_lote:
                self._cc_salvar_debug(page, "erro_lote")
                msg = str(e_lote).split("\n")[0][:28]
                for item_id, _, _ in lote:
                    if item_id not in self._cc_finalizados:
                        self._cc_definir_status(item_id, f"❌ Erro: {msg}", "Erro")
                if not self._cc_limpar_selecao(page):
                    raise

    def _cc_executar_playwright_worker(self, cfg, itens_tabela, indices_pendentes):
        self._cc_finalizados = set()
        url_alvo = cfg["url"]
        produto_alvo = cfg["produto"]
        parceiro_manual = cfg["parceiro_manual"]
        data_br = datetime.strptime(cfg["data_iso"], "%Y-%m-%d").strftime("%d/%m/%Y")
        motivo_interrupcao = ""

        grupos = {}
        for i in indices_pendentes:
            registro = self.cc_df_filtrado.iloc[i].to_dict()
            grupos.setdefault(registro["Convenio"], []).append((i, itens_tabela[i], registro))

        pasta_sessao = os.path.join(self._cc_pasta_script(), "sessao_navegador")
        page = None

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=pasta_sessao,
                    headless=False,
                    args=["--start-maximized"]
                )
                page = context.pages[0] if context.pages else context.new_page()

                page.goto(url_alvo, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)

                if "login" in page.url.lower() or page.locator("input[type='password']").is_visible():
                    self.after(0, lambda: self.cc_btn_disparar.configure(text="FAÇA O LOGIN NO NAVEGADOR..."))
                    page.wait_for_url(lambda url: "login" not in url.lower(), timeout=120000)
                    time.sleep(3)

                page.wait_for_selector("table, tbody, tr", timeout=30000)

                self._cc_abrir_filtros(page)
                produto_item = self._cc_selecionar_filtro(page, "Produto", [produto_alvo], produto_alvo)
                if not produto_item:
                    raise RuntimeError(f"Produto '{produto_alvo}' não encontrado nos filtros")
                url_base = page.url
                produto_na_url = "monProduct" in url_base

                for n_grupo, (convenio, grupo) in enumerate(grupos.items()):
                    if self.cc_solicitar_parada:
                        motivo_interrupcao = "Interrupção solicitada pelo usuário."
                        break

                    if n_grupo > 0:
                        page.goto(url_base, wait_until="domcontentloaded", timeout=60000)
                        page.wait_for_selector("table, tbody, tr", timeout=30000)
                        time.sleep(2)
                        self._cc_abrir_filtros(page)
                        if not produto_na_url:
                            self._cc_selecionar_filtro(page, "Produto", [produto_alvo], produto_alvo)

                    alvo_parceiro = parceiro_manual or convenio
                    palavras = normalizar_para_comparar(alvo_parceiro).split()
                    termos = list(dict.fromkeys([normalizar_para_comparar(alvo_parceiro), " ".join(palavras[:2]), palavras[-1] if palavras else ""]))
                    termos = [t for t in termos if t]

                    parceiro_item = self._cc_selecionar_filtro(page, "Parceiro", termos, alvo_parceiro)
                    if not parceiro_item:
                        self._cc_salvar_debug(page, "parceiro_nao_encontrado")
                        for _, item_id, _ in grupo:
                            self._cc_definir_status(item_id, "❌ Erro: parceiro não achado", "Erro")
                        continue

                    self._cc_fechar_filtros(page)

                    try:
                        self._cc_processar_grupo(page, grupo, data_br)
                    except Exception as e_grupo:
                        self._cc_salvar_debug(page, "erro_grupo")
                        msg = str(e_grupo).split("\n")[0][:28]
                        for _, item_id, _ in grupo:
                            if item_id not in self._cc_finalizados:
                                self._cc_definir_status(item_id, f"❌ Erro: {msg}", "Erro")
                        motivo_interrupcao = f"Erro ao processar '{convenio}': {e_grupo}"
                        break

                if self.cc_solicitar_parada and not motivo_interrupcao:
                    motivo_interrupcao = "Interrupção solicitada pelo usuário."

                context.close()

        except Exception as e_geral:
            if page is not None:
                self._cc_salvar_debug(page, "erro_geral")
            motivo_interrupcao = f"Erro na automação web: {e_geral}"

        for _, item_id, _ in [g for grupo in grupos.values() for g in grupo]:
            if item_id not in self._cc_finalizados:
                self.after(0, self.cc_atualizar_status_linha, item_id, "⏳ Pendente", "Pendente")

        self.after(0, self._cc_finalizar_loop, motivo_interrupcao)

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    app = PainelUnificado()
    app.mainloop()