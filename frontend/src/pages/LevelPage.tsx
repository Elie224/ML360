import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import { areAllQuizzesCompleted, hasQuizInProgress } from '../progression'
import type { QuizListItem } from '../types'

function moduleDifficulty(questionCount: number) {
  if (questionCount <= 9) return 'Facile'
  if (questionCount <= 15) return 'Moyen'
  return 'Challenge'
}

function resolveLevelQuizzes(
  levelOrder: number,
  levelSlug: string,
  quizzes: QuizListItem[],
) {
  const direct = quizzes.filter((quiz) => quiz.level.slug === levelSlug)
  if (direct.length > 0) {
    return direct
  }

  // Ensure Expert level is never empty by promoting the most advanced modules.
  if (levelOrder === 4) {
    return quizzes
      .filter((quiz) => quiz.level.order === 3)
      .sort((a, b) => b.question_count - a.question_count)
      .slice(0, 6)
  }

  return []
}

export function LevelPage() {
  const { slug, levelSlug } = useParams()
  const [searchTerm, setSearchTerm] = useState('')
  const completedQuizSlugs = useCompletedQuizSlugs()

  const { data: categories, error: categoryError, loading: categoryLoading } = useAsyncData(fetchCategories, [])
  const { data: quizzes, error: quizError, loading: quizLoading } = useAsyncData(
    () => (slug ? fetchQuizzes(slug) : Promise.resolve([])),
    [slug],
  )

  const activeCategory = useMemo(() => {
    if (!slug || !categories?.length) return null
    return categories.find((category) => category.slug === slug) ?? null
  }, [categories, slug])

  const activeLevel = useMemo(() => {
    if (!activeCategory || !levelSlug) return null
    return activeCategory.levels.find((level) => level.slug === levelSlug) ?? null
  }, [activeCategory, levelSlug])

  const levelQuizzes = useMemo(() => {
    if (!quizzes || !levelSlug || !activeLevel) return []
    const base = resolveLevelQuizzes(activeLevel.order, levelSlug, quizzes)
    const search = searchTerm.trim().toLowerCase()
    if (!search) return base
    return base.filter((quiz) => [quiz.title, quiz.description].join(' ').toLowerCase().includes(search))
  }, [activeLevel, levelSlug, quizzes, searchTerm])

  const levelIsUnlocked = useMemo(() => {
    if (!activeCategory || !activeLevel) {
      return false
    }

    const orderedLevels = [...activeCategory.levels].sort((a, b) => a.order - b.order)
    const currentIndex = orderedLevels.findIndex((level) => level.slug === activeLevel.slug)
    if (currentIndex <= 0) {
      return true
    }

    const previousLevel = orderedLevels[currentIndex - 1]
    const previousLevelQuizzes = resolveLevelQuizzes(previousLevel.order, previousLevel.slug, quizzes ?? [])
    return areAllQuizzesCompleted(previousLevelQuizzes, completedQuizSlugs)
  }, [activeCategory, activeLevel, completedQuizSlugs, quizzes])

  const lockedModules = useMemo(() => {
    const bySlug = new Map<string, boolean>()
    const ordered = [...levelQuizzes].sort((a, b) => a.id - b.id)

    ordered.forEach((quiz, index) => {
      if (index === 0) {
        bySlug.set(quiz.slug, true)
        return
      }

      const previousQuiz = ordered[index - 1]
      bySlug.set(quiz.slug, completedQuizSlugs.has(previousQuiz.slug))
    })

    return bySlug
  }, [completedQuizSlugs, levelQuizzes])

  if (!slug || !levelSlug) {
    return <p className="ml-shell text-sm text-danger">Niveau introuvable.</p>
  }

  return (
    <div className="ml-shell space-y-6">
      <header className="glass-card p-5 sm:p-7">
        <Link
          to={`/category/${slug}`}
          className="inline-flex items-center gap-2 rounded-full border border-stroke bg-white px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:text-primary"
        >
          ← Retour aux niveaux
        </Link>

        <div className="mt-4">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Niveau</p>
          <h1 className="mt-2 font-display text-3xl font-bold text-slate-900 sm:text-4xl">
            {normalizeFrenchText(activeLevel?.title ?? 'Chargement...')}
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600 sm:text-base">
            {normalizeFrenchText(activeLevel?.objective ?? 'Chargement du niveau...')}
          </p>
          <p className="mt-2 text-sm text-slate-500">Catégorie : {normalizeFrenchText(activeCategory?.title ?? '...')}</p>
        </div>
      </header>

      <section className="glass-card p-5 sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div className="rounded-full border border-stroke bg-white px-4 py-2 text-sm text-slate-600">
            {levelQuizzes.length} modules
          </div>
          <label className="w-full max-w-sm">
            <span className="mb-1 block text-xs uppercase tracking-[0.18em] text-slate-500">Recherche de module</span>
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Ex: clustering, regression, politique"
              className="w-full rounded-xl border border-stroke bg-white px-4 py-2.5 text-sm outline-none ring-primary transition focus:ring-2"
            />
          </label>
        </div>

        {categoryLoading ? <p className="text-sm text-slate-500">Chargement des catégories...</p> : null}
        {categoryError ? <p className="text-sm font-medium text-danger">{categoryError}</p> : null}
        {quizLoading ? <p className="text-sm text-slate-500">Chargement des modules...</p> : null}
        {quizError ? <p className="text-sm font-medium text-danger">{quizError}</p> : null}

        {!categoryLoading && !activeCategory ? (
          <p className="rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-sm text-slate-600">
            Cette catégorie est introuvable.
          </p>
        ) : null}

        {!categoryLoading && activeCategory && !activeLevel ? (
          <p className="rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-sm text-slate-600">
            Ce niveau est introuvable.
          </p>
        ) : null}

        {!categoryLoading && activeCategory && activeLevel && !levelIsUnlocked ? (
          <p className="rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-sm text-slate-600">
            Vous devez terminer le niveau ou le module précédent.
          </p>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {levelQuizzes.map((quiz) => {
            const difficulty = moduleDifficulty(quiz.question_count)
            const moduleUnlocked = levelIsUnlocked && (lockedModules.get(quiz.slug) ?? false)
            const canResume = moduleUnlocked && !completedQuizSlugs.has(quiz.slug) && hasQuizInProgress(quiz.slug)
            return (
              <article
                key={quiz.slug}
                className="group rounded-2xl border border-stroke bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-float"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-lg" aria-hidden>
                      {quiz.question_count > 14 ? '🧠' : quiz.question_count > 9 ? '📈' : '🌱'}
                    </p>
                    <h3 className="mt-1 font-display text-lg font-semibold text-slate-900">{normalizeFrenchText(quiz.title)}</h3>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{difficulty}</span>
                </div>

                <div className="mt-3 text-sm text-slate-600">
                  <p>{quiz.question_count} questions</p>
                </div>

                {moduleUnlocked ? (
                  <Link
                    to={`/quiz/${quiz.slug}`}
                    className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition group-hover:bg-primary"
                  >
                    {canResume ? 'Reprendre' : 'Continuer'}
                    <span aria-hidden>→</span>
                  </Link>
                ) : (
                  <div className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-500">
                    Module verrouillé
                  </div>
                )}

                {!moduleUnlocked ? <p className="mt-2 text-xs text-slate-500">Vous devez terminer le niveau ou le module précédent.</p> : null}
              </article>
            )
          })}
        </div>

        {!quizLoading && activeLevel && levelQuizzes.length === 0 ? (
          <p className="mt-4 rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-sm text-slate-500">
            Aucun module ne correspond à la recherche pour ce niveau.
          </p>
        ) : null}
      </section>
    </div>
  )
}
