# Dossier de reproductibilité

Les données d'entrée sont celles fournies : data/source/python-3.11.18-docs-text.zip. SHA256 exact dans configs/corpus.json. Les 499 fichiers TXT ont été décodés en audit ; seuls les neuf chemins approuvés sont indexés. Les mentions de droits sont dans legal/ sans indexation. data/raw conserve les octets originaux ; data/processed est reconstructible.

## Références immuables
- Embeddings : sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, révision e8f8c211226b894fcb81acc59f3b34ba3efd5f42.
- LLM expérimental : Qwen/Qwen2.5-0.5B-Instruct, révision 7ae557604adf67be50417f59c2c2f167def9a775.
- Configurations : A 400 caractères / 80 overlap / top-k 3 ; B 800 / 120 / 5.
- Prompt : configs/prompt.txt ; hash par run de génération MLflow.
- Manifestes de modèles : reports/model_files.json ; poids non inclus dans la livraison.
- Corpus, index et chunks : SHA256 dans inventory.json et artifacts/current/manifest.json.
- Sélection et seuil calibré : reports/selection.json ; dev uniquement.
- Baseline : configs/baseline.json, liée au hash des questions et à la révision embeddings.

## Reconstruction avec les dépendances corrigées
Exécuter depuis la racine du dépôt, dans un environnement Python 3.11 ou 3.12. Les commandes PowerShell d'installation sont dans README.md.

```powershell
python -m scripts.ingest data/source/python-3.11.18-docs-text.zip
python -m src.evaluation.campaign
python -m scripts.prepare_replay
python -m scripts.verify
python -m scripts.gates
python -m pytest tests -q
python -m dvc repro
python -m dvc status
```

DVC est configuré avec cache:false pour ces petits fichiers ; Git conserve les octets et les hashes SHA256 offrent un contrôle supplémentaire. dvc.lock conserve les empreintes de ses étapes. Aucun remote n'est supposé disponible. Le pipeline est réellement exécuté ; une incompatibilité de pathspec a été résolue par le pin 0.12.1.

## Génération locale gratuite, sans API
Après installation des dépendances, configurer ces variables ou .env :
```powershell
$env:PYHELP_PROVIDER="transformers"
$env:PYHELP_MODEL="Qwen/Qwen2.5-0.5B-Instruct"
$env:PYHELP_LLM_REVISION="7ae557604adf67be50417f59c2c2f167def9a775"
python -m src.evaluation.campaign --generation-only
python -m scripts.robustness
python -m scripts.demo_monitoring
```
Le téléchargement initial de ce modèle nécessite environ 1 Go de poids. Il est évalué comme une option limitée, pas recommandé comme modèle fiable. Le modèle Ollama proposé dans README est une autre configuration, à évaluer séparément. Le connecteur ne convertit pas automatiquement une désignation Ollama en référence Hugging Face.

## Environnement effectivement utilisé
reports/environment.json et environment_executed.freeze.txt décrivent l'environnement initial. Les fichiers environment_final.json et environment_final.freeze.txt décrivent les dépendances corrigées finales. Le freeze inclut des composants hérités de l'environnement de travail ; il sert de preuve, pas de fichier d'installation universel Windows. requirements.txt fixe les versions directes nécessaires. Les dépendances transitives ne constituent pas un lock universel à hashes multiplateforme ; en cas de reproduction stricte, conserver également une image ou un environnement résolu sur le poste cible.

Les expériences initiales utilisaient Torch 2.6 / Transformers 4.48 / Sentence Transformers 3.4. Après l'audit, la comparaison a été reconstruite avec les versions corrigées Torch 2.15 / Transformers 5.22 / Sentence Transformers 6.2 ; les résultats qualitatifs et le rappel de la baseline sont inchangés. Les campagnes de génération initiale et finale sont distinguées par fichiers et runs. Plusieurs campagnes se déroulent sur un hôte partagé : la latence n'est pas un benchmark matériel exclusif.

## Transport des expériences et du dépôt
Les runs MLflow sont inclus sous mlruns/ dans le ZIP de remise. Après extraction, lancer `python -m scripts.relocate_mlflow` pour adapter les URI d'artefacts. Le dépôt Git local est inclus, sans identité personnelle ni clé. Les poids, environnements virtuels et caches ne sont pas inclus. Le dépôt distant GitHub et les tests Windows nécessitent le poste ou le compte de l'étudiant.

## Non-régression et retour arrière
Le rejeu CI utilise les vrais vecteurs enregistrés et le vrai index, sans réencoder : il ne certifie pas un encodeur changé. Une modification de corpus, modèle ou prompt exige une campagne complète, une revue des erreurs et une décision explicite sur la baseline. Pour revenir en arrière, restaurer le commit Git et ses artefacts correspondants, puis lancer verify et gates. Le gate sémantique doit rester bloquant tant que des erreurs critiques subsistent.
