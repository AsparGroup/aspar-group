# NOTORIA V1 — Monorepo Scaffold

Plateforme B2B de génération vidéo avatar **asynchrone** (pas de live).

## Objectif
Ce dépôt fournit une base mono-repo prête pour implémenter:
- `orchestrator-api` (API + orchestration des jobs + service registry),
- workers GPU séparés (`tts`, `video`, `lipsync`, `enhance`, `qa`),
- composants partagés (`shared`),
- stack d'infra locale (`postgres`, `redis`, `minio`) via Docker Compose.

## Arborescence

```text
.
├── AGENTS.md
├── README.md
├── .env.example
├── docs/
│   └── openapi/
│       ├── orchestrator-api.openapi.yaml
│       └── worker.openapi.yaml
├── infra/
│   └── docker-compose.yml
├── scripts/
│   ├── bootstrap.sh
│   └── healthcheck.sh
├── shared/
│   ├── schemas/
│   │   ├── common.py
│   │   ├── jobs.py
│   │   └── service_registry.py
│   └── utils/
│       ├── ids.py
│       └── logging.py
├── services/
│   ├── orchestrator-api/
│   │   ├── alembic/
│   │   ├── alembic.ini
│   │   ├── app/
│   │   │   ├── db.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── worker-tts/
│   ├── worker-video/
│   ├── worker-lipsync/
│   ├── worker-enhance/
│   └── worker-qa/
└── tests/
    ├── test_common_schemas.py
    ├── test_ids.py
    └── test_registry_schemas.py
```

## Service Registry (dans orchestrator-api)
Le registry est persisté en **Postgres** via table `registry_services`.

Champs:
- `service_name`
- `category` (`video|tts|lipsync|enhance|qa`)
- `type` (`local|saas`)
- `base_url`
- `auth_type`
- `auth_secret_ref`
- `endpoints` (JSON)
- `limits` (JSON)
- `fallback_service`
- `enabled`

Endpoints:
- `GET /registry/services`
- `POST /registry/services`
- `PATCH /registry/services/{id}`

Migration + seed Alembic:
- migration `20260225_0001` crée la table et seed:
  - locaux: `ltx_local`, `xtts_local`, `wav2lip_local`, `enhance_local`, `qa_local`
  - placeholders cloud fallback: `ltx_cloud`, `xtts_cloud`, `wav2lip_cloud`, `enhance_cloud`, `qa_cloud`

## Services

### orchestrator-api (FastAPI)
- `POST /v1/jobs` : crée un job asynchrone et retourne un `job_id` UUID v4.
- `GET /v1/jobs/{job_id}` : retourne l'état du job.
- `POST /v1/jobs/{job_id}/retry` : remet le job en `queued`.
- `GET /registry/services`, `POST /registry/services`, `PATCH /registry/services/{id}`.
- `GET /healthz` et `GET /metrics`.

### workers (stubs FastAPI)
Services stub séparés:

### Template worker générique
Un template partagé (`shared/worker/template.py`) est réutilisé par tous les workers.
Fonctionnalités incluses:
- téléchargement d'inputs depuis MinIO (si `params.input_uris` est fourni),
- production d'un output local (`output.json`),
- upload vers bucket `notoria`,
- génération d'URL presignée MinIO renvoyée dans `outputs.presigned_url`,
- logging structuré JSON + timings (`duration_ms`) et métriques Prometheus.

- `worker-tts`
- `worker-video`
- `worker-lipsync`
- `worker-enhance`
- `worker-qa`

Chaque worker (template générique FastAPI) expose:
- `GET /health`
- `POST /generate` (reçoit `JobRequest`, renvoie `JobResult`)
- `POST /status` (optionnel)
- `GET /metrics`


### worker-tts (implémentation stub basée template)
- Endpoint `POST /generate` attend `JobRequest` avec `script` + `params.voice_id`.
- Génère un fichier `voice.wav` local puis upload dans MinIO bucket `notoria`.
- Retourne `outputs.presigned_url` vers l'objet uploadé.
- `USE_FAKE_TTS=true` (par défaut) pour CI/tests: backend léger qui génère un WAV de silence.
- TODO: brancher un backend XTTS réel (sans téléchargement de modèle lourd dans ce scaffold).


### worker-video (implémentation stub basée template)
- Endpoint `POST /generate` attend `JobRequest` avec `params.prompt` (ou fallback `script`) et supporte `params.image_url` (optionnel), `params.duration`, `params.aspect`.
- Génère un fichier `broll.mp4` local puis upload dans MinIO bucket `notoria`.
- Retourne `outputs.presigned_url` vers l'objet uploadé.
- `USE_FAKE_VIDEO=true` (par défaut) pour CI/tests: backend léger qui génère un MP4 factice.
- `CUDA_VISIBLE_DEVICES` configurable via env pour préparer l'intégration GPU.
- TODO: brancher un backend LTX-Video réel (image-to-video) sans téléchargement de modèle lourd dans ce scaffold.

