# PRD — Plataforma Interna Operacional SuperDados

## 1. Visão Geral

### 1.1 Nome do produto
**SuperDados — Plataforma Interna de Pesquisa Eleitoral Online**

### 1.2 Tipo de produto
Plataforma interna operacional para planejamento, coleta, validação, ponderação, análise e entrega de pesquisas eleitorais online.

### 1.3 Objetivo do produto
Construir uma plataforma interna que permita à equipe SuperDados executar pesquisas eleitorais digitais com controle metodológico, rastreabilidade estatística, baixo custo operacional e geração de relatórios técnicos confiáveis.

### 1.4 Produto nesta fase
Nesta fase, o produto **não será um SaaS aberto ao cliente final**. Será uma operação assistida por tecnologia, em que a equipe SuperDados configura, monitora, valida e entrega as pesquisas.

### 1.5 Base metodológica
A plataforma será baseada no método de Recrutamento Digital por Referência, com coleta online, controle de qualidade, ponderação estatística por múltiplas variáveis e calibração com dados oficiais.

---

## 2. Problema

Pesquisas eleitorais tradicionais possuem alto custo operacional, dependem de equipes de campo e têm baixa velocidade de execução. Por outro lado, pesquisas digitais são mais baratas e rápidas, mas enfrentam problemas de viés de amostragem, duplicidade, baixa qualidade de respostas e questionamentos sobre validade metodológica.

A SuperDados precisa criar um produto operacional que resolva esse trade-off: **usar a eficiência da coleta digital sem perder rigor metodológico**.

---

## 3. Objetivos do MVP

### 3.1 Objetivo principal
Permitir que a equipe SuperDados execute uma pesquisa eleitoral municipal piloto de ponta a ponta, desde a configuração até a entrega do relatório final.

### 3.2 Objetivos específicos
- Criar pesquisas internas com escopo, município, amostra e questionário definidos.
- Coletar respostas online com controle mínimo de duplicidade.
- Armazenar respostas em banco estruturado.
- Validar e classificar respostas como válidas, suspeitas ou descartadas.
- Aplicar ponderação estatística por variáveis de controle.
- Comparar amostra bruta versus amostra ponderada.
- Gerar dashboard interno de resultados.
- Exportar relatório técnico em PDF.
- Manter trilha de auditoria da pesquisa.

---

## 4. Não Objetivos do MVP

O MVP não terá, nesta primeira fase:

- Plataforma self-service para clientes externos.
- Pagamento online.
- Cadastro aberto de clientes.
- Painel público de divulgação.
- Aplicativo mobile próprio.
- Painel próprio de respondentes.
- Automação completa de compra de mídia.
- Modelagem preditiva avançada.
- Integração automática com sistemas do TSE.

---

## 5. Personas Internas

### 5.1 Administrador SuperDados
Responsável por configurar o sistema, criar usuários, gerenciar permissões e acompanhar todas as pesquisas.

### 5.2 Coordenador de Pesquisa
Responsável por criar a pesquisa, definir questionário, acompanhar coleta e aprovar resultados finais.

### 5.3 Analista de Dados
Responsável por limpar a base, validar respostas, rodar ponderação, revisar pesos e interpretar resultados.

### 5.4 Gestor Comercial / Atendimento
Responsável por acompanhar o status da entrega e acessar relatórios para apresentar ao cliente.

### 5.5 Cliente externo — somente visualização futura
No MVP, o cliente não terá acesso direto obrigatório. Em uma fase posterior, poderá acessar um portal com status, dashboard e relatórios.

---

## 6. Fluxo Operacional do Produto

1. Equipe cria uma nova pesquisa.
2. Define município, objetivo, público-alvo, amostra e datas de coleta.
3. Seleciona ou monta questionário-base.
4. Gera link de coleta com identificador único da pesquisa.
5. Roda anúncios externos em Meta Ads, WhatsApp ou outros canais.
6. Respondente acessa formulário e responde.
7. Sistema salva resposta bruta.
8. Sistema executa validações automáticas de qualidade.
9. Analista revisa respostas suspeitas.
10. Sistema aplica ponderação estatística.
11. Dashboard exibe resultado bruto e ponderado.
12. Equipe revisa notas metodológicas.
13. Sistema gera relatório final.
14. Pesquisa é marcada como concluída.

---

## 7. Módulos do Produto

## 7.1 Módulo de Autenticação e Usuários

### Descrição
Permite acesso seguro da equipe interna à plataforma.

### Funcionalidades
- Login com e-mail e senha.
- Recuperação de senha.
- Perfis de permissão.
- Registro de último acesso.

