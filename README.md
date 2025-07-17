# 🧝‍♂️ Ch-aronte

> **Seu guia pelo submundo do Arch Linux.**
> Um instalador imersivo, automatizado com Ansible, para quem quer aprender de verdade — sem copiar e colar no escuro.

---

## 🌐 Visão Geral

O **Ch-aronte** é um instalador minimalista para o Arch Linux, feito com Ansible e Shell Script, voltado para iniciantes curiosos e amantes do caos controlado. Ele automatiza o processo de instalação mantendo o usuário no comando, com foco em **aprendizado**, **imersão** e um toque de **estética cyberpunk** (sim, é meio cringe, mas é *nosso* cringe).

Projetado para ser usado em um ambiente **liveboot**, o projeto tem planos futuros para ambientes **VM** e pós-instalação completa com gerenciamento de **dotfiles**.

---

## 🌳 Estrutura do Projeto

```bash
.
├── ansible.cfg
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── group_vars
│   └── all
│       └── config.yml
├── Inventario.yml
├── LICENSE
├── main.yaml
├── README.md
├── respostas.env
├── roles
│   ├── chroot
│   │   └── tasks
│   │       └── main.yml
│   ├── particionamento
│   │   └── tasks
│   │       └── main.yml
│   ├── setup
│   │   ├── tasks
│   │   │   └── main.yml
│   │   └── vars
│   │       └── scripts_dirs.yml
│   └── sistema
│       ├── tasks
│       │   └── main.yml
│       └── vars
│           └── necessarios.yml
├── scripts
│   ├── A-particionamento.sh
│   ├── B-reflector.sh
│   ├── C-instalacao.sh
│   ├── D-regiao.sh
│   ├── E-personalizacao.sh
│   ├── F-bootloader.sh
│   └── resources.sh
├── SECURITY.md
└── WIP.yml

```

---

## 🚀 Funcionalidades

* [x] **Instalador Minimal** — com detecção automática de BIOS/UEFI
* [ ] **Gerenciador de Dotfiles** — WIP
* [ ] **Configuração Pós-Instalação** — WIP

---

## 🧩 Componentes-Chave

### 🔹 `main.yaml`

Playbook principal — o **núcleo do ritual**.
Contém as seguintes tags:

* `particionamento` particiona baseado nas coisas settadas em A-particionamento.sh
* `instalacao`: instala o sistema base e pacotes adicionais definidos, já tem um sistema preparado pra plugins, só falta integrar direito com C-instalacao.sh.
### 🔹 `ansible.cfg`

Configurações base para o Ansible:

* Inventário e diretório temporário
* SSH desativado (pensado para liveboot)

### 🔹 `Inventario.yml`

Usado principalmente em execuções automatizadas (ex: VMs). Pode ser adaptado para diversos cenários.

### 🔹 `group_vars/all/config.yml`

Configurações globais do sistema: usuário, hostname, timezone, mirrors, pacotes, etc.

---

## 📦 Roles (Módulos)

### 1. `setup`

Configura permissões de execução para scripts auxiliares.

### 2. `particionamento`

Particiona o disco (com base no modo de boot detectado).

### 3. `sistema`

Instala o sistema base e pacotes adicionais definidos.

### 4. `chroot`

Executa ações dentro do ambiente chroot: configuração de região, bootloader, personalização.

#### Futuras Roles:

* `dotfiles`
* `limpeza`
* `backup`

---

## ⚙️ Tecnologias Utilizadas

* **Ansible** – Orquestração e automação
* **Shell Script** – Execução de tarefas no sistema alvo
* **YAML** – Playbooks e variáveis
* **Arch Linux** – O sistema base (claro)

---

## 🛠️ Como Usar

### Pré-requisitos:

* Ansible e Git instalados
* Acesso à internet no ambiente LiveBoot (via `iwctl`)
* Arch Linux Live ISO em execução

### Passos:

```bash
iwctl                          # Conecte-se ao WiFi
pacman -Sy ansible          # Instale os pré-requisitos
pacman -Sy git
git clone https://github.com/Dexmachi/Ch-aronte.git
cd Ch-aronte
chmod +x scripts/A-particionamento.sh
./scripts/A-particionamento.sh
```

**⚠️ Siga as instruções que surgirem no terminal — o script é interativo e explicativo.**

---

## 🧪 Estado Atual do Projeto

* Repositório: [github.com/Dexmachi/Ch-aronte](https://github.com/Dexmachi/Ch-aronte)
* Commits: **17**
* Linguagens: **Shell + YAML (Ansible)**
* Licença: **FOSS / sem releases oficiais ainda**
* Traduções: Somente em **pt-BR**
  Contribuições são bem-vindas, desde que mantenham o estilo narrativo do projeto.

---

## ✨ Contribuindo

Qualquer ajuda é bem-vinda — principalmente:

* **Automatização de dotfiles**
* **Traduções criativas** (com lore cyberpunk/hack em mente)
* **Melhorias nas roles Ansible**
* **Sugestões para pós-instalação (DEs, TWM, hardening, etc)**

- siga as regras:
  1. crie uma branch
  2. implemente suas funções
  3. crie uma PR da sua branch para main e aguarde aprovação

## Special thanks:
Inspiração principal veio do projeto `https://github.com/0xzer0x/archible`, do usuário [0xzer0x](https://github.com/0xzer0x)

If you're reading this (i doubt it but oh well), thank you very much for your amazing tool, I hope to achieve this level of creativity and expertize you've got to make it come true.

---

<div align="center">
  ⁂ Navegue com consciência. Instale com estilo. Aprenda o Arch com alma. ⁂
</div>

---
