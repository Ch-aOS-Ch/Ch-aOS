from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, cast

if TYPE_CHECKING:
    from typing import TypedDict

    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload

    class EphemeralEnvironment(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: list[int]


class KeyBackend(ABC):
    """
    Interface and template methods for sops key backends.
    """

    @property
    @abstractmethod
    def key_type(self) -> str:
        """Returns the type of key (e.g., 'pgp', 'age', 'vault')"""
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        protected_methods = [
            "list_keys",
            "handle_add",
            "handle_rem",
            "_generic_add",
            "_generic_rem",
        ]

        for method in protected_methods:
            if method in cls.__dict__:
                raise TypeError(
                    f"{method} is a protected method and must not be overridden."
                )

    def list_keys(
        self, sops_file_override: str
    ) -> tuple[set[str], list[str], list[str], list[str]]:
        """
        Lists all keys for this backend type found in the given SOPS configuration file.
        Args:
            sops_file_override (str): The path to the SOPS configuration file.
        Returns:
            tuple[set[str], list[str], list[str], list[str]]: A tuple containing
                - A set of all found keys for this backend type.
                - A list of warning messages.
                - A list of error messages.
        """
        from omegaconf import DictConfig, OmegaConf

        from ..utils import flatten

        warnings: list[str] = []
        errors: list[str] = []
        messages: list[str] = []

        key_type = self.key_type
        if key_type == "vault":
            key_type = "hc_vault"

        try:
            sops_config = OmegaConf.load(sops_file_override)
            sops_config = cast(DictConfig, sops_config)
            creation_rules = sops_config.get("creation_rules")
            if not creation_rules:
                messages.append(
                    "No 'creation_rules' found in the sops config. Nothing to do."
                )
                errors.append(
                    "No 'creation_rules' found in the sops config. Nothing to do."
                )
                return set(), warnings, errors, messages

            all_keys_in_config: set[str] = set()
            for rule in creation_rules:
                for key_group in rule.get("key_groups", []):
                    if (
                        key_type in key_group
                        and getattr(key_group, key_type) is not None
                    ):
                        all_keys_in_config.update(flatten(getattr(key_group, key_type)))

            if not all_keys_in_config:
                messages.append("No keys to be shown.")
                warnings.append("No keys to be shown.")

            return all_keys_in_config, warnings, errors, messages

        except Exception as e:
            errors.append(f"Failed to read sops config file: {e}")
            messages.append(f"Failed to read sops config file: {e}")
            return set(), warnings, errors, messages

    def handle_add(
        self, payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Handles the addition of new keys to the sops file regarding this key backend.
        Args:
            payload: The payload containing rotation options and context.
            sops_file_override: The path to the sops config file to modify.
            keys: The list of raw keys to add (e.g., public key strings, vault
                key identifiers, etc.).
        Returns:
            tuple[list[str], list[str]]: A tuple containing a list of informational messages and a list of error messages.
        """
        messages: list[str] = []
        errors: list[str] = []

        valids, val_msgs, val_errs = self.validate_for_add(keys, payload)
        messages.extend(val_msgs)
        errors.extend(val_errs)

        if valids:
            gen_msgs, gen_errs = self._generic_add(payload, sops_file_override, valids)
            messages.extend(gen_msgs)
            errors.extend(gen_errs)

        return messages, errors

    def handle_rem(
        self, payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Handles the removal of keys to the sops file regarding this key backend.
        """
        messages: list[str] = []
        errors: list[str] = []

        try:
            all_keys_in_config, _, list_errs, _ = self.list_keys(sops_file_override)
            if list_errs and "Failed to read" in list_errs[0]:
                return messages, list_errs

            valids, val_msgs, val_errs = self.validate_for_rem(keys, payload)
            messages.extend(val_msgs)
            errors.extend(val_errs)

            keys_to_remove: set[str] = set()
            for clean_key in valids:
                if clean_key in all_keys_in_config:
                    keys_to_remove.add(clean_key)
                else:
                    messages.append(
                        f"Key: {clean_key} not found in sops config. Skipping."
                    )

            if keys_to_remove:
                gen_msgs, gen_errs = self._generic_rem(
                    payload, sops_file_override, keys_to_remove
                )
                messages.extend(gen_msgs)
                errors.extend(gen_errs)

        except Exception as e:
            errors.append(f"Failed to update sops config file: {e}")

        return messages, errors

    def _generic_add(
        self, payload: SecretsRotatePayload, sops_file_override: str, valids: set[str]
    ) -> tuple[list[str], list[str]]:
        """
        Generic internal handler for adding validated keys to the config.
        """
        from omegaconf import DictConfig, OmegaConf

        from ..utils import flatten

        messages: list[str] = []
        errors: list[str] = []
        if not valids:
            messages.append("No valid keys. Returning.")
            return messages, errors

        try:
            create = payload.create
            config_data = OmegaConf.load(sops_file_override)
            config_data = cast(DictConfig, config_data)
            creation_rules = config_data.get("creation_rules", [])
            if not creation_rules:
                errors.append(
                    f"No 'creation_rules' found in {sops_file_override}. Cannot add keys."
                )
                return messages, errors

            rule_index = payload.index
            rules_to_process = creation_rules
            if rule_index is not None:
                if not (0 <= rule_index < len(creation_rules)):
                    errors.append(
                        f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                    )
                    return messages, errors
                rules_to_process = [creation_rules[rule_index]]

            if not create:
                total_added_keys = set()
                for rule in rules_to_process:
                    for key_group in rule.get("key_groups", []):
                        if (
                            self.key_type in key_group
                            and getattr(key_group, self.key_type) is not None
                        ):
                            existing_keys = list(
                                flatten(getattr(key_group, self.key_type))
                            )
                            keys_to_write = list(existing_keys)
                            current_keys_set = set(keys_to_write)
                            for key_to_add in valids:
                                if key_to_add not in current_keys_set:
                                    keys_to_write.append(key_to_add)
                                    total_added_keys.add(key_to_add)

                            setattr(key_group, self.key_type, keys_to_write)

                if not total_added_keys:
                    messages.append(
                        f"All provided keys are already in the relevant sops config '{self.key_type}' sections, or no '{self.key_type}' sections were found. No changes made."
                    )
                    return messages, errors

                OmegaConf.save(config_data, sops_file_override)
                messages.append(
                    f"Successfully updated sops config! New keys added: {list(total_added_keys)}"
                )
            else:
                for rule in rules_to_process:
                    new_group = OmegaConf.create({self.key_type: list(valids)})
                    if "key_groups" in rule and rule.key_groups is not None:
                        rule.key_groups.append(new_group)
                    else:
                        rule.key_groups = [new_group]

                OmegaConf.save(config_data, sops_file_override)
                messages.append(
                    f"Successfully updated sops config! New {self.key_type.upper()} key group created with keys: {list(valids)}"
                )

        except Exception as e:
            errors.append(
                f"Failed to load or save sops config file {sops_file_override}: {e}"
            )
        return messages, errors

    def _generic_rem(
        self,
        payload: SecretsRotatePayload,
        sops_file_override: str,
        keys_to_remove: set[str],
    ) -> tuple[list[str], list[str]]:
        """
        Generic internal handler for removing specific keys from the config.
        """
        from omegaconf import DictConfig, OmegaConf

        from ..utils import flatten

        messages: list[str] = []
        errors: list[str] = []
        rule_index = payload.index
        ikwid = payload.context.i_know_what_im_doing

        if not keys_to_remove:
            messages.append("No keys to remove. Exiting.")
            return messages, errors

        try:
            config_data = OmegaConf.load(sops_file_override)
            config_data = cast(DictConfig, config_data)
            creation_rules = config_data.get("creation_rules", [])
            if not creation_rules:
                errors.append(
                    "No 'creation_rules' found in the sops config. Nothing to do."
                )
                return messages, errors

            if not ikwid:
                msgs = ["Keys to remove:"]
                for key in keys_to_remove:
                    msgs.append(f"  {key}")
                messages.append("\n".join(msgs))

            rules_to_process = creation_rules
            if rule_index is not None:
                if not (0 <= rule_index < len(creation_rules)):
                    errors.append(
                        f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                    )
                    return messages, errors
                rules_to_process = [creation_rules[rule_index]]

            for rule in rules_to_process:
                if rule.get("key_groups"):
                    for i in range(len(rule.key_groups) - 1, -1, -1):
                        key_group = rule.key_groups[i]
                        if (
                            self.key_type in key_group
                            and getattr(key_group, self.key_type) is not None
                        ):
                            updated_keys = [
                                k
                                for k in flatten(getattr(key_group, self.key_type))
                                if k not in keys_to_remove
                            ]
                            if updated_keys:
                                setattr(key_group, self.key_type, updated_keys)
                            else:
                                delattr(key_group, self.key_type)

                        if not key_group:
                            del rule.key_groups[i]

            OmegaConf.save(config_data, sops_file_override)
            messages.append(
                f"Successfully updated sops config! Keys removed: {list(keys_to_remove)}"
            )

        except Exception as e:
            errors.append(f"Failed to update sops config file: {e}")
        return messages, errors

    @abstractmethod
    def validate_for_add(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        """
        Validates the format of keys for addition and processes any side effects (like fetching keys).
        Args:
            keys: List of raw keys from the user.
            payload: The payload context (contains e.g. pgp_server).
        Returns:
            tuple[set[str], list[str], list[str]]: (valid_keys, info_messages, error_messages)
        """
        raise NotImplementedError

    @abstractmethod
    def validate_for_rem(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        """
        Validates and sanitizes keys for removal.
        Args:
            keys: List of raw keys from the user.
            payload: The payload context.
        Returns:
            tuple[set[str], list[str], list[str]]: (clean_keys, info_messages, error_messages)
        """
        raise NotImplementedError

    @abstractmethod
    def prepare_export_content(
        self, payload: SecretsExportPayload
    ) -> tuple[str, list[str]]:
        """
        Prepares the content to export the secrets for this key backend.
        Args:
            payload: The payload containing all necessary information for the export.
        Returns:
            tuple[str, list[str]]: (content_to_export, info_messages)
        """
        raise NotImplementedError

    @abstractmethod
    def import_key(
        self, key_content: str, confirmed: bool = False
    ) -> tuple[list[str], list[str]]:
        """
        Imports a key into the backend if necessary (e.g., fetching from a server or vault).
        Args:
            key_content: The raw key content or identifier to import.
            confirmed: Whether the user has confirmed the import action (if applicable).
        Returns:
            tuple[list[str], list[str]]: info_messages, error_messages
        """
        raise NotImplementedError

    @abstractmethod
    def parse_key_content(
        self, key_content: str, provider_name: str
    ) -> tuple[str, str, str]:
        """
        Parses the raw key content to extract the relevant key identifiers (e.g., fingerprints).
        Args:
            key_content: The raw key content to parse.
            provider_name: The name of the provider (for error messages).
        Returns:
            tuple[str, str, str]: public_key_identifier, secret_key_identifier, sanitized_key_content
        """
        raise NotImplementedError

    @contextmanager
    @abstractmethod
    def ephemeral_key_context(
        self, pub_key: str, sec_key: str, parsed_key_content: str
    ) -> Iterator[EphemeralEnvironment]:
        """
        Sets up an ephemeral environment for the duration of a subprocess call
        """
        raise NotImplementedError
