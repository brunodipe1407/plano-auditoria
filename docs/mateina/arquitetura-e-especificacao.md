# Mateína — Documento de Arquitetura e Especificação (v1.0)

> **Nome provisório.** "Mateína" é a molécula que inicia a manhã do gaúcho — e *iniciar* é exatamente a métrica central deste app. Alternativas em avaliação: Alvorada, Minuano. Decisão pendente do product owner (seção 16).

| Campo | Valor |
|---|---|
| Produto | Assistente pessoal de rotina e execução para adultos com TDAH |
| Plataforma | Android nativo (Kotlin + Jetpack Compose) |
| Distribuição | APK pessoal (sideload), fora da Play Store |
| Data | 20/07/2026 |
| Status | Especificação consolidada — pronta para Sprint 0 |
| Fontes | Conversa de concepção (jul/2026) + documento de conceito e boas práticas + especificação de dados históricos do product owner |

---

## 1. Visão e recorte

**Pitch.** Assistente minimalista para adultos com TDAH, já em tratamento medicamentoso, que ainda lutam para *iniciar* e *manter* rotinas. O app reduz carga mental mostrando **uma ação por vez** e aprende com os padrões do próprio usuário — na v1, por perguntas diretas; nas versões seguintes, por análise do histórico.

**Posicionamento.** Assistente pessoal de rotina e execução — **não** é tratamento, terapia digital ou dispositivo médico. Descrição segura: *"Assistente de rotina para reduzir o atrito no início de tarefas, organizar hábitos e apoiar pessoas que enfrentam dificuldades de atenção e função executiva."* Ainda que o uso seja pessoal (RDC 657/2022 da Anvisa não incide), a postura é adotada desde o dia 1 como seguro gratuito para uma eventual publicação futura.

**Quatro princípios centrais** (invioláveis em qualquer tela ou texto):

1. **Uma ação por vez** — a interface de execução nunca exibe a lista completa.
2. **Metas mínimas** — 3 minutos contam; a meta não infla com bom desempenho (proteção contra o efeito catraca).
3. **Retomada sem culpa** — falhar não existe como conceito; existe retomar.
4. **Preparação antecipada do ambiente** — a noite anterior fabrica a manhã seguinte.

**Anti-escopo** (o que o app deliberadamente NÃO é): não mede produtividade; não tem ranking nem comparação entre pessoas; não usa streaks punitivos como medida principal; não exibe "dias em vermelho"; não faz afirmações terapêuticas; não recomenda doses, horários ou mudanças de medicação; não coleta dados fora do aparelho.

---

## 2. Usuário, problema e princípios de design

**Perfil.** Adulto com TDAH, medicado, com as quatro fricções clássicas de função executiva: (a) acordar e cumprir a rotina da manhã; (b) iniciar tarefas (paralisia pré-início); (c) noção de tempo — transições e hiperfoco; (d) esquecimentos — remédio, itens, compromissos.

**Tese do produto.** As quatro fricções não são quatro features: são **um motor** (rotina = sequência de micropassos, um por tela, com tempo visível) acessado por **três portas** (noite, manhã, resgate). A manhã contém as quatro fricções em miniatura.

**Princípios de design derivados:**

| Princípio | Racional | Implicação concreta |
|---|---|---|
| Intrusivo do bem | O celular é a ferramenta e o maior distrator; app passivo perde da rolagem infinita | Alarme em tela cheia, notificações acionáveis, widget na home (v1.1) |
| Zero vergonha | TDAH + culpa = app desinstalado | Sem streaks punitivos; contagem de retomadas; "falhou ontem" não existe |
| Verbos físicos concretos | Ação abstrata trava; ação física destrava | "Abrir a cortina", nunca "Organizar a manhã" |
| Anti tudo-ou-nada | "Estraguei a manhã, logo o dia acabou" é mais destrutivo que o atraso em si | Modo Resgatar o dia sempre a um toque |
| Efeito catraca protegido | Desempenho excepcional não pode virar obrigação futura | Meta mínima permanece mínima; progressão só com consentimento explícito |
| Efeito novidade gerenciado | Cérebro TDAH roda a novidade, e novidade expira (~3ª semana) | Roadmap em fases = injeção programada de novidade a cada release (~3–4 semanas) |
| Medição sem pedágio | O instrumento não pode alterar o fenômeno que mede nem custar toques extras | Modelo híbrido de toques (seção 8.3); registro automático, nunca formulário |

---

## 3. Jornada do usuário (dia típico)