### worker-lipsync (implémentation stub basée template)
- Endpoint `POST /generate` attend `JobRequest` avec `params.avatar_base_uri` et `params.voice_uri`.
- Génère un fichier `avatar_lipsynced.mp4` local puis upload dans MinIO bucket `notoria`.
- Retourne `outputs.presigned_url` vers l'objet uploadé.
- Expose des métriques placeholder dans `metrics`: `lipsync_score`, `av_drift_ms`.
- `USE_FAKE_LIPSYNC=true` (par défaut) pour CI/tests.
- TODO: brancher un backend Wav2Lip réel sans téléchargement de modèle lourd dans ce scaffold.

### worker-enhance (implémentation stub basée template)
- Endpoint `POST /generate` attend `JobRequest` avec `params.video_uri`.
- Paramètres pipeline supportés: `params.enable_upscale` (Real-ESRGAN optionnel) et `params.enable_face_restore` (GFPGAN optionnel).
- Génère un fichier `enhanced.mp4` local puis upload dans MinIO bucket `notoria`.
- Retourne `outputs.presigned_url` vers l'objet uploadé.
- `USE_FAKE_ENHANCE=true` (par défaut) pour CI/tests.
- TODO: brancher le pipeline réel Real-ESRGAN/GFPGAN sans téléchargement de modèle lourd dans ce scaffold.

### worker-qa (implémentation stub basée template)
- Endpoint `POST /generate` attend `JobRequest` avec `params.final_cut_uri` et accepte des métriques optionnelles `params.av_drift_ms`, `params.lipsync_score`.
- Produit `qa_report.json` + `outputs.qa_passed`.
- Règles V1:
  - `av_drift_ms <= 50`
  - `lipsync_score >= lipsync_threshold`
  - `freeze_frame_detected == false`
  - `blink_rate` dans une plage placeholder (`blink_rate_min`, `blink_rate_max`)
- En échec, renvoie `errors` et `outputs.recommended_step_to_retry` (`lipsync`/`video`/`tts`).
- `USE_FAKE_QA=true` (par défaut) pour CI/tests.

## Infra locale (docker-compose)
`infra/docker-compose.yml` démarre:
- `postgres`
- `redis`
- `minio`
- `minio-init`
- `orchestrator-api` (avec `alembic upgrade head` au démarrage)
- `worker-tts`, `worker-video`, `worker-lipsync`, `worker-enhance`, `worker-qa`

## Démarrage rapide

```bash
cp .env.example .env
bash scripts/bootstrap.sh
bash scripts/healthcheck.sh
```

URLs utiles:
- Orchestrator docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001

## Conventions clés
- Un `job_id` unique par commande.
- Logs JSON structurés.
- Métriques Prometheus sur `/metrics`.
- Contrats d'API dans `docs/openapi/`.

## Tests
Exemples de checks locaux:

```bash
python -m py_compile services/orchestrator-api/app/main.py services/orchestrator-api/app/db.py services/orchestrator-api/app/models.py services/worker-tts/app/main.py services/worker-video/app/main.py services/worker-lipsync/app/main.py services/worker-enhance/app/main.py services/worker-qa/app/main.py shared/worker/template.py shared/schemas/common.py shared/schemas/jobs.py shared/schemas/service_registry.py shared/utils/ids.py shared/utils/logging.py tests/test_common_schemas.py tests/test_ids.py tests/test_registry_schemas.py tests/test_worker_template.py tests/test_worker_tts.py tests/test_worker_video.py tests/test_worker_lipsync.py tests/test_worker_enhance.py tests/test_worker_qa.py tests/test_orchestrator_pipeline.py
python -m unittest discover -s tests -p 'test_*.py'
```


## Pipeline orchestrator (V1)
Étapes exécutées par l'orchestrator:
1. `script_agent` (LLM stub) -> `spoken_script` + `timing_map`
2. `tts` -> `voice.wav`
3. `video` -> `avatar_base.mp4`
4. `lipsync` -> `avatar_lipsynced.mp4`
5. `enhance` -> `enhanced.mp4`
6. `qa` -> pass/fail + report
7. `delivery` -> URLs finales des assets

### Routing services
- Résolution des workers via Service Registry par `category` (`tts|video|lipsync|enhance|qa`).
- Vérification `GET /health` avant dispatch worker.
- Dispatch `POST /generate`.
- Fallback vers `fallback_service` en cas de timeout/erreur 5xx.
- Retries par step: `max 2` (configurable via `ORCHESTRATOR_MAX_RETRIES`).


## n8n intake webhook
Endpoint: `POST /webhooks/n8n/order_created`

Payload minimal:
```json
{
  "customer_id": "cust_123",
  "avatar_id": "avatar_fr_01",
  "script": "Bonjour, ceci est votre vidéo personnalisée.",
  "language": "fr",
  "format": "mp4",
  "plan": "pro"
}
```

Réponse:
```json
{
  "job_id": "<uuid>",
  "status_url": "/v1/jobs/<uuid>"
}
```

Exemple workflow n8n: `docs/n8n/workflow.order_created.json`
- reçoit formulaire
- appelle le webhook orchestrator
- notifie Slack/Email avec `job_id`
