"""Calculadora aproximada das diferenças por atraso na 1ª progressão (sem fichas).

O histórico recebido é gerado pela regra de progressão; 13º e férias são estimados.

Rodar: streamlit run app.py
"""
import io

import altair as alt
import pandas as pd
import streamlit as st

import calculo as c

st.set_page_config(page_title="Ação de progressão - Cálculo do valor a receber", layout="wide")

# Duas séries, validadas no fundo escuro (#212121): azul = recebido/sem correção, verde-água = devido/corrigido
AZUL, VERDE = "#5b9cf0", "#12a594"
TEXTO_FRACO, GRADE = "#9a9a9a", "#333333"
REGRAS = {"18 progressão / 12 promoção": (18, 12), "12 para tudo": (12, 12)}
PERSONALIZAR = "Personalizar"   # 12 ou 18 meses escolhidos passo a passo
FIM = (2026, 10)          # último mês já pago (diferenças até aqui)
ATUALIZAR_ATE = (2026, 12)  # depois do último mês, só Selic
HONORARIOS = 0.09           # honorários advocatícios do escritório, sobre o total corrigido
VERMELHO = "#f87171"


def br(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_ano(ym: c.Ym) -> str:
    return f"{ym[1]:02d}/{ym[0]}"



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"], .stMarkdown, .stTabs button { font-family: 'DM Sans', sans-serif; }
h1 { font-weight: 600 !important; letter-spacing: -0.01em; }
.secao { font-size: 11px; font-weight: 600; color: #9a9a9a; letter-spacing: 0.08em; text-transform: uppercase;
         margin: 1.6rem 0 0.6rem; padding-bottom: 6px; border-bottom: 1px solid #404040; }
.mg { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); margin-bottom: 8px; }
.mg-card { background: #2e2e2e; border: 1px solid #404040; border-radius: 10px; padding: 0.8rem 1rem; }
.mg-card.destaque { border-color: #12a594; background: linear-gradient(180deg, rgba(18,165,148,0.16), #2e2e2e 85%); }
.mg-label { font-size: 11px; color: #9a9a9a; letter-spacing: 0.05em; margin-bottom: 4px; }
.mg-value { font-size: 1.55rem; font-weight: 600; color: #f0f0f0; line-height: 1.2; white-space: nowrap; }
.mg-card.destaque .mg-value { font-size: 1.9rem; }
.mg-value .un { font-size: 0.8rem; font-weight: 500; color: #9a9a9a; margin-right: 3px; }
.mg-sub { font-size: 12.5px; color: #9a9a9a; margin-top: 4px; }
.mg-sub.verde { color: #2dd4bf; font-weight: 600; }
.mg-barra { height: 4px; border-radius: 2px; background: #404040; margin-top: 8px; overflow: hidden; }
.mg-barra > div { height: 100%; border-radius: 2px; }
/* Mês e ano da 1ª progressão: sem o botão de limpar, para "setembro" caber na caixa */
[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Clear value"] { display: none; }
/* Passos do "Personalizar": nome e data à esquerda, 12 | 18 à direita, lado a lado também no celular */
.st-key-passos { gap: 0.35rem; }
.st-key-passos [data-testid="stCaptionContainer"] { margin-top: 0.5rem; }
/* Barra lateral: mês e ano (e os passos) lado a lado também no celular */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.5rem; }
[data-testid="stSidebar"] [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-passos [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] { align-items: flex-end; }
.passo { font-size: 14px; line-height: 1.25; white-space: nowrap; }
.passo span { display: block; font-size: 12px; color: #9a9a9a; }
.passo-cab { display: flex; justify-content: space-between; font-size: 11px; color: #9a9a9a; letter-spacing: 0.05em;
             text-transform: uppercase; padding-bottom: 6px; margin-bottom: 10px; border-bottom: 1px solid #404040; }
.rotulo-duplo { font-size: 14px; line-height: 1.6; margin: 0; padding-bottom: 2px; cursor: help; }
.rotulo-duplo .dica { display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px;
    border: 1px solid #9a9a9a; border-radius: 50%; font-size: 10px; color: #9a9a9a; margin-left: 4px;
    vertical-align: 1px; }
.ext { background: #2e2e2e; border: 1px solid #404040; border-radius: 10px; padding: 0.4rem 1rem; }
.ext-row { display: grid; grid-template-columns: 22px minmax(150px, 1.2fr) 2fr minmax(140px, auto); gap: 12px;
           align-items: center; padding: 9px 0; border-top: 1px solid #383838; font-size: 14px; }
.ext-row:first-child { border-top: none; }
.ext-op { color: #9a9a9a; font-family: 'DM Mono', monospace; text-align: center; }
.ext-v { text-align: right; font-family: 'DM Mono', monospace; font-size: 14px; color: #e4e4e4; white-space: nowrap; }
.ext-row.tot { border-top: 1px solid #555; font-weight: 600; }
.ext-row.desc .ext-v { color: #f87171; }
.ext-row.final { border-top: 1px solid #12a594; }
.ext-row.final .ext-l { color: #2dd4bf; font-weight: 600; }
.ext-row.final .ext-v { color: #2dd4bf; font-weight: 600; font-size: 17px; }
.ext-pct { font-size: 12px; color: #9a9a9a; margin-left: 6px; }
/* Celular: título menor, extrato sem a coluna da barrinha (o % vai para baixo do rótulo) e títulos de seção
   com espaço à direita para os ícones das tabelas */
@media (max-width: 640px) {
    h1 { font-size: 1.75rem !important; line-height: 1.2 !important; }
    .mg-card.destaque .mg-value { font-size: 1.6rem; }
    .mg-value { font-size: 1.35rem; }
    .ext { padding: 0.2rem 0.8rem; }
    .ext-row { grid-template-columns: 14px 1fr auto; gap: 8px; font-size: 13.5px; padding: 8px 0; }
    .ext-row > div:nth-child(3) { display: none; }
    .ext-pct { display: block; margin-left: 0; font-size: 11.5px; }
    .ext-v { font-size: 13px; }
    .ext-row.final .ext-v { font-size: 15px; }
    .secao { padding-right: 120px; }
}
</style>
""", unsafe_allow_html=True)


def secao(texto: str) -> None:
    st.markdown(f'<div class="secao">{texto}</div>', unsafe_allow_html=True)


def card(rotulo: str, valor: str, sub: str = "", destaque: bool = False, sub_verde: bool = False,
         barra: tuple[float, str] | None = None) -> str:
    """Card no estilo do Cap22: rótulo pequeno, número grande, uma linha de apoio e, se houver, uma barra de parte."""
    if valor.startswith("R$ "):
        valor = f'<span class="un">R$</span>{valor[3:]}'
    html = f'<div class="mg-label">{rotulo}</div><div class="mg-value">{valor}</div>'
    if sub:
        html += f'<div class="mg-sub{" verde" if sub_verde else ""}">{sub}</div>'
    if barra:
        html += f'<div class="mg-barra"><div style="width:{barra[0]:.1f}%;background:{barra[1]}"></div></div>'
    return f'<div class="mg-card{" destaque" if destaque else ""}">{html}</div>'


def extrato(linhas: list[tuple]) -> None:
    """Conta que fecha na tela: (sinal, rótulo, valor, classe, parte do total ou None, cor da barra)."""
    html = []
    for op, rotulo, valor, classe, parte, cor in linhas:
        barra = ""
        if parte is not None:
            pct = f"{100 * parte:.1f}%".replace(".", ",")
            barra = (f'<div class="mg-barra" style="margin-top:0"><div style="width:{100 * parte:.1f}%;'
                     f'background:{cor}"></div></div>')
            rotulo += f'<span class="ext-pct">{pct}</span>'
        html.append(f'<div class="ext-row {classe}"><div class="ext-op">{op}</div><div class="ext-l">{rotulo}</div>'
                    f'<div>{barra}</div><div class="ext-v">R$ {br(valor)}</div></div>')
    st.markdown(f'<div class="ext">{"".join(html)}</div>', unsafe_allow_html=True)


def grade(cards: list[str]) -> None:
    st.markdown(f'<div class="mg">{"".join(cards)}</div>', unsafe_allow_html=True)


def estilo(chart):
    """Gráfico no tom do fundo escuro: sem moldura, grade discreta, textos em cinza."""
    return (chart.configure(background="transparent", font="DM Sans")
            .configure_view(stroke=None)
            .configure_axis(labelColor=TEXTO_FRACO, titleColor=TEXTO_FRACO, gridColor=GRADE, domain=False,
                            ticks=False, labelFontSize=11, labelPadding=6)
            .configure_legend(labelColor="#c8c8c8", labelFontSize=12, symbolStrokeWidth=3, columnPadding=18))


# ---- barra lateral: as 4 informações -------------------------------------------
sb = st.sidebar
sb.header("Seus dados")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]
ANOS = list(range(FIM[0], 1989, -1))
# Admissão só com mês e ano: o dia não muda o resultado (no mês de admissão ainda não há diferença)
sb.markdown('<div class="rotulo-duplo" style="cursor: default">1. Admissão</div>', unsafe_allow_html=True)
col_am, col_aa = sb.columns([1, 1])
mes_adm = col_am.selectbox("Mês da admissão", MESES, index=None, placeholder="mês", label_visibility="collapsed")
ano_adm = col_aa.selectbox("Ano da admissão", ANOS, index=None, placeholder="ano", label_visibility="collapsed")
faltam = mes_adm is None or ano_adm is None
adm_ym = None if faltam else (int(ano_adm), MESES.index(mes_adm) + 1)
MESES_PROGRESSAO = {"março": 3, "setembro": 9}   # as progressões só acontecem nesses meses
# Um rótulo só para mês e ano, para as duas caixas ficarem na mesma linha
sb.markdown('<div class="rotulo-duplo" title="Progressões só acontecem em março e setembro. Veja na ficha '
            'financeira o primeiro mês com o subsídio do nível A-II.">2. Recebeu a 1ª progressão em '
            '<span class="dica">?</span></div>', unsafe_allow_html=True)
col_m, col_a = sb.columns([1, 1])
mes_paga = col_m.selectbox("Mês", list(MESES_PROGRESSAO), index=None, placeholder="mês",
                           label_visibility="collapsed")
ano_paga = col_a.selectbox("Ano", ANOS, index=None, placeholder="ano",
                           label_visibility="collapsed")
regra_op = sb.radio("3. Regra de progressão", [*REGRAS, PERSONALIZAR],
                    help="Quantos meses levou cada passo da sua carreira:\n"
                         "- **18/12**: 18 meses para subir de número (A-I → A-II) e 12 para mudar de letra "
                         "(A-III → B-I).\n"
                         "- **12 para tudo**: 12 meses em todos os passos.\n"
                         "- **Personalizar**: você escolhe 12 ou 18 em cada passo.\n\n"
                         "A 1ª progressão também conta: era devida 18 ou 12 meses após a admissão.")
meses_pers = None
if regra_op == PERSONALIZAR:
    if faltam or mes_paga is None or ano_paga is None:
        sb.caption("Preencha a admissão e a 1ª progressão para escolher os passos.")
    else:
        adm_p = adm_ym
        paga_p = (int(ano_paga), MESES_PROGRESSAO[mes_paga])
        if paga_p > adm_p:
            # Uma linha por passo, com 12 | 18 ao lado. Começa pela regra 18/12 (12 nas promoções); as escolhas
            # ficam guardadas até mudar a admissão ou a 1ª progressão. Lidas em ordem, as datas já saem ajustadas.
            ss = st.session_state
            if ss.get("pers_base") != (adm_p, paga_p):
                for k in [k for k in ss if str(k).startswith("pm_")]:
                    del ss[k]
                ss.pers_base = (adm_p, paga_p)

            def manter_escolha(key: str) -> None:
                """Tocar de novo na opção marcada não a desmarca: volta para a última escolha."""
                if ss[key] is None:
                    ss[key] = ss[key + "_ult"]
                ss[key + "_ult"] = ss[key]

            def classe(i: int, d: c.Ym) -> str:
                return c.nome_na_data(i, d).split("-")[0]

            caixa = sb.container(key="passos")
            caixa.markdown('<div class="passo-cab"><span>passo · recebido em</span><span>meses</span></div>',
                           unsafe_allow_html=True)
            idx0 = c.nivel_para_idx20("A-I", adm_p)
            meses_pers, d = [], paga_p
            for k, idx in enumerate(range(idx0 + 1, 20)):
                key = f"pm_{k}"
                if key not in ss:
                    cand = c.add(d, 18)
                    ss[key] = ss[key + "_ult"] = 18 if k == 0 or classe(idx - 1, cand) == classe(idx, cand) else 12
                col_t, col_m = caixa.columns([1.25, 1], vertical_alignment="center", gap="small")
                m = col_m.segmented_control(f"Meses do passo {k + 1}", [12, 18], key=key, on_change=manter_escolha,
                                            args=(key,), label_visibility="collapsed")
                if k:
                    d = c.add(d, m)
                quando = mes_ano(d) + (" · prevista" if d > FIM else "")
                col_t.markdown(f'<div class="passo">{c.nome_na_data(idx - 1, d)} → {c.nome_na_data(idx, d)}'
                               f'<span>{quando}</span></div>', unsafe_allow_html=True)
                meses_pers.append(m)
            caixa.caption("Desde 01/2025, os nomes são os da tabela de 20 níveis.")
com_reflexos = sb.checkbox(
    "4. Incluir 13º e 1/3 de férias", True,
    help="Valores estimados, sem as fichas: 50% do 13º em junho e o restante em novembro; 1/3 de férias uma vez "
         "por ano, em dezembro, a partir de 12 meses de exercício. A diferença é o valor sobre o nível devido menos "
         "o valor sobre o nível recebido. O mês real das férias muda pouco o total (até ~2%).")
com_honorarios = sb.checkbox(f"5. Descontar {HONORARIOS * 100:g}% de honorários advocatícios", True)
MES_FERIAS = 12  # 1/3 de férias estimado em dezembro de cada ano (o mês que ficou mais perto dos valores reais nas fichas testadas)

st.title("Ação de progressão - Cálculo do valor a receber")
st.caption("Cálculo aproximado, sem as fichas financeiras.")

# Os campos começam vazios: cada pessoa preenche os próprios dados
if faltam or mes_paga is None or ano_paga is None:
    st.info("Preencha na barra lateral o mês e o ano da admissão e da 1ª progressão.")
    st.stop()

adm = adm_ym
primeira_paga = (int(ano_paga), MESES_PROGRESSAO[mes_paga])
if regra_op == PERSONALIZAR:
    progressao = meses_pers[0] if meses_pers else 18   # prazo da 1ª progressão, escolhido na 1ª linha
else:
    progressao, promocao = REGRAS[regra_op]

erro = None
if primeira_paga <= adm:
    erro = "A 1ª progressão precisa ser depois da admissão."
elif primeira_paga > FIM:
    erro = f"A 1ª progressão precisa ser até {mes_ano(FIM)}."

res = None
if not erro:
    # O nível devido em cada mês até FIM é o recebido `atraso` meses depois; por isso a regra gera os passos
    # recebidos até FIM + atraso. Os passos depois de FIM não mudam o recebido até FIM, só completam o devido.
    atraso = max(c.diff(primeira_paga, c.add(adm, progressao)), 0)
    if meses_pers:
        hist = c.historico_personalizado(adm, primeira_paga, meses_pers, c.add(FIM, atraso))
    else:
        hist = c.gerar_historico(adm, primeira_paga, progressao, promocao, c.add(FIM, atraso))
    try:
        res = c.calcular(c.Parametros(
            admissao=adm, intersticio_1=progressao, historico=hist, fim=FIM,
            reflexos=c.REFLEXOS_ESTIMADO if com_reflexos else c.REFLEXOS_NAO, atualizar_ate=ATUALIZAR_ATE,
            selic=c.ler_selic(), mes_ferias=MES_FERIAS))
    except Exception as e:
        erro = str(e)

if erro:
    st.error(erro)
    st.stop()

# Sem atraso (1ª progressão recebida no prazo ou antes) não há diferença a calcular
devida = c.add(adm, progressao)
if primeira_paga <= devida:
    quando = "no prazo" if primeira_paga == devida else "antes do prazo"
    st.info(f"Sem atraso: a 1ª progressão era devida em {mes_ano(devida)} ({progressao} meses após a admissão) "
            f"e foi recebida em {mes_ano(primeira_paga)}, {quando}. Não há diferenças a receber.")
    st.stop()

aba_res, aba_mes, aba_met = st.tabs(["Resumo", "Mês a mês", "Bases do cálculo"])

df = pd.DataFrame(res.linhas)
df["data"] = pd.to_datetime(df["mes"] + "/01", format="%Y/%m/%d")
antes20 = df["mes"].map(lambda m: c.str_ym(m) < c.INICIO_20)
df["pos_pago"] = df["n_pago"] + antes20 * c.OFFSET
df["pos_devido"] = df["n_devido"] + antes20 * c.OFFSET

# ---- resumo -------------------------------------------------------------------
with aba_res:
    for a in res.avisos:
        st.warning(a)
    sub_mes = df[(df["verba"] == "subsídio") & (df["diferenca"] > 0)]["mes"]
    meses_dif = len(sub_mes)
    periodo = f"{mes_ano(c.str_ym(sub_mes.iloc[0]))} a {mes_ano(c.str_ym(sub_mes.iloc[-1]))}" if meses_dif else "—"
    nominal = res.total()
    juros = res.saldo_atualizado - nominal
    atraso_sub = f"devida {mes_ano(res.primeira_devida)} · recebida {mes_ano(res.primeira_paga)}"
    corrigido = res.saldo_atualizado
    desconto = round(corrigido * HONORARIOS, 2) if com_honorarios else 0.0
    liquido = round(corrigido - desconto, 2)
    pct_hon = f"{HONORARIOS * 100:g}%"
    sub_valor = (f"R$ {br(corrigido)} corrigido até {mes_ano(ATUALIZAR_ATE)} − {pct_hon} de honorários"
                 if com_honorarios else f"corrigido pela Selic até {mes_ano(ATUALIZAR_ATE)}, sem desconto")
    grade([
        card("Valor a receber", f"R$ {br(liquido)}", sub_valor, destaque=True, sub_verde=True),
        card("Atraso da 1ª progressão", f"{res.shift} {'mês' if res.shift == 1 else 'meses'}", atraso_sub),
        card("Meses com diferença", f"{meses_dif}", periodo),
    ])

    secao("De onde vem o valor")
    partes = [("Subsídio", res.total("subsídio"), AZUL)]
    if com_reflexos:
        partes += [("13º salário", res.total("13º"), AZUL), ("1/3 de férias", res.total("1/3 férias"), AZUL)]
    partes.append(("Correção pela Selic", juros, VERDE))
    linhas_ext = [*(("+" if i else "", nome, v, "", (v / corrigido if corrigido else 0), cor) for i, (nome, v, cor) in enumerate(partes))]
    if com_honorarios:
        linhas_ext += [("=", f"Total corrigido até {mes_ano(ATUALIZAR_ATE)}", corrigido, "tot", None, None),
                       ("−", f"Honorários advocatícios ({pct_hon})", desconto, "desc", None, None)]
    linhas_ext.append(("=", "Valor a receber", liquido, "final", None, None))
    extrato(linhas_ext)

    # nível recebido x devido
    secao("Nível recebido × nível devido")
    niv = df[df["verba"] == "subsídio"].copy()
    lo = int(niv[["pos_pago", "pos_devido"]].min().min())
    hi = int(niv[["pos_pago", "pos_devido"]].max().max())
    # Rótulo de cada posição: nível antigo (13 níveis) com o novo (20 níveis) entre parênteses
    def rotulo_nivel(pos: int) -> str:
        novo = c.L20[pos - 1]
        antigo = pos - c.OFFSET
        return f"{c.L13[antigo - 1]} ({novo})" if 1 <= antigo <= len(c.L13) else novo

    nomes = "[" + ",".join(f'"{rotulo_nivel(p)}"' for p in range(1, len(c.L20) + 1)) + "]"
    escala_n = alt.Scale(domain=[lo - 0.3, hi + 0.3], nice=False)
    eixo_x = alt.X("data:T", title=None, axis=alt.Axis(format="%Y", tickCount="year", grid=False))
    eixo_niv = alt.Axis(values=list(range(lo, hi + 1)), labelExpr=f"{nomes}[datum.value - 1]", labelOverlap=False)
    eixo_y = alt.Y("pos:Q", title=None, scale=escala_n, axis=eixo_niv)
    faixa = alt.Chart(niv).mark_area(interpolate="step-after", color=VERDE, opacity=0.18).encode(
        x=eixo_x, y=alt.Y("pos_pago:Q", title=None, scale=escala_n, axis=eixo_niv), y2="pos_devido:Q")
    longo = pd.concat([niv.assign(série="recebido", pos=niv["pos_pago"]),
                       niv.assign(série="devido", pos=niv["pos_devido"])])[["data", "série", "pos"]]
    cores = alt.Scale(domain=["recebido", "devido"], range=[AZUL, VERDE])
    linhas = alt.Chart(longo).mark_line(interpolate="step-after", strokeWidth=2.5).encode(
        x=eixo_x, y=eixo_y, color=alt.Color("série:N", scale=cores, legend=alt.Legend(orient="top", title=None)))
    hover = alt.selection_point(fields=["data"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    dica = [alt.Tooltip("mes:N", title="mês"), alt.Tooltip("nivel_pago:N", title="recebido"),
            alt.Tooltip("nivel_devido:N", title="devido"),
            alt.Tooltip("diferenca:Q", title="diferença no mês (R$)", format=",.2f")]
    alvo = alt.Chart(niv).mark_rule(strokeWidth=12, opacity=0).encode(x=eixo_x, tooltip=dica).add_params(hover)
    guia = alt.Chart(niv).mark_rule(color="#777", strokeWidth=1).encode(x=eixo_x).transform_filter(hover)
    pontos = alt.Chart(longo).mark_point(size=70, filled=True, stroke="#212121", strokeWidth=2, opacity=1).encode(
        x=eixo_x, y=eixo_y, color=alt.Color("série:N", scale=cores, legend=None)
    ).transform_filter(hover)
    st.altair_chart(estilo((faixa + linhas + alvo + guia + pontos).properties(height=340, padding={"left": 12, "right": 4})), width="stretch")
    st.caption("A faixa verde é o período em que o nível recebido ficou abaixo do devido. No eixo, o nível da "
               "tabela antiga (13 níveis, até 2024) e, entre parênteses, o equivalente na tabela atual (20 níveis). "
               "Passe o mouse ou toque para ver cada mês.")

    # valor acumulado
    secao("Valor acumulado")
    car = df.groupby("data", as_index=False).agg(mes=("mes", "first"), diferenca=("diferenca", "sum"),
                                                  saldo=("saldo", "last"))
    car["sem correção"] = car["diferenca"].cumsum().round(2)
    at = pd.DataFrame(res.atualizacao)
    if not at.empty:
        at["data"] = pd.to_datetime(at["mes"] + "/01", format="%Y/%m/%d")
        car = pd.concat([car, at.assign(**{"sem correção": car["sem correção"].iloc[-1]})[
            ["data", "mes", "saldo", "sem correção"]]])
    car = car.rename(columns={"saldo": "corrigido pela Selic"})
    series = ["sem correção", "corrigido pela Selic"]
    acc = car.melt(["data", "mes"], series, var_name="série", value_name="R$")
    cores_a = alt.Scale(domain=["sem correção", "corrigido pela Selic"], range=[AZUL, VERDE])
    eixo_v = alt.Y("R$:Q", title=None,
                   axis=alt.Axis(labelExpr="datum.value == 0 ? '0' : format(datum.value / 1000, ',.0f') + ' mil'",
                                 tickCount=6))
    rgb = "18,165,148"
    area = alt.Chart(acc).transform_filter(alt.datum["série"] == series[-1]).mark_area(
        color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                           stops=[alt.GradientStop(color=f"rgba({rgb},0)", offset=0),
                                  alt.GradientStop(color=f"rgba({rgb},0.30)", offset=1)])
    ).encode(x=eixo_x, y=eixo_v)
    l2 = alt.Chart(acc).mark_line(strokeWidth=2.5).encode(
        x=eixo_x, y=eixo_v, color=alt.Color("série:N", scale=cores_a,
                                  legend=alt.Legend(orient="top", title=None)))
    fim_df = acc[acc["data"] == acc["data"].max()].assign(rot=lambda d: d["R$"].map(lambda v: "R$ " + br(v)))
    rotulos = alt.Chart(fim_df).mark_text(align="right", dy=-12, fontSize=12, fontWeight=600).encode(
        x=eixo_x, y=eixo_v, text="rot:N", color=alt.Color("série:N", scale=cores_a, legend=None))
    hover2 = alt.selection_point(fields=["data"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    dica2 = [alt.Tooltip("mes:N", title="mês"), alt.Tooltip("sem correção:Q", format=",.2f"),
             alt.Tooltip("corrigido pela Selic:Q", format=",.2f")]
    alvo2 = alt.Chart(car).mark_rule(strokeWidth=12, opacity=0).encode(x=eixo_x, tooltip=dica2).add_params(hover2)
    guia2 = alt.Chart(car).mark_rule(color="#777", strokeWidth=1).encode(x=eixo_x).transform_filter(hover2)
    pts2 = alt.Chart(acc).mark_point(size=70, filled=True, stroke="#212121", strokeWidth=2, opacity=1).encode(
        x=eixo_x, y=eixo_v, color=alt.Color("série:N", scale=cores_a, legend=None)).transform_filter(hover2)
    st.altair_chart(estilo((area + l2 + rotulos + alvo2 + guia2 + pts2).properties(height=300, padding={"left": 12, "right": 4})), width="stretch")

# ---- mês a mês ----------------------------------------------------------------
with aba_mes:
    secao("Memória de cálculo")
    tab = pd.DataFrame({
        "ano/mês": df["mes"], "verba": df["verba"],
        "nível recebido": df["nivel_pago"], "valor recebido": df["valor_pago"],
        "nível devido": df["nivel_devido"], "valor devido": df["valor_devido"],
        "diferença": df["diferenca"], "saldo corrigido": df["saldo"]})
    # No mês em que entrou a tabela de 20 níveis, o nome muda sem progressão: mostra o antigo entre parênteses
    virada = df["mes"] == c.ym_str(c.INICIO_20)

    def com_antigo(nome: str, n: int) -> str:
        antigo = n - c.OFFSET
        return f"{nome} (nova tabela; antigo {c.L13[antigo - 1]})" if 1 <= antigo <= len(c.L13) else nome

    tab.loc[virada, "nível recebido"] = [com_antigo(a, n) for a, n in zip(df.loc[virada, "nivel_pago"],
                                                                         df.loc[virada, "n_pago"])]
    tab.loc[virada, "nível devido"] = [com_antigo(a, n) for a, n in zip(df.loc[virada, "nivel_devido"],
                                                                       df.loc[virada, "n_devido"])]
    # A taxa que corrige o saldo em cada mês é a Selic do mês anterior, a mesma para todas as linhas do mês.
    # Os juros entram só na 1ª linha do mês (o saldo é corrigido uma vez por mês): em cada linha,
    # saldo corrigido = saldo da linha anterior + juros no mês + diferença.
    SELIC = c.ler_selic()
    COL_SELIC, COL_JUROS = "Selic do mês anterior (%)", "juros no mês (R$)"

    def selic_anterior(mes: str) -> str:
        v = SELIC.get(c.ym_str(c.add(c.str_ym(mes), -1)))
        return "" if v is None else f"{v * 100:.2f}".replace(".", ",")

    primeiro_mes = df["mes"].iloc[0]
    tab.insert(7, COL_SELIC, ["" if m == primeiro_mes else selic_anterior(m) for m in df["mes"]])
    # Fecho da conta: os meses só com Selic, os honorários advocatícios e o valor a receber
    fecho = [{"ano/mês": a["mes"], "verba": "atualização Selic", COL_SELIC: selic_anterior(a["mes"]),
              "saldo corrigido": a["saldo"]} for a in res.atualizacao]
    n_meses = len(tab) + len(fecho)
    if com_honorarios:
        fecho.append({"verba": f"honorários advocatícios ({pct_hon})", "diferença": -desconto, "saldo corrigido": liquido})
    fecho.append({"verba": "valor a receber", "saldo corrigido": liquido})
    tab = pd.concat([tab, pd.DataFrame(fecho)], ignore_index=True)
    juros, anterior = [], 0.0
    for k, r in tab.iterrows():
        if k == 0 or k >= n_meses:          # 1º mês (nada a corrigir) e linhas do fecho
            juros.append(None)
        else:
            dif = 0.0 if pd.isna(r["diferença"]) else r["diferença"]
            juros.append(round(r["saldo corrigido"] - anterior - dif, 2))
        if k < n_meses:
            anterior = r["saldo corrigido"]
    tab.insert(8, COL_JUROS, juros)
    tab = tab.fillna({k: "" for k in ("ano/mês", "verba", "nível recebido", "nível devido", COL_SELIC)})
    st.dataframe(tab.style.format({k: br for k in ("valor recebido", "valor devido", "diferença", COL_JUROS,
                                                   "saldo corrigido")}, na_rep=""),
                 hide_index=True, width="stretch", height=500)
    st.caption("Saldo corrigido = saldo da linha anterior + juros no mês + diferença. As últimas linhas fecham a "
               "conta: atualização pela Selic depois do último mês"
               + (f", honorários advocatícios ({pct_hon}) sobre o total corrigido" if com_honorarios else "")
               + " e o valor a receber.")

    buf = io.StringIO()
    tab.to_csv(buf, sep=";", decimal=",", index=False, float_format="%.2f")
    st.download_button("Baixar memória de cálculo (CSV)", buf.getvalue().encode("utf-8-sig"), "memoria_de_calculo.csv",
                       "text/csv")

    secao("Seus níveis · confira com as suas fichas")
    st.dataframe(pd.DataFrame([{
        "nível": n,
        "recebido em": mes_ano(c.str_ym(d)) + (" (previsto)" if c.str_ym(d) > FIM else ""),
        "devido em": mes_ano(c.add(c.str_ym(d), -res.shift if i else 0)),
    } for i, (d, n) in enumerate(hist)]), hide_index=True, width="content")
    st.caption(f"Em 01/2025 a carreira passou a ter 20 níveis e os nomes mudaram sem subir de posição "
               f"(ex.: C-I virou C-IV, C-II virou C-V).")

# ---- como é calculado ---------------------------------------------------------
with aba_met:
    secao("Tabelas de subsídio · 13 níveis, até 12/2024")
    st.dataframe(pd.DataFrame({mes_ano(k): v for k, v in c.T13.items()}, index=c.L13).style.format(br),
                 width="stretch")
    st.caption("Cada coluna vale a partir do mês indicado. 2008 a 2013: MP 440/2008, Lei 11.890/2008 e "
               "Lei 12.775/2012 (Anexo IV-a).")
    secao("Tabelas de subsídio · 20 níveis, a partir de 01/2025")
    st.dataframe(pd.DataFrame({mes_ano(k): v for k, v in c.T20.items()}, index=c.L20).style.format(br),
                 width="stretch")

    secao("Selic mensal (%)")
    sel = pd.DataFrame([(int(k[:4]), int(k[5:]), v * 100) for k, v in c.ler_selic().items()],
                       columns=["ano", "mês", "taxa"])
    grade_selic = sel.pivot(index="ano", columns="mês", values="taxa").reindex(columns=range(1, 13))
    grade_selic.columns = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    # Texto já formatado: mês sem taxa (antes de 2008/12 ou ainda sem dado) fica em branco
    st.dataframe(grade_selic.astype(float).map(lambda v: "" if pd.isna(v) else f"{v:.2f}".replace(".", ",")),
                 width="stretch")

    secao("Regras do cálculo")
    st.markdown(f"""
- **Atraso**: mês em que recebeu a 1ª progressão − (admissão + 18 meses, ou 12 na regra "12 para tudo"; em
  "Personalizar", os meses da 1ª linha da tabela).
- **Nível devido**: é a carreira que a pessoa teria se a 1ª progressão viesse no prazo. Como cada passo conta a
  partir do anterior, todos atrasaram o mesmo tanto: cada nível deveria ter chegado o mesmo número de meses antes
  que a 1ª progressão atrasou.
- **Níveis recebidos**: sempre em março ou setembro. Na regra 18/12, 18 meses nos números (A-I → A-II) e 12 nas
  letras (A-III → B-I); na regra "12 para tudo", 12 meses em todos; em "Personalizar", 12 ou 18 meses
  escolhidos em cada passo.
- **13º e 1/3 de férias**: estimados; 13º com metade em junho e o resto em novembro; 1/3 de férias em dezembro.
- **Selic composta**: saldo do mês = saldo anterior × (1 + Selic do mês anterior) + diferenças do mês.
- **Honorários advocatícios**: {HONORARIOS * 100:g}% sobre o total corrigido, pagos ao escritório.
- **Período**: diferenças de {mes_ano(c.INICIO_DIFERENCAS)} (ou da admissão, se posterior) até {mes_ano(FIM)};
  correção pela Selic até {mes_ano(ATUALIZAR_ATE)}.
- **Limites**: é uma aproximação; afastamentos e licenças não são considerados.
""")
