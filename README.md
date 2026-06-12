# SuperDados - Controle de Convites e Anticontaminacao

MVP de backend para pesquisas eleitorais online usando FastAPI, SQLAlchemy, PostgreSQL e Alembic. O LimeSurvey fica como motor externo de formulario; este servico controla convites, valida abertura de token, importa respostas brutas e classifica risco de contaminacao da amostra.

## Rodar localmente no modo facil

Este modo usa SQLite em um arquivo local `superdados.db`. E o melhor caminho para testar a API pela primeira vez, sem Docker e sem PostgreSQL.

1. Crie o ambiente:

```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

2. Inicie a API:

```bash
uvicorn app.main:app --reload
```

A API cria as tabelas automaticamente quando roda em SQLite local.

Acesse:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Rodar localmente com migrations

Se quiser criar as tabelas manualmente via Alembic:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Por padrao, o Alembic usa `sqlite:///./superdados.db`.

## Rodar com PostgreSQL via Docker

1. Copie as variaveis:

```bash
copy .env.example .env
```

2. Suba o banco:

```bash
docker compose up -d postgres
```

3. Ajuste o `.env` para apontar para PostgreSQL, se ainda nao estiver assim:

```env
DATABASE_URL=postgresql+psycopg://superdados:superdados@localhost:5432/superdados
```

4. Rode as migrations:

```bash
alembic upgrade head
```

5. Inicie a API:

```bash
uvicorn app.main:app --reload
```

## Docker Compose completo

```bash
docker compose up --build
```

O servico `app` espera o PostgreSQL ficar saudavel, roda `alembic upgrade head` e inicia o Uvicorn.

## Hospedar em producao

Para o MVP, o caminho mais simples e publicar a API em um provedor com HTTPS e Postgres gerenciado. O Render funciona bem para este formato: ele conecta com GitHub, cria Web Service Python e tambem oferece Postgres gerenciado.

### Opcao recomendada: Render

1. Entre em https://dashboard.render.com.
2. Crie um novo Postgres:
   - `New` -> `Postgres`
   - nome sugerido: `superdados-db`
   - regiao: escolha a mesma que usara no Web Service.
3. Crie um novo Web Service:
   - `New` -> `Web Service`
   - conecte o repositorio `Jusdahh/SuperDados`
   - runtime: `Python`
   - build command:

```bash
pip install -r requirements.txt
```

4. Configure o start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Configure as variaveis de ambiente:

```env
DATABASE_URL=<Internal Database URL do Postgres do Render>
APP_ENV=production
HASH_SALT=<um texto secreto longo>
LIMESURVEY_BASE_URL=https://ueldjudah.limesurvey.net
PUBLIC_INVITE_EXPIRES_HOURS=168
PUBLIC_COOKIE_SECURE=true
```

O app tambem inclui `render.yaml`, entao voce pode usar a opcao de Blueprint do Render para criar Web Service e banco a partir desse arquivo. Mesmo assim, revise as variaveis antes de usar em producao.

Depois do deploy, o Render vai gerar uma URL HTTPS parecida com:

```text
https://superdados-api.onrender.com
```

O link unico para anuncio da Meta ficaria:

```text
https://superdados-api.onrender.com/entry/1?utm_source=meta&utm_campaign=rodada_1
```

Antes de anunciar, gere um estoque de tokens no ambiente de producao e importe no LimeSurvey:

```bash
python -m scripts.limesurvey_export_invites \
  --base-url https://superdados-api.onrender.com \
  --survey-id 1 \
  --quantity 5000 \
  --source-channel meta_ads \
  --expires-in-hours 168 \
  --output participantes_meta.csv
```

Importante: se voce criou pesquisas e tokens localmente em `superdados.db`, eles nao vao automaticamente para o banco de producao. Em producao, crie a pesquisa novamente via `/docs`, ajuste `external_form_id` para `318945`, gere tokens e importe o CSV novo no LimeSurvey.

### Referencias de deploy

