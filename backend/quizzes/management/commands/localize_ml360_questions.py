import re

from django.core.management.base import BaseCommand
from django.db import transaction

from quizzes.models import Choice, Question


def _translate_text(value: str) -> str:
    text = value

    # Prompt patterns from generated datasets.
    text = re.sub(
        r"In the module '([^']+)', which statement best defines ([^?]+)\?",
        r"Dans le module '\1', quelle affirmation définit le mieux \2 ?",
        text,
    )
    text = re.sub(
        r"Why is ([^?]+) important in this module\?",
        r"Pourquoi \1 est-il important dans ce module ?",
        text,
    )
    text = re.sub(
        r"Which statement best describes ([^?]+)\?",
        r"Quelle affirmation décrit le mieux \1 ?",
        text,
    )
    text = re.sub(
        r"Which risk is most directly associated with ([^?]+)\?",
        r"Quel risque est le plus directement associé à \1 ?",
        text,
    )
    text = re.sub(
        r"Which concept is most closely linked to this goal: ([^.]+)\.?",
        r"Quel concept est le plus étroitement lié à cet objectif : \1.",
        text,
    )
    text = re.sub(
        r"Which scenario best illustrates ([^?]+)\?",
        r"Quel scénario illustre le mieux \1 ?",
        text,
    )
    text = re.sub(
        r"Which interpretation best matches the ML diagram for ([^?]+) in ([^?]+)\?",
        r"Quelle interprétation correspond le mieux au schéma ML pour \1 dans \2 ?",
        text,
    )
    text = re.sub(
        r"Which concept matches this description: ([^.]+) is an advanced lever in ([^.]+) for solving real-world problems linked to ([^.]+)\.",
        r"Quel concept correspond à cette description : \1 est un levier avancé en \2 pour résoudre des problèmes concrets liés à \3.",
        text,
    )
    text = re.sub(
        r"Which concept matches this description: ([^.]+) is applied in ([^.]+) to reason about model behavior inside ([^.]+)\.",
        r"Quel concept correspond à cette description : \1 est appliqué en \2 pour raisonner sur le comportement du modèle dans \3.",
        text,
    )

    # Explanation patterns.
    text = re.sub(
        r"([A-Za-zÀ-ÿ0-9 _'’-]+) is correctly defined by the first option because it captures the core idea used in ([^.]+)\.",
        r"\1 est correctement défini par la bonne option, car elle capture l'idée centrale utilisée dans \2.",
        text,
    )
    text = re.sub(
        r"The correct answer explains the main learning objective behind ([^.]+) in this module\.",
        r"La bonne réponse explique l'objectif d'apprentissage principal lié à \1 dans ce module.",
        text,
    )

    # Choice label patterns.
    text = re.sub(
        r"([A-Za-zÀ-ÿ0-9 _'’-]+) is a foundational idea in ([^.]+) used to understand ([^.]+)\.",
        r"\1 est un concept fondamental en \2 pour comprendre \3.",
        text,
    )
    text = re.sub(
        r"It helps learners identify the basic role of ([^.]+) before using more advanced workflows\.",
        r"Cela aide les apprenants à identifier le rôle de base de \1 avant d'utiliser des workflows plus avancés.",
        text,
    )
    text = re.sub(
        r"A common mistake is to use ([^.]+) without first checking the basic assumptions of ([^.]+)\.",
        r"Une erreur fréquente consiste à utiliser \1 sans d'abord vérifier les hypothèses de base de \2.",
        text,
    )
    text = re.sub(
        r"A common mistake is to optimize ([^.]+) locally while ignoring deployment, drift, cost, or safety impacts\.",
        r"Une erreur fréquente consiste à optimiser \1 localement en ignorant les impacts de déploiement, de dérive, de coût ou de sécurité.",
        text,
    )
    text = re.sub(
        r"A common mistake is to apply ([^.]+) mechanically without validating whether it improves the workflow\.",
        r"Une erreur fréquente consiste à appliquer \1 mécaniquement sans vérifier si cela améliore réellement le workflow.",
        text,
    )
    text = re.sub(
        r"A beginner studies ([^.]+) and uses ([^.]+) to explain a simple learning example\.",
        r"Un debutant etudie \1 et utilise \2 pour expliquer un exemple d'apprentissage simple.",
        text,
    )

    return text


class Command(BaseCommand):
    help = "Localize generated ML360 questions/choices from English templates to French."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be updated without writing changes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        question_updates = 0
        choice_updates = 0

        for question in Question.objects.select_related("quiz").all():
            new_prompt = _translate_text(question.prompt)
            new_explanation = _translate_text(question.explanation)

            changed = False
            if new_prompt != question.prompt:
                question.prompt = new_prompt
                changed = True
            if new_explanation != question.explanation:
                question.explanation = new_explanation
                changed = True

            if changed:
                question_updates += 1
                if not dry_run:
                    question.save(update_fields=["prompt", "explanation"])

        for choice in Choice.objects.select_related("question").all():
            new_label = _translate_text(choice.label)
            if new_label != choice.label:
                choice_updates += 1
                if not dry_run:
                    choice.label = new_label
                    choice.save(update_fields=["label"])

        if dry_run:
            transaction.set_rollback(True)

        mode = "Dry-run" if dry_run else "Done"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: {question_updates} question(s) updated, {choice_updates} choice(s) updated."
            )
        )