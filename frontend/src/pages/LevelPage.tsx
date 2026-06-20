import { motion } from 'framer-motion'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import { areAllQuizzesCompleted, hasQuizInProgress } from '../progression'
import type { QuizListItem } from '../types'

function moduleDifficulty(questionCount: number) {
  if (questionCount <= 9) return 'Debutant'
  if (questionCount <= 15) return 'Intermediaire'
  return 'Expert'
}

function moduleEta(questionCount: number) {
  return `${Math.max(8, Math.round(questionCount * 1.3))} min`
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
    if (!activeCategory || !activeLevel) return false

    const orderedLevels = [...activeCategory.levels].sort((a, b) => a.order - b.order)
    const currentIndex = orderedLevels.findIndex((level) => level.slug === activeLevel.slug)
    if (currentIndex <= 0) return true

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
    return <p className="ml-shell text-sm text-rose-500">Niveau introuvable.</p>
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
          to={`/category/${slug}`}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 transition hover:border-ml-500 hover:text-ml-600"
        >
          Retour aux niveaux
        </Link>

        <div className="mt-4 space-y-2">
          <p className="section-eyebrow">Niveau</p>
          <h1 className="text-balance font-display text-3xl font-black text-slate-950 sm:text-4xl">
            {normalizeFrenchText(activeLevel?.title ?? 'Chargement...')}
          </h1>
          <p className="max-w-3xl text-sm text-slate-600 sm:text-base">
            {normalizeFrenchText(activeLevel?.objective ?? 'Chargement du niveau...')}
          </p>
        </div>
      </motion.header>

      <section className="panel p-5 sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-eyebrow">Modules</p>
            <h2 className="section-title">Selectionne un module</h2>
          </div>
          <label className="w-full max-w-sm">
            <span className="mb-1 block text-xs uppercase tracking-[0.16em] text-slate-500">Recherche</span>
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Ex: clustering, regression, politique"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none ring-2 ring-transparent transition focus:border-ml-400 focus:ring-ml-100"
            />
          </label>
        </div>

        {categoryLoading ? <p className="text-sm text-slate-500">Chargement des categories...</p> : null}
        {categoryError ? <p className="text-sm text-rose-500">{categoryError}</p> : null}
        {quizLoading ? <p className="text-sm text-slate-500">Chargement des modules...</p> : null}
        {quizError ? <p className="text-sm text-rose-500">{quizError}</p> : null}

        {!categoryLoading && activeCategory && activeLevel && !levelIsUnlocked ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            Vous devez terminer le niveau precedent pour debloquer celui-ci.
          </p>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {levelQuizzes.map((quiz, index) => {
            const difficulty = moduleDifficulty(quiz.question_count)
            const moduleUnlocked = levelIsUnlocked && (lockedModules.get(quiz.slug) ?? false)
            const canResume = moduleUnlocked && !completedQuizSlugs.has(quiz.slug) && hasQuizInProgress(quiz.slug)

            return (
              <motion.article
                key={quiz.slug}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.05 * index }}
                whileHover={{ y: -3 }}
                className="module-card"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-balance font-display text-lg font-bold text-slate-950">{normalizeFrenchText(quiz.title)}</h3>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{difficulty}</span>
                </div>

                <p className="mt-2 text-sm text-slate-600">{normalizeFrenchText(quiz.description)}</p>

                <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1">{quiz.question_count} questions</span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1">{moduleEta(quiz.question_count)}</span>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Link
                    to={`/module/${quiz.slug}`}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-ml-500 hover:text-ml-600"
                  >
                    Voir le module
                  </Link>

                  {moduleUnlocked ? (
                    <Link
                      to={`/quiz/${quiz.slug}`}
                      className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-ml-600"
                    >
                      {canResume ? 'Reprendre le QCM' : 'Commencer le QCM'}
                    </Link>
                  ) : (
                    <span className="inline-flex items-center rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-500">
                      Module verrouille
                    </span>
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
