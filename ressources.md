# Ressources

Les lectures pour aller plus loin après le talk « Juger vite, bloquer juste » (IndabaX Madagascar 2026), puis les sources des chiffres cités. Liens vérifiés le 28/10/2026.

## Par où commencer

Si vous ne lisez que trois choses :

1. [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) (Simon Willison) : pourquoi un agent qui lit des données privées, du contenu non fiable et qui peut écrire vers l'extérieur est attaquable.
2. [OWASP Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) : la prompt injection est toujours LLM01.
3. [The Anatomy of an Agent Harness](https://blog.langchain.com/the-anatomy-of-an-agent-harness/) (Vivek Trivedy, LangChain) : « if you're not the model, you're the harness ».

## Sécurité des agents

- [OWASP Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) et [son dépôt GitHub](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10).
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) : goal hijack, tool misuse, identity and privilege abuse… et le principe de least agency.
- [OWASP LLM01 : Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).
- [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) (Simon Willison).
- [Agents Rule of Two](https://ai.meta.com/blog/practical-ai-agent-security/) (Meta) : jamais plus de deux des trois propriétés dangereuses dans une même session.
- [EchoLeak](https://simonwillison.net/2025/Jun/11/echoleak/) : une injection « zero-click » dans Microsoft 365 Copilot, un cas réel.
- [CaMeL](https://simonwillison.net/2025/Apr/11/camel/) et [le papier de Google DeepMind](https://arxiv.org/abs/2503.18813) : séparer les données non fiables du plan de l'agent.
- [Securing our frontier model training environment](https://openai.com/index/securing-our-frontier-model-training-environment/) (OpenAI) : « la limite doit tenir même si l'agent essaie de la contourner ».

## Harness et agentic engineering

- [The Anatomy of an Agent Harness](https://blog.langchain.com/the-anatomy-of-an-agent-harness/) (Vivek Trivedy, LangChain).
- [How to build a custom agent harness](https://www.langchain.com/blog/how-to-build-a-custom-agent-harness) (LangChain).
- [DeepAgents : customization](https://docs.langchain.com/oss/python/deepagents/customization) et [permissions](https://docs.langchain.com/oss/python/deepagents/permissions) : le framework de notre démo.
- [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) : un harness de production, composant par composant.
- [Context Rot](https://trychroma.com/research/context-rot) (Chroma) : plus le contexte est long, plus le modèle se trompe.
- [Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/) (Simon Willison).
- [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/en/) : un cours en ligne.
- [HumanLayer blog](https://www.humanlayer.dev/blog) et [Latent Space](https://www.latent.space/) : deux blogs à suivre.
- [Spec-Driven Development](https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development) (Panaversity).
- [AI Coding Dictionary](https://www.aihero.dev/ai-coding-dictionary) (AI Hero) : le vocabulaire, terme par terme.
- [Claude courses](https://claude.com/resources/courses) (Anthropic) et [Anthropic Skills](https://github.com/anthropics/skills).
- [Awesome LLM Apps](https://github.com/Shubhamsaboo/awesome-llm-apps), [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) et [Awesome Claude Plugins](https://github.com/quemsah/awesome-claude-plugins) : des exemples à lire.

## Modèles System 1 et Jev

- Daniel Kahneman, *Thinking, Fast and Slow* (2011) : System 1 et System 2.
- [La documentation de TypeSafe](https://docs.typesafe.ai/llms.txt) : Noul, Choice, Score, et le [primer machine learning](https://docs.typesafe.ai/introduction/machine-learning-primer.md).
- [Building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev) (LangChain).
- [TypeSafe Jev review](https://www.eesel.ai/blog/typesafe-jev-review) (eesel) : ce que c'est, ses limites.

## Évals

- [Jev for agent evals in LangSmith](https://www.langchain.com/blog/jev-agent-evals-langsmith) (LangChain) : Jev comme juge, comparé à des LLM-as-judge.
- Dans ce dépôt : [le golden set](backend/evals/golden_set.csv), [le juge](backend/evals/judge.py) et [les résultats du talk](backend/evals/results/).

## Les sources du talk

Ce que les agents font déjà :

- Navier–Stokes, OpenAI (8/09/2026) : [annonce](https://openai.com/fr-FR/index/navier-stokes-solution/) et [dépôt](https://github.com/openai/NavierStokesAndEuler).
- Les mathématiques chez OpenAI (6/10/2026) : [annonce](https://openai.com/fr-FR/index/sharing-ai-progress-in-mathematics/) et [dépôt](https://github.com/openai/math).
- [How AI is transforming work at Anthropic](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic) (Anthropic).
- Project Glasswing (Anthropic) : [présentation](https://www.anthropic.com/glasswing) et [bilan](https://www.anthropic.com/news/glasswing-initial-update).
- [Patch the Planet](https://openai.com/index/patch-the-planet/) (OpenAI).
- PHP2Shell (21/10/2026) : [Wiz](https://www.wiz.io/blog/php2shell-php-rce), [CERT-FR](https://cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-014/) et [la PHP Foundation](https://thephp.foundation/blog/2026/10/21/todays-php-security-release-and-how-were-strengthening-php-security/).
- L'incident Hugging Face (OpenAI) : [billet](https://openai.com/fr-FR/index/hugging-face-incident-and-the-road-ahead/) et [enquête de METR](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/).
- [We Must Pace the Frontier](https://darioamodei.com/post/we-must-pace-the-frontier) (Dario Amodei) et [Recursive self-improvement](https://www.anthropic.com/institute/recursive-self-improvement) (Anthropic).

Les prix cités : [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing) et [Jev](https://flaviocopes.com/jev-pricing/).