- Render FastAPI: https://render.com/docs/deploy-fastapi
- Render Postgres: https://render.com/docs/postgresql-creating-connecting

## Testes

```bash
pytest
```

Os testes usam SQLite em memoria para validar o fluxo do MVP sem depender do PostgreSQL.

## Fluxo principal

1. `POST /surveys` cria a pesquisa interna.
2. `POST /surveys/{survey_id}/invites` gera tokens internos para importar no LimeSurvey.
3. `POST /invites/validate-open` valida a primeira abertura, grava hashes de IP, dispositivo e user agent, e bloqueia troca de dispositivo.
4. `POST /responses/import` importa uma resposta exportada/enviada pelo LimeSurvey, impede reuso do token, salva resposta bruta e cria a validacao automatica.
5. `GET /surveys/{survey_id}/responses?status=valid` lista respostas por status.
6. `PATCH /responses/{response_id}/validation` revisa manualmente uma resposta.
7. `GET /surveys/{survey_id}/exports/valid-responses` retorna apenas respostas validas para futura ponderacao.

## Integracao pratica com LimeSurvey

Esta integracao usa o LimeSurvey como motor de formulario e o SuperDados como camada de controle e auditoria. O fluxo recomendado para o MVP e:

1. Criar a pesquisa no SuperDados.
2. Criar a pesquisa equivalente no LimeSurvey.
3. Gerar tokens no SuperDados e exporta-los em CSV de participantes do LimeSurvey.
4. Importar os participantes/tokens no LimeSurvey e ativar a pesquisa em modo fechado por tokens.
5. Exportar respostas do LimeSurvey em CSV.
6. Importar esse CSV no SuperDados para validacao, score de risco e exportacao da base valida.

### 1. Criar pesquisa no SuperDados

Com a API rodando em `http://127.0.0.1:8000`:

```bash
curl -X POST http://127.0.0.1:8000/surveys \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Pesquisa municipal\",\"city\":\"Sao Paulo\",\"state\":\"SP\",\"external_form_provider\":\"limesurvey\",\"external_form_id\":\"LS-100\"}"
```

Guarde o `id` retornado. Ele sera usado nos scripts abaixo.

### 2. Criar pesquisa no LimeSurvey

No painel administrativo do LimeSurvey:

1. Crie uma nova pesquisa.
2. Monte as perguntas do questionario.
3. Inclua campos/perguntas que aparecerao na exportacao com nomes compativeis com o motor de risco, especialmente:
   - `municipio_votacao`
   - `attention_check`
   - opcionalmente `device_fingerprint`
   - opcionalmente `user_agent`
4. Configure a pesquisa para armazenar respostas completas.

O `device_fingerprint` e o `user_agent` nao sao garantidos pelo CSV padrao do LimeSurvey. Para usa-los no MVP, crie perguntas ocultas ou campos equivalentes e preencha via template/script do LimeSurvey. Se esses campos nao existirem, o script de importacao usa valores fallback.

### 3. Ativar modo fechado por tokens

No LimeSurvey, use a area de participantes da pesquisa:

1. Abra a pesquisa.
2. Acesse `Survey participants` ou `Participantes da pesquisa`.
3. Inicialize/crie a tabela de participantes, se o LimeSurvey pedir.
4. Importe os participantes por CSV.
5. Ative a pesquisa. Com tabela de participantes/tokens ativa, a pesquisa deixa de funcionar como link publico aberto e passa a exigir token.

O manual do LimeSurvey informa que a importacao de participantes por CSV exige `firstname`, `lastname` e `email`, e aceita campos opcionais como `token`, `language`, `validfrom`, `validuntil` e `attribute_*`. O script abaixo gera esses campos.

Importante: o LimeSurvey limita o codigo de acesso/token a no maximo 36 caracteres e aceita apenas letras, numeros e `_`. O backend gera tokens com 32 caracteres nesse formato.

### 4. Exportar convites do SuperDados para CSV do LimeSurvey

