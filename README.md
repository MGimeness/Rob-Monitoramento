# Robô de Monitoramento

Painel desktop (Windows) para automatizar disparos de monitoramento, cobranças de confirmação e atualização de plantões em uma plataforma de monitoramento via API.

> ⚠️ Projeto de uso interno. Lida com dados de pacientes e credenciais: **nunca** versione `config.json`, `credentials.json`, `token.json`, `api_token.txt` ou logs.

## Funcionalidades

O painel lê uma planilha privada do Google Drive (uma aba por convênio) e é dividido em 3 abas:

### 1. Disparos de Monitoramento
Envia, pelo WhatsApp Desktop, a mensagem diária de monitoramento para os grupos/pacientes ativos.

- Você escolhe os convênios (abas da planilha) e carrega a lista de pacientes com status ativo.
- A mensagem muda conforme o tipo de plantão (PAD) de cada paciente:
  - **Diurno de amanhã**
  - **Noturno de hoje**
  - **Diurno e Noturno (24h)**
  - **SSA**, com texto próprio.
- Entende regras de **dia par/ímpar** no campo PAD (ex.: "Noturno par / Diurno ímpar") e pula quem não tem plantão naquele dia.
- Ignora grupos bloqueados definidos no `config.json`.
- A automação busca o contato pelo nome, cola a mensagem e envia. Há 5 segundos de contagem para focar o WhatsApp.
- Pausa de forma segura se o mouse for movido ou ESC/Espaço for pressionado.
- Mostra tabela com status por paciente (pendente, enviando, enviado, erro), indicadores e botão para atualizar a planilha sem reiniciar.

### 2. Confirmações e Cobranças
Cobra no WhatsApp os plantões que ainda estão **PENDENTES** na planilha.

- Procura a coluna do **Noturno de hoje** e a do **Diurno de amanhã** e lista só os pacientes ativos com a palavra "PENDENTE" em um desses turnos.
- Monta a mensagem de cobrança só com os turnos pendentes de cada paciente.
- Pula conversas com mensagem não lida, para não atropelar uma resposta em andamento.
- Usa o mesmo mecanismo de envio, pausa de segurança, tabela de status e atualização da planilha da aba 1.
- Avisa quando a coluna da data não é encontrada na planilha.

### 3. Atualização Command Center
Cruza a planilha com a plataforma de monitoramento (API) e **confirma os plantões automaticamente**, sem digitar no painel web.

- Você escolhe a data, o convênio e o turno (Diurno, Noturno ou Ambos).
- Para cada paciente, lê o profissional escalado na planilha e localiza o plantão correspondente na API (por nome do paciente, turno e horário).
- Só confirma quando o **profissional da planilha confere com o do painel**. Tolera acentos, nomes do meio omitidos e pequenos erros de digitação.
- Regras de proteção:
  - Plantão **diurno com "cobertura"** não é confirmado.
  - Célula vazia ou "PENDENTE" não é confirmada.
  - Plantões já confirmados são ignorados.
  - Duplicidades confirmam só um registro.
- Após o envio, **confere no servidor** se a confirmação realmente valeu.
- Opcionalmente, define o usuário logado como **responsável de monitoramento** nos plantões que seguem não confirmados. Plantões de profissionais COOP, escalista ou Social Saúde, ou que já têm outro responsável, não são alterados.
- O token de acesso pode ser colado ou obtido automaticamente via navegador (Playwright).
- Mostra detalhes por linha (duplo clique), registra tudo em `command_center_log.txt` e exibe um balanço final.

> A aba 3 usa uma API interna de uma plataforma de terceiros. Use apenas com autorização e para fins internos.

## Requisitos

- **Windows** (usa `os.startfile` e o WhatsApp Desktop)
- Python 3.10 ou superior
- WhatsApp Desktop instalado e logado
- Conta Google com acesso à planilha
- Microsoft Edge ou Google Chrome (para obter o token automaticamente na aba 3)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/MGimeness/Rob-Monitoramento.git
   cd Rob-Monitoramento
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. (Para a aba 3) Instale os navegadores do Playwright:
   ```bash
   playwright install
   ```

## Configuração

### 1. Arquivo `config.json`
Copie `config.exemplo.json` para `config.json` e preencha com seus dados (ID da planilha, URLs da API, grupos bloqueados). Nenhum dado sensível fica no código.

### 2. Credenciais do Google
1. No [Google Cloud Console](https://console.cloud.google.com/), crie um projeto e ative a **Google Drive API**.
2. Crie uma credencial **OAuth (aplicativo para computador)** e baixe o arquivo.
3. Salve como `credentials.json` na mesma pasta do script.
4. No primeiro uso, uma janela do navegador pedirá autorização (escopo somente leitura do Drive) e o `token.json` será gerado automaticamente.

## Como usar

```bash
python painel_robo.pyw
```

1. Preencha o campo **Nome** (obrigatório).
2. Aguarde a mensagem "Planilha Conectada com Sucesso!".
3. Escolha a aba desejada, marque os convênios e carregue a lista.
4. Nas abas 1 e 2, ao iniciar, clique na janela do WhatsApp Desktop dentro dos 5 segundos de contagem e **não use mouse/teclado** até o fim. Para pausar com segurança, mova o mouse ou aperte ESC/Espaço.

## Segurança

O `.gitignore` deve conter:

```
config.json
credentials.json
token.json
api_token.txt
command_center_log.txt
cc_perfil_browser/
```
