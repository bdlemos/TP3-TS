# Sistema de Ficheiros Seguro com Controlo de Acesso Multi-Nível (Bell-LaPadula Adaptado)

## Descrição do Projeto

Este projeto implementa um sistema de ficheiros seguro utilizando FUSE (Filesystem in Userspace) em Python. O objetivo é aplicar um modelo de controlo de acesso baseado nos princípios do Bell-LaPadula (BLP), focado na confidencialidade da informação em sistemas com múltiplos níveis de segurança.

O sistema de ficheiros virtualiza o acesso a um diretório existente no sistema operativo, aplicando regras de segurança que determinam se um utilizador pode ler, escrever, criar ou listar ficheiros e diretórios com base no seu nível de autorização (clearance) e no nível de classificação da informação.

Foram implementadas adaptações ao modelo BLP clássico, como a introdução de "utilizadores de confiança" (trusted users) que possuem privilégios para realizar operações de "write-down" (escrever informação de um nível superior para um inferior), simulando um processo de desclassificação controlada. Todas as ações significativas são registadas num ficheiro de auditoria.

Este projeto foi desenvolvido como parte do Trabalho Prático 3, que visa explorar e implementar adaptações ao modelo Bell-LaPadula para endereçar algumas das suas limitações práticas.

## Funcionalidades Principais

* **Sistema de Ficheiros Virtual via FUSE:** Monta um diretório existente num novo ponto de montagem, intercetando as operações do sistema de ficheiros.
* **Controlo de Acesso Multi-Nível:**
    * Níveis de Segurança: `UNCLASSIFIED`, `CONFIDENTIAL`, `SECRET`, `TOP_SECRET`.
    * **No Read Up:** Utilizadores não podem ler ficheiros/diretórios com nível de classificação superior ao seu nível de autorização.
    * **No Write Down (com exceção):**
        * Utilizadores normais não podem escrever/criar ficheiros em níveis de classificação inferiores ao seu (para proteger a integridade da classificação).
        * **Utilizadores de Confiança (Trusted Users):** Podem realizar "write-down" e "create-down", permitindo a desclassificação controlada de informação.
    * **Write Up / Same Level:** Utilizadores podem escrever/criar ficheiros no seu próprio nível ou em níveis superiores (consistente com BLP para confidencialidade).
* **Autenticação de Utilizador:**
    * Simulada através de uma variável de ambiente `USER` definida num ficheiro `.env`.
    * O cliente permite "fazer login" para definir este utilizador.
    * Níveis de autorização e status de "trusted" são definidos no ficheiro `users.json`.
* **Cliente Interativo (Shell):**
    * Interface de linha de comandos (`client.py`) para interagir com o sistema de ficheiros seguro.
    * Comandos suportados:
        * `login`: Define o utilizador atual.
        * `ls`: Lista o conteúdo do diretório atual (não recursivo).
        * `cd <diretório>`: Muda o diretório atual.
        * `pwd`: Mostra o diretório atual.
        * `cat <ficheiro>`: Lê e exibe o conteúdo de um ficheiro.
        * `new <ficheiro>`: Cria um novo ficheiro ou sobrescreve um existente.
        * `add <ficheiro>`: Anexa conteúdo a um ficheiro (cria se não existir).
        * `rm <ficheiro>`: Remove um ficheiro.
        * `exit`: Sai do cliente.
* **Auditoria:**
    * Todas as tentativas de acesso (permitidas ou negadas) e operações significativas são registadas no ficheiro `audit.log` com timestamp, utilizador, ação, caminho e status.
* **Estrutura de Diretórios de Exemplo:**
    * O sistema é testado com uma estrutura de diretórios que reflete os níveis de segurança (ex: `data/secure_files/unclassified`, `data/secure_files/confidential`, etc.).

## Tecnologias Utilizadas

* **Python 3**
* **python-fuse (FUSEpy):** Biblioteca para criar sistemas de ficheiros em espaço de utilizador.
* **python-dotenv:** Para gerir a configuração do utilizador através de um ficheiro `.env`.

## Estrutura de Ficheiros do Projeto
```
├── auth.py             # Lógica de autenticação e níveis de autorização dos utilizadores
├── client.py           # Aplicação cliente interativa (shell)
├── data/               # Diretório de exemplo com ficheiros e subdiretórios classificados
│   ├── secure_files/
│   │    ├── confidential/
│   │    │   └── conf.txt
│   │    ├── secret/
│   │    │   └── secret.txt
│   │    ├── top_secret/
│   │    │   └── top.txt
│   │    └── unclassified/
│   │        └── info.txt
│   └──users.json
├── fuse_main.py        # Implementação principal do sistema de ficheiros FUSE
├── logger.py           # Módulo para registo de auditoria
├── README.md           # Este ficheiro
└── .env                # Ficheiro (criado pelo cliente) para armazenar o USER atual (não versionar)
└── audit.log           # Ficheiro de log de auditoria (criado em tempo de execução)
```
## Como Executar

A execução envolve dois processos principais: o servidor FUSE e o cliente.

1.  **Iniciar o Servidor FUSE (`fuse_main.py`):**
    Abra um terminal e execute:
    ```bash
    make run
    ```
    * O processo FUSE ficará em execução em primeiro plano (`foreground=True`). Mantenha este terminal aberto.

2.  **Executar o Cliente (`client.py`):**
    Abra **outro** terminal e execute:
    ```bash
    python3 client.py
    ```
    * O cliente solicitará o nome de utilizador para "login". Utilizadores e os seus níveis/status de confiança estão definidos em `auth.py` (ex: `admin`, `bernardo`, `joao`).
    * Após o login, pode usar os comandos do cliente (ls, cd, cat, etc.) para interagir com os ficheiros em `/tmp/montagem`.

3.  **Para parar o sistema:**
    * No terminal do cliente, digite `exit`.
    * No terminal do servidor FUSE, pressione `Ctrl+C` para desmontar o sistema de ficheiros e terminar o processo.
