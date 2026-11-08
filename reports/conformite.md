# Matrice de conformité — Projet 1
Matrice établie avant développement. État final : chaîne locale exécutée ; résultats et limites dans execution.md ; promotion du petit LLM bloquée par les erreurs observées.

| Exigence PDF | Composant / livrable | Contrôle et preuve |
|---|---|---|
| 2.2.1 dépôt, README | dépôt Git local, README.md | git status, instructions PowerShell ; publication GitHub manuelle |
| 2.2.2, 11 reproductibilité | configs, scripts, environnement, manifestes SHA256 | reconstruction double identique, verify |
| 2.2.3 versionnement | Git + DVC local + empreintes | dvc status, git commit, release manifest |
| 2.2.4 expériences | src/evaluation/campaign.py, MLflow | runs A/B, paramètres, métriques, artefacts |
| 2.2.5-7, 8 tests et gates | tests/, CI, scripts/gates.py | pytest, validation, non-régression |
| 2.2.8 déploiement | FastAPI, interface HTML, PowerShell | /health, /ask, tests HTTP et smoke |
| 2.2.9, 9 monitoring | monitoring/events.py, summarize.py | démo normal/hors corpus/invalide/erreur |
| 2.2.10, 3.3.9 gouvernance | reports/gouvernance.md | fixtures injection/contradiction, analyse limites |
| 3.3.1 cadrage | README, rapport | usages étudiants Python FR/EN ; refus versions différentes |
| 3.3.2 documents | ingestion/pipeline.py, raw, inventaire | ZIP CRC, UTF-8, chemins sûrs, neuf SHA256 |
| 3.3.3 chunking, embeddings | configs A/B, Encoder | tailles, overlap, IDs stables, modèle figé |
| 3.3.4, 3.4 RAG unique | Retriever, Assistant | IndexFlatIP unique actif, références réellement récupérées |
| 3.3.5 limites | guard + prompt + JSON validé | faible score, ambiguïté, injection ; contradictions via LLM à évaluer |
| 3.3.6 comparaison | A 400/80/3 et B 800/120/5 | même corpus et modèle, deux index reconstruits isolés hors service |
| 3.3.7, 3.5 retrieval | jeu annoté et campaign | Recall@k par groupes de preuves, précision des passages, erreurs |
| 3.5 génération | campagne LLM et grille revue | exactitude/fidélité humaines ; proxys automatiques distingués |
| 3.5 robustesse | jeu hors corpus, ambigu et fixtures | abstention, injection, incomplet, contradiction |
| 3.5 performance/coût | temps monotone, psutil, tokens | moyenne/P95, erreurs, disponibilité observée, pas de coût fictif |
| 3.6 livrables | données, code, résultats, MLflow, CI | archive de livraison et rapport |
| 7 extensions | périmètre volontairement limité | pas d'agent, multi-index, fine-tuning, Kubernetes |
| 8 sécurité | ZIP, saisies, secrets, dépendances | tests, pip-audit documenté ; aucune garantie de sécurité totale |
| 10 rapport 8-12 pages | reports/rapport_technique.pdf | comptage et rendu visuel |
| 10 démonstration 2 min | reports/demo_2_minutes.md | scénario minuté ; vidéo à enregistrer par étudiant |
| 11 problème, droits, versions, mesure | README, legal, inventaire, méthodologie | textes licences hors index, provenance archive utilisateur |
