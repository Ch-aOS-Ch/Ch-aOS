## Contributing to Ch-aronte

_ANY_ help is welcomed!
Be that in the form of issues, critiques about documentation, code or ideas!

Please just be sure to follow these steps:
1. Be sure to write your changes into an <your-name>-<feature> branch.
2. Do use python, rust, C, whatever language, as long as you can 1: integrate it SEAMLESSLY into the chaos CLI helper and 2: it does not break compatibility with future Ch-imera integration (this means: make everything truly declarative).
3. In case of python usage, try to stick only to passlib+omegaconf+pyinfra. All other dependencies MUST be documented.
4. All code must be properly commented and documented.
5. All additions to the Ch-obolos plugin system must have proper documentation in the README.md file inside the Ch-obolos folder, also they NEED to be fully translatable to nixlang, in order to facilitate future compatibility with Ch-imera.
  5.1. Avoid using hardcoded paths, use variables instead.
  5.2. Be sure to keep the code modular and reusable, this means adding _new_ roles instead of adding code to existing ones, follow regular conventions AND base yourself off of the roles/README.md documentation.
  5.3. Be sure to make the probable new changes or additions to Ch-obolos FULLY declarative, avoid imperative code as much as possible, trust me, I know it's hard, but this is needed for the Ch-imera compatibility.

*you _can_ use things other than python for necessary evils, but try not to, as most languages are kind of bad at configuration management when comparing both, also, the CLI is the only thing that gets dependencies, all other code must be built without said dependencies, unless absolutely necessary.