**21h00 — Preparar o amanhã.** Notificação acionável: *"Vamos preparar o amanhã? Primeira ação: separar a roupa."* Sequência sugerida (uma por tela): separar a roupa → colocar o tênis perto da esteira → deixar a garrafa de água pronta → ver o primeiro compromisso de amanhã → escolher a primeira tarefa importante do trabalho. Último card (v2): contexto opcional do dia (sono, energia, estresse, medicação) — uma tela, no máximo 4 toques.

**Manhã.** Alarme dispara em tela cheia → usuário leva o celular até o espelho do banheiro → **encosta na tag NFC**: o som cala e a tela já mostra *"Agora: escovar os dentes · ~2 minutos"*. Sequência: escovar os dentes (âncora) → beber água → abrir a cortina / contato com a luz do dia → banho rápido → vestir a roupa separada → 3 minutos de movimento (passo com timer) → ver **somente** o primeiro compromisso → checklist de saída (chaves, carteira, crachá). Celebração curta ao final.

**Dia que desandou.** Botão **Resgatar o dia** (sempre visível na tela Hoje): *"A manhã saiu do planejado. Vamos reiniciar com uma ação de 2 minutos?"* → escovar os dentes → depois, **uma escolha única**: banho, trocar de roupa ou beber água. Nunca exibe a pilha de tarefas atrasadas.

**Domingo.** Revisão semanal: um resumo em linguagem neutra + **uma única sugestão de ajuste** + três botões (Aplicar sugestão · Manter como está · Escolher outro ajuste).

---

## 4. Os três modos do motor de rotinas

O motor é único: sequência ordenada de micropassos, execução um-por-tela, log de eventos automático. Os modos diferem apenas no gatilho, no conteúdo e no tom.

### 4.1 Preparar o amanhã (noite)

- Gatilho: notificação no horário configurado (padrão 21h; precisão relaxada, ±10 min aceitável).
- Botões da notificação (máx. 3 no Android): **Começar** · **+10 min** · **Versão mínima**. Dispensar (deslizar) = "hoje não", sem registro de culpa.
- Versão mínima da rotina noturna: apenas separar a roupa + ver o primeiro compromisso.

### 4.2 Começar a manhã

- Gatilho primário: alarme próprio (seção 5). Gatilho alternativo: leitura da tag NFC a qualquer momento (dias sem alarme, fins de semana) — a tag abre o app direto no modo manhã, mesmo com o app fechado.
- Regra de exibição: **ação atual + prévia discreta do próximo passo**. Indicador "3 de 7" pequeno, sem lista.
- Ações disponíveis por passo: **Concluir** (primário, botão grande) · Versão mínima · Adiar · Pular. Pular está sempre disponível e nunca gera mensagem negativa.
- Passo com timer (movimento): botão **Iniciar** dispara barra visual que esvazia; aos 3 min: *"Você concluiu a meta de hoje. Encerrar ou continuar por mais 3 minutos?"* Continuações são registradas mas a meta permanece 3 min.
- Encerramento: tela de celebração curta (dopamina imediata) + horário de conclusão.

### 4.3 Resgatar o dia

- Entrada: botão destacado na tela Hoje; também oferecido proativamente se a rotina da manhã não iniciou até o fim da janela configurada (notificação gentil, uma única vez).
- Fluxo: 1 pergunta → 1 ação de 2 minutos (escovar os dentes) → 1 escolha única entre três opções → encerramento com *"Você retomou o dia."*
- Toda conclusão via resgate gera estado **Retomada** no histórico — contabilizada como sucesso, não como falha parcial.

---

## 5. Mecânica de alarme e NFC

**Decisão registrada:** o despertador próprio permanece no v1 (ADR-02, seção 14). Consequência: o "checklist de confiança" é parte da feature, não luxo.

### 5.1 Cadeia do alarme

1. Agendamento com `AlarmManager.setAlarmClock()` — isento de Doze, exibe ícone de alarme no status bar, semanticamente correto para despertador.
2. Disparo → `BroadcastReceiver` → notificação com **full-screen intent** → `AlarmActivity` (`setShowWhenLocked(true)`, `setTurnScreenOn(true)`).
3. Som contínuo com atributos `USAGE_ALARM` (fura modo silencioso e DND-com-alarmes-permitidos). Reprodução na própria Activity em primeiro plano; serviço em primeiro plano (`foregroundServiceType="systemExempted"`, coberto pela permissão de alarme exato) como rede de segurança — decidir na implementação com teste no aparelho físico.
4. Desligamento: leitura NFC via `enableReaderMode` na AlarmActivity. O som cala **e** a rotina da manhã abre imediatamente — sem janela para o feed sequestrar a atenção.

