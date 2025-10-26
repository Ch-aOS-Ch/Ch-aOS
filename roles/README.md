# How to Write an Ansible Role for Ch-aronte

Be sure to follow the project's [CONTRIBUTING.md](../CONTRIBUTING.md) guidelines when creating new Ansible roles.

Here are the steps to follow:

1.  **Create Role Structure:** Inside the `roles/` directory, create a new folder for your role (e.g., `your_role_name`). Inside this, create a `tasks/` folder, and then a `main.yml` (IT SHOULD BE USING .YML, NOT .YAML, THIS IS TO FACILITATE REGEX SEARCHING) file (e.g., `roles/your_role_name/tasks/main.yml`).

2.  **Write Ansible Tasks:** In `main.yml`, write your Ansible tasks. Focus on making them **declarative** (describe the desired state) and **idempotent** (can be run multiple times without issues). Always prefer Ansible modules over raw shell commands. Use variables for dynamic values.
like so:
![task](../imagens/2025-07-25T01-15-34Z_code.png)

> [!WARNING]
>
> Notice how, even in portuguese, the task is _self explained_, "you'll format root partition in root to the format in formato when formato exists and root exists", try to adhere to this method
---

3.  **Integrate with `main.yaml`:** Add your new role to the `roles` section of the `main.yaml` file in the project root. Make sure to assign a `tag` to your role matching its name. This tag is used for selective execution, which is an requirement.
like so:
![main](../imagens/2025-10-26T11-19-29Z_code.png)

> [!WARNING]
>
> This is to facilitate the usage of the ansible module, allowing for an easier CLI down the road

4.  **Test Your Role:** Thoroughly test your new role to ensure it works as expected, is idempotent, and handles different scenarios correctly.

**Key Principles for Role Development:**

*   **Declarativity:** Describe the *what*, not the *how*.
Notice this partitions Ch-obolo:
![Services Ch-obolo](../imagens/2025-10-26T11-21-50Z_code.png)
*   **Idempotency:** Safe to run repeatedly.
*   **Modularity:** Keep roles focused on a single purpose.
*   **Adherence to `CONTRIBUTING.md`:** Follow all general project guidelines.
