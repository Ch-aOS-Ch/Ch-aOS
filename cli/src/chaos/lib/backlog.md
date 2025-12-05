# Backlog de Features para o "Ramble"

Este arquivo documenta as funcionalidades planejadas e ideias para a evolução do sistema `ramble`.

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

- **Exemplo de Código:**
  ```python
  # Em handlers.py, uma nova função auxiliar
  
  import re
  from rich.text import Text
  from rich.console import Group
  
  def _render_with_links(text_content):
      """
      Processa um bloco de texto, encontra os links [[...]] e retorna um 
      objeto renderizável pela biblioteca Rich.
      """
      renderables = []
      last_end = 0
      
      for match in re.finditer(r"\[\[(.*?)\]\]", text_content):
          link_target = match.group(1)
          start, end = match.span()
          
          # Adiciona o texto antes do link
          renderables.append(Text.from_markup(text_content[last_end:start]))
          
          # Constrói o caminho do link e verifica se existe
          # (a lógica exata de resolução de caminho vai aqui)
          link_path = Path(f"~/.local/share/chaos/ramblings/{link_target.replace('.', '/')}.yml").expanduser()
          
          if link_path.exists():
              # Link válido
              renderables.append(Text(link_target, style="blue underline"))
          else:
              # Link quebrado
              renderables.append(Text(f"{link_target} [QUEBRADO]", style="red"))
          
          last_end = end
  
      # Adiciona o restante do texto após o último link
      renderables.append(Text.from_markup(text_content[last_end:]))
      
      return Group(*renderables)
  
  # Exemplo de como seria usado dentro de _read_and_print_ramble:
  # ...
      if 'what' in ramble_data and ramble_data.what:
          renderables.append(Markdown(f"**What is it?**"))
          # Em vez de passar o Markdown direto, passamos pelo nosso renderizador
          processed_content = _render_with_links(ramble_data.what)
          renderables.append(Padding.indent(processed_content, 4))
          renderables.append(Text("\n"))
  # ...
  ```

## 3. Comandos de Refatoração (Mover/Renomear)

Para facilitar a organização da base de conhecimento à medida que ela cresce, comandos de refatoração são necessários.

- **Novo Comando `ramble move`:** Um comando `ramble move <alvo_antigo> <alvo_novo>` será implementado.
  - Exemplo: `ramble move seguranca.ssh ssh.hardening`

- **Ideia de Implementação:**
  - O comando fará o parsing dos argumentos para obter os caminhos de arquivo de origem e destino.
  - Ele usará `os.path.exists()` para verificar se a origem existe e se o destino já não existe (para evitar sobreposições acidentais, ou pedir confirmação).
  - A operação principal será executada com `shutil.move()`, que move o arquivo. O comando também deve garantir que o diretório de destino exista, usando `os.makedirs(exist_ok=True)`.
  - **Atualização de Backlinks (Avançado):** Para uma implementação mais robusta, este comando dependeria da feature de Busca. Após mover o arquivo, ele poderia executar uma busca por `[[alvo_antigo]]` em toda a base de `rambles` e substituir as ocorrências por `[[alvo_novo]]`, consertando automaticamente os links quebrados pela refatoração.

- **Exemplo de Código:**
  ```python
  # Em handlers.py
  
  import shutil
  from pathlib import Path
  
  def handleMoveRamble(args):
      RAMBLE_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
      
      old_target = args.target_antigo # ex: "seguranca.ssh"
      new_target = args.target_novo   # ex: "ssh.hardening"
  
      old_path = RAMBLE_DIR / old_target.replace('.', '/')
      new_path = RAMBLE_DIR / new_target.replace('.', '/')
      
      old_file = Path(str(old_path) + ".yml")
      new_file = Path(str(new_path) + ".yml")
  
      if not old_file.exists():
          console.print(f"[bold red]ERRO:[/] O ramble de origem não existe: {old_file}")
          sys.exit(1)
  
      if new_file.exists():
          console.print(f"[bold red]ERRO:[/] O ramble de destino já existe: {new_file}")
          sys.exit(1)
  
      # Garante que o diretório de destino exista
      new_file.parent.mkdir(parents=True, exist_ok=True)
  
      # Move o arquivo
      shutil.move(str(old_file), str(new_file))
      console.print(f"Rambe movido de [cyan]{old_target}[/] para [cyan]{new_target}[/]")
  
      # Lógica avançada de atualização de backlinks (opcional)
      if Confirm.ask("Tentar atualizar os backlinks automaticamente?"):
          # Aqui entraria a lógica de busca e substituição
          console.print("Procurando e atualizando backlinks... (não implementado)")
  ```

## 4. Sistema de Exportação de Diários

Para permitir o compartilhamento e arquivamento de ideias, um sistema de exportação será implementado com foco na integridade do diário.

- **Novo Comando `ramble export`:** Um comando `ramble export <diario>` será adicionado.
  - Exemplo: `ramble export projetos --format md > projetos.md`
- **Restrição de Escopo:** Esta funcionalidade intencionalmente não suportará a exportação de páginas individuais, para incentivar a coesão e a sequência de ideias dentro de um diário.

- **Ideia de Implementação:**
  - O comando receberá o nome de um diário. Ele listará todos os arquivos `.yml` dentro do diretório correspondente (ex: `~/.local/share/chaos/ramblings/projetos/`).
  - O comando iterará sobre cada arquivo da lista. Para cada um:
    - O conteúdo será lido e, se necessário, decifrado em memória (usando a mesma lógica dos outros comandos).
    - O YAML será analisado para extrair as chaves (`title`, `what`, `how`, `scripts`, etc.).
  - Um único e longo texto em Markdown será construído. Cada página pode ser um capítulo, com o `title` se tornando um `<h1>` (`# Titulo`), e as outras chaves se tornando `<h2>` (`## O que é`), etc.
  - O resultado final será impresso no `stdout`, permitindo ao usuário redirecionar para um arquivo (`> projetos.md`), o que segue a filosofia Unix.

- **Exemplo de Código:**
  ```python
  # Em handlers.py
  
  from pathlib import Path
  
  def handleExportRamble(args):
      journal_name = args.diario
      RAMBLE_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
      journal_dir = RAMBLE_DIR / journal_name
  
      if not journal_dir.is_dir():
          console.print(f"[bold red]ERRO:[/] Diário '{journal_name}' não encontrado.")
          sys.exit(1)
  
      all_pages_content = []
      
      # Ordena os arquivos para uma exportação consistente
      sorted_files = sorted(journal_dir.glob("*.yml"))
  
      for ramble_file in sorted_files:
          data, _ = _read_ramble_content(ramble_file, args.sops_file_override)
          
          page_md = []
          title = data.get('title', ramble_file.stem)
          page_md.append(f"# {title}\n")
          
          if data.get('what'):
              page_md.append(f"## O que é\n\n{data.get('what')}\n")
          if data.get('why'):
              page_md.append(f"## Por que usar\n\n{data.get('why')}\n")
          if data.get('how'):
              page_md.append(f"## Como funciona\n\n{data.get('how')}\n")
          
          # Adiciona um separador entre as páginas
          all_pages_content.append("\n".join(page_md))
  
      # Imprime o resultado final no stdout
      final_export = "\n---\n".join(all_pages_content)
      print(final_export)
  ```
