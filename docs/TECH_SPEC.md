# TECH_SPEC.md
**Project:** crypto‑shield  
**Owner:** AxentX – Product Security Team  
**Status:** Draft → Review → Approved → Implementation  

---  

## 1. Overview  

**crypto‑shield** is a SaaS platform that provides businesses with end‑to‑end crypto‑payment security and custody management. It mitigates operational, regulatory, and technical risks by:

| Capability | Description |
|------------|-------------|
| **Risk‑Engine** | Real‑time transaction scoring using ML models (vLLM) and rule‑based heuristics. |
| **Custody Vault** | Encrypted, multi‑signature hot/cold wallet management with hardware‑security‑module (HSM) integration. |
| **Compliance Layer** | AML/KYC checks, sanctions screening, audit‑trail generation. |
| **Developer API** | REST/GraphQL endpoints for payment initiation, status queries, and vault operations. |
| **Dashboard** | React SPA for ops teams to monitor risk scores, vault balances, and alerts. |

The service is built as a set of loosely‑coupled micro‑services deployed on Kubernetes, with a shared PostgreSQL data store and Redis cache. All components are containerised and versioned via Helm charts.

---  

## 2. Architecture Diagram  

```
+-------------------+      +-------------------+      +-------------------+
|   Front‑End SPA   | <--->|   API Gateway     | <--->|   Auth Service    |
+-------------------+      +-------------------+      +-------------------+
                                 |
          +----------------------+----------------------+
          |                      |                      |
+----------------+   +-------------------+   +-------------------+
| Risk Engine    |   | Custody Service   |   | Compliance Service|
| (vLLM + Rules) |   | (HSM, Multi‑sig)  |   | (AML/KYC)         |
+----------------+   +-------------------+   +-------------------+
          |                      |                      |
          +----------+-----------+-----------+----------+
                     |                       |
               +-----------+           +-----------+
               | PostgreSQL|           | Redis     |
               +-----------+           +-----------+
```

---  

## 3. Core Components  

| Service | Language / Runtime | Key Libraries | Responsibilities |
|---------|--------------------|---------------|------------------|
| **API Gateway** | Go (1.22) | `gin-gonic`, `jwt-go`, `go‑redis` | Request routing, auth, rate‑limiting, OpenAPI spec |
| **Auth Service** | Rust | `actix‑web`, `argon2`, `jsonwebtoken` | User & client credential management, MFA |
| **Risk Engine** | Python 3.11 | `vllm`, `pandas`, `scikit‑learn`, `fastapi` | Score transactions, model inference, rule engine |
| **Custody Service** | Go | `go‑ethereum`, `aws‑sdk-go` (KMS/HSM), `grpc` | Wallet creation, signing, hot/cold key rotation |
| **Compliance Service** | Node.js 20 | `axios`, `typeorm`, `open‑aml‑sdk` | Sanctions list lookup, KYC verification, audit log |
| **Dashboard** | React 18 + TypeScript | `mui`, `react‑query`, `recharts` | Ops UI, real‑time alerts, reporting |
| **Data Store** | PostgreSQL 15 | `pgcrypto` extension | Persistent entities (users, wallets, transactions, logs) |
| **Cache** | Redis 7 (cluster) | N/A | Session store, risk‑engine cache, rate‑limit counters |

---  

## 4. Data Model  

### 4.1 Entity‑Relationship Overview  

| Table | Primary Key | Important Columns | Relationships |
|-------|-------------|-------------------|----------------|
| `users` | `id` (UUID) | `email`, `hashed_pw`, `mfa_secret`, `role` | 1‑N `wallets`, 1‑N `api_keys` |
| `api_keys` | `key_id` (UUID) | `secret_hash`, `scopes`, `expires_at` | N‑1 `users` |
| `wallets` | `wallet_id` (UUID) | `address`, `type` (hot/cold), `status`, `hsm_id` | N‑1 `users` |
| `transactions` | `tx_id` (UUID) | `wallet_id`, `amount`, `currency`, `status`, `risk_score`, `created_at` | N‑1 `wallets` |
| `risk_rules` | `rule_id` (UUID) | `name`, `condition_json`, `action` | – |
| `compliance_logs` | `log_id` (UUID) | `tx_id`, `sanctions_match`, `kyc_status`, `details` | N‑1 `transactions` |
| `audit_events` | `event_id` (UUID) | `entity_type`, `entity_id`, `action`, `actor_id`, `timestamp` | – |

