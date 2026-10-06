# STATE_ROUTER — pointeur unique vers le fichier maître ASPAR

Ce dépôt ne contient PAS le fichier maître du projet ASPAR. Il vit ailleurs, en un seul exemplaire, jamais dupliqué ici.

- **Fichier maître** : `ETAT_LIVE_ASPAR.md`
- **Emplacement réel** : Google Drive, dossier `01_BUSINESS`
- **Drive ID** : `1TBPbFeolSAyRBvE4WyqOnQiNh2oKdbqP`
- **Chemin local (lien symbolique, Mac de Majdi)** : `/Users/asparincaspar/odoo-sms-bridge/ETAT_LIVE_ASPAR.md` → pointe vers le fichier réel dans le dossier Google Drive Desktop synchronisé.

## Règle
**READ BEFORE WORK / LOCK BEFORE WRITE / REREAD BEFORE COMMIT / WRITE SAME FILE / UNLOCK / NEVER DUPLICATE.**

Avant toute action ASPAR importante, lire `ETAT_LIVE_ASPAR.md` en entier (via le lien local si Claude Code / Codex, via le Drive ID si ChatGPT). Après toute action réelle qui change l'état des choses, éditer ce même fichier directement, jamais créer de copie datée ni de fichier parallèle.

## Protocole anti-conflit obligatoire
Plusieurs exécutants peuvent lire en parallèle, mais un seul peut écrire à la fois.

Avant écriture :
1. Relire le fichier maître immédiatement avant modification.
2. Vérifier le bloc `LOCK_OWNER` / `LOCK_SINCE` / `REVISION` en tête du fichier.
3. Si un autre writer possède un lock actif, ne pas écraser : attendre ou basculer en lecture seule.
4. Poser son propre `LOCK_OWNER`, enregistrer, puis relire pour confirmer que le lock est visible.
5. Appliquer uniquement sa modification, incrémenter `REVISION`, mettre à jour `LAST_UPDATE` et `UPDATED_BY`.
6. Relire après écriture pour vérifier que le contenu attendu est présent et qu'aucune modification concurrente n'a été perdue.
7. Libérer le lock en vidant `LOCK_OWNER` et `LOCK_SINCE`.

Format attendu en tête de fichier :

```text
LAST_UPDATE: ISO-8601
UPDATED_BY: CHATGPT | CLAUDE_CODE | CODEX | WORKER_NAME
REVISION: entier croissant
LOCK_OWNER:
LOCK_SINCE:

ACTIVE_TASK:
OWNER:
STATUS:
CURRENT_STEP:
LAST_RESULT:
BLOCKERS:
NEXT_ACTION:
```

Google Drive Desktop est le mécanisme de synchronisation du fichier physique unique, mais il ne doit pas être utilisé comme substitut au verrouillage applicatif : la synchronisation peut avoir un léger délai. Toute écriture doit donc suivre le protocole ci-dessus.

## Rôle de ce dépôt GitHub
Ce dépôt (`AsparGroup/aspar-group`) porte la stratégie, l'architecture et le code (agent-os/langgraph, décisions ADR, positionnement par domaine). Il ne contient pas une deuxième copie de l'état opérationnel. `ETAT_LIVE_ASPAR.md` reste l'unique état vivant partagé.
