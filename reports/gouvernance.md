# Gouvernance et registre des risques
Propriétaire académique : équipe ISDIA3, ENSAF. Validation finale : étudiant et encadrant. Usage : assistance pédagogique, sans exécution de code ni accès à des fichiers utilisateurs.

| Risque | Conséquence | Protection | Test / limite |
|---|---|---|---|
| Hallucination | apprentissage erroné, code faux | prompt documentaire, abstention, revue des sources | citations réelles mais fidélité non prouvée ; revue humaine requise |
| Retrieval non pertinent | réponse plausible sans preuve | seuil calibré dev, liste de sources visible | recall FR/EN et erreurs détaillées ; score ne prouve pas suffisance |
| Injection documentaire | modification des instructions | corpus sélectionné et hashé, contexte non fiable, motifs suspects | fixture isolée ; détection lexicale non exhaustive |
| Injection utilisateur | fuite d'instructions | consigne système, refus motifs explicites | reformulations adversariales restent possibles |
| Contradiction | réponse incohérente | consigne d'abstention au modèle | scénario synthétique isolé ; pas de détecteur sémantique garanti |
| Document incomplet | réponse inventée | refus contexte absent/faible | contexte partiel avec score élevé reste difficile |
| Ancienneté | conseil dépassé | version affichée 3.11.18, refus explicite versions 3.12+ | expressions de versions non reconnues possibles |
| Corpus hétérogène | historique daté dans FAQ | conserver version et provenance ; ne pas prétendre actualité | la FAQ fournie contient des formulations historiques sur Python 2 |
| Données personnelles | exposition locale ou externe | logs sans question/réponse, pas d'authentification exposée à Internet | servir sur 127.0.0.1 ; audit manuel avant tout hébergement |
| Secrets | clé publiée | .env ignoré, .env.example vide, aucune clé dans logs | revue Git avant push ; pas de valeur sensible dans les tests |
| API externe | coût, indisponibilité, dépendance | désactivée par défaut, clé/modèle explicites, timeout, 503 | aucun appel réel Mistral/Gemini effectué ici |
| Dépendances | vulnérabilités | versions explicites, audit CI et campagne locale | audit daté, ne garantit pas l'absence de nouvelles vulnérabilités |
| Empoisonnement d'index | récupération altérée | SHA256 index, chunks et corpus | corruption refusée ; hashes à protéger dans Git |
| ZIP malveillant | écriture hors dossier, bombe | pas d'extractall, chemins validés, symlinks/doublons refusés, limites volumes | tests chemins, symlink, encodage, CRC et taille |
| Multilingue | service moins bon en français | métriques séparées, transparence | corpus anglais, modèle multilingue insuffisant sur certains termes |

## Droits et provenance
L'archive est celle fournie par l'utilisateur ; son origine téléchargée exacte n'est pas prouvée par le nom du fichier. SHA256 : voir configs/corpus.json. La structure, les titres et les fichiers internes identifient Python 3.11.18 ; aucune attestation cryptographique de l'éditeur n'a été fournie. Les documents et mentions de droits sont préservés à l'identique.
La documentation relève de la licence PSF ; les exemples de code sont proposés sous double licence PSF et Zero-Clause BSD selon les textes embarqués. Les textes complets sont dans legal/license.txt et legal/copyright.txt. Source de référence à consulter : https://docs.python.org/3.11/license.html. Les licences ne sont pas indexées et ne constituent pas de nouvelles sources de réponse.
Modèles : voir leurs cartes et licences aux révisions inscrites dans reports/model_files.json. Ne pas substituer un autre modèle sans reconstruire l'index et réévaluer.

## Promotion et exploitation
1. Modifier code/configuration via branche et PR ; conserver corpus officiel distinct des fixtures.
2. Passer tests, intégrité, recherche rejouée et audit de dépendances.
3. Si encodeur, corpus, prompt ou LLM change : reconstruire, campagne réelle, revue des réponses et risques.
4. Encadrant/mainteneur examine les résultats et autorise la nouvelle baseline ; conserver l'ancienne version pour retour arrière.
5. Déployer localement, vérifier /health puis /ask avec une vraie question, et surveiller erreurs et abstentions.
6. En cas de dérive : revenir au commit et artefacts précédents ; ne pas abaisser les seuils sans analyse.

## Vulnérabilité transitive résiduelle identifiée
L'audit de la fermeture des dépendances de l'environnement exécuté a trouvé DiskCache 5.6.3 (CVE-2025-69872 / PYSEC-2026-2447), sans correctif publié dans l'avis consulté : un attaquant pouvant écrire dans le répertoire du cache peut injecter un objet pickle exécuté à sa lecture. Cette dépendance appartient à l'outillage DVC, pas au service FastAPI.
Mitigation appliquée : core.site_cache_dir pointe vers .dvc/private-cache ; scripts.secure_dvc crée ce répertoire sous le contrôle de l'utilisateur et vérifie propriétaire et mode 0700 sous Linux. Ces contrôles ont été exécutés ici. Ne jamais importer un cache non fiable. Sur Windows, vérifier des ACL réservées au compte utilisateur ; ce contrôle Windows n'a pas été exécuté. Un usage sur une machine partagée sans ces protections reste exclu. Le rapport d'audit n'est pas falsifié ni nettoyé pour masquer cet avis.
Msgpack, multidict et pip ont été mis à jour après l'audit transitif initial.
