# Backlog de Features para o "Ramble"

Este arquivo documenta as funcionalidades planejadas e ideias para a evolução do sistema `ramble`.

## 1. Sistema de Busca e Tags

Atualmente, é possível apenas ler uma página conhecida. Para melhorar a descoberta de informação, um sistema de busca e organização por tags é necessário.

- **Tags no Frontmatter:** Usuários poderão adicionar uma chave `tags` em suas páginas:
  ```yaml
  title: Gerenciamento de SSH
  tags: [security, networking, ssh]
  ...
  ```

- **Novo Comando `ramble find`:** Um novo comando será criado para buscar e filtrar anotações.
  - **Busca por palavra-chave:** `ramble find "chave ssh"`
  - **Filtragem por Tag:** `ramble find --tag security`
  - **Combinação:** `ramble find "autenticação" --tag ssh`

- **Ideia de Implementação:**
  - O comando precisará percorrer recursivamente todos os arquivos `.yml` em `~/.local/share/chaos/ramblings/`.
  - Para cada arquivo encontrado, o conteúdo será lido. Se o arquivo contiver uma chave `sops`, ele será decifrado em memória usando a mesma lógica do `handleReadRamble`.
  - **Filtragem de Tags:** Se a flag `--tag` for usada, o cabeçalho (frontmatter) do YAML será analisado com `omegaconf`. Se a chave `tags` não contiver a tag desejada, o arquivo é descartado da lista de resultados.
  - **Busca de Keyword:** O conteúdo (decifrado, se necessário) será verificado para a presença da string de busca. A busca pode ser uma simples verificação de contenção (`'keyword' in content`) ou usar expressões regulares para mais poder.
  - **Saída:** O comando exibirá uma lista dos caminhos das páginas que correspondem aos critérios (ex: `diario.pagina`), possivelmente com as linhas que contêm a correspondência, similar a um `grep`.

## 2. Links Entre Páginas (Backlinking)

Para transformar o `ramble` em uma verdadeira base de conhecimento, é essencial poder conectar ideias entre diferentes páginas.

- **Sintaxe de Link:** Será adotada uma sintaxe padrão, similar a outras ferramentas de PKM, como `[[diario.pagina]]`.

- **Ideia de Implementação:**
  - A função `_read_and_print_ramble` (em `handlers.py`) é o local ideal para esta lógica.
  - Durante a renderização do conteúdo de uma página, um `re.sub` será usado para encontrar todas as ocorrências de `\[\[(.*?)\]\]`.
  - A função de callback do `re.sub` receberá o alvo do link (ex: `diario.pagina`) como um argumento.
  - Ela então construirá o caminho completo para o arquivo (`~/.local/share/chaos/ramblings/diario/pagina.yml`) e usará `os.path.exists()` para verificar sua validade.
  - Usando a biblioteca `rich`, a função de callback retornará um objeto `Text` estilizado:
    - **Link Válido:** `Text("diario.pagina", style="blue underline")`.
    - **Link Quebrado:** `Text("diario.pagina [QUEBRADO]", style="red")`.
  - Esta abordagem de renderização "just-in-time" é performática para a leitura de arquivos individuais e evita a complexidade de manter um banco de dados ou índice central de links.

## 3. Comandos de Refatoração (Mover/Renomear)

Para facilitar a organização da base de conhecimento à medida que ela cresce, comandos de refatoração são necessários.

- **Novo Comando `ramble move`:** Um comando `ramble move <alvo_antigo> <alvo_novo>` será implementado.
  - Exemplo: `ramble move seguranca.ssh ssh.hardening`

- **Ideia de Implementação:**
  - O comando fará o parsing dos argumentos para obter os caminhos de arquivo de origem e destino.
  - Ele usará `os.path.exists()` para verificar se a origem existe e se o destino já não existe (para evitar sobreposições acidentais, ou pedir confirmação).
  - A operação principal será executada com `shutil.move()`, que move o arquivo. O comando também deve garantir que o diretório de destino exista, usando `os.makedirs(exist_ok=True)`.
  - **Atualização de Backlinks (Avançado):** Para uma implementação mais robusta, este comando dependeria da feature de Busca. Após mover o arquivo, ele poderia executar uma busca por `[[alvo_antigo]]` em toda a base de `rambles` e substituir as ocorrências por `[[alvo_novo]]`, consertando automaticamente os links quebrados pela refatoração.

## 4. Sistema de Exportação de Diários

Para permitir o compartilhamento e arquivamento de ideias, um sistema de exportação será implementado com foco na integridade do diário.

- **Novo Comando `ramble export`:** Um comando `ramble export <diario>` será adicionado.
  - Exemplo: `ramble export projetos --format md > projetos.md`
- **Restrição de Escopo:** Esta funcionalidade intencionalmente não suportará a exportação de páginas individuais, para incentivar a coesão e a sequência de ideias dentro de um diário.

- **Ideia de Implementação:**
  - O comando receberá o nome de um diário. Ele listará todos os arquivos `.yml` dentro do diretório correspondente (ex: `~/.local/share/chaos/ramblings/projetos/`).
  - Para garantir a "sequência de ideias", a lista de arquivos será ordenada alfabeticamente.
  - O comando iterará sobre cada arquivo da lista ordenada. Para cada um:
    - O conteúdo será lido e, se necessário, decifrado em memória (usando a mesma lógica dos outros comandos).
    - O YAML será analisado para extrair as chaves (`title`, `what`, `how`, `scripts`, etc.).
  - Um único e longo texto em Markdown será construído. Cada página pode ser um capítulo, com o `title` se tornando um `<h1>` (`# Titulo`), e as outras chaves se tornando `<h2>` (`## O que é`), etc.
  - O resultado final será impresso no `stdout`, permitindo ao usuário redirecionar para um arquivo (`> projetos.md`), o que segue a filosofia Unix.
