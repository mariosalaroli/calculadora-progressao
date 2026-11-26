"""Motor do cálculo de diferenças de subsídio por atraso na 1ª progressão ("shift").

Modelo: a 1ª progressão era devida em ADMISSÃO + INTERSTÍCIO_1 mas foi paga depois.
O atraso (shift, em meses) se propaga: o nível devido no mês t é o nível efetivamente
pago no mês t + shift. Os intervalos seguintes (12, 18 meses...) vêm do histórico real,
então não precisam ser informados.

Os níveis são tratados na escala de 20 (nível antigo nº n = nível novo nº n + OFFSET),
para que o shift atravesse a reestruturação de 13 -> 20 níveis.
"""
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass, field

AQUI = os.path.dirname(os.path.abspath(__file__))

L13 = ["A-I", "A-II", "A-III", "B-I", "B-II", "B-III", "C-I", "C-II", "C-III", "S-I", "S-II", "S-III", "S-IV"]
L20 = ["A-I", "A-II", "A-III", "A-IV", "A-V", "B-I", "B-II", "B-III", "B-IV", "B-V",
       "C-I", "C-II", "C-III", "C-IV", "C-V", "S-I", "S-II", "S-III", "S-IV", "S-V"]
OFFSET = 7                 # transposição: nível antigo nº n -> nível novo nº n + 7
INICIO_20 = (2025, 1)      # vigência da carreira de 20 níveis

T13 = {
    # 2008–2013: MP 440/2008, Lei 11.890/2008 e Lei 12.775/2012, Anexo IV-a (planilha enviada pelo usuário)
    (2008, 7): [10905.76, 11256.03, 11466.20, 11681.19, 11720.04, 12278.06, 12626.62, 12930.92, 13242.56, 13666.32, 13995.68, 14332.98, 14511.60],
    (2009, 7): [12413.65, 13483.71, 13747.10, 14016.00, 14290.57, 14880.56, 15173.58, 15472.78, 15778.30, 16437.12, 16734.49, 17037.67, 17347.00],
    (2010, 7): [12960.77, 14232.00, 14516.64, 14806.97, 15103.11, 15707.23, 16021.38, 16341.81, 16668.64, 17335.39, 17647.43, 17965.08, 18478.45],
    (2013, 1): [13608.81, 14943.60, 15242.47, 15547.32, 15858.27, 16492.59, 16822.45, 17158.90, 17502.07, 18202.16, 18529.80, 18863.33, 19402.37],
    (2014, 1): [14275.64, 15675.84, 15989.35, 16309.14, 16635.32, 17300.73, 17646.75, 17999.69, 18359.67, 19094.07, 19437.76, 19787.64, 20353.09],
    (2015, 1): [15003.70, 16475.30, 16804.81, 17140.90, 17483.72, 18183.07, 18546.73, 18917.67, 19296.02, 20067.86, 20429.09, 20796.81, 21391.10],
    (2016, 8): [15828.90, 17381.44, 17729.07, 18083.65, 18445.32, 19183.14, 19566.80, 19958.14, 20357.30, 21171.59, 21552.69, 21940.63, 22567.61],
    (2017, 1): [16933.64, 18594.53, 18966.43, 19345.75, 19732.67, 20521.98, 20932.41, 21351.07, 21778.09, 22649.21, 23056.90, 23471.92, 24142.66],
    (2018, 1): [18057.95, 19829.12, 20225.70, 20630.21, 21042.80, 21884.53, 22322.22, 22768.67, 23224.04, 24153.00, 24587.76, 25030.34, 25745.61],
    (2019, 1): [19197.06, 21079.96, 21501.56, 21931.59, 22370.22, 23265.03, 23730.33, 24204.95, 24689.04, 25676.60, 26138.79, 26609.28, 27369.67],
    (2023, 5): [20924.80, 22977.16, 23436.70, 23905.43, 24383.54, 25358.88, 25866.06, 26383.40, 26911.05, 27987.49, 28491.28, 29004.12, 29832.94],
}
T20 = {
    (2025, 1): [18033.52, 18543.82, 19068.57, 19608.16, 20163.02, 21320.30, 21921.61, 22543.99, 23181.93, 23837.92,
                25029.82, 25738.10, 26466.42, 27215.36, 27985.48, 29591.73, 30429.11, 31290.17, 32175.61, 33086.10],
    (2026, 4): [20000.00, 20565.95, 21147.92, 21746.35, 22361.72, 23645.19, 24314.29, 25002.32, 25709.82, 26437.35,
                27759.21, 28544.73, 29352.48, 30183.08, 31037.19, 32818.59, 33747.27, 34702.24, 35684.22, 36694.00],
}