### 5.2 Tag NFC

- Hardware: NTAG213 (custo de poucos reais, Mercado Livre), colada no espelho do banheiro.
- Gravação: registro NDEF com URI custom (ex.: `mateina://tag/espelho`), feita pelo próprio app na tela de configuração ("Gravar tag").
- Dupla função: (a) desligar o alarme; (b) iniciar a rotina da manhã com o app fechado, via intent filter NDEF — dias sem alarme continuam tendo gatilho físico.
- **Rota de fuga (inegociável):** segurar botão por 15 segundos silencia o alarme em qualquer circunstância (tag perdida, NFC falhou). Evento registrado sem qualquer mensagem de julgamento.
- Alternativa QR (v1.1, configurável): CameraX + ML Kit, para aparelhos sem NFC ou preferência do usuário.

### 5.3 Regras do despertador

- **Sem soneca.** A mecânica da tag resolve o problema que a soneca fingia resolver. A rota de fuga não é soneca: silencia de vez.
- Horários independentes para dias de semana e fim de semana; dias individuais configuráveis.
- Re-registro dos alarmes em `BOOT_COMPLETED` e `MY_PACKAGE_REPLACED` (reinicialização e atualização do app).

### 5.4 Checklist de confiança (onboarding obrigatório)

Confiança no alarme é requisito existencial: uma falha com atraso real mata o app no mesmo dia. O primeiro uso conduz:

1. Permissão de notificações (Android 13+).
2. Permissão de alarme exato: declarar `USE_EXACT_ALARM` (justificável — o app É um despertador, Android 13+); fallback `SCHEDULE_EXACT_ALARM` com intent de configurações no Android 12/12L.
3. Full-screen intent: no Android 14+, verificar `canUseFullScreenIntent()`; se negado (sideload), direcionar para `Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT`.
4. Isenção de otimização de bateria (`ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`) + orientações específicas do fabricante (referência: dontkillmyapp.com).
5. Botão **"Testar alarme agora"** — dispara o fluxo completo em 10 segundos, incluindo leitura da tag.
6. Recomendação exibida ao usuário: manter o despertador antigo em paralelo na primeira semana, como redundância, até o app ganhar confiança.

---

## 6. Sistema de notificações

**Canais** (controle individual de som, vibração e importância pelo usuário):

| Canal | Conteúdo | Padrão |
|---|---|---|
| Alarme | Despertador (full-screen) | Máxima importância, som de alarme |
| Rotina da manhã | Oferta de resgate, retomadas | Alta, discreta |
| Preparar o amanhã | Lembrete das 21h | Alta |
| Medicamentos (v1.1) | Lembrete de horário prescrito | Alta, conteúdo privado na tela bloqueada |
| Compromissos | Primeiro compromisso do dia (v3, com integração de calendário) | Média |

**Regras de qualidade:** toda notificação é relevante ao momento, acionável (máx. 3 botões) e auto-cancelada quando desatualizada (ex.: lembrete das 21h some se a rotina já começou). Notificações nunca empilham cobrança ("restam 6 tarefas" é proibido).

**Privacidade na tela bloqueada:** canal de medicamentos usa `VISIBILITY_PRIVATE` com versão pública genérica: *"Você tem um lembrete de saúde."*

---

## 7. Linguagem e microcopy

Regra de ouro: cada tarefa começa com **verbo físico e concreto**. A interface descreve, nunca julga.

| Evitar | Preferir |
|---|---|
| Você falhou novamente. | Hoje foi diferente do planejado. |
| Você perdeu sua sequência. | Você realizou sua rotina em 12 dos últimos 15 dias. |
| Restam seis tarefas atrasadas. | Qual é o menor passo possível agora? |
| Sua produtividade caiu 40%. | Você retomou o dia. |
| Apenas 3 minutos de exercício. | Três minutos contam. |
| Organizar a manhã. | Abrir a cortina. / Encher o copo de água. |

Métrica de destaque emocional: **"Você retomou N vezes neste mês"** — valoriza a capacidade de voltar, não a perfeição.

Limites clínicos da redação: contato com a luz da manhã é sugerido como sinalização do começo do dia, **sem** prescrever duração, intensidade ou equipamento; exercício é apoiado como constância, **sem** apresentar 3 minutos como dose terapêutica; medicação segue os limites da seção 12.3.

---

## 8. Modelo de dados — event sourcing

### 8.1 Princípio arquitetural

O app grava um **log imutável e append-only de eventos** e *deriva* todos os agregados, indicadores e gráficos por consulta. Nada de gravar "4 de 5 ações" — isso é resultado de query, não dado.

