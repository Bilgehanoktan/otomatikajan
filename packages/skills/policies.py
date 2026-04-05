from dataclasses import dataclass


@dataclass
class SkillPolicy:
    allow_network: bool = False
    allow_filesystem: bool = True
    allow_shell: bool = False
    timeout_s: int = 120
    queue: str = "default"


DEFAULT_POLICIES = {
    "optimization": SkillPolicy(
        allow_network=False,
        allow_filesystem=False,
        allow_shell=False,
        timeout_s=20,
        queue="default",
    ),
    "debugging": SkillPolicy(
        allow_network=False,
        allow_filesystem=True,
        allow_shell=False,
        timeout_s=300,
        queue="critical",
    ),
    "file_search": SkillPolicy(
        allow_network=False,
        allow_filesystem=True,
        allow_shell=False,
        timeout_s=60,
        queue="default",
    ),
    "vault_memory": SkillPolicy(
        allow_network=False,
        allow_filesystem=True,
        allow_shell=False,
        timeout_s=30,
        queue="background",
    ),
    "skill_creator": SkillPolicy(
        allow_network=False,
        allow_filesystem=True,
        allow_shell=False,
        timeout_s=90,
        queue="background",
    ),
}
