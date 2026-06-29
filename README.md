# CAGE/RS – Plano de Auditoria

Aplicativo web de **arquivo único** para planejamento de auditoria baseado na metodologia de
risco do TCU (Roteiro de Auditoria de Gestão de Riscos, TCU/2017, adaptado), usado pela
**CAGE/SEFAZ-RS**. Transforma o template Excel `plano_cage.xlsx` em uma ferramenta interativa,
com fluxo encadeado entre módulos, cálculo ao vivo e blocos dinâmicos.

**🔗 Acesse:** https://brunodipe1407.github.io/plano-auditoria/

---

## Características

- **HTML único, offline e autocontido** — sem dependências externas (CDN, fontes remotas, APIs).
  A logomarca da CAGE está embutida em base64. Funciona aberto localmente (`file://`) ou no GitHub Pages.
- **Modelo de dados central e reativo** — uma única estrutura de estado alimenta todos os módulos;
  mudou em um lugar, reflete em todos.
- **Português do Brasil**, responsivo (desktop, tablet e smartphone).
- Identidade visual fiel à planilha (navy `#002060` / teal `#00C4B3` + escala de calor de risco).

## Módulos

1. **Entendimento** — cabeçalho-mestre (unidade, base, objeto, responsáveis) e objetivos do trabalho.
2. **Identificação e Análise de Riscos** — riscos dinâmicos com causas/consequências e Fonte do Risco
   (com sugestão automática de causas a partir do catálogo de vulnerabilidades).
3. **Matriz de Riscos e Controles** — probabilidade, impacto e avaliação de controle como dropdowns;
   classificações, situação do controle, risco residual, síntese, teste e prioridade **calculados ao vivo**.
4. **Mapa de Calor** — grade 5×5 (Impacto × Probabilidade) plotando cada risco analisado.
5. **Matriz de Planejamento** — recebe apenas os riscos em escopo; subquestões, critérios,
   procedimentos e programa de trabalho (PT).
6. **Matriz de Achados** e **7. Matriz de Referência** — geradas a partir das subquestões planejadas.
8. **Catálogo de Vulnerabilidades**, **Tabelas** (referência) e **Orientações** (ajuda contextual por campo).

## Motor de cálculo

- Pontuação de Probabilidade e Impacto (1–5) e Índice Inerente (P×I, 1–25).
- Classificação do Risco Inerente em **faixas contíguas** (1–5 Irrelevante · 6–10 Baixo ·
  11–15 Moderado · 16–20 Alto · 21–25 Crítico) — corrige as lacunas do template original.
- Matriz combinada Risco Inerente × Avaliação do Controle (25 combinações) →
  Risco Residual, Síntese, Teste Recomendado e Prioridade.
- **Override manual** das colunas calculadas com **justificativa obrigatória** e marca de
  "ajustado pelo auditor", mantendo o valor sugerido visível.
- Fluxo de escopo obrigatório: apenas riscos com conclusão "Escopo" seguem para Planejamento e Achados.

## Persistência e exportação

- **Salvar/abrir auditoria como JSON** — forma confiável de guardar e retomar o trabalho.
- **Autosave** automático no navegador (localStorage), com indicador de última gravação.
- **Exportar** em **Word** (`.doc`), **Excel** (`.xls`, múltiplas abas) e **PDF** (via impressão do navegador).

> ⚠️ O autosave em localStorage não funciona dentro de iframes isolados (previews);
> funciona normalmente com o arquivo aberto localmente ou no GitHub Pages.

## Versões e confidencialidade

Existem duas versões do app:

- **Versão pública** (`index.html`, publicada neste repositório) — **sem nomes de pessoas**.
  As listas de coordenadores, supervisores e auditores ficam vazias e os campos de responsável
  tornam-se editáveis (texto livre); a lista de unidades é mantida.
- **Versão local com nomes** (não versionada) — contém as listas completas de responsáveis
  extraídas do template, para uso interno. **Não deve ser publicada.**

## Tecnologia

HTML + CSS + JavaScript puro (vanilla), sem framework e sem build. Todo o conteúdo
(estilos, lógica, dados e logo) está embutido em um único arquivo `index.html`.
