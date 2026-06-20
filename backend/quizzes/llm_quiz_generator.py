import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from django.utils.text import slugify

from quizzes.dataset_generator import (
    MODULE_LIBRARY,
    _module_difficulty_sequence,
    _module_question_count,
    supported_category_keys,
    supported_levels,
    supported_modules,
)

SYSTEM_PROMPT = """Tu es un expert en machine learning et en ingenierie pedagogique.
Ta mission: generer des questions de quiz utiles pour apprendre, pas des formulations vagues.

REGLES OBLIGATOIRES:
1) Chaque choix doit contenir une proposition technique concrete et verifiable.
2) Les distracteurs doivent etre plausibles mais faux pour une raison conceptuelle precise.
3) L'explication doit:
   - definir clairement le concept correct
   - expliquer pourquoi chaque mauvaise reponse est fausse
   - rester specifique (pas de phrase vide type 'moins pertinent')
    - contenir entre 90 et 120 mots utiles
4) Sortie JSON stricte uniquement:
{
  "questions": [
    {
      "type": "text",
      "question": "...",
      "image_url": null,
      "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "explanation": "...",
      "difficulty": "easy"
    }
  ]
}
- type: "text" uniquement
- correct_answer: A/B/C/D
- difficulty: easy/medium/hard
"""

OPTION_LETTERS = ("A", "B", "C", "D")
MIN_EXPLANATION_WORDS = 90
MAX_EXPLANATION_WORDS = 120


def _words_count(text: str) -> int:
    return len((text or "").split())


def _target_answer_sequence(question_count: int) -> list[str]:
    base = question_count // len(OPTION_LETTERS)
    remainder = question_count % len(OPTION_LETTERS)
    counts = {letter: base for letter in OPTION_LETTERS}
    for idx in range(remainder):
        counts[OPTION_LETTERS[idx]] += 1

    sequence = []
    while len(sequence) < question_count:
        progressed = False
        for letter in OPTION_LETTERS:
            if counts[letter] > 0:
                sequence.append(letter)
                counts[letter] -= 1
                progressed = True
        if not progressed:
            break
    return sequence


def _rebalance_correct_answers(questions: list[dict]) -> list[dict]:
    target_sequence = _target_answer_sequence(len(questions))
    balanced = []

    for idx, question in enumerate(questions):
        target_correct = target_sequence[idx]
        current_correct = question["correct_answer"]
        if current_correct == target_correct:
            balanced.append(question)
            continue

        swapped = dict(question)
        choices = dict(swapped["choices"])
        choices[target_correct], choices[current_correct] = choices[current_correct], choices[target_correct]
        swapped["choices"] = choices
        swapped["correct_answer"] = target_correct
        balanced.append(swapped)

    return balanced


