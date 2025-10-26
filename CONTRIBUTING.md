## Contributing to Ch-aronte

_ANY_ help is welcomed!
Be that in the form of issues, critiques about documentation, code or ideas!

Please just be sure to follow these steps:
1. Be sure to write your changes into an <your-name>-<feature> branch.
2. Do _not_ use python, rust, C, whatever language, only use bash and ansible.*, this allows for little to no dependencies when running the installer, and keeps the codebase simple.
3. Write all of your printed messages into lib/ui.sh in the form of an _variable_, that way we can easily translate the scripts. (For instance, `MSG_WELCOME="Welcome to Ch-aronte!"` and `MSG_WELCOME="Bem-vind@ ao Ch-aronte!"`).
4. All code must be properly commented and documented.
5. All additions to the Ch-obolos plugin system must have proper documentation in the README.md file inside the Ch-obolos folder, also they NEED to be fully translatable to nixlang, in order to facilitate future compatibility with Ch-imera.
  5.1. Avoid using ansible modules that are not already inside the main ansible installation, this is to avoid dependency hell.
  5.2. Avoid using shell commands that are not POSIX compliant, this is to facilitate future compatibility with other shells.
  5.3. Avoid using hardcoded paths, use variables instead.
  5.4. Be sure to keep the code modular and reusable, this means adding _new_ ansible roles instead of adding code to existing ones, follow regular ansible conventions AND base yourself off of the roles/README.md documentation.
  5.5. Be sure to make the probable new changes or additions to Ch-obolos FULLY declarative, avoid imperative code as much as possible, trust me, I know it's hard, but this is needed for the Ch-imera compatibility.

*you _can_ use PYTHON for necessary evils, but it should be used or called in an script.