### Perfis iniciais
- Admin
- Coordenador
- Analista
- Visualizador

### Regras
- Apenas Admin pode criar usuários.
- Apenas Admin e Coordenador podem criar pesquisas.
- Apenas Analista e Admin podem aprovar ponderação.
- Visualizador apenas consulta dashboards e relatórios.

---

## 7.2 Módulo de Cadastro de Pesquisa

### Descrição
Permite criar e configurar uma pesquisa eleitoral.

### Campos principais
- Nome da pesquisa.
- Tipo da pesquisa: municipal, estadual, nacional ou tracking.
- Status: rascunho, em coleta, em validação, ponderada, concluída, arquivada.
- Município/UF.
- Cargo pesquisado.
- Ano eleitoral.
- Data de início da coleta.
- Data de fim da coleta.
- Tamanho amostral desejado.
- Margem de erro estimada.
- Nível de confiança.
- Contratante.
- Uso: interno ou divulgação pública.
- Responsável técnico.
- Observações metodológicas.

### Regras
- Toda pesquisa deve ter município/UF definido.
- Toda pesquisa deve ter tamanho amostral alvo.
- Pesquisa pública deve exigir campos adicionais de compliance.
- Pesquisa não pode ser concluída sem relatório metodológico.

---

## 7.3 Módulo de Questionário

### Descrição
Permite criar, editar e versionar questionários.

### Funcionalidades
- Criar questionário a partir de modelo padrão.
- Adicionar perguntas de intenção espontânea.
- Adicionar perguntas de intenção estimulada.
- Adicionar perguntas de rejeição.
- Adicionar perguntas socioeconômicas.
- Adicionar perguntas de qualidade.
- Versionar questionário.
- Bloquear edição após início da coleta.

### Perguntas obrigatórias do questionário base
- Município de votação.
- Idade ou faixa etária.
- Sexo/gênero conforme categorias metodológicas definidas.
- Escolaridade.
- Renda ou classe, se usada na ponderação.
- Intenção de voto espontânea.
- Intenção de voto estimulada.
- Rejeição.
- Pergunta de atenção/qualidade.

### Regras
- O questionário não deve ultrapassar 8 minutos estimados.
- Perguntas usadas na ponderação não podem ser removidas.
- Alterações após início da coleta devem gerar nova versão.

---

## 7.4 Módulo de Coleta

### Descrição
Responsável por gerar links, receber respostas e armazenar dados brutos.

### Funcionalidades
- Gerar link único por pesquisa.
- Registrar origem da resposta via UTM.
- Salvar timestamp de início e fim.
- Registrar duração total da resposta.
- Registrar dispositivo/navegador quando permitido.
- Registrar IP ou hash de IP quando permitido pela política de privacidade.
- Bloquear duplicidade básica.
- Exibir tela de encerramento quando a coleta for finalizada.

### Canais previstos
- Meta Ads.
- WhatsApp.
- Link direto.
- Portais parceiros.
- Outros canais digitais.

### Regras
- Respostas devem ser salvas como dados brutos antes de qualquer tratamento.
- Nenhuma resposta bruta deve ser sobrescrita.
- Ajustes e exclusões devem ocorrer em tabelas derivadas ou por status.

---

## 7.5 Módulo de Qualidade da Amostra

### Descrição
Classifica respostas para garantir qualidade mínima dos dados.

### Status de resposta
- Válida.
- Suspeita.
- Descartada.
- Em revisão.

### Critérios automáticos iniciais
- Tempo de resposta abaixo do mínimo aceitável.
- Questionário incompleto.
- Resposta duplicada provável.
- Município informado diferente do município-alvo.
- Falha em pergunta de atenção.
- Padrão inconsistente de respostas.
- Respostas abertas inválidas ou claramente artificiais.

### Funcionalidades
- Lista de respostas suspeitas.
- Filtros por motivo de suspeita.
- Aprovação manual.
- Descarte manual com justificativa.
- Log de decisão.

### Regras
- Toda resposta descartada deve ter motivo registrado.
- O relatório deve informar total bruto, total descartado e total válido.
- A ponderação deve usar apenas respostas válidas.

---

## 7.6 Módulo de Base de Calibração

### Descrição
Armazena os parâmetros populacionais usados para ponderação.

### Fontes previstas
- IBGE.
- TSE.
- Outras fontes oficiais, quando justificadas.

### Variáveis mínimas
- Sexo.
- Faixa etária.
- Escolaridade.
- Região ou zona geográfica.