def _rewrite_explanations_batch(
    *,
    api_key: str,
    model: str,
    category_label: str,
    level_name: str,
    module_name: str,
    batch: list[dict],
) -> list[str]:
    payload = []
    for idx, q in enumerate(batch, start=1):
        payload.append(
            {
                "index": idx,
                "question": q["question"],
                "choices": q["choices"],
                "correct_answer": q["correct_answer"],
                "current_explanation": q["explanation"],
            }
        )

    prompt = (
        "Reecris les explications des questions suivantes en francais naturel et precis.\n"
        f"Contexte: {category_label} / {level_name} / {module_name}.\n"
        f"Chaque explication doit faire entre {MIN_EXPLANATION_WORDS} et {MAX_EXPLANATION_WORDS} mots, "
        "etre specifique, expliquer pourquoi la bonne reponse est correcte, et pourquoi les distracteurs sont faux.\n"
        "Retourne uniquement un JSON strict sous la forme:"
        '{"explanations":[{"index":1,"explanation":"..."}]}'
        " avec exactement une explication par question.\n"
        f"Questions: {json.dumps(payload, ensure_ascii=False)}"
    )
    raw = call_openai(prompt=prompt, api_key=api_key, model=model)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("Aucun JSON pour la reecriture des explications")
    data = json.loads(match.group(0))
    rows = data.get("explanations")
    if rows is None:
        rows = data.get("items")
    if rows is None and isinstance(data.get("questions"), list):
        rows = data.get("questions")
    if rows is None and isinstance(data, dict):
        # Fallback: map style {"1":"...", "2":"..."}
        maybe_values = []
        for idx in range(1, len(batch) + 1):
            maybe_values.append({"index": idx, "explanation": data.get(str(idx), "")})
        rows = maybe_values
    if not isinstance(rows, list):
        raise ValueError("Format invalide de reecriture des explications")

    if len(rows) > len(batch):
        rows = rows[: len(batch)]

    rewritten = []
    by_index = {}
    for idx, item in enumerate(rows, start=1):
        if isinstance(item, dict):
            key = item.get("index", idx)
            text = item.get("explanation") or item.get("text") or item.get("content") or ""
            by_index[key] = text
        elif isinstance(item, str):
            by_index[idx] = item
    for idx in range(1, len(batch) + 1):
        explanation = str(by_index.get(idx, "")).strip()
        if not explanation:
            explanation = str(batch[idx - 1].get("explanation", "")).strip()
        rewritten.append(explanation)
    return rewritten


def _normalize_explanation_length(question: dict) -> str:
    explanation = str(question.get("explanation", "")).strip()
    words = explanation.split()
    if len(words) > MAX_EXPLANATION_WORDS:
        return " ".join(words[:MAX_EXPLANATION_WORDS])

    if len(words) >= MIN_EXPLANATION_WORDS:
        return explanation

    correct = question.get("correct_answer", "A")
    choices = question.get("choices", {})
    wrong_letters = [letter for letter in OPTION_LETTERS if letter != correct]

    supplements = [
        f"Pour valider cette question, il faut relier le besoin exprime a l'option {correct}.",
        f"L'option {correct} ({choices.get(correct, '')}) repond au critere principal attendu dans l'enonce.",
    ]
    for letter in wrong_letters:
        supplements.append(
            f"L'option {letter} ({choices.get(letter, '')}) est un distracteur plausible, "
            "mais elle rate la condition centrale demandee."
        )
    supplements.append(
        "En pratique, compare toujours definition, hypothese et impact metier avant de valider la reponse finale."
    )

    merged = explanation
    for sentence in supplements:
        if len(merged.split()) >= MIN_EXPLANATION_WORDS:
            break
        merged = f"{merged} {sentence}".strip()

    merged_words = merged.split()
    filler = "Cette verification limite les confusions frequentes et rend la decision plus fiable en pratique."
    while len(merged_words) < MIN_EXPLANATION_WORDS:
        merged = f"{merged} {filler}".strip()
        merged_words = merged.split()
    if len(merged_words) > MAX_EXPLANATION_WORDS:
        merged = " ".join(merged_words[:MAX_EXPLANATION_WORDS])
    return merged


def _enforce_explanation_lengths(
    *,
    api_key: str,
    model: str,
    category_label: str,
    level_name: str,
    module_name: str,
    questions: list[dict],
) -> list[dict]:
    normalized = [dict(q) for q in questions]
    pending_indexes = [
        idx
        for idx, q in enumerate(normalized)
        if _words_count(q.get("explanation", "")) < MIN_EXPLANATION_WORDS
        or _words_count(q.get("explanation", "")) > MAX_EXPLANATION_WORDS
    ]

    if not pending_indexes:
        return normalized

    max_rewrite_rounds = 3
    for _ in range(max_rewrite_rounds):
        if not pending_indexes:
            break

        batch = [normalized[idx] for idx in pending_indexes]
        rewritten = _rewrite_explanations_batch(
            api_key=api_key,
            model=model,
            category_label=category_label,
            level_name=level_name,
            module_name=module_name,
            batch=batch,
        )

        for local_idx, global_idx in enumerate(pending_indexes):
            normalized[global_idx]["explanation"] = rewritten[local_idx]

        pending_indexes = [
            idx
            for idx, q in enumerate(normalized)
            if _words_count(q.get("explanation", "")) < MIN_EXPLANATION_WORDS
            or _words_count(q.get("explanation", "")) > MAX_EXPLANATION_WORDS
        ]

    if pending_indexes:
        for idx in pending_indexes:
            normalized[idx]["explanation"] = _normalize_explanation_length(normalized[idx])

    return normalized


