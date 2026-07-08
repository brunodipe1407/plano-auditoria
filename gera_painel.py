#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera_painel.py — Regenera o Painel BI dos PLANCONS (painel_plancon.html) a partir da matriz Excel.

Uso:
    python gera_painel.py [matriz_plancon.xlsx] [--aba BASE_BI] [--saida painel_plancon.html]
                          [--rodada N] [--data DD/MM/AAAA]

Dependências:
    pip install pandas openpyxl

Formato esperado — aba BASE_BI (uma linha por avaliação município × linha do instrumento):

    Coluna            Obrigatória  Conteúdo
    ----------------  -----------  ------------------------------------------------------------
    MUNICIPIO         sim          nome do município (como deve aparecer no painel)
    CREPDEC           sim          nº da CREPDEC (1–10)
    LINHA             sim          nº da linha do instrumento (ex.: 9–105)
    CRITERIO          sim          nº do critério (1–26)
    NOTA_DC           sim          nota da DC/RS (0 / 0,5 / 1) — vazia quando a DC não pontuou
    NOTA_REEXEC       sim          nota da reexecução (0 / 0,5 / 1)
    CLASSIFICACAO     sim          COERENTE · SUPERAVALIACAO · SUBAVALIACAO · VICIO_V3 ·
                                   DC_SEM_NOTA · STANDALONE (acentos/minúsculas são aceitos)
    ESTRATO           não          estrato do município (COERENTE, MERITO_SUPER, ...)
    RESSALVA          não          texto de ressalva do município
    CRITERIO_TITULO   não          título do critério (se ausente, usa os títulos padrão C01–C26)
    CENARIO           não          cenário da linha do instrumento
    SUBITEM           não          sub-item da linha do instrumento

    O índice de coerência (geral e por município) e a marcação de standalone são RECALCULADOS
    a partir das linhas — não precisam vir na planilha. Um município é standalone quando todas
    as suas linhas estão classificadas como STANDALONE.

Aba META (opcional, colunas CHAVE | VALOR): rodada, data, oficial_idx, oficial_coe,
    oficial_sup, oficial_sub. Os argumentos --rodada/--data têm prioridade sobre a META.
    Sem valores oficiais, assume-se oficial = calculado.