Consequências:

- **Capturamos tudo desde o dia 1; exibimos progressivamente.** As "três versões de analytics" (seção 13) são fases de *exibição*, não de coleta. Quando o funil chegar na v2, ele nasce com meses de histórico retroativo.
- Escrita trivial e à prova de bugs (um `INSERT` por interação).
- O histórico é uma trilha de auditoria imutável do próprio comportamento.

### 8.2 Esquema Room (4 tabelas)

**`routine_template`** — modelos de rotina

| Coluna | Tipo | Notas |
|---|---|---|
| id | Long PK | |
| tipo | Enum | NOITE, MANHA |
| nome | String | |
| horarios | JSON | alarme/lembrete por dia da semana; janela de início (ex.: 06h45–07h30) |
| ativo | Boolean | |

**`step_template`** — modelos de micropasso

| Coluna | Tipo | Notas |
|---|---|---|
| id | Long PK | |
| routineId | FK | |
| ordem | Int | |
| titulo | String | verbo físico concreto |
| tipoPasso | Enum | SIMPLES, TIMER, CHECKLIST_SAIDA, CONTEXTO (v2) |
| duracaoEstimadaSeg | Int | exibida como "~2 minutos" |
| metaMinimaSeg | Int? | só TIMER (ex.: 180) |
| textoVersaoMinima | String? | ex.: "Só molhar o rosto" |

**`event_log`** — o coração do sistema (append-only)

| Coluna | Tipo | Notas |
|---|---|---|
| id | Long PK | |
| timestamp | Instant | fonte única de verdade temporal |
| tipoEvento | Enum | taxonomia abaixo |
| routineInstanceId | String? | UUID gerado a cada execução de rotina |
| routineTemplateId | Long? | |
| stepTemplateId | Long? | |
| payload | JSON? | modo, motivo, duração, escolha etc. |

**`daily_context`** (v2) — 1 linha por dia

| Coluna | Tipo | Notas |
|---|---|---|
| date | LocalDate PK | |
| sono / energia / estresse | Enum? | RUIM–MEDIA–BOA / BAIXA–MEDIA–ALTA |
| tipoDia | Enum? | TRABALHO, FOLGA |
| medicacao | Enum? | TOMEI, NAO_TOMEI, INCERTO — campo sensível (seção 12.3) |
| observacao | String? | curta |

### 8.3 Taxonomia de eventos

| Grupo | Eventos |
|---|---|
| Alarme | ALARM_SCHEDULED, ALARM_FIRED, ALARM_DISMISSED_NFC, ALARM_DISMISSED_ESCAPE |
| Rotina | ROUTINE_STARTED {modo: NORMAL, MINIMO, RESGATE; origem: ALARME, NFC, MANUAL, NOTIFICACAO}, ROUTINE_COMPLETED, ROUTINE_ABANDONED |
| Micropasso | STEP_PRESENTED, STEP_STARTED (somente passos TIMER), STEP_COMPLETED, STEP_MINIMAL, STEP_POSTPONED, STEP_SKIPPED, STEP_SUBSTITUTED, STEP_TIMER_EXTENDED |
| Resgate | RESCUE_OFFERED, RESCUE_ACCEPTED, RESCUE_DECLINED |
| Notificação | NOTIF_SHOWN, NOTIF_ACTION {COMECAR, ADIAR, MINIMA}, NOTIF_DISMISSED |
| Fricção (v1.1) | FRICTION_ASKED, FRICTION_ANSWERED {motivo}, ADJUSTMENT_SUGGESTED, ADJUSTMENT_CHOICE |
| Revisão | REVIEW_SHOWN, REVIEW_CHOICE {APLICAR, MANTER, OUTRO} |
| Medicação (v1.1) | MED_REMINDER_SHOWN, MED_MARKED {TOMEI, NAO_TOMEI, INCERTO} |

**Modelo híbrido de toques (ADR-06):** passos SIMPLES têm 1 toque — a latência é `apresentada → desfecho`, aproximação honesta e declarada como tal nos painéis. Passos TIMER têm botão Iniciar (o toque já é necessário para o cronômetro), permitindo latência real `apresentada → iniciada`. O instrumento não altera o fenômeno que mede nem cobra pedágio em toques.

### 8.4 Estados derivados da microtarefa

Os 7 estados do conceito mapeiam-se a eventos — são **derivados**, nunca gravados diretamente:

