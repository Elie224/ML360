import { motion } from 'framer-motion'
import { Link, useParams } from 'react-router-dom'
import { fetchQuizDetail } from '../api'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData } from '../hooks'

function estimateDuration(questionCount: number) {
  const minutes = Math.max(8, Math.round(questionCount * 1.3))
  return `${minutes} min`
}

function difficultyFromQuestionCount(questionCount: number) {
  if (questionCount <= 10) return 'Debutant'
  if (questionCount <= 18) return 'Intermediaire'
  return 'Expert'
}

function buildSkills(title: string) {
  const seed = normalizeFrenchText(title)
  return [
    `Maitriser les concepts cles de ${seed}`,
    'Analyser des scenarios de modelisation',
    'Eviter les erreurs classiques en production',
  ]
}

function buildPrerequisites(levelName: string) {
  if (levelName.toLowerCase().includes('beginner')) {
    return ['Connaissances de base en data', 'Logique mathematique elementaire']
  }
  if (levelName.toLowerCase().includes('intermediate')) {
    return ['Notions de modeles supervises', 'Lecture de metriques de performance']
  }
  return ['Maitrise des fondamentaux ML', 'Experience pratique sur des cas reels']
}

export function ModulePage() {
  const { slug } = useParams()
  const { data: quiz, error, loading } = useAsyncData(() => fetchQuizDetail(slug ?? ''), [slug])

  if (!slug) {
    return <p className="ml-shell text-sm text-rose-500">Module introuvable.</p>
  }

  return (
    <div className="ml-shell space-y-6 py-6">
      <motion.header
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="panel p-6 sm:p-8"
      >
        <Link
          to={quiz ? `/category/${quiz.category.slug}/level/${quiz.level.slug}` : '/'}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 transition hover:border-ml-500 hover:text-ml-600"
        >
          Retour aux modules
        </Link>

        {loading ? <p className="mt-6 text-sm text-slate-500">Chargement du module...</p> : null}
        {error ? <p className="mt-6 text-sm font-medium text-rose-500">{error}</p> : null}

        {quiz ? (
          <div className="mt-6 space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ml-600">Module ML360</p>
            <h1 className="text-balance font-display text-3xl font-extrabold text-slate-950 sm:text-4xl">
              {normalizeFrenchText(quiz.title)}
            </h1>
            <p className="max-w-3xl text-sm text-slate-600 sm:text-base">{normalizeFrenchText(quiz.description)}</p>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="stat-card">
                <p className="stat-label">Niveau</p>
                <p className="stat-value">{quiz.source_level_name}</p>
              </div>
              <div className="stat-card">
                <p className="stat-label">Questions</p>
                <p className="stat-value">{quiz.questions.length}</p>
              </div>
              <div className="stat-card">
                <p className="stat-label">Duree estimee</p>
                <p className="stat-value">{estimateDuration(quiz.questions.length)}</p>
              </div>
              <div className="stat-card">
                <p className="stat-label">Difficulte</p>
                <p className="stat-value">{difficultyFromQuestionCount(quiz.questions.length)}</p>
              </div>
            </div>
          </div>
        ) : null}
      </motion.header>

      {quiz ? (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
          className="grid gap-4 lg:grid-cols-2"
        >
          <article className="panel p-6">
            <h2 className="font-display text-xl font-bold text-slate-950">Competences acquises</h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              {buildSkills(quiz.title).map((item) => (
                <li key={item} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
                  {item}
                </li>
              ))}
            </ul>
          </article>

          <article className="panel p-6">
            <h2 className="font-display text-xl font-bold text-slate-950">Prerequis</h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              {buildPrerequisites(quiz.source_level_name).map((item) => (
                <li key={item} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
                  {item}
                </li>
              ))}
            </ul>
          </article>
        </motion.section>
      ) : null}

      {quiz ? (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08 }}
          className="panel p-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Pret a demarrer</p>
              <h3 className="font-display text-2xl font-bold text-slate-950">Commencer le QCM</h3>
            </div>
            <Link
              to={`/quiz/${quiz.slug}`}
              className="inline-flex items-center gap-2 rounded-xl bg-ml-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-ml-700"
            >
              Commencer le QCM
              <span aria-hidden>{'->'}</span>
            </Link>
          </div>
        </motion.section>
      ) : null}
    </div>
  )
}
