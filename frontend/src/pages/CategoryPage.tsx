import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import { areAllQuizzesCompleted } from '../progression'
import type { QuizListItem } from '../types'

const levelTheme: Record<number, { icon: string; label: string; color: string; text: string; description: string }> = {
  1: {
    icon: '🟢',
    label: 'Débutant',
    color: 'bg-emerald-500',
    text: 'text-emerald-700',
    description: 'Pose les bases et construis des réflexes solides.',
  },
  2: {
    icon: '🔵',
    label: 'Consolidation',
    color: 'bg-sky-500',
    text: 'text-sky-700',
    description: 'Relie théorie et pratique avec des cas progressifs.',
  },
  3: {
    icon: '🟣',
    label: 'Maîtrise',
    color: 'bg-violet-500',
    text: 'text-violet-700',
    description: 'Développe intuition, robustesse et esprit critique.',
  },
  4: {
    icon: '🟡',
    label: 'Expert',
    color: 'bg-amber-400',
    text: 'text-amber-700',
    description: 'Prends des décisions pro dans des scénarios complexes.',
  },
}

function resolveLevelQuizzes(levelOrder: number, levelSlug: string, quizzes: QuizListItem[]) {
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

export function CategoryPage() {
  const { slug } = useParams()
  const completedQuizSlugs = useCompletedQuizSlugs()

  const { data: categories, error: categoryError, loading: categoryLoading } = useAsyncData(fetchCategories, [])
  const { data: quizzes, error: quizError, loading: quizLoading } = useAsyncData(
    () => (slug ? fetchQuizzes(slug) : Promise.resolve([])),
    [slug],
  )

  const activeCategory = useMemo(() => {
    if (!slug || !categories?.length) {
      return null
    }
    return categories.find((category) => category.slug === slug) ?? null
  }, [categories, slug])

  const levelSections = useMemo(() => {
    if (!activeCategory) {
      return []
    }

    const orderedLevels = [...activeCategory.levels].sort((a, b) => a.order - b.order)
    const items = quizzes ?? []
    return orderedLevels.map((level, index) => {
      const levelQuizzes = resolveLevelQuizzes(level.order, level.slug, items)
      const previousLevel = orderedLevels[index - 1]
      const previousLevelQuizzes = previousLevel
        ? resolveLevelQuizzes(previousLevel.order, previousLevel.slug, items)
        : []
      return {
        level,
        unlocked: index === 0 || areAllQuizzesCompleted(previousLevelQuizzes, completedQuizSlugs),
        totalModules: levelQuizzes.length,
        totalQuestions: levelQuizzes.reduce((sum, quiz) => sum + quiz.question_count, 0),
      }
    })
  }, [activeCategory, completedQuizSlugs, quizzes])

  if (!slug) {
    return <p className="ml-shell text-sm text-danger">Catégorie introuvable.</p>
  }

  return (
    <div className="ml-shell space-y-6">
      <header className="glass-card p-5 sm:p-7">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-full border border-stroke bg-white px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:text-primary"
        >
          ← Retour aux catégories
        </Link>

        <div className="mt-4">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Parcours catégorie</p>
          <h1 className="mt-2 font-display text-3xl font-bold text-slate-900 sm:text-4xl">
            {normalizeFrenchText(activeCategory?.title ?? 'Chargement...')}
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600 sm:text-base">
            {normalizeFrenchText(activeCategory?.description ?? 'Chargement de la catégorie...')}
          </p>
        </div>
      </header>

      <section className="glass-card p-5 sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div className="rounded-full border border-stroke bg-white px-4 py-2 text-sm text-slate-600">
            {activeCategory?.levels.length ?? 0} niveaux
          </div>
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

        <div className="grid gap-4 lg:grid-cols-2">
          {levelSections.map(({ level, unlocked, totalModules, totalQuestions: levelQuestions }) => {
            const theme = levelTheme[level.order] ?? levelTheme[1]
            const canOpen = unlocked

            return (
              <article key={level.slug} className="level-node animate-slide-up">
                <div className="space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg" aria-hidden>
                        {theme.icon}
                      </span>
                      <p className={`text-xs font-bold uppercase tracking-[0.16em] ${theme.text}`}>
                        Niveau {level.order} • {theme.label}
                      </p>
                    </div>
                    <h3 className="font-display text-xl font-bold text-slate-900">{normalizeFrenchText(level.objective)}</h3>
                    <p className="text-sm text-slate-600">{theme.description}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600">
                  <span className="rounded-full bg-slate-100 px-3 py-1">{totalModules} modules</span>
                  <span className="rounded-full bg-slate-100 px-3 py-1">{levelQuestions} questions</span>
                </div>

                {canOpen ? (
                  <Link
                    to={`/category/${slug}/level/${level.slug}`}
                    className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary"
                  >
                    Ouvrir ce niveau
                    <span aria-hidden>→</span>
                  </Link>
                ) : (
                  <div className="inline-flex items-center gap-2 rounded-xl bg-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-500">
                    Niveau verrouillé
                  </div>
                )}

                {!canOpen ? <p className="text-xs text-slate-500">Vous devez terminer le niveau ou le module précédent.</p> : null}
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
