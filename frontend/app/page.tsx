import { BackendStatus } from "@/components/BackendStatus";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 dark:bg-black">
      <main className="flex w-full max-w-2xl flex-col items-center gap-8 text-center">
        <span className="rounded-full border border-black/10 px-3 py-1 text-xs font-medium uppercase tracking-widest text-zinc-500 dark:border-white/15 dark:text-zinc-400">
          Phase 0 · Scaffold
        </span>

        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
          CutPoint
        </h1>

        <p className="max-w-md text-lg leading-relaxed text-zinc-600 dark:text-zinc-400">
          AI hairstyle recommendation, virtual try-on, and salon booking —
          built locally, verified end to end.
        </p>

        <BackendStatus />

        <p className="text-sm text-zinc-400 dark:text-zinc-500">
          Frontend (Next.js) and backend (FastAPI) are wired up. Feature
          phases land next.
        </p>
      </main>
    </div>
  );
}