| Estado | Derivação |
|---|---|
| Concluída | STEP_COMPLETED (modo ≠ RESGATE) |
| Versão mínima | STEP_MINIMAL — **conta como meta cumprida** |
| Adiada | STEP_POSTPONED |
| Pulada conscientemente | STEP_SKIPPED |
| Não iniciada | STEP_PRESENTED sem evento de desfecho na instância |
| Substituída | STEP_SUBSTITUTED — conta como desfecho positivo |
| Retomada | STEP_COMPLETED/STEP_MINIMAL com modo = RESGATE — conta como sucesso |

### 8.5 Dicionário de indicadores (fórmulas testáveis)

Cada fórmula abaixo vira caso de teste unitário no Sprint 0 — o papel de trabalho do app.

| # | Indicador | Fórmula | Regras |
|---|---|---|---|
| 1 | Taxa de ativação | dias com ROUTINE_STARTED(MANHA) ÷ dias do período | período padrão 7d e 28d |
| 2 | Preparação noturna | dias com ROUTINE_STARTED(NOITE) ÷ dias do período | |
| 3 | Início na janela | dias com início dentro da janela configurada ÷ dias com início | janela definida pelo usuário |
| 4 | Latência de início | **mediana**(t desfecho do 1º passo − t STEP_PRESENTED do 1º passo) | mediana, nunca média; rótulo "tempo típico" |
| 5 | Taxa de retomada | dias com RESCUE_ACCEPTED e ≥1 desfecho positivo ÷ dias com RESCUE_OFFERED | |
| 6 | Meta mínima de movimento | dias com STEP_COMPLETED ou STEP_MINIMAL do passo TIMER ÷ dias do período | mínima = sucesso pleno; sem "apenas" |
| 7 | Funil da rotina | por etapa: dias com desfecho positivo na etapa ÷ **dias em que a rotina foi iniciada** | denominador fixo evita distorção por adiamentos a montante |
| 8 | Ponto de atrito | etapa com maior soma de STEP_POSTPONED + STEP_SKIPPED + não-iniciada no período | |
| 9 | Facilitador | comparação de taxa de ativação entre dias com/sem preparação noturna | exibir **n dos dois grupos**; redação "associação observada", jamais causalidade |
| 10 | Retomadas no mês | contagem de dias com desfecho positivo em modo RESGATE | métrica de destaque emocional |

**Limiares de exibição (constantes de produto):** nenhuma análise com < 7 dias de dados; padrões por dia da semana só com ≥ 4 semanas; todo insight exibe a base ("Baseado em 18 manhãs registradas"); com dados insuficientes: *"Ainda não há registros suficientes para identificar um padrão confiável."*

**Métricas proibidas:** índice geral 0–100, ranking, comparação entre pessoas, streak como medida principal, horas "produtivas", nota vermelha, mensagens de queda de desempenho, correlação simplista medicação×produtividade.

---

## 9. Mapa de telas

**Navegação:** bottom bar com 3 abas — **Hoje · Histórico · Ajustes**. Análises vivem como sub-aba de Histórico. Execução de rotina e alarme são telas imersivas sem navegação (uma decisão por tela). Revisão semanal é um diálogo de tela cheia disparado no domingo (e acessível por Histórico).

| # | Tela | Propósito | Elementos-chave |
|---|---|---|---|
| T1 | Onboarding / Checklist de confiança | Garantir alarme confiável no 1º uso | Passos da seção 5.4; gravação da tag; teste de alarme |
| T2 | Hoje | Estado do dia orientado à ação | Preparação de ontem (sim/não); rotina iniciada (hora); **próxima ação**; movimento; primeiro compromisso; botão destacado **Resgatar o dia**; mensagem curta neutra. Sem gráficos. |
| T3 | AlarmActivity | Acordar | Tela cheia sobre o bloqueio; hora; instrução "encoste no espelho"; leitura NFC ativa; rota de fuga (segurar 15 s) |
| T4 | Execução de passo | O coração do app | Título com verbo; "~X minutos"; botão grande **Concluir**; secundários Mínima · Adiar · Pular; prévia discreta do próximo; indicador "3 de 7" pequeno |
| T5 | Passo com timer | Meta mínima de movimento | Botão Iniciar; barra que esvazia; ao fim: Encerrar ou +3 min |
| T6 | Checklist de saída | Anti-esquecimento | Itens configuráveis (chaves, carteira, crachá, remédio); toque único por item |
| T7 | Celebração | Dopamina imediata | Mensagem curta; horário de conclusão; nada de nota ou percentual |
| T8 | Resgatar o dia | Anti tudo-ou-nada | Pergunta única; ação de 2 min; depois escolha única entre 3 |
| T9 | Preparar o amanhã | Rotina noturna | Mesmo motor de T4; versão mínima disponível; card de contexto (v2) como último passo opcional |
| T10 | Editor de rotinas | Configuração única e rara | Lista reordenável; título (verbo), duração, versão mínima, tipo; horários e janela; sem assistente complexo |
| T11 | Histórico — Calendário | Diário visual 28 dias | Símbolos por dia (iniciada, preparação, meta mínima, resgate, descanso planejado); toque abre detalhe do dia |
| T12 | Histórico — Análises | Painel v1 | Cards dos indicadores 1–2, 5–6, 8, 10 + linha de regularidade semanal; v2 adiciona funil, heatmap, comparação noite×manhã |
| T13 | Revisão semanal | Um ajuste por semana | Resumo neutro; **1 sugestão**; botões Aplicar · Manter · Outro |
| T14 | Ajustes | Configuração | Alarmes e janelas; canais de notificação; tag NFC; biometria; exportar/excluir dados; sobre |

