# Rugby Stats Expert V8 — prêt pour un premier déploiement de test

## Ce qui est inclus
Serveur MCP Python accessible sur `/mcp`, outils de recherche/analyses sur CSV autorisé, explorateur **métadonnées uniquement** du dépôt Rugby-Data, Dockerfile et `render.yaml`. Le CSV fourni ne contient **aucune donnée de joueur**. Aucune source de statistiques officielles n’est synchronisée.

## Mise en ligne sans terminal (GitHub + Render)
1. Créer un compte sur https://github.com puis un dépôt `rugby-stats-expert` (privé recommandé pendant les tests).
2. Extraire ce ZIP. Dans le dépôt, **Add file → Upload files** puis envoyer le contenu du dossier `rugby_stats_expert_v8` (les fichiers à la racine du dépôt, y compris `Dockerfile`, `render.yaml`, `server.py`, `requirements.txt`, `open_rugby.py`, `data/players.csv`). Les dossiers doivent garder leur structure.
3. Créer un compte https://dashboard.render.com ; **New → Web Service**, connecter le dépôt GitHub. Choisir **Docker**, instance **Free** (si proposée), et lancer **Deploy**. Render peut aussi détecter le `render.yaml` via **New → Blueprint**.
4. Une fois déployé, récupérer l’URL HTTPS `https://NOM.onrender.com/mcp`. Vérifier le serveur avec un client MCP compatible, puis ajouter l’URL dans ChatGPT **sur le web** si le compte dispose de l’option d’ajout de serveur MCP personnalisé.
5. Tester les outils `competitions` et `external_source_status`. Le premier doit annoncer `records_loaded: 0` tant qu’aucun CSV autorisé n’a été importé.

## Limites et précautions
- Les serveurs gratuits Render peuvent s’endormir après inactivité ; pas de garantie de disponibilité pour une application publique.
- L’accès public au dépôt Rugby-Data n’autorise pas nécessairement la redistribution des statistiques. Ce connecteur ne télécharge pas de matchs dans la base locale.
- Serveur **lecture seule**, sans compte utilisateur ni contrôle de quota : prototype de test, **pas** un lancement public de production.
- L’interface `web/index.html` est locale et n’est pas encore une interface intégrée ChatGPT Apps SDK.
- Ne pas inclure de secrets ni de données sous licence non autorisée dans GitHub.

## Test local
`pip install -r requirements.txt` puis `python server.py` (serveur MCP sur `http://localhost:10000/mcp`).
`python -m unittest discover -s tests` pour exécuter les tests hérités de la V7.
