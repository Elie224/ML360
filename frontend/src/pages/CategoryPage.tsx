import { motion } from 'framer-motion'
import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import { areAllQuizzesCompleted } from '../progression'
import type { QuizListItem } from '../types'

const levelTheme: Record<number, { badge: string; title: string; tone: string; description: string }> = {
  1: {
    badge: 'DEB',
    title: 'Debutant',
    tone: 'text-emerald-700',
    description: 'Acquerir les fondamentaux et la logique des modeles.',
  },
  2: {
    badge: 'INT',
    title: 'Intermediaire',
    tone: 'text-orange-700',
    description: 'Appliquer les methodes sur des cas progressifs.',
  },
  3: {
    badge: 'EXP',
    title: 'Expert',
    tone: 'text-violet-700',
    description: 'Raisonner avec robustesse sur des scenarios complexes.',
  },
  4: {
    badge: 'PRO',
    title: 'Maitrise',
    tone: 'text-blue-700',
    description: 'Consolider les decisions produit et production.',
  },
}

function resolveLevelQuizzes(levelOrder: number, levelSlug: string, quizzes: QuizListItem[]) {
  const direct = quizzes.filter((quiz) => quiz.level.slug === levelSlug)
  if (direct.length > 0) return direct

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
    if (!slug || !categories?.length) return null
    return categories.find((category) => category.slug === slug) ?? null
  }, [categories, slug])

  const levelSections = useMemo(() => {
    if (!activeCategory) return []

    const orderedLevels = [...activeCategory.levels].sort((a, b) => a.order - b.order)
    const items = quizzes ?? []

    return orderedLevels.map((level, index) => {
      const levelQuizzes = resolveLevelQuizzes(level.order, level.slug, items)
      const previousLevel = orderedLevels[index - 1]
      const previousLevelQuizzes = previousLevel ? resolveLevelQuizzes(previousLevel.order, previousLevel.slug, items) : []
      const completedModules = levelQuizzes.filter((quiz) => completedQuizSlugs.has(quiz.slug)).length
      const progress = levelQuizzes.length ? Math.round((completedModules / levelQuizzes.length) * 100) : 0

      return {
        level,
        unlocked: index === 0 || areAllQuizzesCompleted(previousLevelQuizzes, completedQuizSlugs),
        totalModules: levelQuizzes.length,
        totalQuestions: levelQuizzes.reduce((sum, quiz) => sum + quiz.question_count, 0),
        progress,
      }
    })
  }, [activeCategory, completedQuizSlugs, quizzes])

  if (!slug) {
    return <p className="ml-shell text-sm text-rose-500">Categorie introuvable.</p>
  }

  return (
    <div className="ml-shell space-y-6 py-6">
      <motion.header
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="panel p-6 sm:p-8"
      >
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 transition hover:border-ml-500 hover:text-ml-600"
        >
          Retour aux parcours
        </Link>

        <div className="mt-4 space-y-2">
          <p className="section-eyebrow">Parcours categorie</p>
          <h1 className="text-balance font-display text-3xl font-black text-slate-950 sm:text-4xl">
            {normalizeFrenchText(activeCategory?.title ?? 'Chargement...')}
          </h1>
          <p className="max-w-3xl text-sm text-slate-600 sm:text-base">
            {normalizeFrenchText(activeCategory?.description ?? 'Chargement de la categorie...')}
          </p>
        </div>
      </motion.header>

      <section className="panel p-5 sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-eyebrow">Systeme de niveaux</p>
            <h2 className="section-title">Progression verticale</h2>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {activeCategory?.levels.length ?? 0} niveaux
          </span>
        </div>

        {categoryLoading ? <p className="text-sm text-slate-500">Chargement des categories...</p> : null}
        {categoryError ? <p className="text-sm text-rose-500">{categoryError}</p> : null}
        {quizLoading ? <p className="text-sm text-slate-500">Chargement des modules...</p> : null}
        {quizError ? <p className="text-sm text-rose-500">{quizError}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {levelSections.map(({ level, unlocked, totalModules, totalQuestions, progress }, index) => {
            const theme = levelTheme[level.order] ?? levelTheme[1]
            return (
              <motion.article
                key={level.slug}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.06 * index }}
                whileHover={{ y: -3 }}
                className="level-card"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-8 min-w-8 items-center justify-center rounded-lg bg-slate-100 px-2 text-xs font-bold text-slate-700">
                        {theme.badge}
                      </span>
                      <p className={`text-xs font-semibold uppercase tracking-[0.14em] ${theme.tone}`}>
                        Niveau {level.order} - {theme.title}
                      </p>
                    </div>
                    <h3 className="font-display text-xl font-bold text-slate-950">{normalizeFrenchText(level.objective)}</h3>
                    <p className="text-sm text-slate-600">{theme.description}</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{progress}%</span>
                </div>

                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    className="h-full rounded-full bg-gradient-to-r from-ml-500 to-cyan-500"
                  />
                </div>

                <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1">{totalModules} modules</span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1">{totalQuestions} questions</span>
                </div>

                <div className="mt-4">
                  {unlocked ? (
                    <Link
                      to={`/category/${slug}/level/${level.slug}`}
                      className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-ml-600"
                    >
                      Ouvrir ce niveau
                      <span aria-hidden>{'->'}</span>
                    </Link>
                  ) : (
                    <div className="inline-flex items-center rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-500">
                      Niveau verrouille
                    </div>
                  )}
                </div>
              </motion.article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
