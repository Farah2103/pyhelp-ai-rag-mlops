# Quality gates et portée

| Gate | Critère | Justification | Exécution |
|---|---|---|---|
| Données | sélection exacte, CRC et SHA256 conformes, UTF-8 valide | intégrité obligatoire du corpus approuvé | verify + tests |
| Code et contrat | tous les tests essentiels passent | aucune régression de sécurité ZIP, citations ou contrat HTTP acceptée | pytest en CI |
| Recherche | Recall test au moins égal à baseline.json | aucune perte sur le benchmark réel figé (B) | replay FAISS de vrais vecteurs en CI |
| Dépendances CI | audit sans vulnérabilité connue non traitée | empêcher une livraison avec risques connus de la chaîne légère | pip-audit avec résolution transitive |
| Dépendances NLP | audit des versions directes, rapport distinct | anciennes versions détectées et mises à jour | audit direct, portée explicitement limitée |
| Promotion sémantique | aucun échec sur négatifs et réponses critiques correctes/fidèles vérifiées | une erreur sur immutabilité, exceptions ou environnement a des conséquences pédagogiques réelles | scripts.release_gate, séparé de la CI rapide |

Le rappel minimal vient de la baseline mesurée, pas d'un pourcentage arbitraire d'objectif métier. Un même seuil ne justifie pas le passage d'un système différent. Les commits des questions, du corpus et de l'encodeur sont contrôlés.
Les questions critiques concernent immutabilité, contrôle de flux, arguments mutables, exécution comme script, exceptions, venv et portée des variables. Elles doivent obtenir 2/2 en exactitude et fidélité lors d'une revue des sorties. Une abstention n'est pas notée « correcte » si elle empêche le service attendu sur une preuve disponible : elle doit être analysée.
La génération du petit modèle a effectivement montré des erreurs. Le gate de promotion reste donc bloquant pour cette configuration ; le projet peut être étudié, testé et exécuté localement. Ce blocage est un résultat de l'industrialisation, pas une erreur cachée dans le pipeline. La revue fournie est une revue assistée, à confirmer pour une soutenance ou une promotion.
La CI ne prétend pas valider la sémantique d'un LLM avec des mocks. Une campagne complète avec le LLM choisi et une revue des preuves restent nécessaires lorsque le modèle ou le prompt change.

L’audit transitif final de 168 distributions conserve un avis DiskCache sans version corrigée publiée. La mitigation et sa portée sont dans gouvernance.md ; les droits du cache privé sont vérifiés par scripts.secure_dvc sous Linux. Les caches reçus d’un tiers et les postes partagés non protégés restent exclus.