def _module_concepts(category_key: str, level_name: str, module_name: str) -> list[str]:
    category = MODULE_LIBRARY.get(category_key)
    if not category:
        raise ValueError(f"Categorie inconnue: {category_key}")
    level_modules = category["levels"].get(level_name)
    if not level_modules:
        raise ValueError(f"Niveau inconnu: {level_name}")
    for title, concepts in level_modules:
        if title == module_name:
            return concepts
    raise ValueError(f"Module introuvable: {module_name}")


def _difficulty_mix_from_sequence(sequence: list[str]) -> dict[str, int]:
    return {
        "easy": sequence.count("easy"),
        "medium": sequence.count("medium"),
        "hard": sequence.count("hard"),
    }


def build_user_prompt(
    category_label: str,
    level_name: str,
    module_name: str,
    concepts: list[str],
    question_count: int,
    difficulty_mix: dict[str, int],
) -> str:
    concept_list = "\n".join(f"- {c}" for c in concepts)
    return f"""Genere {question_count} questions de quiz pour:
Categorie: {category_label}
Niveau: {level_name}
Module: {module_name}

Concepts a couvrir (au moins 1 question par concept):
{concept_list}

Repartition des difficultes:
- easy: {difficulty_mix['easy']}
- medium: {difficulty_mix['medium']}
- hard: {difficulty_mix['hard']}

Contraintes pedagogiques:
- Chaque choix doit apprendre quelque chose de concret.
- Evite les formulations meta du type 'coherent', 'plausible', 'annexe'.
- Utilise definitions courtes, cas d'usage, erreurs classiques, comparaisons utiles.
- Chaque explication doit contenir entre {MIN_EXPLANATION_WORDS} et {MAX_EXPLANATION_WORDS} mots utiles.
- Repartis les bonnes reponses de maniere equilibree entre A/B/C/D (environ 25% chacune, marge de +-1 question selon la taille).
- Le format JSON doit respecter exactement le schema demande.

Exemple attendu de bon choix:
Question: Quelle formule definit le F1 score?
Bon choix: 2 x (precision x rappel) / (precision + rappel)
Mauvais choix plausible: accuracy = (TP+TN)/N

Renvoie UNIQUEMENT le JSON final."""


