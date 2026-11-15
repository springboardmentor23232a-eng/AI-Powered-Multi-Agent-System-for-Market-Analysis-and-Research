import { useAuth } from '../auth/AuthContext'
import PreferencesCard from '../components/PreferencesCard'
import ResearchHistoryCard from '../components/ResearchHistoryCard'
import WatchlistCard from '../components/WatchlistCard'
import { Button } from '../components/ui'

export default function WorkspacePage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <h1 className="font-semibold">Stock Research Analyst</h1>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user.email}</span>
            <Button variant="secondary" onClick={logout}>Sign out</Button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-5xl gap-6 px-4 py-8 md:grid-cols-2">
        <WatchlistCard />
        <PreferencesCard />
        <div className="md:col-span-2">
          <ResearchHistoryCard />
        </div>
      </main>
    </div>
  )
}