### Funcionalidades
- Importar base por município/UF.
- Visualizar distribuição populacional.
- Validar soma dos targets.
- Versionar base de calibração.
- Associar base a uma pesquisa.

### Regras
- Toda ponderação deve estar vinculada a uma versão da base de calibração.
- Alterações em targets devem gerar nova versão.
- O sistema deve permitir reprocessar ponderação com nova base.

---

## 7.7 Módulo de Ponderação Estatística

### Descrição
Aplica pesos estatísticos para ajustar a amostra coletada ao perfil do eleitorado.

### Método inicial
Raking / Iterative Proportional Fitting.

### Entradas
- Respostas válidas.
- Variáveis socioeconômicas da amostra.
- Targets populacionais da base de calibração.
- Configurações de limite de peso.

### Saídas
- Peso individual por respondente.
- Distribuição ponderada.
- Resultado bruto.
- Resultado ponderado.
- Diagnóstico de convergência.
- Alertas de excesso de peso.

### Configurações iniciais
- Variáveis usadas na ponderação.
- Número máximo de iterações.
- Tolerância de convergência.
- Peso mínimo.
- Peso máximo.
- Tratamento de células raras.

### Regras
- Ponderação deve ser reproduzível.
- Cada execução deve gerar um ID único.
- O sistema deve preservar parâmetros usados em cada rodada.
- O analista deve poder comparar múltiplas execuções.
- Apenas uma ponderação pode ser marcada como oficial.

---

## 7.8 Módulo de Resultados e Dashboard

### Descrição
Exibe resultados da pesquisa para análise interna.

### Visões obrigatórias
- Resultado geral bruto.
- Resultado geral ponderado.
- Intenção espontânea.
- Intenção estimulada.
- Rejeição.
- Cruzamentos por sexo.
- Cruzamentos por faixa etária.
- Cruzamentos por escolaridade.
- Cruzamentos por região.
- Composição da amostra bruta.
- Composição da amostra ponderada.
- Evolução diária da coleta.

### Funcionalidades
- Filtros por variável.
- Exportação CSV.
- Exportação XLSX.
- Exportação de gráficos.
- Comparação bruto versus ponderado.

### Regras
- Dashboard deve indicar claramente se está mostrando dado bruto ou ponderado.
- Resultados não oficiais devem ter marcação visual.
- Apenas pesquisas com ponderação oficial podem gerar relatório final.

---

## 7.9 Módulo de Relatório Técnico

### Descrição
Gera relatório final da pesquisa.

### Conteúdo obrigatório
- Nome da pesquisa.
- Localidade.
- Período de coleta.
- Tamanho da amostra bruta.
- Tamanho da amostra válida.
- Método de recrutamento.
- Método de ponderação.
- Variáveis de ponderação.
- Fontes de calibração.
- Margem de erro.
- Nível de confiança.
- Resultados principais.
- Tabelas de cruzamento.
- Observações metodológicas.

### Funcionalidades
- Gerar PDF.
- Gerar versão interna.
- Gerar versão para cliente.
- Incluir ou ocultar detalhes sensíveis.
- Registrar data de emissão.

### Regras
- Relatório deve ser gerado a partir de uma ponderação oficial.
- Relatório deve incluir nota metodológica.
- Relatório deve preservar histórico da versão emitida.

---

## 7.10 Módulo de Compliance Eleitoral

### Descrição
Organiza informações necessárias para pesquisas que possam ser divulgadas publicamente.

### Campos adicionais para pesquisa pública
- Contratante.
- Pagador.
- Valor contratado.
- Origem dos recursos.
- Responsável técnico.
- Estatístico responsável, se aplicável.
- Metodologia.
- Plano amostral.
- Questionário completo.
- Sistema interno de registro.
- Status de registro externo.
- Data prevista de divulgação.

### Status de compliance
- Não aplicável.
- Pendente.
- Em preparação.
- Registrada.
- Liberada para divulgação.
- Bloqueada.

### Regras
- Pesquisa marcada como pública não pode ser divulgada sem checklist concluído.
- O sistema deve diferenciar pesquisa interna de pesquisa pública.
- O relatório público deve conter nota metodológica adequada.

---

## 8. Modelo de Dados Inicial

### 8.1 Tabela: users
- id
- name
- email
- password_hash
- role
- created_at
- updated_at
- last_login_at

### 8.2 Tabela: surveys
- id
- title
- type
- status
- city_id
- state
- office
- election_year
- sample_target
- margin_error_estimated
- confidence_level
- collection_start
- collection_end
- client_name
- usage_type
- technical_owner
- created_by
- created_at
- updated_at

