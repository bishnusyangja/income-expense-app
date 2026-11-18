import Link from "next/link";
import type { ReactNode } from "react";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <Link href="/" className="mb-8 inline-block font-serif text-2xl text-pine">
          Ledger
        </Link>
        <div className="rounded-3xl border border-line bg-card p-8 shadow-[0_20px_50px_rgba(28,22,18,0.08)]">
          <h1 className="font-serif text-3xl tracking-tight">{title}</h1>
          <p className="mt-2 text-ink/65">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
