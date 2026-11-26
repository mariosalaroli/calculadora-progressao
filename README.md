# Ação de progressão — cálculo do valor a receber

Calculadora aproximada das diferenças de subsídio devidas pelo atraso na 1ª progressão (carreira AFFC),
corrigidas pela Selic, sem precisar das fichas financeiras.

Informe o mês e o ano da admissão e da 1ª progressão e a regra de progressão.
O app mostra o valor a receber, a composição (subsídio, 13º, 1/3 de férias, Selic, honorários advocatícios),
a comparação de níveis e a tabela mês a mês, que pode ser baixada em CSV.

## Rodar localmente

```
pip install -r requirements.txt
streamlit run app.py
```

## Atualizar

- Selic: acrescente a taxa do mês em `selic_mensal.csv` (formato `AAAA/MM;taxa`).
- Período: `FIM` (último mês com diferenças) e `ATUALIZAR_ATE` (correção pela Selic) no início de `app.py`.
- Tabelas de subsídio: `T13` e `T20` em `calculo.py`.

É uma aproximação: afastamentos, licenças e progressões fora da regra não são considerados.