**Widget de home (v1.1, Glance):** próxima ação do dia + toque abre execução.

---

## 10. Arquitetura técnica Android

### 10.1 Stack

| Camada | Escolha | Nota |
|---|---|---|
| Linguagem / UI | Kotlin + Jetpack Compose (Material 3) | Declarativo; instinto de JS transfere bem |
| Persistência | Room (SQLite) + DataStore (preferências) | event_log com índice em (timestamp, tipoEvento) |
| Agendamento | AlarmManager (alarme: `setAlarmClock`; lembrete 21h: `setWindow` ±10 min) + WorkManager (revisão semanal, manutenção) | |
| Alarme/UI de bloqueio | Full-screen intent + `setShowWhenLocked` / `setTurnScreenOn` + som `USAGE_ALARM` | |
| NFC | `enableReaderMode` (AlarmActivity) + intent filter NDEF (abertura com app fechado) | |
| Gráficos | Vico (Compose) — v1 usa cards numéricos + 1 gráfico de linha | |
| DI | Hilt | |
| Testes | JUnit para o dicionário de indicadores (seção 8.5); teste manual do alarme via checklist | |
| Min SDK | 26 (Android 8.0) · Target SDK 35 | cobre recursos de tela bloqueada modernos |

### 10.2 Estrutura de pacotes (módulo único)

```
br.com.mateina/
  alarm/      # AlarmManager, receivers (alarme, boot, update), AlarmActivity, som
  nfc/        # gravação e leitura de tags, dispatch NDEF
  routine/    # motor de execução, modos, resgate
  data/       # Room, entidades, EventLogger (escritor único do log)
  analytics/  # queries derivadas, dicionário de indicadores, limiares
  notif/      # canais, builders, ações
  ui/         # telas Compose (T1–T14), tema, navegação
  di/         # Hilt
```

Regra: **EventLogger é o único escritor** do event_log; ViewModels nunca inserem eventos diretamente.

### 10.3 Permissões

`POST_NOTIFICATIONS` · `USE_EXACT_ALARM` (Android 13+) + `SCHEDULE_EXACT_ALARM` (fallback 12/12L) · `USE_FULL_SCREEN_INTENT` · `NFC` · `RECEIVE_BOOT_COMPLETED` · `FOREGROUND_SERVICE` (+ `SYSTEM_EXEMPTED` se serviço de toque for adotado) · `VIBRATE`. **Sem permissão `INTERNET` na v1** (seção 12.1).

### 10.4 Riscos técnicos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Fabricante mata o app (Xiaomi/Samsung) | Alarme não toca — falha existencial | `setAlarmClock` + isenção de bateria + orientação por fabricante no onboarding + teste de alarme + paralelo com despertador antigo na 1ª semana |
| "NFC seguro" (Samsung) bloqueia leitura com tela bloqueada | Tag não cala o alarme | AlarmActivity sobre o keyguard deve permitir leitura; **testar no Sprint 2 em aparelho físico**; plano B: orientar desbloqueio por biometria antes do toque; rota de fuga sempre presente |
| Full-screen intent negada no Android 14+ (sideload) | Alarme vira notificação comum | Checagem `canUseFullScreenIntent()` no onboarding + atalho para a permissão |
| Doze/idle atrasa lembrete das 21h | Preparação noturna perde o gatilho | `setWindow` com folga aceitável; lembrete não é crítico ao segundo |
| Compilação lenta no desktop de desenvolvimento | Frustração no ciclo | Testar em aparelho físico via USB; nunca emulador; builds incrementais |

---

## 11. Fricção adaptativa e revisão semanal (v1.1)

