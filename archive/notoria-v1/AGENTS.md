# AGENTS.md — NOTORIA V1

## Scope
Ces instructions s'appliquent à tout le dépôt.

## Objectif du repo
Construire **NOTORIA V1**: plateforme B2B de génération vidéo avatar asynchrone (pas de live), orientée workers asynchrones et outputs stockés en objet (MinIO/S3).

## Monorepo attendu
- `services/orchestrator-api`
- `services/worker-tts`
- `services/worker-video`
- `services/worker-lipsync`
- `services/worker-enhance`
- `services/worker-qa`
- `shared`
- `infra`

## Conventions de code
- Python 3.11+.
- API HTTP: FastAPI.
- Schémas: Pydantic.
- Logs structurés JSON (pas de logs texte libres en prod).
- Métriques Prometheus exposées sur `/metrics`.
- Typage explicite, fonctions courtes, constantes en MAJUSCULES.
- Nommage des files d'attente/events: `notoria.<domain>.<event>`.

## Règles architecture produit
- **Pas de live**: pipeline strictement asynchrone.
- Un `job_id` unique (UUID v4) par commande.
- Tous les outputs transitent via MinIO/S3 (pas de dépendance locale finale).
- Interactions inter-services idempotentes.
- Service Registry persistant (Postgres) + migrations Alembic obligatoires.

## Lancer local
```bash
cp .env.example .env
bash scripts/bootstrap.sh
bash scripts/healthcheck.sh
```

## Exécuter les tests
```bash
python -m py_compile services/orchestrator-api/app/main.py services/worker-tts/app/main.py services/worker-video/app/main.py services/worker-lipsync/app/main.py services/worker-enhance/app/main.py services/worker-qa/app/main.py
python -m unittest discover -s tests -p 'test_*.py'
```

## Ajouter un nouveau worker
1. Créer `services/worker-<name>/app/main.py` en réutilisant `shared.worker.create_worker_app`.
2. Implémenter un `processor(payload, inputs_dir, outputs_dir)`.
3. Définir les env vars dans `.env.example` et `infra/docker-compose.yml`.
4. Ajouter tests unitaires `tests/test_worker_<name>.py`.
5. Documenter le contrat d'entrée/sortie dans `README.md` et `docs/openapi/`.

## Règles sécurité / secrets
- Ne jamais committer de secrets.
- `auth_secret_ref` stocke une référence secret manager, pas le secret brut.
- Utiliser `.env.example` pour documenter les variables.

## Env flags fake (CI)
- `USE_FAKE_TTS`
- `USE_FAKE_VIDEO`
- `USE_FAKE_LIPSYNC`
- `USE_FAKE_ENHANCE`
- `USE_FAKE_QA`

Ces flags doivent rester disponibles pour exécuter les tests sans modèles lourds/GPU.
