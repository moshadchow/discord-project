import { apiClient } from '../api/client';

export function HomePage() {
  const apiBaseUrl = apiClient.defaults.baseURL;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8">
        <header className="border-b border-slate-200 pb-5">
          <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
            Discord Issue Management
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Admin Portal</h1>
        </header>

        <section className="grid flex-1 gap-4 py-6 lg:grid-cols-[240px_minmax(0,1fr)_280px]">
          <aside className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-700">Channels</h2>
          </aside>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-700">
              Conversation & Attachments
            </h2>
            <p className="mt-3 text-sm text-slate-500">
              Frontend foundation is ready for issue workflows.
            </p>
          </section>

          <aside className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-700">
              Issue Details
            </h2>
          </aside>
        </section>

        <footer className="border-t border-slate-200 pt-4 text-sm text-slate-500">
          API base URL: {apiBaseUrl}
        </footer>
      </div>
    </main>
  );
}