**Detecção de atrito.** Quando uma mesma tarefa acumula N desfechos negativos (padrão: 3 entre adiada/pulada/não iniciada em 7 dias), o app pergunta **uma vez**, fora do momento de execução: *"O que dificultou esta tarefa?"* Opções: Estava cansado · Não encontrei o que precisava · A tarefa parecia longa · O horário não funcionou · Esqueci · Outro motivo.

**Resposta prática, nunca moral.** A sugestão sempre altera o *ambiente ou a estrutura*, jamais pede disciplina: colocar o tênis ao lado da cama; reduzir o exercício de 10 para 3 minutos; mover o lembrete para depois da escovação; preparar a roupa na noite anterior; criar versão mínima do passo; mudar a posição do passo na sequência.

**Revisão semanal (domingo).** Resumo neutro (iniciou X de 7; retomou Y vezes; facilitador observado; ponto de atrito) + **uma única sugestão** + três botões (Aplicar · Manter · Outro). Uma mudança por semana — nunca uma lista de recomendações. Aplicar a sugestão edita o template automaticamente e registra ADJUSTMENT_CHOICE.

**Progressão consentida.** Após 2 semanas consistentes na meta mínima: *"A meta de 3 minutos está funcionando. Deseja mantê-la ou testar 5 minutos?"* A decisão é sempre do usuário; recusar não gera nova pergunta por 4 semanas.

---

## 12. Privacidade, segurança e dados sensíveis

### 12.1 Local-first radical

- **A v1 não declara a permissão `INTERNET`.** Privacidade auditável e verificável no próprio manifest: é tecnicamente impossível o app enviar dados para fora.
- Sem conta, sem cadastro, sem SDK de terceiros, sem analytics remoto, sem publicidade.
- Backup: exportação manual (JSON completo do event_log + CSV dos indicadores) para o armazenamento do aparelho; backup criptografado opcional na v1.1. `allowBackup` do Android avaliado com cautela (dados sensíveis).

### 12.2 Controles do usuário

Biometria opcional (BiometricPrompt) para abrir Histórico/Análises ou o app inteiro · exclusão de um dia específico · exclusão total · escolha de quais campos entram em relatórios exportados · relatório para profissional de saúde com tendências gerais, **sem** observações privadas.

### 12.3 Medicamentos — limites invioláveis

O lembrete (v1.1) registra somente o horário prescrito pelo profissional; aceita marcar Tomei · Não tomei · Não tenho certeza; **nunca** recomenda dose extra, **nunca** compensa dose esquecida, **nunca** sugere alteração de horário ou interrupção; diante de dúvida, orienta consultar a prescrição ou o profissional. Associações pessoais (v2+) são exibidas como "associação observada em seus registros", jamais causalidade. Registros de medicação são marcados sensíveis: notificação privada na tela bloqueada e exclusão do export por padrão.

### 12.4 LGPD por design

Mesmo sem tratamento por terceiros no uso pessoal: finalidade definida, coleta mínima, transparência (tela "que dados existem e por quê"), salvaguardas reforçadas para dados de saúde. Postura pronta para eventual publicação.

---

## 13. Roadmap por fases

Cadência-alvo: uma release a cada 3–4 semanas — cada uma é também **injeção programada de novidade** (resposta ao problema da 3ª semana).

### v1 — MVP "Manhã no trilho"

Motor de rotinas (noite + manhã + resgate) · alarme + NFC + rota de fuga + checklist de confiança · modelo híbrido de toques · notificações acionáveis (21h) · editor simples · rotinas seed (5 ações noturnas, 8 matinais conforme seção 3) · passo timer com meta mínima · checklist de saída · celebração · **event_log completo desde o dia 1** · Hoje (T2) · Histórico: calendário 28d, taxa de início, preparação noturna, meta mínima, retomadas, etapas mais adiadas · Revisão semanal com 1 sugestão.

### v1.1

Fricção adaptativa (seção 11) · lembrete seguro de medicamento (12.3) · widget de home (Glance) · QR alternativo ao NFC · backup criptografado · refinamento do relatório semanal.

### v2 — Analytics de exibição

Comparação preparação noturna × manhã (com n dos grupos) · mapa de calor dia/horário · funil da rotina · card de contexto diário (sono, energia, estresse, medicação — último passo opcional da noite) · identificação de facilitadores e barreiras · exportação de relatório (CSV/PDF).

### v3 — Inteligência e integrações

Detecção automática de padrões (com limiares e n) · recomendações adaptativas · integração somente-leitura com calendário (primeiro compromisso real) e relógio/wearable · **assistente de IA para quebrar tarefas** (aqui entra o botão "travei" com micropassos — pode usar modelo local, filosofia ButIA) · experimentos pessoais controlados (ex.: testar dois horários de lembrete) · relatórios personalizados para acompanhamento profissional.