Use o script `scripts/limesurvey_export_invites.py`. Ele cria convites no backend e grava um CSV importavel no LimeSurvey:

```bash
python -m scripts.limesurvey_export_invites \
  --base-url http://127.0.0.1:8000 \
  --survey-id 1 \
  --quantity 500 \
  --source-channel whatsapp \
  --utm-source painel \
  --utm-campaign rodada-1 \
  --utm-content lote-a \
  --expires-in-hours 72 \
  --output limesurvey_participants.csv
```

Por padrao, o campo `language` fica vazio para o LimeSurvey usar o idioma principal da pesquisa. Se precisar informar idioma, use um codigo aceito pela sua pesquisa:

```bash
python -m scripts.limesurvey_export_invites \
  --survey-id 1 \
  --quantity 500 \
  --language pt \
  --output limesurvey_participants.csv
```

O CSV gerado contem:

- `firstname`, `lastname`, `email`, `emailstatus`
- `token`
- `usesleft`: `1`, para limitar o token a uma resposta no LimeSurvey
- `language`
- `validuntil`
- `attribute_1`: id interno do convite
- `attribute_2`: canal de origem
- `attribute_3`: utm_source
- `attribute_4`: utm_campaign
- `attribute_5`: utm_content

Depois importe `limesurvey_participants.csv` na tela de participantes/tokens do LimeSurvey.

### 5. Exportar respostas do LimeSurvey

Quando houver respostas:

1. Abra a pesquisa no LimeSurvey.
2. Acesse `Responses` / `Responses & statistics`.
3. Use `Export` / `Export results`.
4. Escolha CSV.
5. Exporte respostas completas.
6. Garanta que o CSV contenha a coluna `token`.

Colunas esperadas pelo importador:

- `id`: id da resposta no LimeSurvey;
- `token`: token usado pelo respondente;
- `startdate`: data/hora de inicio, se disponivel;
- `submitdate` ou `datestamp`: data/hora de envio, se disponivel;
- `ipaddr`: IP, se o LimeSurvey exportar;
- `user_agent`: opcional;
- `device_fingerprint`: opcional;
- demais colunas de perguntas entram em `raw_payload`.

Se o CSV tiver nomes diferentes, use os parametros `--token-column`, `--response-id-column`, `--ip-column`, `--user-agent-column`, `--device-fingerprint-column`, `--started-at-column` e `--submitted-at-column`.

### 6. Importar respostas no SuperDados

Com a API rodando:

```bash
python -m scripts.limesurvey_import_responses \
  --base-url http://127.0.0.1:8000 \
  --survey-id 1 \
  --input limesurvey_responses.csv
```

Exemplo com delimitador `;` e nomes de colunas customizados:

```bash
python -m scripts.limesurvey_import_responses \
  --base-url http://127.0.0.1:8000 \
  --survey-id 1 \
  --input limesurvey_responses.csv \
  --delimiter ";" \
  --token-column token \
  --response-id-column id \
  --submitted-at-column datestamp \
  --default-device-fingerprint limesurvey-export
```

O script envia cada linha para `POST /responses/import`. O backend impede segunda resposta para o mesmo token, salva hashes tecnicos e calcula o score de risco.

### 7. Consultar respostas por status

```bash
curl "http://127.0.0.1:8000/surveys/1/responses?status=valid"
curl "http://127.0.0.1:8000/surveys/1/responses?status=suspicious"
curl "http://127.0.0.1:8000/surveys/1/responses?status=discarded"
```

Exportar apenas a base valida:

```bash
curl "http://127.0.0.1:8000/surveys/1/exports/valid-responses"
```

### 8. Usar um unico link em anuncios da Meta

Para campanhas pagas, nao divulgue diretamente o link generico do LimeSurvey. Use o endpoint publico do SuperDados como porta de entrada.

O fluxo e:

```text
Anuncio da Meta
    -> link publico do SuperDados
    -> SuperDados reserva um token livre para aquele navegador
    -> redirecionamento para o LimeSurvey com o token
```