A planilha `matriz_plancon_exemplo.xlsx` (no repositório) reproduz exatamente o painel de
referência e serve de gabarito do formato.
"""

import argparse
import json
import sys
import unicodedata
from collections import Counter
from datetime import date

try:
    import pandas as pd
except ImportError:
    sys.exit("ERRO: pandas não instalado. Rode:  pip install pandas openpyxl")

# ---------------------------------------------------------------- utilidades

def norm(txt):
    """Normaliza rótulos: maiúsculas, sem acentos, não-alfanuméricos viram '_'."""
    s = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    s = "".join(c if c.isalnum() else "_" for c in s.upper())
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")

def vazio(v):
    return v is None or (isinstance(v, float) and v != v) or str(v).strip() == ""

def texto(v):
    return "" if vazio(v) else str(v).strip()

# nomes lógicos -> apelidos aceitos na planilha (após normalização)
SINONIMOS = {
    "MUNICIPIO":       ["MUNICIPIO", "NOME_MUNICIPIO", "NM_MUNICIPIO"],
    "CREPDEC":         ["CREPDEC", "CREP", "NR_CREPDEC"],
    "LINHA":           ["LINHA", "NUM_LINHA", "LINHA_INSTRUMENTO", "NR_LINHA"],
    "CRITERIO":        ["CRITERIO", "NUM_CRITERIO", "CRITERIO_NUM", "NR_CRITERIO"],
    "NOTA_DC":         ["NOTA_DC", "DC", "NOTA_DEFESA_CIVIL"],
    "NOTA_REEXEC":     ["NOTA_REEXEC", "NOTA_REEXECUCAO", "REEXEC", "REEXECUCAO", "NOTA_RX", "RX"],
    "CLASSIFICACAO":   ["CLASSIFICACAO", "CLASSE", "CLS", "CLASSIF"],
    "ESTRATO":         ["ESTRATO"],
    "RESSALVA":        ["RESSALVA", "RESSALVAS"],
    "CRITERIO_TITULO": ["CRITERIO_TITULO", "TITULO_CRITERIO", "TITULO"],
    "CENARIO":         ["CENARIO"],
    "SUBITEM":         ["SUBITEM", "SUB_ITEM"],
}
OBRIGATORIAS = ["MUNICIPIO", "CREPDEC", "LINHA", "CRITERIO",
                "NOTA_DC", "NOTA_REEXEC", "CLASSIFICACAO"]

# classificação textual -> código usado pelo painel (0..5)
CLASSES = {
    "COERENTE": 0, "COE": 0,
    "SUPERAVALIACAO": 1, "SUPERAVALIACAO_DC": 1, "SUP": 1,
    "SUBAVALIACAO": 2, "SUBAVALIACAO_DC": 2, "SUB": 2,
    "VICIO_V3": 3, "VICIO": 3, "V3": 3,
    "DC_SEM_NOTA": 4, "SEM_NOTA_DC": 4, "SEM_NOTA": 4,
    "STANDALONE": 5, "STD": 5,
}
ESTRATOS_CONHECIDOS = {"COERENTE", "MERITO_SUPER", "MERITO_MISTA",
                       "MEDICAO_OCR", "MEDICAO_DC", "STANDALONE", ""}

TITULOS_PADRAO = {
    1: "Natureza e grupo de risco definidos",
    2: "Código COBRADE correto",
    3: "Dados demográficos e socioeconômicos",
    4: "Responsável pelo acionamento identificado",
    5: "Contato do responsável disponível",
    6: "Ações previstas coerentes com o risco",
    7: "Áreas de risco identificadas e caracterizadas",
    8: "Número de afetados estimado",
    9: "Pontos sensíveis mapeados",
    10: "Abrigos com estrutura mínima",
    11: "Sala de atendimento médico nos abrigos",
    12: "Serviços de saúde com leitos e ambulâncias",
    13: "Efetivo de segurança pública adequado",
    14: "Inventário de veículos e máquinas",
    15: "Participação de ONGs e voluntariado",
    16: "Suprimentos emergenciais listados",
    17: "Ponto de encontro seguro definido e mapeado",
    18: "Rotas de evacuação principais e alternativas (Mapa)",
    19: "Sinalização e treinamento da população",
    20: "Inclusão de anexos legais",
    21: "Inclusão de mapas",
    22: "Validação por coordenador e prefeito",
    23: "Consulta pública realizada",
    24: "Audiência pública e prestação de contas",
    25: "Exercícios simulados previstos",
    26: "Revisão programada do plano",
}

# ---------------------------------------------------------------- leitura

def mapear_colunas(df):
    achadas = {norm(c): c for c in df.columns}
    mapa, faltando = {}, []
    for logico, apelidos in SINONIMOS.items():
        col = next((achadas[a] for a in apelidos if a in achadas), None)
        if col is not None:
            mapa[logico] = col
        elif logico in OBRIGATORIAS:
            faltando.append(logico)
    if faltando:
        sys.exit("ERRO: colunas obrigatórias ausentes na aba BASE_BI: "
                 + ", ".join(faltando)
                 + "\nColunas encontradas: " + ", ".join(map(str, df.columns)))
    return mapa

def nota(v, rotulo, ctx, avisos):
    if vazio(v):
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        sys.exit(f"ERRO: {rotulo} inválida ({v!r}) em {ctx}")
    if x not in (0.0, 0.5, 1.0):
        avisos.add(f"{rotulo} fora de 0/0,5/1 (ex.: {x} em {ctx})")
    return x

def inteiro(v, rotulo, ctx):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        sys.exit(f"ERRO: {rotulo} inválido ({v!r}) em {ctx}")

def ler_meta(xls, args):
    meta = {}
    if "META" in xls.sheet_names:
        df = xls.parse("META", dtype=object)
        if len(df.columns) >= 2:
            for _, r in df.iterrows():
                chave = norm(r.iloc[0]) if not vazio(r.iloc[0]) else ""
                if chave:
                    meta[chave.lower()] = r.iloc[1]
    rodada = args.rodada if args.rodada is not None else meta.get("rodada")
    data = args.data or texto(meta.get("data")) or date.today().strftime("%d/%m/%Y")
    if vazio(rodada):
        print("AVISO: rodada não informada (aba META ou --rodada); rodapé ficará sem o número.")
        rodada = ""
    else:
        rodada = inteiro(rodada, "rodada", "META/--rodada")
    oficial = {}
    for k in ("idx", "coe", "sup", "sub"):
        v = meta.get(f"oficial_{k}")
        if not vazio(v):
            oficial[k] = float(v) if k == "idx" else inteiro(v, f"oficial_{k}", "aba META")
    return rodada, data, oficial

# ---------------------------------------------------------------- construção

def construir_dados(df, mapa, avisos):
    cols = {logico: df[c].tolist() for logico, c in mapa.items()}
    g = lambda logico, i: cols[logico][i] if logico in cols else None

    mun_idx, municipios = {}, []      # nome -> posição; [nome, crepdec, idx, estrato, ressalva, std]
    mun_cls = {}                      # nome -> Counter de classes
    linhas, criterios, rows = {}, {}, []

    for i in range(len(df)):
        nome = texto(g("MUNICIPIO", i))
        if not nome:
            continue  # linha em branco
        ctx = f"BASE_BI linha {i + 2} ({nome})"

        crep = inteiro(g("CREPDEC", i), "CREPDEC", ctx)
        num_linha = inteiro(g("LINHA", i), "LINHA", ctx)
        crit = inteiro(g("CRITERIO", i), "CRITERIO", ctx)

        cls_txt = norm(g("CLASSIFICACAO", i))
        if cls_txt not in CLASSES:
            sys.exit(f"ERRO: CLASSIFICACAO desconhecida {texto(g('CLASSIFICACAO', i))!r} em {ctx}.\n"
                     "Valores aceitos: COERENTE, SUPERAVALIACAO, SUBAVALIACAO, "
                     "VICIO_V3, DC_SEM_NOTA, STANDALONE")
        cls = CLASSES[cls_txt]

        dc = nota(g("NOTA_DC", i), "NOTA_DC", ctx, avisos)
        rx = nota(g("NOTA_REEXEC", i), "NOTA_REEXEC", ctx, avisos)

        estrato = texto(g("ESTRATO", i))
        ressalva = texto(g("RESSALVA", i))
        cenario = texto(g("CENARIO", i))
        subitem = texto(g("SUBITEM", i))
        titulo = texto(g("CRITERIO_TITULO", i))

        # município (1ª aparição define a ordem no painel)
        if nome not in mun_idx:
            mun_idx[nome] = len(municipios)
            municipios.append([nome, crep, None, estrato, ressalva, 0])
            mun_cls[nome] = Counter()
        else:
            m = municipios[mun_idx[nome]]
            if m[1] != crep:
                sys.exit(f"ERRO: CREPDEC divergente para {nome}: {m[1]} x {crep} ({ctx})")
            if estrato and not m[3]:
                m[3] = estrato
            elif estrato and m[3] != estrato:
                avisos.add(f"ESTRATO divergente para {nome}: {m[3]!r} x {estrato!r} (mantido o 1º)")
            if ressalva and not m[4]:
                m[4] = ressalva
        mun_cls[nome][cls] += 1

        # linha do instrumento (o critério deve ser único por linha)
        li = linhas.get(str(num_linha))
        if li is None:
            linhas[str(num_linha)] = [crit, cenario, subitem]
        else:
            if li[0] != crit:
                sys.exit(f"ERRO: CRITERIO divergente para a LINHA {num_linha}: {li[0]} x {crit} ({ctx})")
            if cenario and not li[1]:
                li[1] = cenario
            elif cenario and li[1] != cenario:
                avisos.add(f"CENARIO divergente na LINHA {num_linha} (mantido o 1º)")
            if subitem and not li[2]:
                li[2] = subitem
            elif subitem and li[2] != subitem:
                avisos.add(f"SUBITEM divergente na LINHA {num_linha} (mantido o 1º)")

        if titulo and not criterios.get(str(crit)):
            criterios[str(crit)] = titulo

        rows.append([mun_idx[nome], num_linha, dc, rx, cls])

    # títulos: completa com os padrão C01–C26
    for c in sorted({v[0] for v in linhas.values()}):
        criterios.setdefault(str(c), TITULOS_PADRAO.get(c, ""))
        if not criterios[str(c)]:
            avisos.add(f"critério {c} sem título (informe CRITERIO_TITULO)")

    # standalone derivado + validação de mistura
    for nome, cont in mun_cls.items():
        m = municipios[mun_idx[nome]]
        if cont[5]:
            if any(v and k != 5 for k, v in cont.items()):
                sys.exit(f"ERRO: {nome} mistura linhas STANDALONE com outras classificações.")
            m[5] = 1

    # índice por município = 100*coe/(coe+sup+sub), 1 casa decimal
    for nome, cont in mun_cls.items():
        m = municipios[mun_idx[nome]]
        base = cont[0] + cont[1] + cont[2]
        m[2] = round(100 * cont[0] / base, 1) if (base and not m[5]) else None

    # dicionários ordenados por número (ordem estável no JSON)
    criterios = {k: criterios[k] for k in sorted(criterios, key=int)}
    linhas = {k: linhas[k] for k in sorted(linhas, key=int)}
    return municipios, criterios, linhas, rows

def montar_D(municipios, criterios, linhas, rows, rodada, data, oficial_meta):
    ativo = [m[5] == 0 for m in municipios]
    coe = sum(1 for r in rows if r[4] == 0 and ativo[r[0]])
    sup = sum(1 for r in rows if r[4] == 1 and ativo[r[0]])
    sub = sum(1 for r in rows if r[4] == 2 and ativo[r[0]])
    base = coe + sup + sub
    calc = {"idx": round(100 * coe / base, 1) if base else 0.0,
            "coe": coe, "sup": sup, "sub": sub}
    oficial = {**calc, **oficial_meta}
    D = {"meta": {"rodada": rodada, "data": data,
                  "n_indice": sum(ativo),
                  "oficial": oficial, "calc": calc},
         "criterios": criterios, "linhas": linhas,
         "mun": municipios, "rows": rows}
    return D, calc, oficial

# ---------------------------------------------------------------- principal

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="Gera o painel BI dos PLANCONS a partir da matriz Excel (aba BASE_BI).")
    ap.add_argument("entrada", nargs="?", default="matriz_plancon.xlsx",
                    help="arquivo .xlsx de entrada (padrão: matriz_plancon.xlsx)")
    ap.add_argument("--aba", default="BASE_BI", help="nome da aba com a base (padrão: BASE_BI)")
    ap.add_argument("--saida", default="painel_plancon.html",
                    help="arquivo .html de saída (padrão: painel_plancon.html)")
    ap.add_argument("--rodada", type=int, default=None,
                    help="número da rodada (prioridade sobre a aba META)")
    ap.add_argument("--data", default=None,
                    help="data exibida no rodapé, DD/MM/AAAA (padrão: META ou data de hoje)")
    args = ap.parse_args()

    try:
        xls = pd.ExcelFile(args.entrada, engine="openpyxl")
    except FileNotFoundError:
        sys.exit(f"ERRO: arquivo não encontrado: {args.entrada}")
    if args.aba not in xls.sheet_names:
        sys.exit(f"ERRO: aba {args.aba!r} não existe em {args.entrada}. "
                 f"Abas disponíveis: {', '.join(xls.sheet_names)}")

    df = xls.parse(args.aba, dtype=object)
    mapa = mapear_colunas(df)
    for opcional in ("ESTRATO", "CENARIO", "SUBITEM", "CRITERIO_TITULO"):
        if opcional not in mapa:
            print(f"AVISO: coluna opcional {opcional} ausente — o painel ficará sem essa informação.")

    avisos = set()
    municipios, criterios, linhas, rows = construir_dados(df, mapa, avisos)
    if not rows:
        sys.exit("ERRO: nenhuma linha de dados válida na aba " + args.aba)

    rodada, data, oficial_meta = ler_meta(xls, args)
    D, calc, oficial = montar_D(municipios, criterios, linhas, rows, rodada, data, oficial_meta)

    estranhos = {m[3] for m in municipios if m[3]} - ESTRATOS_CONHECIDOS
    if estranhos:
        avisos.add("estratos fora do padrão (exibidos em cinza): " + ", ".join(sorted(estranhos)))

    dados_json = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.replace("__DADOS_JSON__", dados_json, 1)
    with open(args.saida, "w", encoding="utf-8", newline="") as f:
        f.write(html)

    # ------------------------------------------------ relatório
    n_std = sum(1 for m in municipios if m[5])
    cls_cont = Counter(r[4] for r in rows)
    rot = {0: "coerente", 1: "superavaliação", 2: "subavaliação",
           3: "vício V3", 4: "DC sem nota", 5: "standalone"}
    print(f"Painel gerado: {args.saida} ({len(html) // 1024} KB)")
    print(f"  Municípios: {len(municipios)} ({D['meta']['n_indice']} no índice + {n_std} standalone)"
          f" · linhas do instrumento: {len(linhas)} · critérios: {len(criterios)}")
    print(f"  Avaliações: {len(rows)} — "
          + " · ".join(f"{rot[c]}: {cls_cont[c]}" for c in sorted(cls_cont)))
    print(f"  Índice de coerência (calculado): {calc['idx']}%"
          f"  [coe {calc['coe']} · sup {calc['sup']} · sub {calc['sub']}]")
    if oficial != calc:
        print("  ATENÇÃO: valores oficiais (META) diferem dos calculados: "
              f"oficial {oficial} x calc {calc}")
    for a in sorted(avisos):
        print("  AVISO:", a)

# ---------------------------------------------------------------- template
# HTML/CSS/JS completo do painel (com a animação de contagem gradual);
# __DADOS_JSON__ é substituído pelo JSON gerado a partir da planilha.
TEMPLATE = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Painel BI — Reexecução de Avaliação PLANCON · CAGE/RS</title>
<style>
:root{
  --navy:#1F4E79; --navy2:#2E5E96; --bg:#F2F5F9; --card:#FFFFFF; --ink:#1c2733;
  --green:#2E7D32; --amber:#C77800; --blue:#3B6FB5; --red:#B03030; --grey:#8A96A3;
  --salmon:#E8927C; --shadow:0 2px 10px rgba(16,42,67,.10);
}
*{box-sizing:border-box; margin:0}
body{font-family:"Segoe UI",Calibri,sans-serif; background:var(--bg); color:var(--ink); font-size:14px}
header{background:linear-gradient(100deg,var(--navy),var(--navy2)); color:#fff; padding:18px 28px 14px}
header h1{font-size:21px; font-weight:600}
header .sub{font-size:12px; color:#c9d9ea; margin-top:2px}
.badge{display:inline-block; background:#ffffff22; border:1px solid #ffffff55; border-radius:20px;
  padding:2px 12px; font-size:11px; margin-left:10px; vertical-align:middle}
.kpis{display:flex; gap:14px; padding:16px 28px 0; flex-wrap:wrap}
.kpi{background:var(--card); border-radius:12px; box-shadow:var(--shadow); padding:14px 20px; min-width:170px; flex:1}
.kpi .v{font-size:28px; font-weight:700}
.kpi .l{font-size:11px; color:var(--grey); text-transform:uppercase; letter-spacing:.5px; margin-top:2px}
.kpi.acc{border-top:4px solid var(--green)}
.kpi.sup{border-top:4px solid var(--amber)}
.kpi.sub{border-top:4px solid var(--blue)}
.kpi.n{border-top:4px solid var(--navy)}
.bar-ctrl{display:flex; gap:10px; align-items:center; padding:16px 28px 6px; flex-wrap:wrap}
.tabs{display:flex; background:var(--card); border-radius:10px; box-shadow:var(--shadow); overflow:hidden}
.tabs button{border:0; background:transparent; padding:10px 22px; font-size:14px; font-weight:600; cursor:pointer; color:var(--grey)}
.tabs button.on{background:var(--navy); color:#fff}
.chips{display:flex; gap:6px; flex-wrap:wrap}
.chip{border:1px solid #c8d4e2; background:var(--card); border-radius:16px; padding:5px 13px; font-size:12px; cursor:pointer; user-select:none}
.chip.on{background:var(--navy2); border-color:var(--navy2); color:#fff}
input[type=search],select{border:1px solid #c8d4e2; border-radius:8px; padding:8px 12px; font-size:13px; background:var(--card)}
main{padding:14px 28px 40px}
.card{background:var(--card); border-radius:12px; box-shadow:var(--shadow); padding:18px 20px; margin-bottom:16px}
.card h2{font-size:15px; color:var(--navy); margin-bottom:12px}
.legend{display:flex; gap:16px; font-size:12px; color:#4a5866; margin-bottom:10px; flex-wrap:wrap}
.legend i{display:inline-block; width:11px; height:11px; border-radius:3px; margin-right:5px; vertical-align:-1px}
.critrow{display:flex; align-items:center; gap:10px; padding:3px 0; cursor:pointer; border-radius:6px}
.critrow:hover{background:#eef3f9}
.critrow.sel{background:#e4ecf6; outline:1px solid #b9cbe0}
.critrow .lbl{width:270px; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.critrow .pct{width:52px; text-align:right; font-weight:700; font-size:12px}
.stack{flex:1; height:18px; border-radius:5px; overflow:hidden; display:flex; background:#e9edf2}
.stack div{height:100%}
table{border-collapse:collapse; width:100%; font-size:12.5px}
th{background:var(--navy); color:#fff; padding:7px 9px; text-align:left; position:sticky; top:0; cursor:pointer}
td{padding:6px 9px; border-bottom:1px solid #e6ebf1}
tr.rowm{cursor:pointer}
tr.rowm:hover td{background:#eef3f9}
tr.sel td{background:#e4ecf6}
.estrato{display:inline-block; border-radius:10px; padding:1px 9px; font-size:11px; color:#fff}
.num{text-align:right}
.std{background:var(--salmon); color:#fff; border-radius:10px; padding:1px 8px; font-size:10px; font-weight:700}
.grid2{display:grid; grid-template-columns:1fr 1fr; gap:16px}
@media(max-width:1100px){.grid2{grid-template-columns:1fr}}
.detail-empty{color:var(--grey); font-size:13px; padding:20px; text-align:center}
.mini{font-size:11px; color:var(--grey)}
footer{padding:0 28px 30px; font-size:11px; color:var(--grey)}
.scroll{max-height:560px; overflow-y:auto}
.hidden{display:none}
</style>
</head>
<body>
<header>
  <h1>Painel BI — Reexecução automatizada de avaliação dos PLANCONS Municipais seguindo Instrumento executado pela DC/RS
    <span class="badge">CAGE/RS</span></h1>
  <div class="sub">Dados estáticos consolidados · análise por critério e por município (nomenclatura segue analises realizadas pela DC/RS)· fonte: out\matriz_plancon.xlsx (aba BASE_BI)</div>
</header>

<div class="kpis">
  <div class="kpi acc"><div class="v" id="k-idx">—</div><div class="l">Índice de coerência</div></div>
  <div class="kpi n"><div class="v" id="k-n">—</div><div class="l">Municípios no filtro</div></div>
  <div class="kpi acc"><div class="v" id="k-coe">—</div><div class="l">Linhas coerentes</div></div>
  <div class="kpi sup"><div class="v" id="k-sup">—</div><div class="l">Superavaliação DC</div></div>
  <div class="kpi sub"><div class="v" id="k-sub">—</div><div class="l">Subavaliação DC</div></div>
</div>

<div class="bar-ctrl">
  <div class="tabs">
    <button id="tab-crit" class="on" onclick="setView('crit')">Por critério</button>
    <button id="tab-mun" onclick="setView('mun')">Por município</button>
  </div>
  <div class="chips" id="chips-crep"></div>
  <span style="flex:1"></span>
  <label class="chip" id="chip-std" onclick="toggleStd()" title="ENCANTADO e GRAMADO DOS LOUREIROS: reexecutados considerando ausência de notas da DC/RS - não entram no cálculo">
    incluir avaliações em branco (2) </label>
</div>

<main>
  <!-- ================= POR CRITÉRIO ================= -->
  <div id="view-crit">
    <div class="grid2">
      <div class="card">
        <h2>Coerência por critério (C01–C26)
          <span class="mini" style="float:right"><label><input type="checkbox" id="ord-incoer" onchange="renderCrit()"> ordenar por incoerência</label></span></h2>
        <div class="legend">
          <span><i style="background:var(--green)"></i>Coerente</span>
          <span><i style="background:var(--amber)"></i>Superavaliação DC</span>
          <span><i style="background:var(--blue)"></i>Subavaliação DC</span>
          <span class="mini">— % sobre a base comparável (coe+sup+sub) do filtro atual · clique para detalhar</span>
        </div>
        <div id="crit-bars"></div>
      </div>
      <div class="card">
        <h2 id="crit-det-t">Detalhe do critério</h2>
        <div id="crit-det"><div class="detail-empty">Clique em um critério à esquerda para ver cenários e municípios mais divergentes.</div></div>
      </div>
    </div>
  </div>

  <!-- ================= POR MUNICÍPIO ================= -->
  <div id="view-mun" class="hidden">
    <div class="grid2">
      <div class="card">
        <h2>Municípios
          <span style="float:right; font-weight:normal">
            <input type="search" id="busca" placeholder="buscar município…" oninput="renderMun()">
            <select id="f-estrato" onchange="renderMun()"><option value="">todos os estratos</option></select>
          </span></h2>
        <div class="scroll">
        <table id="tb-mun"><thead><tr>
          <th onclick="sortMun('m')">Município</th><th onclick="sortMun('c')" class="num">CREP</th>
          <th onclick="sortMun('i')" class="num">Índice</th><th onclick="sortMun('coe')" class="num">Coe</th>
          <th onclick="sortMun('sup')" class="num">Sup</th><th onclick="sortMun('sub')" class="num">Sub</th>
          <th>Estrato</th></tr></thead><tbody></tbody></table>
        </div>
      </div>
      <div class="card">
        <h2 id="mun-det-t">Ficha do município</h2>
        <div id="mun-det"><div class="detail-empty">Clique em um município à esquerda para abrir a ficha com o perfil por critério e as linhas divergentes.</div></div>
      </div>
    </div>
  </div>
</main>

<footer>
  Painel offline (arquivo único, sem dependências) · Base analítica validada por amostra <span id="f-rodada"></span>
  (coe/sup/sub idênticos) · Avaliações de municípios com avaliação em branco foram reexecutadas, mas NÃO compõem o índice de coerência ·
  CAGE/RS - Auditoria Operacional <span id="f-data"></span>
</footer>

<script>
const D = __DADOS_JSON__;
/* rows: [mIdx, linha, dc, rx, cls]; cls: 0 coe,1 sup,2 sub,3 vicio,4 dc_sem_nota,5 std
   mun: [nome, crepdec, idx, estrato, ressalva, standalone] */
const CORES = {0:"var(--green)",1:"var(--amber)",2:"var(--blue)"};
const ROT = {0:"coerente",1:"superavaliação",2:"subavaliação",3:"vício V3",4:"DC sem nota",5:"standalone"};
const EST_COR = {COERENTE:"#2E7D32", MERITO_SUPER:"#C77800", MERITO_MISTA:"#7A5EA8",
                 MEDICAO_OCR:"#B03030", MEDICAO_DC:"#B03030", STANDALONE:"#E8927C"};
let view="crit", crep=0, incluiStd=false, critSel=null, munSel=null, munSort={k:"i",asc:true};
let revelado=false, critRevelado=false; // painel inicia zerado; a 1ª interação revela os valores com contagem

const fmt = n => n.toLocaleString("pt-BR");
const pct1 = x => x.toLocaleString("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1})+"%";

document.getElementById("f-rodada").textContent = D.meta.rodada;
document.getElementById("f-data").textContent = "gerado em "+D.meta.data;

/* ---------- animação de contagem ---------- */
const ANIM_INICIAL=2000, ANIM_FILTRO=700; // duração (ms): 1ª revelação / troca de filtro
const easeOut = t => 1-Math.pow(1-t,3);
const anims = {};
function tween(chave,dur,draw){
  if(anims[chave]) cancelAnimationFrame(anims[chave]);
  const t0=performance.now();
  const passo=agora=>{const p=Math.min(1,(agora-t0)/dur); draw(p<1?easeOut(p):1);
    if(p<1) anims[chave]=requestAnimationFrame(passo); else delete anims[chave];};
  anims[chave]=requestAnimationFrame(passo);
}

/* ---------- filtros ---------- */
const creps=[...new Set(D.mun.map(m=>m[1]))].sort((a,b)=>a-b);
const chips=document.getElementById("chips-crep");
const mkChip=(lbl,val)=>{const c=document.createElement("span");c.className="chip"+(val===0?" on":"");
  c.textContent=lbl;c.onclick=()=>{crep=val;[...chips.children].forEach(x=>x.classList.remove("on"));
  c.classList.add("on");render();};chips.appendChild(c);};
mkChip("Todas as CREPDECs",0); creps.filter(c=>c>0).forEach(c=>mkChip("CREPDEC "+String(c).padStart(2,"0"),c));

function toggleStd(){incluiStd=!incluiStd;document.getElementById("chip-std").classList.toggle("on",incluiStd);render();}
function setView(v){view=v;document.getElementById("tab-crit").classList.toggle("on",v==="crit");
  document.getElementById("tab-mun").classList.toggle("on",v==="mun");
  document.getElementById("view-crit").classList.toggle("hidden",v!=="crit");
  document.getElementById("view-mun").classList.toggle("hidden",v!=="mun");render();}

function munAtivo(mi){const m=D.mun[mi];
  if(m[5] && !incluiStd) return false;
  if(crep && m[1]!==crep) return false; return true;}

/* ---------- KPIs ---------- */
let kpiExibido=null; // valores atualmente na tela (null = ainda zerado)
function renderKpis(){
  let coe=0,sup=0,sub=0,ms=new Set();
  for(const [mi,,,,c] of D.rows){ if(!munAtivo(mi)) continue; ms.add(mi);
    if(c===0)coe++; else if(c===1)sup++; else if(c===2)sub++; }
  const base=coe+sup+sub;
  const alvo={idx:base?100*coe/base:0, n:ms.size, coe, sup, sub,
              supP:base?100*sup/base:0, subP:base?100*sub/base:0};
  const de=kpiExibido||{idx:0,n:0,coe:0,sup:0,sub:0,supP:0,subP:0};
  const dur=kpiExibido?ANIM_FILTRO:ANIM_INICIAL;
  tween("kpis",dur,e=>{
    const v={}; for(const k in alvo) v[k]=e===1?alvo[k]:de[k]+(alvo[k]-de[k])*e;
    document.getElementById("k-idx").textContent = base?pct1(v.idx):"—";
    document.getElementById("k-n").textContent = fmt(Math.round(v.n));
    document.getElementById("k-coe").textContent = fmt(Math.round(v.coe));
    document.getElementById("k-sup").textContent = fmt(Math.round(v.sup))+(base?" ("+pct1(v.supP)+")":"");
    document.getElementById("k-sub").textContent = fmt(Math.round(v.sub))+(base?" ("+pct1(v.subP)+")":"");
    kpiExibido=v;
  });
}

/* ---------- POR CRITÉRIO ---------- */
function statsPorCriterio(){
  const st={};
  for(const [mi,linha,,,c] of D.rows){ if(!munAtivo(mi)||c>2) continue;
    const crit=D.linhas[linha][0]; (st[crit]??=[0,0,0])[c]++; }
  return st;
}
function renderCrit(){
  if(!revelado){render();return;}
  const st=statsPorCriterio(), box=document.getElementById("crit-bars"); box.innerHTML="";
  const anima=!critRevelado; critRevelado=true;
  if(!anima && anims["crit-bars"]){cancelAnimationFrame(anims["crit-bars"]); delete anims["crit-bars"];}
  let ks=Object.keys(st).map(Number).sort((a,b)=>a-b);
  if(document.getElementById("ord-incoer").checked)
    ks.sort((a,b)=>{const A=st[a],B=st[b];return (A[0]/(A[0]+A[1]+A[2]))-(B[0]/(B[0]+B[1]+B[2]));});
  const itens=[];
  for(const k of ks){
    const [co,su,sb]=st[k], tot=co+su+sb; if(!tot) continue;
    const row=document.createElement("div");row.className="critrow"+(critSel===k?" sel":"");
    row.onclick=()=>{critSel=k;renderCrit();renderCritDet();};
    row.innerHTML=`<span class="lbl"><b>C${String(k).padStart(2,"0")}</b> ${D.criterios[k]||""}</span>
      <span class="pct" style="color:var(--green)">${pct1(100*co/tot)}</span>
      <span class="stack">
        <div style="width:${100*co/tot}%;background:var(--green)"></div>
        <div style="width:${100*su/tot}%;background:var(--amber)"></div>
        <div style="width:${100*sb/tot}%;background:var(--blue)"></div></span>`;
    box.appendChild(row);
    if(anima) itens.push({pct:row.querySelector(".pct"), alvo:100*co/tot,
      segs:[...row.querySelectorAll(".stack div")].map(s=>({el:s,w:parseFloat(s.style.width)}))});
  }
  if(anima && itens.length){
    for(const it of itens){it.pct.textContent=pct1(0); for(const s of it.segs) s.el.style.width="0%";}
    tween("crit-bars",ANIM_INICIAL,e=>{
      for(const it of itens){it.pct.textContent=pct1(e===1?it.alvo:it.alvo*e);
        for(const s of it.segs) s.el.style.width=(e===1?s.w:s.w*e)+"%";}
    });
  }
}
function renderCritDet(){
  const el=document.getElementById("crit-det");
  if(critSel==null){el.innerHTML='<div class="detail-empty">Clique em um critério à esquerda.</div>';return;}
  document.getElementById("crit-det-t").textContent=`C${String(critSel).padStart(2,"0")} — ${D.criterios[critSel]||""}`;
  const porCen={}, porMun={};
  for(const [mi,linha,,,c] of D.rows){ if(!munAtivo(mi)||c>2) continue;
    if(D.linhas[linha][0]!==critSel) continue;
    const cen=D.linhas[linha][2]||D.linhas[linha][1]||"—";
    (porCen[cen]??=[0,0,0])[c]++;
    if(c>0)(porMun[mi]??=[0,0])[c-1]++;
  }
  let h='<table><thead><tr><th>Cenário / sub-item</th><th class="num">Coe</th><th class="num">Sup</th><th class="num">Sub</th><th class="num">% coer.</th></tr></thead><tbody>';
  for(const [cen,[co,su,sb]] of Object.entries(porCen)){const t=co+su+sb;
    h+=`<tr><td>${cen}</td><td class="num">${co}</td><td class="num">${su}</td><td class="num">${sb}</td><td class="num"><b>${t?pct1(100*co/t):"—"}</b></td></tr>`;}
  h+="</tbody></table>";
  const tops=Object.entries(porMun).map(([mi,[s,b]])=>[D.mun[mi][0],s,b,s+b]).sort((a,b)=>b[3]-a[3]).slice(0,10);
  if(tops.length){h+='<h2 style="margin-top:16px">Municípios mais divergentes neste critério</h2>';
    h+='<table><thead><tr><th>Município</th><th class="num">Superav.</th><th class="num">Subav.</th></tr></thead><tbody>';
    for(const [m,s,b] of tops) h+=`<tr><td>${m}</td><td class="num">${s}</td><td class="num">${b}</td></tr>`;
    h+="</tbody></table>";}
  el.innerHTML=h;
}

/* ---------- POR MUNICÍPIO ---------- */
function statsMun(){
  const st=new Map();
  for(const [mi,,,,c] of D.rows){ if(!munAtivo(mi)) continue;
    const s=st.get(mi)||{coe:0,sup:0,sub:0,std:0};
    if(c===0)s.coe++;else if(c===1)s.sup++;else if(c===2)s.sub++;else if(c===5)s.std++;
    st.set(mi,s);}
  return st;
}
function sortMun(k){munSort.asc=munSort.k===k?!munSort.asc:true;munSort.k=k;renderMun();}
function renderMun(){
  if(!revelado){render();return;}
  const st=statsMun(), q=(document.getElementById("busca").value||"").toUpperCase();
  const fe=document.getElementById("f-estrato").value;
  let list=[...st.entries()].map(([mi,s])=>({mi,m:D.mun[mi][0],c:D.mun[mi][1],i:D.mun[mi][2],e:D.mun[mi][3],std:D.mun[mi][5],...s}));
  if(q)list=list.filter(x=>x.m.includes(q));
  if(fe)list=list.filter(x=>x.e===fe);
  const k=munSort.k, dir=munSort.asc?1:-1;
  list.sort((a,b)=>{const A=a[k]??-1,B=b[k]??-1;return (A<B?-1:A>B?1:0)*dir;});
  const tb=document.querySelector("#tb-mun tbody");tb.innerHTML="";
  for(const x of list){
    const tr=document.createElement("tr");tr.className="rowm"+(munSel===x.mi?" sel":"");
    tr.onclick=()=>{munSel=x.mi;renderMun();renderMunDet();};
    tr.innerHTML=`<td>${x.m}${x.std?' <span class="std">STANDALONE</span>':""}</td>
      <td class="num">${String(x.c).padStart(2,"0")}</td>
      <td class="num"><b>${x.i!=null?x.i.toLocaleString("pt-BR"):"—"}</b></td>
      <td class="num">${x.coe}</td><td class="num">${x.sup}</td><td class="num">${x.sub}</td>
      <td><span class="estrato" style="background:${EST_COR[x.e]||"#8A96A3"}">${x.e||"—"}</span></td>`;
    tb.appendChild(tr);
  }
}
function renderMunDet(){
  const el=document.getElementById("mun-det");
  if(munSel==null){el.innerHTML='<div class="detail-empty">Clique em um município.</div>';return;}
  const m=D.mun[munSel];
  document.getElementById("mun-det-t").textContent=m[0]+" — CREPDEC "+String(m[1]).padStart(2,"0");
  let h="";
  if(m[5]) h+=`<p style="background:#fdeee9;border:1px solid var(--salmon);border-radius:8px;padding:9px 12px;font-size:12.5px;margin-bottom:12px">
    <b>STANDALONE</b> — mérito medido em todas as linhas do instrumento; a nota da DC é desconhecida
    (${m[0]==="ENCANTADO"?"decodificação irrecuperável":"planilha em branco"}), portanto a comparação é
    INCONSISTENTE e o município <b>não compõe o índice</b>.</p>`;
  else h+=`<p style="font-size:13px;margin-bottom:10px">Índice de coerência: <b>${m[2]!=null?m[2].toLocaleString("pt-BR"):"—"}</b> ·
    Estrato: <span class="estrato" style="background:${EST_COR[m[3]]||"#8A96A3"}">${m[3]}</span>
    ${m[4]?`<br><span class="mini">Ressalva: ${m[4]}</span>`:""}</p>`;
  // perfil por critério
  const perfil={};
  for(const [mi,linha,dc,rx,c] of D.rows){ if(mi!==munSel) continue;
    const crit=D.linhas[linha][0]; (perfil[crit]??=[0,0,0,0])[c<=2?c:3]++; }
  h+='<h2>Perfil por critério</h2><div>';
  for(const k of Object.keys(perfil).map(Number).sort((a,b)=>a-b)){
    const [co,su,sb,ou]=perfil[k],tot=co+su+sb+ou;
    h+=`<div class="critrow" style="cursor:default"><span class="lbl" style="width:210px"><b>C${String(k).padStart(2,"0")}</b> ${(D.criterios[k]||"").slice(0,34)}</span>
      <span class="stack">${m[5]
        ?`<div style="width:100%;background:var(--salmon)" title="standalone: ${tot} linha(s)"></div>`
        :`<div style="width:${100*co/tot}%;background:var(--green)"></div>
          <div style="width:${100*su/tot}%;background:var(--amber)"></div>
          <div style="width:${100*sb/tot}%;background:var(--blue)"></div>
          <div style="width:${100*ou/tot}%;background:#c9d2dc"></div>`}</span></div>`;
  }
  h+="</div>";
  // linhas divergentes / notas
  const divs=[];
  for(const [mi,linha,dc,rx,c] of D.rows){ if(mi!==munSel) continue;
    if(m[5]){ if(rx!=null) divs.push([linha,dc,rx,c]); }
    else if(c===1||c===2||c===3||c===4) divs.push([linha,dc,rx,c]); }
  divs.sort((a,b)=>a[0]-b[0]);
  h+=`<h2 style="margin-top:14px">${m[5]?"Notas de mérito (standalone)":"Linhas divergentes / com ressalva"} — ${divs.length}</h2>`;
  h+='<div class="scroll" style="max-height:300px"><table><thead><tr><th>Linha</th><th>Crit.</th><th>Cenário / sub-item</th><th class="num">DC</th><th class="num">Reexec.</th><th>Classificação</th></tr></thead><tbody>';
  const nb=v=>v==null?"?":v.toLocaleString("pt-BR",{minimumFractionDigits:1});
  for(const [l,dc,rx,c] of divs){const li=D.linhas[l];
    h+=`<tr><td>${l}</td><td>C${String(li[0]).padStart(2,"0")}</td><td>${li[2]||li[1]||"—"}</td>
      <td class="num">${nb(dc)}</td><td class="num"><b>${nb(rx)}</b></td><td>${ROT[c]}</td></tr>`;}
  h+="</tbody></table></div>";
  el.innerHTML=h;
}

/* ---------- boot ---------- */
const estratos=[...new Set(D.mun.map(m=>m[3]).filter(Boolean))].sort();
const fe=document.getElementById("f-estrato");
for(const e of estratos){const o=document.createElement("option");o.value=o.textContent=e;fe.appendChild(o);}
function render(){revelado=true; renderKpis(); if(view==="crit"){renderCrit();renderCritDet();} else {renderMun();renderMunDet();}}
/* sem render() inicial de propósito: o painel abre zerado ("—") e o primeiro clique
   em qualquer botão dispara a revelação com contagem gradual (ANIM_INICIAL) */
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