### Backlog pós-v3 (do conceito original)

Transições e hiperfoco no expediente · rotina noturna estendida (higiene do sono) · body doubling / acompanhamento por outra pessoa · perfis múltiplos (família).

---

## 14. Decisões registradas (ADR)

| # | Decisão | Racional | Data |
|---|---|---|---|
| ADR-01 | Android nativo: Kotlin + Jetpack Compose | Alarme confiável exige APIs nativas sem camada de plugin; Compose declarativo aproveita instinto de JS; app é Android-only | jul/2026 |
| ADR-02 | Despertador próprio permanece na v1, com NFC | Decisão do product owner; checklist de confiança vira parte da feature | jul/2026 |
| ADR-03 | Tag NFC com dupla função: calar alarme + iniciar rotina (app fechado) | Um gesto físico, três funções; elimina a janela de distração pós-alarme | jul/2026 |
| ADR-04 | Sem soneca; rota de fuga de 15 s sempre disponível | Fail-safe primeiro, fricção depois; soneca contradiz a mecânica da tag | jul/2026 |
| ADR-05 | Event sourcing: log imutável, agregados derivados | Capturar tudo desde o dia 1, exibir progressivamente; trilha de auditoria do comportamento | jul/2026 |
| ADR-06 | Modelo híbrido de toques (timer com Iniciar; demais com 1 toque) | Medição sem pedágio; latência aproximada declarada como tal | jul/2026 |
| ADR-07 | Sem streaks punitivos; métrica emocional = retomadas | Zero vergonha; medir a volta, não a perfeição | jul/2026 |
| ADR-08 | Meta mínima não infla; progressão só consentida | Proteção contra efeito catraca | jul/2026 |
| ADR-09 | v1 sem permissão INTERNET; local-first radical | Privacidade auditável no manifest; dados de saúde sensíveis | jul/2026 |
| ADR-10 | Posicionamento não-médico (postura Anvisa/LGPD desde o dia 1) | Uso pessoal hoje, seguro gratuito para publicação futura | jul/2026 |
| ADR-11 | Mediana para latência; associação ≠ causalidade; limiares mínimos de exibição | Rigor estatístico proporcional a dados pessoais | jul/2026 |
| ADR-12 | Funil com denominador fixo: rotina iniciada | Evita distorção por adiamentos a montante | jul/2026 |

---

## 15. Plano de construção (Claude Code)

| Sprint | Entrega | Critério de aceite |
|---|---|---|
| 0 | Projeto, tema, navegação, Room + event_log, EventLogger, **testes unitários do dicionário de indicadores (8.5)** | Todas as fórmulas passam nos testes com dados sintéticos |
| 1 | Motor de execução (T4/T5/T7), editor (T10), rotinas seed, modos noite/manhã manuais | Rotina completa executável de ponta a ponta, eventos gravados |
| 2 | Alarme + NFC + AlarmActivity + checklist de confiança (T1/T3) — **testar cedo em aparelho físico, incluindo tela bloqueada e "NFC seguro"** | Teste de alarme dispara em tela bloqueada; tag cala e abre rotina; rota de fuga funciona |
| 3 | Notificações (21h, canais), Resgatar o dia (T8), tela Hoje (T2) | Notificação acionável com 3 botões; resgate gera eventos RESGATE |
| 4 | Histórico (T11/T12), Revisão semanal (T13), Ajustes (T14), export/exclusão | Indicadores v1 corretos contra o log; revisão aplica ajuste no template |

**Ambiente:** Android Studio no desktop; build e depuração **sempre em aparelho físico via USB** (emulador vetado pela lentidão da máquina); APK release assinado manualmente para instalação.

**Definition of Done da v1:** uma semana inteira dormindo com o app como despertador, em paralelo ao antigo, **sem nenhuma falha de alarme** — e pelo menos um uso real do modo Resgatar o dia registrado no histórico.

---

## 16. Nome (decisão pendente)

| Candidato | Racional |
|---|---|
| **Mateína** | A molécula que inicia a manhã do gaúcho; "iniciar" é a métrica central do produto; curto e sonoro |
| Alvorada | O amanhecer; referência regional; tema matinal literal |
| Minuano | O vento que limpa o céu; ideia de recomeço |

---

## 17. Conceito-síntese

O painel do app não pergunta *"quanto você produziu?"*. Ele responde:

> **O que ajudou você a começar, o que dificultou e qual pequeno ajuste pode tornar amanhã mais fácil?**
