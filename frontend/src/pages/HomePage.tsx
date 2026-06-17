import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchQuizzes } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData, useCompletedQuizSlugs } from '../hooks'
import type { Category, QuizListItem } from '../types'

const categoryVisuals: Record<string, { icon: string; gradient: string; illustration: string }> = {
  'apprentissage-supervise': {
    icon: '📊',
    illustration: 'Régression, classification, impact métier',
    gradient: 'from-blue-600 to-indigo-500',
  },
  'apprentissage-non-supervise': {
    icon: '🧭',
    illustration: 'Clustering, structure cachée, exploration',
    gradient: 'from-cyan-600 to-blue-600',
  },
  'apprentissage-semi-supervise': {
    icon: '🧬',
    illustration: 'Pseudo-labels, données rares, intelligence hybride',
    gradient: 'from-violet-600 to-fuchsia-500',
  },
  'apprentissage-par-renforcement': {
    icon: '🎯',
    illustration: 'Agent, récompense, stratégie adaptative',
    gradient: 'from-amber-500 to-orange-500',
  },
}

function computeCategoryStats(category: Category, quizzes: QuizListItem[]) {
  const modules = quizzes.filter((quiz) => quiz.category.slug === category.slug)
  return {
    modules: modules.length,
    questions: modules.reduce((sum, quiz) => sum + quiz.question_count, 0),
  }
}

export function HomePage() {
  const { data: categories, error: categoryError, loading: categoryLoading } = useAsyncData(fetchCategories, [])
  const { data: allQuizzes } = useAsyncData(() => fetchQuizzes(), [])
  const [searchCategory, setSearchCategory] = useState('')
  const [sortBy, setSortBy] = useState<'title' | 'modules' | 'questions'>('modules')
  useCompletedQuizSlugs()

  const totalModules = allQuizzes?.length ?? 0

  const categoryCards = useMemo(
    () =>
      (categories ?? []).map((category) => {
        const visual = categoryVisuals[category.slug] ?? {
          icon: '🤖',
          illustration: 'Parcours ML moderne',
          gradient: 'from-blue-600 to-violet-600',
        }
        return {
          category,
          visual,
          ...computeCategoryStats(category, allQuizzes ?? []),
        }
      }),
    [allQuizzes, categories],
  )

  const filteredCategoryCards = useMemo(() => {
    const search = searchCategory.trim().toLowerCase()
    const visible = !search
      ? [...categoryCards]
      : categoryCards.filter(({ category, visual }) =>
          [category.title, category.description, visual.illustration].join(' ').toLowerCase().includes(search),
        )

    if (sortBy === 'title') {
      visible.sort((a, b) => a.category.title.localeCompare(b.category.title, 'fr'))
      return visible
    }

    if (sortBy === 'questions') {
      visible.sort((a, b) => b.questions - a.questions)
      return visible
    }

    visible.sort((a, b) => b.modules - a.modules)
    return visible
  }, [categoryCards, searchCategory, sortBy])

  return (
    <div className="ml-shell space-y-6">
      <header className="glass-card relative overflow-hidden p-5 sm:p-7">
        <div className="pointer-events-none absolute inset-0 data-grid-bg opacity-55" />
        <div className="relative space-y-4">
          <div className="inline-flex items-center gap-3 rounded-full border border-stroke bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.2em] text-primary">
            <img src="/ml360-logo.jpg" alt="Logo ML360" className="h-7 w-7 rounded-lg object-contain" />
            ML360
          </div>
          <div>
            <h1 className="font-display text-3xl font-extrabold leading-tight text-slate-900 sm:text-4xl lg:text-5xl">
              Choisis une catégorie et commence.
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-600 sm:text-base">
              Navigation simple et directe : sélectionne une catégorie, puis un niveau, puis un module.
            </p>
          </div>
        </div>
      </header>

      <section id="categories" className="glass-card p-5 sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Catégories</p>
            <h2 className="font-display text-2xl font-bold text-slate-900 sm:text-3xl">Choisis ton terrain de jeu ML</h2>
          </div>
          <div className="rounded-full border border-stroke bg-white px-4 py-2 text-sm text-slate-600">
            {categories?.length ?? 0} catégories • {totalModules} modules
          </div>
        </div>

        <div className="mb-5 grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px]">
          <label>
            <span className="mb-1 block text-xs uppercase tracking-[0.18em] text-slate-500">Rechercher une catégorie</span>
            <input
              type="search"
              value={searchCategory}
              onChange={(event) => setSearchCategory(event.target.value)}
              placeholder="Ex: supervise, reinforcement, clustering"
              className="w-full rounded-xl border border-stroke bg-white px-4 py-2.5 text-sm outline-none ring-primary transition focus:ring-2"
            />
          </label>

          <label>
            <span className="mb-1 block text-xs uppercase tracking-[0.18em] text-slate-500">Trier</span>
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as 'title' | 'modules' | 'questions')}
              className="w-full rounded-xl border border-stroke bg-white px-4 py-2.5 text-sm outline-none ring-primary transition focus:ring-2"
            >
              <option value="modules">Par nombre de modules</option>
              <option value="questions">Par nombre de questions</option>
              <option value="title">Par ordre alphabétique</option>
            </select>
          </label>
        </div>

        {categoryLoading ? <p className="text-sm text-slate-500">Chargement des catégories...</p> : null}
        {categoryError ? <p className="text-sm font-medium text-danger">{categoryError}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {filteredCategoryCards.map(({ category, visual, modules, questions }) => {
            return (
              <article
                key={category.slug}
                className="group relative overflow-hidden rounded-3xl border border-stroke bg-white/95 p-5 shadow-premium transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${visual.gradient} opacity-0 transition group-hover:opacity-10`} />
                <div className="relative space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-xl">
                        {visual.icon}
                      </span>
                      <h3 className="mt-3 font-display text-xl font-bold text-slate-900">{normalizeFrenchText(category.title)}</h3>
                      <p className="mt-1 text-sm text-slate-500">{visual.illustration}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-slate-500">Modules</p>
                      <p className="font-display text-lg font-bold text-slate-900">{modules}</p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-slate-500">Questions</p>
                      <p className="font-display text-lg font-bold text-slate-900">{questions}</p>
                    </div>
                  </div>

                  <Link
                    to={`/category/${category.slug}`}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-primary hover:text-primary"
                  >
                    Explorer
                    <span aria-hidden>→</span>
                  </Link>
                </div>
              </article>
            )
          })}
        </div>

        {!categoryLoading && !categoryError && filteredCategoryCards.length === 0 ? (
          <p className="mt-4 rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-sm text-slate-600">
            Aucune catégorie ne correspond à ta recherche.
          </p>
        ) : null}
      </section>

      <section className="glass-card p-5 sm:p-6">
        <div className="rounded-2xl border border-dashed border-stroke bg-slate-50 p-5 text-center text-sm text-slate-600">
          Clique sur Explorer pour ouvrir une page dédiée à la catégorie choisie.
        </div>
      </section>
    </div>
  )
}