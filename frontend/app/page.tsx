import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-full max-w-3xl flex-col justify-center px-6 py-16">
      <p className="font-serif text-pine">Ledger</p>
      <h1 className="mt-3 font-serif text-5xl leading-tight tracking-tight">
        A calm place for income and spending.
      </h1>
      <p className="mt-4 max-w-xl text-lg text-ink/70">
        Register, sign in, add income by source, then log expenditures that deduct from what is left.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/register"
          className="rounded-xl bg-pine px-5 py-3 font-medium text-white hover:bg-pine-dark"
        >
          Create account
        </Link>
        <Link
          href="/login"
          className="rounded-xl border border-ink/15 bg-card px-5 py-3 font-medium hover:bg-white"
        >
          Log in
        </Link>
      </div>
    </main>
  );
}
