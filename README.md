# PyHelp AI — Assistant documentaire Python 3.11.18
Projet 1 MLOps/LLMOps · ENSAF · ISDIA3 · 2026–2027

Assistant monolithique : neuf documents anglais → nettoyage conservateur → sections/chunks → Sentence Transformers multilingue → un index FAISS actif → contexte → LLM → JSON avec citations. Aucun agent, routing ou fine-tuning. Le HTML est servi par FastAPI.

## Ce qui est livré et ce qui reste à valider
Les résultats réels et limites sont dans reports/execution.md, comparison.csv, generation_summary.json et le rapport PDF. Les mocks de CI ne servent jamais à annoncer la qualité réelle. Le petit modèle CPU de la campagne n'est pas une garantie de qualité. Les références sont contrôlées structurellement ; leur présence ne prouve pas la fidélité. Les tests sous Windows, l'accès à Ollama/Mistral/Gemini et l'exécution GitHub Actions doivent être vérifiés dans leurs environnements respectifs.

## Installation PowerShell (Python 3.11 ou 3.12, 64 bits)
Prévoir environ 4 Go pour embeddings + API ; 8 Go ou plus avec un petit LLM local, selon modèle. Connexion initiale nécessaire pour les packages et modèles. Dans le dossier extrait :
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# CPU : évite les grandes dépendances CUDA sous Linux ; Windows supporté par PyTorch.
python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.verify
python -m pytest tests -q
python -m scripts.gates
```
Si la politique PowerShell bloque l'activation, utiliser directement `.\.venv\Scripts\python.exe` dans les commandes. Ne pas modifier la politique système.

## Choisir le modèle
Le choix est explicite dans `.env`. Les valeurs d'exemple ne sont pas des promesses de disponibilité ou de prix.

| Fournisseur | Réglages | Prérequis |
|---|---|---|
| Ollama (par défaut) | PYHELP_PROVIDER=ollama ; PYHELP_MODEL=qwen2.5:1.5b | Installer Ollama, lancer `ollama pull qwen2.5:1.5b`, conserver le serveur sur localhost |
| Mistral | PYHELP_PROVIDER=mistral ; MISTRAL_MODEL=modèle de votre compte | PYHELP_ALLOW_EXTERNAL=1 et MISTRAL_API_KEY ; vérifier coût/autorisation avant activation |
| Gemini | PYHELP_PROVIDER=gemini ; GEMINI_MODEL=modèle de votre compte | PYHELP_ALLOW_EXTERNAL=1 et GEMINI_API_KEY ; vérifier quota/coût avant activation |
| Transformers CPU (campagne ici) | PYHELP_PROVIDER=transformers ; PYHELP_MODEL=Qwen/Qwen2.5-0.5B-Instruct | PYHELP_LLM_REVISION=7ae557604adf67be50417f59c2c2f167def9a775 ; téléchargement gratuit des poids |

Les clés ne sont jamais nécessaires aux tests CI. Aucun appel externe payant n'a été réalisé pour construire les livrables. Pour les API, question et contexte sont envoyés au fournisseur ; obtenir l'accord approprié avant d'y transmettre des données personnelles.

## Lancer l'application
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```
Ouvrir http://127.0.0.1:8000 (interface) ou http://127.0.0.1:8000/docs (OpenAPI).
L'index livré permet de démarrer sans le reconstruire. Le modèle d'embeddings est téléchargé au premier appel. `/health` indique la vie du service et la présence des fichiers ; il ne vérifie pas la disponibilité du LLM.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$body = @{ question = "How do I create a virtual environment using venv?" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/ask -Method Post -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
```
Réponse : `answer`, `references` (chunk/document, section, version, texte, positions), `status`, `reason`, `latency_ms`, `retrieved_chunks`. Une entrée invalide donne 422 ; un moteur indisponible donne 503. Une insuffisance documentaire donne 200 avec `status=abstention`.

## Reproduire les données et les expériences
L'archive fournie est conservée sous data/source/ ; seuls les neuf fichiers configurés sont indexés. legal/ contient les licences, hors corpus. Les poids ne sont pas inclus ; leur référence immuable et leurs empreintes figurent dans reports/model_files.json.
```powershell
python -m scripts.ingest data/source/python-3.11.18-docs-text.zip
python -m src.evaluation.campaign
python -m scripts.prepare_replay
python -m scripts.gates
# Avec un LLM réellement disponible, après avoir chargé les variables .env :
python -m src.evaluation.campaign --generation-only
# Pipeline complet :
.\scripts\reproduce.ps1
# DVC orchestre la reconstruction et enregistre les empreintes :
python -m scripts.secure_dvc
python -m dvc repro
```
A et B sont des artefacts d'expériences isolés. Le service charge uniquement artifacts/current/index.faiss. La sélection utilise le dev, jamais le test. Le seuil d'abstention est calibré sur dev et sauvegardé dans le manifeste actif. Les valeurs initiales ne constituent pas un optimum.

## MLflow
```powershell
# Installer l'interface complète si nécessaire ; mlflow-skinny assure déjà le suivi des runs.
python -m pip install mlflow==2.20.3
python -m mlflow ui --backend-store-uri ./mlruns --host 127.0.0.1 --port 5000
```
Les runs livrés sont sous mlruns/ dans l'archive complète ; ils ne doivent pas être poussés automatiquement dans Git. Les chemins absolus d'origine y sont réécrits pour l'emplacement de livraison via scripts/relocate_mlflow.py. Exécuter ce script après extraction avant d'ouvrir les artefacts.

## Tests et promotion
```powershell
python -m scripts.verify
python -m pytest tests -q
python -m scripts.gates
python -m pip_audit -r requirements-ci.txt --progress-spinner off
```
La CI rejoue de vrais vecteurs de requêtes préenregistrés contre le vrai index sans télécharger de gros modèle. Elle protège les artefacts et la recherche FAISS ; elle ne valide pas un changement d'encodeur ni la génération. Toute modification de ces composants impose une campagne complète et une revue de la génération. La baseline n'est pas un objectif métier de précision : aucune perte de rappel n'est acceptée sur le petit benchmark figé. Toute nouvelle baseline doit faire l'objet d'une revue humaine dans la PR.

## Monitoring
```powershell
python -m scripts.demo_monitoring
python -m monitoring.summarize monitoring/demo_requests.jsonl
```
La démonstration utilise de vrais appels à l'assistant pour normal/hors corpus ; seule l'erreur 503 est injectée dans le script. Les logs contiennent identifiant, statut, durée, nombre de chunks et RSS, sans texte utilisateur ni clés. Les abstentions sont identifiées par request_id. Rotation et rétention à ajouter pour un usage durable : proposition 7 jours, accès local seulement. La disponibilité observée pendant quelques essais n'est pas un SLA.

## Livraison GitHub
Un dépôt Git local est inclus. Sans connexion GitHub autorisée, aucun dépôt distant n'est créé.
```powershell
git status
git remote add origin https://github.com/VOTRE_COMPTE/pyhelp-ai-rag-mlops.git
git push -u origin main
```
Conserver `.env`, models/, mlruns/ et journaux de requêtes hors Git. Lire reports/reproductibilite.md, reports/gouvernance.md et reports/demo_2_minutes.md avant la soutenance.

Choix du runtime : Python 3.10 est en fin de support depuis le 01/10/2026 (https://devguide.python.org/versions/). Les dépendances corrigées récentes nécessitent Python 3.11+. Le contenu documentaire ciblé reste 3.11.18. La compatibilité Windows et Python 3.11 est à vérifier localement ; les tests exécutés ici utilisent Linux/Python 3.12.

## Résultats de génération et revue
`reports/generation.json` contient les sorties réelles, leur texte brut, le contexte cité et les passages de référence attendus. `reports/revue_generation.csv` est une revue assistée par IA, explicitement non indépendante, à confirmer par l'étudiant. Les colonnes `human_*` restent null tant qu'aucun évaluateur humain ne les a remplies. Le gate `python -m scripts.release_gate` bloque une promotion si des réponses critiques sont erronées ou si les scénarios négatifs échouent ; son blocage observé est documenté.
Le rapport est reconstructible par `python -m scripts.generate_report`. Les figures sont générées par `python -m scripts.plot_reports` (matplotlib inclus).

Audit transitif : une vulnérabilité DiskCache sans correctif publié subsiste dans l’outillage DVC (désérialisation pickle si un tiers peut écrire dans son cache). Le cache DVC est déplacé sous `.dvc/private-cache`, réservé à son propriétaire sous Linux par `scripts.secure_dvc`. Ne jamais réutiliser un cache reçu d’un tiers ; vérifier les ACL sur Windows. L’API ne charge pas DVC. Le résultat complet et cette limitation sont conservés dans reports/dependency_audit_runtime_closure_fixed.json et reports/gouvernance.md.

Arrêter puis redémarrer le service après reconstruction ou remplacement de l’index : le processus conserve son encodeur et son index en mémoire. Pour figer une expérience Ollama, conserver aussi `ollama list` et `ollama show --modelfile VOTRE_MODELE` dans les artefacts du run, car un nom de tag seul ne décrit pas des poids immuables.