def call_openai(prompt: str, api_key: str, model: str, max_retries: int = 3) -> str:
    if OpenAI is None:
        raise RuntimeError("Le package openai n'est pas installe. Lance: pip install openai")

    client = OpenAI(api_key=api_key, timeout=180)

    for attempt in range(max_retries):
        try:
            print(f"  OpenAI attempt {attempt + 1}/{max_retries}...", file=sys.stderr)
            response = client.chat.completions.create(
                model=model,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Reponse vide du modele")
            return content
        except Exception as exc:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Tentative {attempt + 1} echouee ({exc}). Retry dans {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


def parse_llm_response(raw: str, level_name: str, expected_count: int, require_full: bool = True) -> list[dict]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("Aucun objet JSON detecte dans la reponse")

    data = json.loads(match.group(0))
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("La reponse doit contenir une liste non vide dans 'questions'")

    difficulty_sequence = _module_difficulty_sequence(level_name, expected_count)
    validated = []

    for item in questions:
        if len(validated) >= expected_count:
            break
        if not isinstance(item, dict):
            continue
        if not all(k in item for k in ("question", "choices", "correct_answer", "explanation")):
            continue
        choices = item.get("choices")
        if not isinstance(choices, dict) or not all(letter in choices for letter in ("A", "B", "C", "D")):
            continue
        correct_answer = item.get("correct_answer")
        if correct_answer not in ("A", "B", "C", "D"):
            continue

        explanation = str(item["explanation"]).strip()

        validated.append(
            {
                "type": "text",
                "question": str(item["question"]).strip(),
                "image_url": None,
                "choices": {letter: str(choices[letter]).strip() for letter in ("A", "B", "C", "D")},
                "correct_answer": correct_answer,
                "explanation": explanation,
                "difficulty": difficulty_sequence[len(validated)],
            }
        )

    if require_full and len(validated) < expected_count:
        raise ValueError(
            f"Questions valides insuffisantes: {len(validated)}/{expected_count}. Regenerer le module."
        )

    return validated


def _topup_questions(
    *,
    api_key: str,
    model: str,
    category_label: str,
    level_name: str,
    module_name: str,
    concepts: list[str],
    expected_count: int,
    existing_questions: list[dict],
) -> list[dict]:
    questions = list(existing_questions)
    max_rounds = 3
    while len(questions) < expected_count and max_rounds > 0:
        missing = expected_count - len(questions)
        prompt = (
            build_user_prompt(
                category_label=category_label,
                level_name=level_name,
                module_name=module_name,
                concepts=concepts,
                question_count=missing,
                difficulty_mix={"easy": missing, "medium": 0, "hard": 0},
            )
            + (
                "\n\nIMPORTANT: Tu ne dois generer que ces questions manquantes. "
                f"Chaque explication doit avoir au moins {MIN_EXPLANATION_WORDS} mots utiles."
            )
        )
        raw = call_openai(prompt=prompt, api_key=api_key, model=model)
        extra = parse_llm_response(raw=raw, level_name=level_name, expected_count=missing, require_full=False)
        if not extra:
            max_rounds -= 1
            continue
        questions.extend(extra[:missing])
        max_rounds -= 1

    if len(questions) < expected_count:
        raise ValueError(f"Questions valides insuffisantes apres top-up: {len(questions)}/{expected_count}")

    return _rebalance_correct_answers(questions[:expected_count])


def generate_module_quiz(
    category_key: str,
    level_name: str,
    module_name: str,
    api_key: str,
    model: str,
    question_count: int | None,
    dry_run: bool,
) -> dict:
    category_label = MODULE_LIBRARY[category_key]["category"]
    concepts = _module_concepts(category_key, level_name, module_name)

    module_index = supported_modules(category_key, level_name).index(module_name) + 1
    expected_count = question_count or _module_question_count(level_name, module_index)

    difficulty_sequence = _module_difficulty_sequence(level_name, expected_count)
    difficulty_mix = _difficulty_mix_from_sequence(difficulty_sequence)

    prompt = build_user_prompt(
        category_label=category_label,
        level_name=level_name,
        module_name=module_name,
        concepts=concepts,
        question_count=expected_count,
        difficulty_mix=difficulty_mix,
    )

    if dry_run:
        print("=== SYSTEM PROMPT ===")
        print(SYSTEM_PROMPT)
        print("\n=== USER PROMPT ===")
        print(prompt)
        return {}

    max_attempts = 5
    last_error = None
    questions = None
    prompt_attempt = prompt
    for attempt in range(1, max_attempts + 1):
        print(f"  Validation attempt {attempt}/{max_attempts} pour '{module_name}'", file=sys.stderr)
        raw = call_openai(prompt=prompt_attempt, api_key=api_key, model=model)
        try:
            partial = parse_llm_response(raw=raw, level_name=level_name, expected_count=expected_count, require_full=False)
            if len(partial) < expected_count:
                print(
                    f"  Reponse partielle ({len(partial)}/{expected_count}), top-up des questions manquantes...",
                    file=sys.stderr,
                )
                questions = _topup_questions(
                    api_key=api_key,
                    model=model,
                    category_label=category_label,
                    level_name=level_name,
                    module_name=module_name,
                    concepts=concepts,
                    expected_count=expected_count,
                    existing_questions=partial,
                )
            else:
                questions = partial
            break
        except Exception as exc:
            last_error = exc
            print(f"  Reponse invalide ({exc}), nouvelle tentative...", file=sys.stderr)
            missing_note = (
                f"\n\nTu dois renvoyer EXACTEMENT {expected_count} questions valides avec 4 choix A/B/C/D et un correct_answer valide. "
                "Corrige ton format et regenere l'ensemble complet."
            )
            prompt_attempt = prompt + missing_note
            time.sleep(1.0)

    if questions is None:
        raise ValueError(f"Generation impossible pour {module_name} apres {max_attempts} tentatives: {last_error}")

    questions = _rebalance_correct_answers(questions)
    questions = _enforce_explanation_lengths(
        api_key=api_key,
        model=model,
        category_label=category_label,
        level_name=level_name,
        module_name=module_name,
        questions=questions,
    )

    return {
        "category": category_label,
        "level": level_name,
        "module": module_name,
        "questions": questions,
    }


def write_quiz(path: Path, quiz_payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(quiz_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Ecrit: {path}")


def generate_all_for_category(category_key: str, output_dir: Path, api_key: str, model: str, dry_run: bool) -> None:
    for level_name in supported_levels(category_key):
        for module_name in supported_modules(category_key, level_name):
            print(f"Generation: {category_key} / {level_name} / {module_name}")
            quiz_payload = generate_module_quiz(
                category_key=category_key,
                level_name=level_name,
                module_name=module_name,
                api_key=api_key,
                model=model,
                question_count=None,
                dry_run=dry_run,
            )
            if dry_run:
                continue
            target_path = output_dir / category_key / level_name.lower() / f"{slugify(module_name)}.json"
            write_quiz(target_path, quiz_payload)
            time.sleep(0.7)


def main() -> int:
    parser = argparse.ArgumentParser(description="ML360 LLM quiz generator (OpenAI)")
    parser.add_argument("--category", required=True, choices=supported_category_keys())
    parser.add_argument("--level", choices=["Beginner", "Intermediate", "Advanced"])
    parser.add_argument("--module")
    parser.add_argument("--all", action="store_true", dest="all_modules")
    parser.add_argument("--output")
    parser.add_argument("--output-dir")
    parser.add_argument("--n-questions", type=int)
    parser.add_argument("--api-key")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env_dry_run = os.getenv("ML360_DRY_RUN", "0") == "1"
    dry_run = args.dry_run or env_dry_run

    api_key = os.getenv("OPENAI_API_KEY") or args.api_key
    if not api_key and not dry_run:
        parser.error("Fournis OPENAI_API_KEY ou --api-key")

    if args.all_modules:
        if not args.output_dir:
            parser.error("--output-dir est requis avec --all")
        output_dir = Path(args.output_dir)
        generate_all_for_category(
            category_key=args.category,
            output_dir=output_dir,
            api_key=api_key or "",
            model=args.model,
            dry_run=dry_run,
        )
        return 0

    if not args.level or not args.module:
        parser.error("--level et --module sont requis sans --all")

    quiz_payload = generate_module_quiz(
        category_key=args.category,
        level_name=args.level,
        module_name=args.module,
        api_key=api_key or "",
        model=args.model,
        question_count=args.n_questions,
        dry_run=dry_run,
    )

    if not dry_run:
        if not args.output:
            parser.error("--output est requis en mode module unique")
        write_quiz(Path(args.output), quiz_payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
