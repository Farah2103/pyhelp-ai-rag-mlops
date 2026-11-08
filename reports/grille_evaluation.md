# Méthode de revue de génération
Les colonnes human_* à null signifient « non évalué », jamais zéro. Aucun juge LLM n'est utilisé pour annoncer une exactitude.
Revoir chaque ligne de generation.json à partir de reference_evidence ET des references effectivement données au modèle.
Exactitude : 0 faux, 1 partiel, 2 correct. Pertinence : 0 hors sujet, 1 incomplet, 2 utile. Fidélité : 0 inventé/contredit, 1 soutien partiel, 2 entièrement soutenu.
Langue : oui/non selon la langue de la question. Abstention positive : vérifier que la réponse était couverte par le contexte réellement fourni.
Pour une question négative, mesurer abstention correcte séparément de l'exactitude sur les questions répondables.
Une référence valide signifie seulement que son identifiant appartient au contexte. Cela ne prouve ni la fidélité ni l'exactitude.
Les questions proviennent du corpus ; le dev/test séparé limite l'ajustement au test mais ne constitue pas une validation externe indépendante.
La métrique Recall@k est un rappel de groupes de preuves : un groupe est retrouvé si au moins un chunk du bon document recouvre au moins 40 caractères (ou toute une preuve plus courte). Ce critère tolère les frontières et ne garantit pas la complétude sémantique. La précision des passages est calculée selon ce même recouvrement.

La revue livrée dans revue_generation.csv est effectuée par ChatGPT sur les sorties réelles et leurs extraits : elle est assistée par IA, non indépendante et non validée par un humain. Les notes normalisées sont la somme des notes divisée par deux fois le nombre de cas du sous-ensemble. Pour exactitude et pertinence, le dénominateur est l’ensemble des 32 questions répondables (une abstention correspond à un besoin non satisfait, pas à un énoncé faux). La fidélité et la langue sont agrégées seulement parmi les 28 réponses effectives à ces questions. Les négatifs sont étudiés séparément par leur comportement d’abstention. Aucune moyenne ne constitue une preuve de qualité généralisable.