Ym = tuple[int, int]


# ---- datas ------------------------------------------------------------------
def add(ym: Ym, k: int) -> Ym:
    n = ym[0] * 12 + ym[1] - 1 + k
    return (n // 12, n % 12 + 1)


def diff(a: Ym, b: Ym) -> int:
    return (a[0] - b[0]) * 12 + (a[1] - b[1])


def ym_str(ym: Ym) -> str:
    return f"{ym[0]}/{ym[1]:02d}"


def str_ym(s: str) -> Ym:
    s = s.strip().replace("-", "/")
    return (int(s[:4]), int(s[5:7]))


# ---- níveis -----------------------------------------------------------------
def nivel_para_idx20(nome: str, desde: Ym) -> int:
    """Converte o nome do nível (na escala vigente na data) para o índice na escala de 20."""
    nome = nome.strip().upper().replace(" ", "-")
    if desde >= INICIO_20:
        return L20.index(nome)
    return L13.index(nome) + OFFSET


PRIMEIRA_TABELA = min(T13)
INICIO_DIFERENCAS = (2009, 2)   # só valem diferenças a partir deste mês (limite da ação)


def nome_na_data(idx20: int, ym: Ym) -> str:
    """Nome do nível vigente na data para um índice da escala de 20."""
    if ym >= INICIO_20:
        return L20[min(idx20, 19)]
    return L13[min(max(idx20 - OFFSET, 0), 12)]


def nome_e_valor(ym: Ym, idx20: int) -> tuple[str, int, float]:
    """Nome do nível, nº do nível e subsídio no mês, para um índice da escala de 20."""
    if ym < PRIMEIRA_TABELA:
        raise ValueError(f"Não há tabela de subsídio cadastrada antes de {ym_str(PRIMEIRA_TABELA)}.")
    if ym >= INICIO_20:
        k = max(k for k in T20 if k <= ym)
        idx20 = min(idx20, 19)
        return L20[idx20], idx20 + 1, T20[k][idx20]
    k = max(k for k in T13 if k <= ym)
    i = min(max(idx20 - OFFSET, 0), 12)
    return L13[i], i + 1, T13[k][i]


# ---- entradas ---------------------------------------------------------------
def ler_selic(caminho: str | None = None) -> dict[str, float]:
    with open(caminho or os.path.join(AQUI, "selic_mensal.csv"), encoding="utf-8") as f:
        return {r[0]: float(r[1].replace(",", ".")) / 100 for r in list(csv.reader(f, delimiter=";"))[1:] if r}


def ler_reflexos(caminho: str | None = None) -> list[tuple[str, str, float]]:
    with open(caminho or os.path.join(AQUI, "reflexos_pagos.csv"), encoding="utf-8") as f:
        return [(r[0], r[1], float(r[2].replace(",", "."))) for r in list(csv.reader(f, delimiter=";"))[1:] if r]


def ler_historico(caminho: str | None = None) -> list[tuple[str, str]]:
    """Níveis efetivamente pagos (a partir de; nível), tirados das fichas. A 1ª linha é a admissão."""
    with open(caminho or os.path.join(AQUI, "historico_niveis.csv"), encoding="utf-8") as f:
        return [(r[0].strip(), r[1].strip()) for r in list(csv.reader(f, delimiter=";"))[1:] if r]


def gerar_historico(admissao: Ym, primeira_paga: Ym, progressao: int, promocao: int, ate: Ym) -> list[tuple[str, str]]:
    """Histórico pago aproximado, sem fichas: entra em A-I, recebe a 1ª progressão na data informada e,
    depois, sobe um nível a cada `progressao` meses dentro da classe e a cada `promocao` meses quando muda
    de classe (A -> B -> C -> S). A passagem para 20 níveis (2025/01) não reinicia a contagem."""
    idx = nivel_para_idx20("A-I", admissao)
    hist = [(ym_str(admissao), nome_na_data(idx, admissao))]
    if primeira_paga <= ate:
        hist.append((ym_str(primeira_paga), nome_na_data(idx + 1, primeira_paga)))
        hist = estender_historico(hist, progressao, promocao, ate)
    return hist


def estender_historico(hist: list[tuple[str, str]], progressao: int, promocao: int,
                       ate: Ym) -> list[tuple[str, str]]:
    """Continua o histórico pago a partir do último passo, pela regra (progressao meses dentro da classe,
    promocao meses ao mudar de classe), com os passos até `ate`. Não muda os passos já informados."""
    hist = list(hist)
    d = str_ym(hist[-1][0])
    idx = nivel_para_idx20(hist[-1][1], d)
    while idx < 19:
        cand = add(d, progressao)
        muda_classe = nome_na_data(idx, cand).split("-")[0] != nome_na_data(idx + 1, cand).split("-")[0]
        d, idx = add(d, promocao if muda_classe else progressao), idx + 1
        if d > ate:
            break
        hist.append((ym_str(d), nome_na_data(idx, d)))
    return hist


REFLEXOS_NAO = "não incluir"
REFLEXOS_ESTIMADO = "estimado: 13º (jun/nov) + 1/3 férias num mês fixo"
REFLEXOS_FICHAS = "pagamentos reais (fichas)"
REFLEXOS_13 = "simplificado: linha /13 = 4/3 de dezembro"


@dataclass
class Parametros:
    admissao: Ym                            # mês de entrada em exercício
    historico: list[tuple[str, str]]        # níveis pagos: (a partir de AAAA/MM, nível); 1ª linha = admissão
    dia_admissao: int = 1                   # para o mês proporcional
    intersticio_1: int = 18                 # meses até a 1ª progressão devida
    fim: Ym = (2026, 10)                    # último mês com diferenças
    proxima_progressao: int | None = None   # projeção do próximo passo pago (meses após o último); None = sem projeção
    reflexos: str = REFLEXOS_FICHAS
    reflexos_pagos: list[tuple[str, str, float]] = field(default_factory=list)
    somar_13_no_saldo: bool = True          # só no modo simplificado; False = linha /13 exibida, fora do saldo
    atualizar_ate: Ym = (2026, 12)
    selic: dict[str, float] = field(default_factory=dict)
    mes_ferias: int = 1                     # só no modo estimado: mês em que o 1/3 de férias é pago todo ano
    inicio: Ym = INICIO_DIFERENCAS          # diferenças antes deste mês não entram


@dataclass
class Resultado:
    shift: int
    primeira_devida: Ym
    primeira_paga: Ym
    linhas: list[dict]          # uma por lançamento
    atualizacao: list[dict]     # meses só com atualização Selic
    avisos: list[str]

    @property
    def saldo_fim(self) -> float:
        carregados = [l for l in self.linhas if l["no_saldo"]]
        return carregados[-1]["saldo"] if carregados else 0.0

    @property
    def saldo_atualizado(self) -> float:
        return self.atualizacao[-1]["saldo"] if self.atualizacao else self.saldo_fim

    def total(self, grupo: str | None = None) -> float:
        return round(sum(l["diferenca"] for l in self.linhas
                         if l["no_saldo"] and (grupo is None or l["grupo"] == grupo)), 2)


def _trunc(v: float) -> float:
    return math.floor(v * 100 + 1e-6) / 100


def _estimar_reflexos(p: Parametros, subs: dict) -> list[tuple[str, str, float]]:
    """Pagamentos de 13º e 1/3 de férias como o órgão faria, sem fichas: adiantamento de 50% em junho,
    13º integral em novembro (proporcional no ano de admissão) e 1/3 de férias em `mes_ferias`,
    a partir de 12 meses de exercício."""
    out = []
    for ano in range(p.admissao[0], p.fim[0] + 1):
        jun, nov, fer = f"{ano}/06", f"{ano}/11", f"{ano}/{p.mes_ferias:02d}"
        if ano == p.admissao[0]:
            meses = 12 - p.admissao[1] + (1 if p.dia_admissao <= 15 else 0)
            if nov in subs and meses > 0:
                out.append((nov, "13", round(subs[nov][0] * meses / 12, 2)))
        else:
            if jun in subs:
                out.append((jun, "ADIANT_13", round(subs[jun][0] / 2, 2)))
            if nov in subs:
                out.append((nov, "13", subs[nov][0]))
        if fer in subs and str_ym(fer) >= add(p.admissao, 12):
            out.append((fer, "FERIAS_1/3", round(subs[fer][0] / 3, 2)))
    return sorted(out)


def calcular(p: Parametros) -> Resultado:
    avisos: list[str] = []
    hist = sorted((str_ym(d), n) for d, n in p.historico if d and n)
    sched = [(d, nivel_para_idx20(n, d)) for d, n in hist]
    if len(sched) < 2:
        raise ValueError("O histórico precisa ter o nível de entrada e ao menos a 1ª progressão paga.")
    primeira_paga = sched[1][0]
    primeira_devida = add(p.admissao, p.intersticio_1)
    shift = diff(primeira_paga, primeira_devida)
    if shift < 0:
        avisos.append("A 1ª progressão foi paga antes do interstício informado: shift negativo.")
    if p.proxima_progressao:
        sched.append((add(sched[-1][0], p.proxima_progressao), sched[-1][1] + 1))

    def idx_pago(ym: Ym) -> int:
        anteriores = [n for d, n in sched if d <= ym]
        return anteriores[-1] if anteriores else sched[0][1]

    # ---- subsídio mês a mês ---------------------------------------------
    linhas: list[dict] = []
    subs: dict[str, tuple] = {}

    def linha(mes, verba, grupo, ref, pago, devido, no_saldo=True):
        vp, vd, np_, nnp, nd, nnd = subs[ref]
        return dict(mes=mes, verba=verba, grupo=grupo, nivel_pago=np_, n_pago=nnp, valor_pago=round(pago, 2),
                    nivel_devido=nd, n_devido=nnd, valor_devido=round(devido, 2),
                    diferenca=round(devido - pago, 2), no_saldo=no_saldo)

    desde = max(p.admissao, p.inicio)           # primeiro mês em que a diferença vale
    ym = max(desde, PRIMEIRA_TABELA)
    if ym > desde:
        avisos.append(f"Sem tabela de subsídio antes de {ym_str(PRIMEIRA_TABELA)}: as diferenças de "
                      f"{ym_str(desde)} a {ym_str(add(PRIMEIRA_TABELA, -1))} não foram calculadas.")
    while ym <= p.fim:
        ip, idv = idx_pago(ym), idx_pago(add(ym, shift))
        np_, nnp, vp = nome_e_valor(ym, ip)
        nd, nnd, vd = nome_e_valor(ym, idv)
        if ym == p.admissao and p.dia_admissao > 1:     # mês proporcional
            fr = (30 - p.dia_admissao + 1) / 30
            vp, vd = _trunc(vp * fr), _trunc(vd * fr)
        subs[ym_str(ym)] = (vp, vd, np_, nnp, nd, nnd)
        linhas.append(linha(ym_str(ym), "subsídio", "subsídio", ym_str(ym), vp, vd))
        if p.reflexos == REFLEXOS_13 and ym[1] == 12:
            linhas.append(linha(f"{ym[0]}/13", "13º + 1/3 férias (/13)", "13º", ym_str(ym),
                                round(vp * 4 / 3, 2), round(vd * 4 / 3, 2), no_saldo=p.somar_13_no_saldo))
        ym = add(ym, 1)

    # ---- reflexos pelos pagamentos reais ---------------------------------
    if p.reflexos == REFLEXOS_ESTIMADO:
        p_reflexos = _estimar_reflexos(p, subs)
    else:
        p_reflexos = p.reflexos_pagos
    if p.reflexos in (REFLEXOS_FICHAS, REFLEXOS_ESTIMADO):
        def escala(mes, verba, grupo, ref, pago):
            vp, vd = subs[ref][0], subs[ref][1]
            return linha(mes, verba, grupo, ref, pago, round(pago * vd / vp, 2) if vp else pago)

        pagos = [(m, r, v) for m, r, v in p_reflexos if str_ym(m) <= p.fim and m in subs]
        adiant = {}
        for mes, rub, v in pagos:
            if rub == "ADIANT_13":
                l = escala(mes, "13º adiantamento", "13º", mes, v)
                adiant[mes[:4]] = l
                linhas.append(l)
        for mes, rub, v in pagos:
            if rub == "13":
                l = escala(mes, "13º (saldo)", "13º", mes, v)
                a = adiant.get(mes[:4])
                if a:
                    l["valor_pago"] = round(l["valor_pago"] - a["valor_pago"], 2)
                    l["valor_devido"] = round(l["valor_devido"] - a["valor_devido"], 2)
                    l["diferenca"] = round(l["valor_devido"] - l["valor_pago"], 2)
                linhas.append(l)
        eventos: list[list] = []
        for m, r, v in pagos:
            if r != "FERIAS_1/3":
                continue
            if eventos and diff(str_ym(m), str_ym(eventos[-1][-1][0])) == 1:
                eventos[-1].append((m, v))
            else:
                eventos.append([(m, v)])
        for ev in eventos:
            total = round(sum(v for _, v in ev), 2)
            ref = ev[-1][0]
            if abs(total * 3 - subs[ref][0]) > 0.10:
                avisos.append(f"1/3 de férias de {ev[0][0]} ({total:.2f}) não bate com 1/3 do subsídio de {ref}.")
            verba = "1/3 férias" + (f" (ref {ref})" if len(ev) > 1 else "")
            linhas.append(escala(ev[0][0], verba, "1/3 férias", ref, total))

    ordem = {"subsídio": 0, "13º adiantamento": 1, "13º (saldo)": 2}
    linhas.sort(key=lambda l: (l["mes"], ordem.get(l["verba"], 3)))

    # ---- Selic composta ----------------------------------------------------
    # saldo do mês = saldo do mês anterior x (1 + Selic do mês anterior) + diferenças do mês
    saldo, ult = 0.0, None
    for l in linhas:
        mes_real = l["mes"] if not l["mes"].endswith("/13") else l["mes"][:5] + "12"
        if mes_real != ult:
            if ult:
                if ult not in p.selic:
                    avisos.append(f"Sem Selic para {ult}; considerada 0.")
                saldo *= 1 + p.selic.get(ult, 0.0)
            ult = mes_real
        l["selic"] = p.selic.get(mes_real)
        if l["no_saldo"]:
            saldo = round(saldo + l["diferenca"], 2)
            l["saldo"] = saldo
        else:
            l["saldo"] = round(saldo + l["diferenca"], 2)   # exibido, mas não carregado
    atual = []
    ym, s = add(p.fim, 1), saldo
    while ym <= p.atualizar_ate:
        if ult not in p.selic:
            avisos.append(f"Sem Selic para {ult}; considerada 0.")
        s = round(s * (1 + p.selic.get(ult, 0.0)), 2)
        ult = ym_str(ym)
        atual.append(dict(mes=ult, selic=p.selic.get(ult), saldo=s))
        ym = add(ym, 1)

    return Resultado(shift, primeira_devida, primeira_paga, linhas, atual, avisos)
