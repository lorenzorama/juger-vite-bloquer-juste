# Juger vite, bloquer juste

Code de la démo du talk IndabaX Madagascar 2026 : un agent mail (DeepAgents + Claude) attaqué par injection de prompt, puis protégé par **Jev**, un modèle « System 1 » de TypeSafe.

- **Config A** : l'agent est naïf, Jev observe seulement (mode shadow).
- **Config B** : Jev est enforced. Il met en quarantaine les mails qui parlent à l'IA (Jev-I) et bloque les brouillons qui sortent de la demande ou laissent fuir un secret (Jev-E).

Jev joue deux rôles, dans deux parties du code : **le gardien** (`app/guard.py`), pendant le run, et **le juge** (`evals/judge.py`), après le run, qui note chaque run contre le golden set. Le gardien bloque une action, le juge note un run.

L'agent n'envoie jamais de mail : il écrit des brouillons dans une boîte locale (fichiers JSONL). Toutes les adresses et tous les codes sont inventés.

## Structure

```
backend/
  app/
    agent.py     l'agent DeepAgents et la boucle d'un run
    tools.py     les 3 tools : list_inbox, read_mail, write_draft
    guard.py     le gardien (guardrail), pendant le run : questions posées à Jev et thresholds
    canon.py     révèle le texte caché d'un mail HTML
    mailbox.py   la boîte mail locale
    main.py      l'API FastAPI (runs en SSE, replays)
    cli.py       lancer un run dans le terminal
  evals/         16 scénarios (10 attacks, 6 tâches benign), A vs B
    golden_set.csv  le golden set : la référence attendue pour chaque scénario
    judge.py        le juge (Jev-as-judge), après le run : note chaque run, la médiane donne la confiance
    results/        les résultats présentés au talk (26/10/2026)
  fixtures/      les boîtes de démo
frontend/        l'interface Next.js
replays/         deux runs enregistrés, en replay sans clé
```

## Lancer

Il faut [uv](https://docs.astral.sh/uv/), Node.js 20+, une clé Anthropic et une clé TypeSafe.

```bash
cp .env.example .env   # puis remplir les deux clés
```

Backend :

```bash
cd backend
uv sync
uv run uvicorn app.main:app --port 8010
```

Frontend, dans un autre terminal :

```bash
cd frontend
npm install
npm run dev
```

Ouvrir http://localhost:3000. Les replays marchent sans clé.

Dans le terminal, sans interface :

```bash
cd backend
uv run python -m app.cli --config A
uv run python -m app.cli --config B
```

Evals, en deux temps :

```bash
cd backend
uv run python -m evals --runs 1           # 1. lance l'agent sur les 16 scénarios, en A et en B
uv run python -m evals.judge <STAMP>      # 2. Jev-as-judge note chaque run contre le golden set
uv run python -m evals.judge <STAMP> --compare   # + le même juge avec Claude Sonnet 5.5
```

`<STAMP>` est la date du run d'évals, affichée à la fin de l'étape 1 (ex. `20261026-214803`). Les logs des runs sont dans `runs/evals/`.

## Pour aller plus loin

Les lectures et les sources du talk sont dans [ressources.md](ressources.md).
