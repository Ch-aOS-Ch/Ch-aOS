# Bem vindo à Ch-aronte, seu instalador arch aprofundado para aprendizado e instalação mínima (por enquanto)

## Tree do projeto:
.
├── ansible.cfg
├── ATENÇÃO.md
├── group_vars
│   └── all
│       └── config.yml
├── Inventario.yml
├── main.yaml
└── roles
    ├── chroot
    │   ├── scripts
    │   │   ├── bootloader.sh
    │   │   ├── personalizacao.sh
    │   │   └── regiao.sh
    │   └── tasks
    │       └── main.yml
    ├── particionamento
    │   ├── scripts
    │   │   └── particionamento.sh
    │   └── tasks
    │       └── main.yml
    ├── setup
    │   ├── tasks
    │   │   └── main.yml
    │   └── vars
    │       └── scripts_dirs.yml
    └── sistema
        ├── scripts
        │   ├── instalacao.sh
        │   └── reflector.sh
        ├── tasks
        │   └── main.yml
        └── vars
            └── necessarios.yml

## Objetivo:
  O Ch-aronte é um instalador FOSS voltado à usuários iniciantes que queiram utilizar Arch Linux, ele é um script feito em ansible e sh scprit imersivo feito para que quem entre nele saiba realmente o que está fazendo, não só copiando e colando código sem saber o que está fazendo.
  Ele é voltado para usuários Brasileiros e Portugueses, mas conta apenas com tradução em pt br, mas todo sistema de automação de tradução é bem vinda, desde que feita com a lógica narrativa e easter eggs do projeto em mente (cyberpunk//hack, essas coisas [sim, eu sei o quão cringe é, mas é divertido]).
  Automações em ansible são bem vindas sempre, desde que bem implementadas.
  O projeto foi feito para ser utilizado em um ambiente liveboot, CONTÚDO tenho planos para fazer uma automação em VM também.

## TODO:
  - [x] Instalador minimal
  - [ ] Manager de dotfiles
  - [ ] Post install

## Arquivos principais:
### 1. `main.yml`
  Esse é o coração do projeto, é com ele que se roda o projeto por completo.
  - **NoDe** Instalação do sistema mínimo
  - **reseta** reinicializa o sistema (automação para VMs (WIP))
  - **post-install** configuração pós-instalação (DE/TWM/Dotfiles (WIP))

### 2. `ansible.cfg`
  Esse é o cérebro do projeto, nele temos
  - inventário: todas as configurações básicas do projeto
  - diretório temporário: o temp pro ansible
  - verificação de chaves ssh (para VMs)

### 3. `Inventario.yml`
  Esse é nosso sistema de inventário, feito majoritáriamente pra VMs

### 4. `group_vars/all/config.yml`
  Nossas variáveis globais

## Roles
### 1. **setup**
  Gere as permissões de execução dos shell scripts

### 2. **particionamento**
  Gere a parte de particionamento do projeto

### 3. **sistema**
  Gere a instalação de sistema base e pacotes extras selecionados pelo usuário.

### 4. **chroot**
  Gere as configurações de chroot.

#### TODOs
##### 1. **dotfiles**
##### 2. **limpeza**
##### 3. backup.
#
O sistema detecta automaticamente se o boot é UEFI ou BIOS:

```yaml
- name: checar modo de boot (uefi, mbr etc)
  ansible.builtin.stat:
    path: "/sys/firmware/efi/fw_platform_size"
  register: efi_size
```

O sistema tem 3 módulos principais, com o único funcional até agora sendo o `NoDe`

# Tecnologias Utilizadas

- **Ansible**: Orquestração e automação
- **Shell Scripts**: Scripts auxiliares de configuração
- **YAML**: Configuração e definição de playbooks
- **Arch Linux**: Sistema operacional alvo[^1]

# Configuração e Uso

## Pré-requisitos
  
  1. Ansible instalado no sistema controlador
  2. Acesso à wifi dentro do live boot
  3. pacotes git e ansible.

## Instalação:
  Dentro do seu liveboot
  1. configure sua WIFI com `iwctl`
  2. rode `pacman -S git ansible`
  3. rode `git clone https://github.com/Dexmachi/Dextall`
  4. rode `cd Dextall`
  5. rode `ansible-playbook main.yaml --tags "NoDe"`
  6. siga as instruções entregues à você pelos scripts

# Estado do Projeto

O projeto está em desenvolvimento ativo com 17 commits realizados, sendo 100% escrito em Shell Script com automação Ansible. O repositório não possui releases publicados nem documentação README tradicional[^1].

<div style="text-align: center">⁂</div>

[^1]: https://github.com/Dexmachi/Dextall.git

[^2]: https://github.com/Dexmachi/Dextall

[^3]: https://github.com/Dexmachi/Dextall/blob/main/ATENÇÃO.md

[^4]: https://github.com/Dexmachi/Dextall/blob/main/main.yaml

[^5]: https://github.com/Dexmachi/Dextall/blob/main/ansible.cfg

[^6]: https://github.com/Dexmachi/Dextall/blob/main/Inventario.yml

[^7]: https://github.com/Dexmachi/Dextall/tree/main/roles

[^8]: https://github.com/Dexmachi/Dextall/blob/main/roles/setup/tasks/main.yml

[^9]: https://github.com/Dexmachi/Dextall/blob/main/group_vars/all/config.yml

[^10]: https://github.com/Dexmachi/Dextall/tree/main/roles/sistema