Primeiro, configure no `.env`:

```env
LIMESURVEY_BASE_URL=https://ueldjudah.limesurvey.net
PUBLIC_COOKIE_SECURE=false
```

O campo `external_form_id` da pesquisa interna precisa ser o numero da pesquisa no LimeSurvey. Para a pesquisa `https://ueldjudah.limesurvey.net/318945`, use:

```json
{
  "external_form_id": "318945"
}
```

Para corrigir uma pesquisa ja criada, use `PATCH /surveys/{survey_id}/integration` na pagina `/docs` com:

```json
{
  "external_form_provider": "limesurvey",
  "external_form_id": "318945"
}
```

Antes da campanha, gere um estoque maior que o numero esperado de cliques e importe o CSV no LimeSurvey:

```bash
python -m scripts.limesurvey_export_invites \
  --survey-id 1 \
  --quantity 5000 \
  --source-channel meta_ads \
  --expires-in-hours 168 \
  --output participantes_meta.csv
```

Depois de importar `participantes_meta.csv` na tabela de participantes do LimeSurvey, o link unico para testar localmente e:

```text
http://127.0.0.1:8000/entry/1?utm_source=meta&utm_campaign=teste
```

Esse link reserva um token ainda livre, grava um cookie no navegador e redireciona para algo como:

```text
https://ueldjudah.limesurvey.net/318945?lang=pt&token=TOKEN_RESERVADO
```

Se a mesma pessoa clicar novamente usando o mesmo navegador, recebe o mesmo token e nao consome outro convite. Se nao houver tokens livres, o endpoint retorna `invite_pool_empty`.

Para uma campanha real, `127.0.0.1` nao funciona porque aponta para o computador de quem clicar. O backend SuperDados precisa ser publicado em um dominio HTTPS, por exemplo:

```text
https://pesquisa.superdados.com.br/entry/1?utm_source=meta&utm_campaign=rodada_1
```

Em producao, configure:

```env
PUBLIC_COOKIE_SECURE=true
```

O cookie reduz geracao repetida no mesmo navegador. Uma pessoa ainda pode tentar contornar isso limpando cookies ou usando outro navegador; por isso o score de risco por IP, dispositivo e velocidade continua necessario.

### Referencias LimeSurvey

- Participantes/tokens e importacao CSV: https://www.limesurvey.org/manual/Tokens
- Exportacao de respostas: https://www.limesurvey.org/manual/Export_responses

## Regras de risco

As regras ficam em `app/services/risk_scoring.py` com thresholds em constantes:

- duracao menor que 60 segundos;
- municipio da votacao diferente da cidade alvo;
- attention check incorreto;
- mais de 5 respostas do mesmo IP na ultima hora;
- mais de 1 resposta do mesmo dispositivo;
- token aberto em outro dispositivo;
- canal de origem ausente.

Classificacao:

- `0..29`: `valid`
- `30..69`: `suspicious`
- `70+`: `discarded`

## Decisoes tecnicas

- Tokens sao gerados com 32 caracteres compativeis com LimeSurvey (`0-9`, `a-z`, `A-Z`, `_`) e comparados via `token_hash`.
- O campo `external_token` existe para facilitar importacao no LimeSurvey no MVP, mas deve ser criptografado ou omitido em producao.
- IP, user agent e fingerprint nao sao armazenados em texto puro; somente SHA-256 com salt configuravel por `HASH_SALT`.
- As colunas JSON usam JSONB no PostgreSQL e variante JSON nos testes com SQLite.
- Nao ha autenticacao neste MVP porque login e permissoes ficaram fora do escopo.

## Limitacoes para a proxima etapa

- Integracao automatica real com LimeSurvey ainda nao foi implementada.
- Exportacao final de respostas validas em CSV ainda pode ser adicionada; hoje o endpoint retorna JSON.
- Revisao manual nao tem controle de usuario autenticado.
- Nao ha dashboard operacional nem ponderacao estatistica.