### 8.3 Tabela: questionnaires
- id
- survey_id
- version
- status
- estimated_minutes
- created_at
- locked_at

### 8.4 Tabela: questions
- id
- questionnaire_id
- question_text
- question_type
- variable_key
- required
- order_index
- options_json

### 8.5 Tabela: responses_raw
- id
- survey_id
- questionnaire_id
- respondent_token
- started_at
- submitted_at
- duration_seconds
- source_channel
- utm_source
- utm_campaign
- utm_content
- device_hash
- ip_hash
- raw_payload_json
- created_at

### 8.6 Tabela: responses_clean
- id
- response_raw_id
- survey_id
- status
- validation_flags_json
- discard_reason
- reviewed_by
- reviewed_at
- cleaned_payload_json
- created_at

### 8.7 Tabela: calibration_targets
- id
- geographic_level
- city_id
- state
- source_name
- source_year
- version
- target_json
- created_at

### 8.8 Tabela: weighting_runs
- id
- survey_id
- calibration_target_id
- method
- variables_json
- parameters_json
- status
- convergence_status
- diagnostics_json
- is_official
- created_by
- created_at

### 8.9 Tabela: respondent_weights
- id
- weighting_run_id
- response_clean_id
- weight
- created_at

### 8.10 Tabela: reports
- id
- survey_id
- weighting_run_id
- report_type
- file_url
- version
- emitted_at
- emitted_by

### 8.11 Tabela: audit_logs
- id
- user_id
- entity_type
- entity_id
- action
- before_json
- after_json
- created_at

---

## 9. Requisitos Funcionais

### RF01 — Criar pesquisa
Usuário autorizado deve poder criar uma nova pesquisa com município, objetivo, amostra e datas.

### RF02 — Criar questionário
Usuário autorizado deve poder montar questionário a partir de um modelo padrão.

### RF03 — Bloquear questionário
Sistema deve bloquear edição do questionário após início da coleta, salvo criação de nova versão.

### RF04 — Gerar link de coleta
Sistema deve gerar link único para cada pesquisa.

### RF05 — Registrar respostas brutas
Sistema deve salvar todas as respostas recebidas sem sobrescrever dados originais.

### RF06 — Validar qualidade da resposta
Sistema deve classificar respostas com base em critérios automáticos.

### RF07 — Revisar respostas suspeitas
Analista deve poder aprovar ou descartar respostas suspeitas com justificativa.

### RF08 — Importar targets populacionais
Sistema deve permitir importar base de calibração por município/UF.

### RF09 — Rodar ponderação
Analista deve poder executar ponderação com parâmetros configuráveis.

### RF10 — Comparar ponderações
Sistema deve permitir comparar resultados de diferentes execuções de ponderação.

### RF11 — Definir ponderação oficial
Analista ou Admin deve poder marcar uma ponderação como oficial.

### RF12 — Exibir dashboard
Sistema deve exibir resultado bruto, ponderado e cruzamentos.

### RF13 — Exportar dados
Sistema deve permitir exportar base limpa, base ponderada e resultados agregados.

### RF14 — Gerar relatório
Sistema deve gerar relatório técnico em PDF.

### RF15 — Registrar auditoria
Sistema deve manter log de ações relevantes.

---

## 10. Requisitos Não Funcionais

### Segurança
- Acesso autenticado.
- Controle de permissões.
- Hash de dados sensíveis quando possível.
- Logs de ações críticas.

### Privacidade
- Coleta mínima de dados pessoais.
- Consentimento do respondente.
- Política de privacidade clara.
- Separação entre dados identificáveis e respostas, se houver identificação.

### Rastreabilidade
- Toda ponderação deve ser reproduzível.
- Toda exclusão de resposta deve ter motivo.
- Toda alteração relevante deve gerar log.

### Performance
- MVP deve suportar ao menos 10 pesquisas simultâneas.
- Cada pesquisa deve suportar ao menos 10.000 respostas brutas.
- Dashboard deve carregar resultados agregados em até 5 segundos para bases municipais.

### Confiabilidade
- Backup diário do banco.
- Controle de versões de questionário e targets.
- Preservação dos dados brutos.

---

## 11. Métricas de Sucesso do MVP

### Produto
- Criar uma pesquisa em menos de 30 minutos.
- Gerar link de coleta automaticamente.
- Processar 400 respostas válidas em uma pesquisa piloto.
- Gerar dashboard com resultado bruto e ponderado.
- Gerar relatório técnico final.

