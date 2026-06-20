import { motion } from 'framer-motion'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import type { Category, QuizListItem } from '../types'

type CategoryVisual = {
  soft: string
  icon: string
  subtitle: string
}

const categoryVisuals: Record<string, CategoryVisual> = {
  'apprentissage-supervise': {
    soft: 'from-blue-50 to-blue-100',
    icon: 'SUP',
    subtitle: 'Regression, classification, prediction',
  },
  'apprentissage-non-supervise': {
    soft: 'from-violet-50 to-violet-100',
    icon: 'UNS',
    subtitle: 'Clustering, structure cachee, segmentation',
  },
  'apprentissage-semi-supervise': {
    soft: 'from-cyan-50 to-cyan-100',
    icon: 'SEMI',
    subtitle: 'Pseudo-labels, rarete de labels, robustesse',
  },
  'apprentissage-par-renforcement': {
    soft: 'from-orange-50 to-orange-100',
    icon: 'RL',
    subtitle: 'Agent, decision sequentielle, recompense',
  },
}

function computeCategoryStats(category: Category, quizzes: QuizListItem[]) {
  const modules = quizzes.filter((quiz) => quiz.category.slug === category.slug)
  return {
    modules: modules.length,
    questions: modules.reduce((sum, quiz) => sum + quiz.question_count, 0),
  }
}

function buildRoadmap(categories: Category[], quizzes: QuizListItem[], completedSet: Set<string>) {
  const order = [
    'apprentissage-supervise',
    'apprentissage-non-supervise',
    'apprentissage-semi-supervise',
    'apprentissage-par-renforcement',
  ]

  const bySlug = new Map(categories.map((cat) => [cat.slug, cat]))

  return order
    .map((slug, index) => {
      const category = bySlug.get(slug)
      if (!category) return null

      const categoryQuizzes = quizzes.filter((quiz) => quiz.category.slug === slug)
      const completed = categoryQuizzes.filter((quiz) => completedSet.has(quiz.slug)).length
      const progress = categoryQuizzes.length ? Math.round((completed / categoryQuizzes.length) * 100) : 0

      return {
        id: slug,
        order: index + 1,
        title: normalizeFrenchText(category.title),
        modules: categoryQuizzes.length,
        progress,
        difficulty: index === 0 ? 'Debutant' : index < 3 ? 'Intermediaire' : 'Expert',
      }
    })
    .filter(Boolean)
}

function scrollToSection(id: 'parcours' | 'roadmap') {
  const target = document.getElementById(id)
  if (!target) return
  target.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export function HomePage() {
  const completedQuizSlugs = useCompletedQuizSlugs()
  const { data: categories, error: categoryError, loading: categoryLoading } = useAsyncData(fetchCategories, [])
  const { data: allQuizzes, error: quizError } = useAsyncData(() => fetchQuizzes(), [])

  const cards = useMemo(
    () =>
      (categories ?? []).map((category) => ({
        category,
        visual: categoryVisuals[category.slug] ?? {
          soft: 'from-slate-50 to-slate-100',
          icon: 'ML',
          subtitle: 'Parcours machine learning',
        },
        ...computeCategoryStats(category, allQuizzes ?? []),
      })),
    [allQuizzes, categories],
  )

  const roadmap = useMemo(
    () => buildRoadmap(categories ?? [], allQuizzes ?? [], completedQuizSlugs),
    [allQuizzes, categories, completedQuizSlugs],
  )

  return (
    <div className="ml-shell space-y-8 py-6">
      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="hero-panel"
      >
        <div className="hero-grid">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-3 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-white/85">
              <img src="/ml360-mark.svg" alt="Logo ML360" className="h-7 w-7" />
              ML360
            </div>
            <h1 className="text-balance font-display text-4xl font-black text-white sm:text-5xl lg:text-6xl">
              Maitrise le Machine Learning de A a Z
            </h1>
            <p className="max-w-3xl text-sm text-white/80 sm:text-base">
              Revise, progresse et valide tes connaissances grace a plus de 1700 questions reparties sur les 4 grands
              paradigmes du Machine Learning.
            </p>
            <div className="flex flex-wrap gap-3">
              <button type="button" onClick={() => scrollToSection('parcours')} className="cta-primary">
                Commencer maintenant
              </button>
              <button type="button" onClick={() => scrollToSection('roadmap')} className="cta-ghost">
                Explorer les parcours
              </button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="kpi-card">
              <p className="kpi-label">Modules</p>
              <p className="kpi-value">88</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-label">Questions</p>
              <p className="kpi-value">1760</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-label">Parcours</p>
              <p className="kpi-value">4</p>
            </div>
            <div className="kpi-card">
              <p className="kpi-label">Niveaux</p>
              <p className="kpi-value">4</p>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section
        id="parcours"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1 }}
        className="panel p-5 sm:p-7"
      >
        <div className="mb-5">
          <p className="section-eyebrow">Parcours ML</p>
          <h2 className="section-title">Choisis ton parcours</h2>
        </div>

        {categoryLoading ? <p className="text-sm text-slate-500">Chargement des parcours...</p> : null}
        {categoryError ? <p className="text-sm text-rose-500">{categoryError}</p> : null}
        {quizError ? <p className="text-sm text-rose-500">{quizError}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {cards.map(({ category, visual, modules, questions }, index) => (
            <motion.article
              key={category.slug}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.08 * index }}
              whileHover={{ y: -4, scale: 1.01 }}
              className="category-card"
            >
              <div className={`absolute inset-0 -z-10 bg-gradient-to-br ${visual.soft} opacity-80`} />
              <div className="flex items-start justify-between gap-3">
                <span className="inline-flex h-10 min-w-10 items-center justify-center rounded-xl bg-white text-xs font-bold text-slate-900 shadow-sm">
                  {visual.icon}
                </span>
                <span className="rounded-full bg-white/80 px-2.5 py-1 text-xs font-semibold text-slate-700">{modules} modules</span>
              </div>

              <div className="mt-3">
                <h3 className="font-display text-xl font-bold text-slate-950">{normalizeFrenchText(category.title)}</h3>
                <p className="mt-1 text-sm text-slate-600">{visual.subtitle}</p>
              </div>

              <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
                <span>{questions} questions</span>
                <Link to={`/category/${category.slug}`} className="font-semibold text-ml-700 transition hover:text-ml-600">
                  {'Explorer ->'}
                </Link>
              </div>
            </motion.article>
          ))}
        </div>
      </motion.section>

      <motion.section
        id="roadmap"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.14 }}
        className="panel p-5 sm:p-7"
      >
        <article>
          <p className="section-eyebrow">Roadmap interactive</p>
          <h2 className="section-title">Ton chemin de progression</h2>

          <div className="roadmap mt-5">
            <div className="roadmap-line" />
            {roadmap.map((step) => (
              <div key={step?.id} className="roadmap-item">
                <div className="roadmap-node" />
                <div className="roadmap-card">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Etape {step?.order}</p>
                      <h3 className="font-display text-lg font-bold text-slate-950">{step?.title}</h3>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{step?.progress}%</span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-4">
                    <span>{step?.modules} modules</span>
                    <span>{step?.difficulty}</span>
                    <span>4 niveaux</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </article>
      </motion.section>
    </div>
  )
}
