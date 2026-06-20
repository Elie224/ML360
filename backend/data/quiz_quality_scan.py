import json
import re
import argparse
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "modules"
LETTERS = ("A", "B", "C", "D")


def norm(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def first_tokens(text: str, n: int = 6) -> str:
    tokens = re.findall(r"[a-zA-Z0-9']+", (text or "").lower())
    return " ".join(tokens[:n])


def words_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def scan(max_a_ratio_global: float, max_a_ratio_module: float):
    files = sorted(ROOT.rglob("*.json"))
    if not files:
        raise SystemExit(f"No quiz json files found under {ROOT}")

    total_questions = 0
    total_files = len(files)
    by_level = Counter()
    by_category = Counter()
    answer_distribution = Counter()

    # Global duplicate checks
    prompts_by_scope = defaultdict(list)  # (category, level, prompt_norm) -> occurrences
    prompts_by_category = defaultdict(list)  # (category, prompt_norm)

    # Quality signals
    short_explanations = []
    repetitive_choice_prefix = []
    duplicate_choice_sets_in_module = []
    low_stem_diversity_modules = []

    top_option_prefixes = Counter()
    module_summary = []
    module_answer_ratios = []

    for file_path in files:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        category = payload.get("category", "")
        level = payload.get("level", "")
        module = payload.get("module", "")
        questions = payload.get("questions", [])

        by_level[level] += len(questions)
        by_category[category] += len(questions)

        module_prompts = []
        module_choice_sets = []
        module_stems = []

        for idx, q in enumerate(questions, start=1):
            total_questions += 1
            prompt = q.get("question", "")
            prompt_norm = norm(prompt)
            module_prompts.append(prompt_norm)
            module_stems.append(first_tokens(prompt, 8))

            prompts_by_scope[(category, level, prompt_norm)].append((module, str(file_path), idx))
            prompts_by_category[(category, prompt_norm)].append((level, module, str(file_path), idx))

            correct = q.get("correct_answer")
            if correct in LETTERS:
                answer_distribution[correct] += 1

            explanation = q.get("explanation", "")
            wc = words_count(explanation)
            if wc < 80:
                short_explanations.append((str(file_path), idx, wc))

            choices = q.get("choices", {})
            choice_values = [choices.get(letter, "") for letter in LETTERS]
            choice_set_norm = tuple(norm(value) for value in choice_values)
            module_choice_sets.append(choice_set_norm)

            starts = [first_tokens(value, 6) for value in choice_values]
            for st in starts:
                top_option_prefixes[st] += 1

            if len(set(starts)) <= 2:
                repetitive_choice_prefix.append((str(file_path), idx, starts))

        dup_choice_sets = len(module_choice_sets) - len(set(module_choice_sets))
        if dup_choice_sets > 0:
            duplicate_choice_sets_in_module.append((str(file_path), dup_choice_sets))

        stem_div = len(set(module_stems)) / max(len(module_stems), 1)
        if stem_div < 0.45:
            low_stem_diversity_modules.append((str(file_path), round(stem_div, 3)))

        module_summary.append(
            {
                "file": str(file_path),
                "questions": len(questions),
                "unique_prompts": len(set(module_prompts)),
                "prompt_uniqueness_ratio": round(len(set(module_prompts)) / max(len(module_prompts), 1), 3),
                "stem_diversity_ratio": round(stem_div, 3),
                "duplicate_choice_sets": dup_choice_sets,
            }
        )

        module_answers = Counter(q.get("correct_answer") for q in questions if q.get("correct_answer") in LETTERS)
        module_total = max(len(questions), 1)
        module_a_ratio = module_answers["A"] / module_total
        module_answer_ratios.append(
            {
                "file": str(file_path),
                "questions": len(questions),
                "A": module_answers["A"],
                "B": module_answers["B"],
                "C": module_answers["C"],
                "D": module_answers["D"],
                "a_ratio": round(module_a_ratio, 4),
            }
        )

    dup_scope = []
    for (category, level, prompt), occurrences in prompts_by_scope.items():
        modules = {m for m, _, _ in occurrences}
        if len(occurrences) > 1 and len(modules) > 1:
            dup_scope.append(
                {
                    "category": category,
                    "level": level,
                    "prompt": prompt,
                    "count": len(occurrences),
                    "examples": occurrences[:3],
                }
            )

    dup_category = []
    for (category, prompt), occurrences in prompts_by_category.items():
        scopes = {(lvl, mod) for lvl, mod, _, _ in occurrences}
        if len(occurrences) > 1 and len(scopes) > 1:
            dup_category.append(
                {
                    "category": category,
                    "prompt": prompt,
                    "count": len(occurrences),
                    "examples": occurrences[:3],
                }
            )

    report = {
        "fileCount": total_files,
        "questionCount": total_questions,
        "distributionByLevel": dict(by_level),
        "distributionByCategory": dict(by_category),
        "correctAnswerDistribution": {
            letter: {
                "count": answer_distribution[letter],
                "ratio": round(answer_distribution[letter] / max(total_questions, 1), 4),
            }
            for letter in LETTERS
        },
        "qualitySignals": {
            "shortExplanationsCount_lt80w": len(short_explanations),
            "repetitiveChoicePrefixCount_le2uniqueStarts": len(repetitive_choice_prefix),
            "duplicateChoiceSetModules": len(duplicate_choice_sets_in_module),
            "lowStemDiversityModules_lt0_45": len(low_stem_diversity_modules),
            "duplicatePromptsByCategoryLevel": len(dup_scope),
            "duplicatePromptsByCategory": len(dup_category),
        },
        "samples": {
            "shortExplanations": short_explanations[:20],
            "repetitiveChoicePrefix": repetitive_choice_prefix[:20],
            "duplicateChoiceSetModules": duplicate_choice_sets_in_module[:20],
            "lowStemDiversityModules": low_stem_diversity_modules[:20],
            "duplicatePromptsByCategoryLevel": dup_scope[:20],
            "duplicatePromptsByCategory": dup_category[:20],
            "topOptionPrefixes": top_option_prefixes.most_common(25),
            "lowestStemDiversityModules": sorted(module_summary, key=lambda x: x["stem_diversity_ratio"])[:20],
            "highestARatioModules": sorted(module_answer_ratios, key=lambda x: x["a_ratio"], reverse=True)[:20],
        },
    }

    out_json = Path(__file__).resolve().parent / "quiz_quality_scan_report.json"
    out_md = Path(__file__).resolve().parent / "quiz_quality_scan_report.md"

    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# Quiz Quality Scan Report",
        "",
        f"- Files: {report['fileCount']}",
        f"- Questions: {report['questionCount']}",
        "",
        "## Quality Signals",
    ]
    for key, value in report["qualitySignals"].items():
        md_lines.append(f"- {key}: {value}")

    md_lines.extend([
        "",
        "## Correct Answer Distribution",
    ])
    for letter in LETTERS:
        data = report["correctAnswerDistribution"][letter]
        md_lines.append(f"- {letter}: {data['count']} ({data['ratio']:.2%})")

    md_lines.extend([
        "",
        "## Top Option Prefixes (Potential Repetition)",
    ])
    for prefix, count in report["samples"]["topOptionPrefixes"][:15]:
        md_lines.append(f"- {count}x :: {prefix}")

    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Report written: {out_json}")
    print(f"Report written: {out_md}")
    print(json.dumps({
        "fileCount": report["fileCount"],
        "questionCount": report["questionCount"],
        "qualitySignals": report["qualitySignals"],
        "correctAnswerDistribution": report["correctAnswerDistribution"],
    }, indent=2, ensure_ascii=False))

    global_a_ratio = report["correctAnswerDistribution"]["A"]["ratio"]
    module_a_violations = [m for m in module_answer_ratios if m["a_ratio"] > max_a_ratio_module]
    if global_a_ratio > max_a_ratio_global or module_a_violations:
        print(
            json.dumps(
                {
                    "error": "A-bias threshold exceeded",
                    "global_a_ratio": global_a_ratio,
                    "max_a_ratio_global": max_a_ratio_global,
                    "module_violations_count": len(module_a_violations),
                    "max_a_ratio_module": max_a_ratio_module,
                    "module_violations_sample": module_a_violations[:10],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        raise SystemExit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ML360 quiz quality scan")
    parser.add_argument("--max-a-ratio-global", type=float, default=0.35)
    parser.add_argument("--max-a-ratio-module", type=float, default=0.5)
    args = parser.parse_args()
    scan(max_a_ratio_global=args.max_a_ratio_global, max_a_ratio_module=args.max_a_ratio_module)