### Metodologia
- Reduzir distorção da amostra após ponderação.
- Documentar todos os critérios de exclusão.
- Obter convergência da ponderação em variáveis mínimas.
- Comparar resultado bruto versus ponderado.

### Operação
- Executar uma pesquisa piloto do início ao fim sem manipulação manual excessiva.
- Reduzir tempo de análise em relação a planilhas manuais.
- Permitir revisão por outro analista com rastreabilidade.

---

## 12. Roadmap de Desenvolvimento

## Fase 1 — Fundação do MVP

### Entregáveis
- Banco de dados inicial.
- Login e permissões.
- Cadastro de pesquisa.
- Questionário padrão.
- Coleta de respostas.
- Armazenamento raw.

### Critério de conclusão
Uma pesquisa pode ser criada, publicada e receber respostas no banco.

---

## Fase 2 — Qualidade e Limpeza

### Entregáveis
- Classificação de respostas.
- Regras automáticas de suspeita.
- Tela de revisão manual.
- Exportação da base limpa.

### Critério de conclusão
Analista consegue transformar respostas brutas em base válida para ponderação.

---

## Fase 3 — Ponderação

### Entregáveis
- Importação de targets.
- Execução de raking.
- Geração de peso por respondente.
- Diagnósticos de convergência.
- Comparação bruto versus ponderado.

### Critério de conclusão
Sistema gera resultados ponderados reproduzíveis.

---

## Fase 4 — Dashboard e Relatório

### Entregáveis
- Dashboard interno.
- Cruzamentos básicos.
- Composição da amostra.
- Exportação CSV/XLSX.
- Relatório PDF.

### Critério de conclusão
Equipe consegue entregar relatório técnico ao cliente.

---

## Fase 5 — Piloto Operacional

### Entregáveis
- Pesquisa municipal real.
- 400 respostas válidas.
- Relatório final.
- Análise de aprendizados.
- Ajustes metodológicos.

### Critério de conclusão
SuperDados executa uma pesquisa completa usando a plataforma.

---

## 13. Stack Recomendada para MVP

### Opção enxuta
- Frontend/Admin: Retool ou Appsmith.
- Formulário: SurveyJS ou LimeSurvey.
- Banco: PostgreSQL.
- Backend estatístico: Python.
- Dashboard: Metabase ou Streamlit.
- Hospedagem: Railway, Render, Supabase ou VPS.

### Opção produto escalável
- Frontend: Next.js.
- Backend: FastAPI.
- Banco: PostgreSQL.
- Fila/Jobs: Celery ou RQ.
- Ponderação: Python/pandas.
- Dashboard: aplicação própria ou Metabase embutido.
- Infra: AWS, GCP ou Render.

### Recomendação inicial
Começar com **PostgreSQL + FastAPI + SurveyJS + Streamlit/Metabase**. Essa combinação permite velocidade sem sacrificar controle técnico.

---

## 14. Riscos Principais

### Risco metodológico
A amostra digital pode ser enviesada demais em certos municípios ou grupos sociais.

### Mitigação
Monitorar composição da amostra em tempo real, definir cotas mínimas operacionais e limitar pesos extremos.

---

### Risco jurídico
Pesquisa eleitoral pública pode exigir registro e documentação específica.

### Mitigação
Separar pesquisas internas de pesquisas públicas e implementar checklist de compliance.

---

### Risco operacional
Compra de mídia pode gerar respostas insuficientes ou muito concentradas em certos perfis.

### Mitigação
Acompanhar coleta por perfil e ajustar campanhas durante o campo.

---

### Risco de reputação
Resultado ruim ou mal explicado pode comprometer a credibilidade da marca.

### Mitigação
Começar com pilotos internos, documentar metodologia e evitar divulgação pública prematura.

---

## 15. Decisões Pendentes

- Escolher stack final do MVP.
- Definir município piloto.
- Definir questionário padrão.
- Definir variáveis finais de ponderação.
- Definir limite mínimo e máximo de peso.
- Definir política de descarte de respostas.
- Definir formato do relatório técnico.
- Definir se haverá estatístico responsável desde o piloto.
- Definir processo jurídico para pesquisas públicas.

---

## 16. Próximo Marco

O próximo marco do produto é construir o **protótipo funcional da operação interna**, composto por:

1. Cadastro de pesquisa.
2. Questionário padrão.
3. Coleta de respostas.
4. Banco raw.
5. Validação de qualidade.
6. Primeira versão do script de ponderação.
7. Dashboard simples.
8. Relatório técnico básico.

Quando esses oito elementos estiverem funcionando juntos, a SuperDados terá um MVP operacional real.

