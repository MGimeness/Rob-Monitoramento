# Robô de Monitoramento

Painel desktop em Python que automatiza a rotina de monitoramento de plantões: lê as planilhas da equipe no Google Drive, confere os plantões com os dados de uma plataforma via API REST e automatiza o envio das mensagens de confirmação aos profissionais, reduzindo tarefas manuais e o tempo de resposta.

> **Versão para portfólio.** Este repositório não contém dados reais: IDs de planilha, URLs internas, tokens e textos da empresa foram removidos e ficam em um arquivo de configuração local (`config.json`), que **não** é enviado ao GitHub.

## O que o projeto faz

- **Leitura de planilhas:** baixa planilhas do Google Drive (Google Drive API com OAuth 2.0) e trata os dados com `pandas`.
- **Conferência de plantões:** normaliza nomes e turnos (diurno/noturno), compara a planilha com os dados da plataforma e identifica pendências e divergências.
- **Integração via API REST:** consome a API da plataforma com autenticação por token (`requests`), incluindo leitura tolerante a falhas e log em arquivo.
- **Envio de mensagens:** automatiza o envio das confirmações de plantão com `PyAutoGUI` e `pyperclip`, com atalho de emergência para pausar/parar.
- **Interface gráfica:** painel com abas, tema escuro e logs em tempo real, feito com `CustomTkinter`; as tarefas longas rodam em threads para não travar a tela.

## Tecnologias

Python, pandas, openpyxl, requests, CustomTkinter, PyAutoGUI, pyperclip, Google Drive API (OAuth 2.0), threading.

## Como usar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Crie o arquivo de configuração a partir do exemplo:
   ```bash
   cp config.exemplo.json config.json
   ```
   e preencha `id_planilha`, `api_base_url`, `site_url`, `cookie_token` e `grupos_bloqueados`.
3. Crie as credenciais do Google (OAuth, tipo "app para computador") no Google Cloud Console e salve o arquivo como `credentials.json` na pasta do projeto. Na primeira execução será aberta uma janela para você autorizar o acesso (somente leitura ao Drive).
4. Informe o token da API pela variável de ambiente `API_TOKEN`, pelo arquivo `api_token.txt` ou direto na interface.
5. Execute:
   ```bash
   python painel_robo.pyw
   ```

## Segurança

Os arquivos `config.json`, `credentials.json`, `token.json`, `api_token.txt`, logs e planilhas estão no `.gitignore`. Nunca envie esses arquivos ao repositório.

## Autora

Michele Samara Cerqueira Gimenes, [github.com/MGimeness](https://github.com/MGimeness)
