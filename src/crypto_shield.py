import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class Vault:
    id: str
    kms_key: str
    private_key: str

class CryptoShield:
    def __init__(self):
        self.vaults = {}
        self.audit_log = []

    def provision_vault(self, requester_id: str, kms_key: str) -> str:
        vault_id = f"vault-{len(self.vaults)}"
        private_key = "private-key-" + vault_id
        vault = Vault(vault_id, kms_key, private_key)
        self.vaults[vault_id] = vault
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "requester_id": requester_id,
            "vault_id": vault_id
        })
        return vault_id

    def get_vault(self, vault_id: str) -> Dict:
        vault = self.vaults.get(vault_id)
        if vault:
            return {
                "id": vault.id,
                "kms_key": vault.kms_key
            }
        else:
            raise ValueError("Vault not found")

    def get_audit_log(self) -> list:
        return self.audit_log
