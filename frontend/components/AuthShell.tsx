import { Scissors } from "lucide-react";

/** Shared input styling for every form field in the auth pages. */
export const INPUT =
  "w-full rounded-lg border border-line-strong bg-surface px-3 py-2.5 text-sm text-ink " +
  "placeholder:text-ink-faint transition-colors focus:border-accent focus:outline-none " +
  "focus:ring-2 focus:ring-accent/20";

/**
 * A labelled form field.
 *
 * The forms used to rely on placeholder text alone, which disappears as soon
 * as you start typing and is not announced as a label by screen readers. The
 * label stays visible and the placeholder is now only an example.
 */
export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-ink-soft">{label}</span>
      {children}
      {hint ? <span className="text-xs text-ink-faint">{hint}</span> : null}
    </label>
  );
}

/** Inline form error, styled as a panel so it is hard to miss. */
export function ErrorNote({ children }: { children: React.ReactNode }) {
  return (
    <p
      role="alert"
      className="rounded-lg border border-negative-line bg-negative-soft px-3 py-2 text-sm text-negative"
    >
      {children}
    </p>
  );
}

/**
 * The card the auth forms sit in.
 *
 * Previously these forms floated directly on the page background, which left
 * them looking unfinished next to the rest of the app. Everything now sits on
 * a raised card, vertically centred, with the inputs a shade darker than the
 * card so the fields read as recessed.
 */
export function AuthShell({
  title,
  subtitle,
  wide,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  wide?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div
      className={`mx-auto flex w-full flex-1 flex-col justify-center px-4 py-12 sm:px-6 ${
        wide ? "max-w-xl" : "max-w-md"
      }`}
    >
      <div className="rounded-2xl border border-line bg-surface-raised p-6 shadow-md sm:p-8">
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent-soft text-accent">
          <Scissors className="h-5 w-5" aria-hidden />
        </span>
        <h1 className="mt-4 text-2xl font-bold text-ink">{title}</h1>
        <p className="mt-1.5 text-sm text-ink-soft">{subtitle}</p>
        {children}
      </div>
      {footer ? <div className="mt-5 text-center text-sm">{footer}</div> : null}
    </div>
  );
}
