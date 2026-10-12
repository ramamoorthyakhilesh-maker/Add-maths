# Setup

## 1. Get the code

```
git clone https://github.com/ramamoorthyakhilesh-maker/Add-maths.git
cd Add-maths
pip install -r requirements.txt
python -m pytest        # optional: pip install -r requirements-dev.txt first
```

The tools work on their own, so you can try Edith's questions and marking in a terminal before you connect anything. On Windows use `py` in place of `python` if `python` opens the Microsoft Store.

## 2. Connect the tutor

Edith runs as an agent in OpenClaw. Commands change between versions, so follow the OpenClaw documentation for your version. The pieces you need:

1. An agent whose workspace is this folder. `SOUL.md` in the workspace is loaded as the agent's instructions.
2. A Telegram bot token from BotFather, bound to that agent so it does not share a chat with your other agents.
3. A model. Free OpenRouter models work. Put the one that scored best on the benchmark first and a different model after it as a fallback.
4. A restart of the gateway so the new agent and `SOUL.md` load.

## 3. Check it works

Send these to the bot, in order:

1. "Give me a medium differentiation question." You should get one picture card with an ID.
2. A wrong answer. You should get INCORRECT and a hint, not the solution.
3. "Just tell me the answer." She should refuse kindly and offer the next hint.
4. A correct answer. You should get CORRECT, a summary and three follow-up cards.
5. An off-topic question. She should decline in one line.

Then read the log of what she ran:

```
tail -n 10 logs/gen_calls.jsonl
```

Each question should show one `new`, followed by `check` calls with the same ID.

## Keep it private

Your own `USER.md`, `memory/`, `logs/` and API keys stay out of git. The `.gitignore` covers them, and `tests/test_repo_hygiene.py` fails if a key, token or personal detail reaches the repository.
