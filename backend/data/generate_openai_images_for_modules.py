import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
MODULES_ROOT = THIS_FILE.parent / "modules"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from quizzes.llm_quiz_generator import (
    DEFAULT_IMAGE_MODEL,
    IMAGE_RATIO_TARGET,
    MAX_IMAGE_QUESTIONS_PER_MODULE,
    _build_image_prompt,
    _enforce_image_quota,
    _generate_image_file,
    _generated_image_filename,
    _generated_image_url,
    _generated_images_dir,
)


def category_key_from_file(file_path: Path) -> str:
    # backend/data/modules/<category>/<level>/<module>.json
    return file_path.parts[-3]


def level_name_from_file(file_path: Path) -> str:
    level_key = file_path.parts[-2]
    return level_key.capitalize()


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY manquant")

    image_model = os.getenv("OPENAI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)
    image_ratio = float(os.getenv("ML360_IMAGE_RATIO", str(IMAGE_RATIO_TARGET)))
    max_images = int(os.getenv("ML360_MAX_IMAGE_QUESTIONS", str(MAX_IMAGE_QUESTIONS_PER_MODULE)))
    out_dir = _generated_images_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(MODULES_ROOT.rglob("*.json"))
    total_modules = len(files)
    generated_count = 0
    reused_count = 0

    for idx, file_path in enumerate(files, start=1):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        category_key = category_key_from_file(file_path)
        level_name = level_name_from_file(file_path)
        category_label = str(payload.get("category", category_key))
        module_name = str(payload.get("module", file_path.stem))

        questions = payload.get("questions")
        if not isinstance(questions, list) or not questions:
            continue

        # Keep reduced deterministic image quota before generating images.
        questions = _enforce_image_quota(
            questions=questions,
            image_ratio_target=image_ratio,
            max_images_per_module=max_images,
        )

        changed = False
        for q_idx, question in enumerate(questions, start=1):
            if question.get("type") != "image":
                question["image_url"] = None
                continue

            file_name = _generated_image_filename(
                category_key=category_key,
                level_name=level_name,
                module_name=module_name,
                question_idx=q_idx,
            )
            output_file = out_dir / file_name
            output_url = _generated_image_url(file_name)

            if output_file.exists() and (question.get("image_url") == output_url):
                reused_count += 1
                continue

            prompt = _build_image_prompt(
                question=question,
                category_label=category_label,
                level_name=level_name,
                module_name=module_name,
            )
            print(f"[{idx}/{total_modules}] Image generation: {file_path.name} q{q_idx}")
            _generate_image_file(
                api_key=api_key,
                image_model=image_model,
                prompt=prompt,
                output_file=output_file,
            )
            question["image_url"] = output_url
            generated_count += 1
            changed = True

        if changed:
            payload["questions"] = questions
            file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"DONE generated={generated_count} reused={reused_count} modules={total_modules} "
        f"ratio={image_ratio} max_images={max_images}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
