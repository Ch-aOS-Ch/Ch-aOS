# 🧝‍♂️ Ch-aronte

**Seu guia pelo submundo do Arch Linux.**

[![Status do Projeto: Ativo](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

**Ch-aronte** não é apenas um instalador. É uma jornada guiada e interativa pelo coração do Arch Linux, projetada para quem deseja instalar com confiança e aprender o processo de verdade — sem copiar e colar comandos no escuro.

Construído com a robustez do **Ansible** e a interatividade do **Shell Script**, ele automatiza as partes tediosas e te entrega o controle onde importa, transformando uma instalação complexa em uma experiência imersiva.

## ✨ Funcionalidades Principais

* ✅ **Instalação Interativa e Guiada**: Um passo a passo que explica o que está acontecendo.
* ✅ **Detecção Automática de Firmware**: Instalação otimizada para **UEFI (com rEFInd)** ou **BIOS (com GRUB)** sem dor de cabeça.
* ✅ **Sistema de Plugins**: Adicione seus próprios pacotes e, futuramente, gerencie seus dotfiles com presets customizados.
* ✅ **Código Aberto e Didático**: A base de código foi refatorada para ser um exemplo prático e legível de automação.

## 🏛️ A Arquitetura: Orquestrador + Worker

O projeto utiliza uma arquitetura híbrida poderosa e flexível:

* **Shell Script (O Orquestrador)**: Atua como a interface interativa com o usuário, coletando informações, validando entradas e orquestrando a sequência de instalação.
* **Ansible (O Worker)**: Atua no backend, executando as tarefas pesadas de forma declarativa e robusta — particionamento, instalação de pacotes e configuração do sistema.

## 🚀 Começando

Projetado para ser executado diretamente do ambiente Live ISO do Arch Linux.

### Pré-requisitos:

* Conexão com a internet (use `iwctl` no live environment).
* Arch Linux Live ISO em execução.

### Passos da Instalação:

```bash
# 1. No ambiente live, conecte-se à internet
iwctl

# 2. (Opcional, mas recomendado) Aumente o espaço em RAM para o liveboot
mount -o remount,size=2G /run/archiso/cowspace

# 3. Instale as dependências
pacman -Sy --noconfirm ansible git
# 4. Clone o repositório e inicie a instalação
git clone [https://github.com/Dexmachi/Ch-aronte.git](https://github.com/Dexmachi/Ch-aronte.git)
cd Ch-aronte

# IMPORTANTE: Execute o script de dentro da pasta do projeto
chmod +x A-coin.sh
./A-coin.sh
```

> [!WARNING]
> O script é seu guia. Siga as instruções no terminal e deixe que o Ch-aronte te conduza pela instalação.

## 🧩 Sistema de Plugins
Personalize sua instalação criando seus próprios "presets" de pacotes.
1. Crie um arquivo custom-SEU-PLUGIN.yml dentro de ./roles/sistema/vars/.
2. Use o formato abaixo para listar os pacotes desejados:
```YAML
pacotes:
  - neovim
  - fish
  - starship

dotfiles:
  - repo: https://github.com/your-user/your-dotfiles.git
    # Para o script decidir como vai aplicar as dotfiles, você pode inserir de 3 formas:
    install_command: "your_custom_dotfile_command.sh" # FORMA 1: você setta um comando específico de como você instala suas dotfiles. Tenha em mente que o script assume que esse comando será rodado dentro da root do seu repo.
    manager: "stow" # FORMA 2: você setta um manager de dotfiles e o script utiliza ele (por exemplo, o stow aplicar todas suas dots).
    # FORMA 3: não colocar nada faz o script buscar por um script "install.sh" dentro da root do seu repositório de dotfiles.
```
> [!WARNING]
> USE BARRAS DE ESPAÇO AO INVÉS DE TABS, O ANSIBLE É SUPER SENSÍVEL A ISSO.

### Para gerar seu plugin do sistema atual, rode:
```bash
cd Ch-aronte
DIR="./roles/sistema/vars/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```
> [!INFO]
> Funciona diretamente do terminal!

## 🗺️ Roadmap do Projeto
- [x] Instalador Minimal com Detecção de Firmware
- [x] Sistema de Plugins para Pacotes Customizados
- [-] Gerenciador de Dotfiles Integrado ao Sistema de Plugins
- [ ] Modo de Execução Totalmente Automatizado com Arquivo de Configuração
- [ ] Suporte ao ALA/ALHA (Arch Linux Archive/History Archive) como alternativa ao flakes.lock.
- [ ] Modo de instalação completamente declarativa, necessitando apenas do arquivo custom*.yml.
- [ ] Modo de configuração pós instalação completamente declarativa, necessitando apenas do arquivo custom*.yml.

## 🤝 Contribuindo

Contribuições são a alma do software livre. Se você tem ideias para melhorar o Ch-aronte, sua ajuda é muito bem-vinda! Dê uma olhada em CONTRIBUTING.md para começar.

As áreas de maior interesse são:
- Traduções criativas e melhorias na narrativa.
- Automatização do gerenciamento de dotfiles.
- Sugestões e implementações de configurações pós-instalação.
- Criação de issues

## 🙏 Agradecimentos

> A inspiração principal para este projeto veio do [archible](https://github.com/0xzer0x/archible) feito pelo [0xzer0x](https://github.com/0xzer0x). Obrigado por criar uma ferramenta tão incrível e por inspirar a comunidade.

<div align="center">
⁂ Navegue com consciência. Instale com estilo. Domine o Arch com alma. ⁂
</div>

---