All UUIDs are version‑4. Sensitive fields are encrypted at rest using `pgcrypto` with a per‑tenant master key stored in the HSM.

### 4.2 Example JSON Payloads  

**Create Transaction (POST /v1/transactions)**  

```json
{
  "wallet_id": "c1d2e3f4-5678-90ab-cdef-1234567890ab",
  "amount": "0.75",
  "currency": "BTC",
  "destination_address": "bc1qxyz...",
  "metadata": { "order_id": "ORD-98765" }
}
```

**Risk Engine Response**  

```json
{
  "tx_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "risk_score": 0.87,
  "risk_level": "HIGH",
  "actions": ["BLOCK", "ALERT"]
}
```

---  

## 5. Key APIs / Interfaces  

All external APIs are versioned under `/v1/`. OpenAPI 3.1 spec is generated automatically from the Go/FastAPI annotations.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/auth/login` | None | Returns JWT access/refresh tokens |
| `POST` | `/v1/auth/mfa` | JWT (partial) | Verify MFA code |
| `POST` | `/v1/wallets` | JWT (admin/client) | Create a new wallet (hot/cold) |
| `GET`  | `/v1/wallets/{id}` | JWT | Retrieve wallet details |
| `POST` | `/v1/transactions` | JWT | Initiate a payment (risk‑engine invoked) |
| `GET`  | `/v1/transactions/{id}` | JWT | Query transaction status |
| `GET`  | `/v1/compliance/sanctions/{address}` | JWT | Run ad‑hoc sanctions check |
| `GET`  | `/v1/healthz` | None | Liveness/Readiness probe |

**Internal gRPC**  

- `CustodyService.SignTx(request) -> response` – used by the Risk Engine after a transaction is approved.  
- `RiskEngine.EvaluateTx(request) -> response` – called by API Gateway synchronously.

---  

## 6. Technology Stack  

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Container Runtime | Docker | 24.0 | Industry standard, CI/CD ready |
| Orchestration | Kubernetes | 1.28 | Autoscaling, multi‑region |
| Service Mesh | Istio | 1.20 | Zero‑trust mTLS, traffic policies |
| CI/CD | GitHub Actions + ArgoCD | – | Automated testing & progressive delivery |
| Observability | Prometheus + Grafana, Loki, OpenTelemetry | – | Metrics, logs, traces |
| Secrets Management | AWS KMS + HashiCorp Vault | – | Centralised key lifecycle |
| ML Inference | vLLM (GPU‑accelerated) | latest | Low‑latency scoring for risk engine |
| Structured Generation | SGLang (optional for future LLM‑driven compliance) | latest | Prototype integration |
| Database | PostgreSQL | 15 | ACID, JSONB for flexible metadata |
| Cache | Redis (cluster) | 7 | Low‑latency state |
| Front‑end | React 18 + TypeScript | – | Modern SPA, component library MUI |
| API Gateway | Go (Gin) | 1.22 | High performance, low overhead |
| Auth Service | Rust (Actix‑Web) | 1.0 | Memory safety, high concurrency |
| Compliance SDK | open‑aml‑sdk (Node) | latest | Up‑to‑date sanctions lists |

---  

## 7. Dependencies  

| Dependency | License | Source |
|------------|---------|--------|
| `vllm-project/vllm` | Apache‑2.0 | https://github.com/vllm-project/vllm |
| `sgl-project/sglang` | MIT | https://github.com/sgl-project/sglang |
| `go-ethereum` | GPL‑3.0 | https://github.com/ethereum/go-ethereum |
| `aws-sdk-go-v2` | Apache‑2.0 | https://github.com/aws/aws-sdk-go-v2 |
| `open-aml-sdk` | MIT | https://github.com/open-aml/open-aml-sdk |
| `pgcrypto` | PostgreSQL | Built‑in extension |

All third‑party libraries are pinned in `go.mod`, `Cargo.toml`, `requirements.txt`, and `package.json` with exact versions. CI runs `go mod tidy`, `cargo audit`, and `npm audit` on each PR.

---  

## 8. Deployment & Operations  

### 8.1 Helm Chart Structure  

```
crypto-shield/
├─ charts/
│  ├─ api-gateway/
│  ├─ auth-service/
│  ├─ risk-engine/
│  ├─ custody-service/
│  ├─ compliance-service/
│  └─ dashboard/
├─ values.yaml          # default config (dev)
└─ values-prod.yaml     # production overrides
```

Key configurable values:

- `replicaCount`
- `resources.limits/cpu/memory`
- `image.repository/tag`
- `service.type` (ClusterIP / LoadBalancer)
- `ingress.enabled` + TLS cert (cert‑manager)

### 8.2 CI/CD Pipeline  

1. **PR Validation** – unit tests, static analysis, Docker build, Helm lint.  
2. **Staging Deploy** – ArgoCD sync to `staging` namespace, run integration tests (contract, risk‑engine).  
3. **Canary Promotion** – 5 % traffic to new version, monitor `risk_score_latency` < 50 ms.  
4. **Full Rollout** – Gradual increase to 100 % if SLOs met.  

All pipelines publish SBOMs (CycloneDX) and push images to `public.ecr.aws/axentx/crypto-shield`.

### 8.3 Monitoring & Alerts  

| Metric | Alert Threshold |
|--------|-----------------|
| `risk_engine.latency_ms` | > 80 ms for 5 min |
| `custody_service.sign_errors` | > 3 per minute |
| `api_gateway.4xx_rate` | > 2 % of traffic |
| `postgresql.replication_lag_seconds` | > 5 s |
| `redis.memory_usage_percent` | > 85 % |

Alerts are routed to PagerDuty with severity based on risk level.

### 8.4 Disaster Recovery  

- **PostgreSQL** – Continuous PITR with WAL archiving, failover via Patroni.  
- **Redis** – Cluster with replica shards; automatic failover.  
- **Vault/HSM** – Keys are backed up to AWS KMS multi‑region; recovery scripts stored in encrypted S3 bucket.  

---  

## 9. Security Considerations  

| Area | Controls |
|------|----------|
| **Authentication** | JWT signed with RSA‑4096, short‑lived access tokens (5 min), refresh tokens (7 days) stored httpOnly Secure cookies. |
| **Authorization** | RBAC per‑client scopes (`payments:write`, `wallets:read`, `admin:*`). |
| **Transport** | mTLS between services (Istio), TLS 1.3 for external traffic (Let’s Encrypt). |
| **Data at Rest** | AES‑256‑GCM encryption for wallet private keys (HSM), `pgcrypto` for PII. |
| **Auditing** | Immutable audit log stored in append‑only table, exported nightly to S3 for SOC‑2. |
| **Compliance** | Built‑in AML/KYC checks, GDPR‑compliant data deletion endpoint (`/v1/users/{id}` → GDPR “right to be forgotten”). |
| **Pen‑Test** | Quarterly external penetration test, internal static analysis (`gosec`, `cargo-audit`). |

---  

## 10. Open Issues & Future Work  

| Issue | Owner | Target Milestone |
|-------|-------|------------------|
| Integration of **SGLang** for LLM‑driven compliance narrative generation | ML Team | Q4 2026 |
| Support for **ERC‑4337** account abstraction | Custody Team | Q2 2027 |
| Multi‑region active‑active deployment (AWS + GCP) | Infra Team | Q3 2027 |
| Add **Webhooks** for transaction status callbacks | Platform Team | Q1 2027 |

---  

## 11. Glossary  

- **HSM** – Hardware Security Module.  
- **AML** – Anti‑Money Laundering.  
- **KYC** – Know Your Customer.  
- **SLO** – Service Level Objective.  
- **SBOM** – Software Bill of Materials.  

---  

*Prepared by:* Senior Product/Engineering Lead – Crypto‑Shield  
*Date:* 2026‑06‑18  

---
