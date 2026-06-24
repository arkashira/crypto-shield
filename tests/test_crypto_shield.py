from crypto_shield import CryptoShield
import pytest

def test_provision_vault():
    crypto_shield = CryptoShield()
    requester_id = "requester-1"
    kms_key = "kms-key-1"
    vault_id = crypto_shield.provision_vault(requester_id, kms_key)
    assert vault_id.startswith("vault-")
    assert len(crypto_shield.vaults) == 1

def test_get_vault():
    crypto_shield = CryptoShield()
    requester_id = "requester-1"
    kms_key = "kms-key-1"
    vault_id = crypto_shield.provision_vault(requester_id, kms_key)
    vault = crypto_shield.get_vault(vault_id)
    assert vault["id"] == vault_id
    assert vault["kms_key"] == kms_key

def test_get_vault_not_found():
    crypto_shield = CryptoShield()
    with pytest.raises(ValueError):
        crypto_shield.get_vault("non-existent-vault")

def test_get_audit_log():
    crypto_shield = CryptoShield()
    requester_id = "requester-1"
    kms_key = "kms-key-1"
    vault_id = crypto_shield.provision_vault(requester_id, kms_key)
    audit_log = crypto_shield.get_audit_log()
    assert len(audit_log) == 1
    assert audit_log[0]["requester_id"] == requester_id
    assert audit_log[0]["vault_id"] == vault_id

def test_provision_vault_timeout():
    crypto_shield = CryptoShield()
    requester_id = "requester-1"
    kms_key = "kms-key-1"
    import time
    start_time = time.time()
    vault_id = crypto_shield.provision_vault(requester_id, kms_key)
    end_time = time.time()
    assert end_time - start_time < 5
