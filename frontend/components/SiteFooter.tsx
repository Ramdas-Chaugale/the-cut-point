export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-zinc-200 py-6 dark:border-zinc-800">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-2 px-4 text-sm text-zinc-500 sm:flex-row sm:px-6">
        <span>CutPoint — AI hairstyle recommendation &amp; salon booking</span>
        <span>
          An individual project by{" "}
          <span className="font-medium text-zinc-700 dark:text-zinc-300">Ramdas Chaugale</span>
        </span>
      </div>
    </footer>
  );
}
