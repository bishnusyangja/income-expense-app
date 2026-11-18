"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Field, TextInput, inputClass } from "@/components/Field";
import {
  ApiError,
  addExpenditure,
  addIncome,
  listExpenditures,
  listIncomes,
} from "@/lib/api";
import { clearSession, getAccessToken, getStoredUser } from "@/lib/auth";
import type { Expenditure, Income, User } from "@/lib/types";

function formatAmount(value: string) {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [incomes, setIncomes] = useState<Income[]>([]);
  const [expenditures, setExpenditures] = useState<Expenditure[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [incomeForm, setIncomeForm] = useState({ title: "", amount: "", note: "" });
  const [incomeErrors, setIncomeErrors] = useState<Record<string, string>>({});
  const [incomeSaving, setIncomeSaving] = useState(false);

  const [expenseForm, setExpenseForm] = useState({
    income_id: "",
    title: "",
    amount: "",
    note: "",
  });
  const [expenseErrors, setExpenseErrors] = useState<Record<string, string>>({});
  const [expenseSaving, setExpenseSaving] = useState(false);

  async function refresh() {
    const [incomeRes, expenseRes] = await Promise.all([listIncomes(), listExpenditures()]);
    setIncomes(incomeRes.data);
    setExpenditures(expenseRes.data);
  }

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    setUser(getStoredUser());
    refresh()
      .catch((error) => {
        if (error instanceof ApiError && error.status === 401) {
          clearSession();
          router.replace("/login");
          return;
        }
        setLoadError(error instanceof Error ? error.message : "Could not load data");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const totals = useMemo(() => {
    const incomeTotal = incomes.reduce((sum, item) => sum + Number(item.amount), 0);
    const remaining = incomes.reduce((sum, item) => sum + Number(item.remaining), 0);
    const spent = incomeTotal - remaining;
    return { incomeTotal, remaining, spent };
  }, [incomes]);

  async function onAddIncome(event: FormEvent) {
    event.preventDefault();
    setIncomeSaving(true);
    setIncomeErrors({});
    try {
      await addIncome({
        title: incomeForm.title,
        amount: incomeForm.amount,
        note: incomeForm.note || undefined,
      });
      setIncomeForm({ title: "", amount: "", note: "" });
      await refresh();
    } catch (error) {
      if (error instanceof ApiError) setIncomeErrors(error.errors);
    } finally {
      setIncomeSaving(false);
    }
  }

  async function onAddExpense(event: FormEvent) {
    event.preventDefault();
    setExpenseSaving(true);
    setExpenseErrors({});
    try {
      await addExpenditure({
        income_id: Number(expenseForm.income_id),
        title: expenseForm.title,
        amount: expenseForm.amount,
        note: expenseForm.note || undefined,
      });
      setExpenseForm((current) => ({ ...current, title: "", amount: "", note: "" }));
      await refresh();
    } catch (error) {
      if (error instanceof ApiError) setExpenseErrors(error.errors);
    } finally {
      setExpenseSaving(false);
    }
  }

  function logout() {
    clearSession();
    router.replace("/login");
  }

  if (loading) {
    return <p className="px-6 py-16 text-center text-ink/60">Loading your ledger...</p>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/" className="font-serif text-2xl text-pine">
            Ledger
          </Link>
          <p className="mt-1 text-ink/65">
            {user ? `Signed in as ${user.first_name} ${user.last_name}` : "Your money at a glance"}
          </p>
        </div>
        <button
          type="button"
          onClick={logout}
          className="rounded-xl border border-ink/15 px-4 py-2 text-sm hover:bg-white"
        >
          Log out
        </button>
      </header>

      {loadError ? (
        <p className="mb-6 rounded-xl bg-clay/10 px-4 py-3 text-clay">{loadError}</p>
      ) : null}

      <section className="mb-8 grid gap-4 sm:grid-cols-3">
        <SummaryCard label="Total income" value={formatAmount(String(totals.incomeTotal))} />
        <SummaryCard label="Spent" value={formatAmount(String(totals.spent))} accent="clay" />
        <SummaryCard label="Remaining" value={formatAmount(String(totals.remaining))} accent="pine" />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-serif text-2xl">Add income</h2>
          <form onSubmit={onAddIncome} className="mt-5 space-y-4">
            <Field label="Title" error={incomeErrors.title}>
              <TextInput
                value={incomeForm.title}
                onChange={(event) =>
                  setIncomeForm((current) => ({ ...current, title: event.target.value }))
                }
                placeholder="Salary"
                required
              />
            </Field>
            <Field label="Amount" error={incomeErrors.amount}>
              <TextInput
                value={incomeForm.amount}
                onChange={(event) =>
                  setIncomeForm((current) => ({ ...current, amount: event.target.value }))
                }
                placeholder="1000.00"
                inputMode="decimal"
                required
              />
            </Field>
            <Field label="Note" error={incomeErrors.note}>
              <TextInput
                value={incomeForm.note}
                onChange={(event) =>
                  setIncomeForm((current) => ({ ...current, note: event.target.value }))
                }
                placeholder="Optional"
              />
            </Field>
            <button
              type="submit"
              disabled={incomeSaving}
              className="rounded-xl bg-pine px-4 py-2.5 font-medium text-white hover:bg-pine-dark disabled:opacity-60"
            >
              {incomeSaving ? "Saving..." : "Add income"}
            </button>
          </form>
        </article>

        <article className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-serif text-2xl">Add expenditure</h2>
          <p className="mt-1 text-sm text-ink/60">Deducted from the selected income remaining balance.</p>
          <form onSubmit={onAddExpense} className="mt-5 space-y-4">
            {expenseErrors.non_field ? (
              <p className="text-sm text-clay">{expenseErrors.non_field}</p>
            ) : null}
            <Field label="Income source" error={expenseErrors.income_id}>
              <select
                className={inputClass}
                value={expenseForm.income_id}
                onChange={(event) =>
                  setExpenseForm((current) => ({ ...current, income_id: event.target.value }))
                }
                required
              >
                <option value="">Select income</option>
                {incomes.map((income) => (
                  <option key={income.id} value={income.id}>
                    {income.title} — {formatAmount(income.remaining)} left
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Title" error={expenseErrors.title}>
              <TextInput
                value={expenseForm.title}
                onChange={(event) =>
                  setExpenseForm((current) => ({ ...current, title: event.target.value }))
                }
                placeholder="Groceries"
                required
              />
            </Field>
            <Field label="Amount" error={expenseErrors.amount}>
              <TextInput
                value={expenseForm.amount}
                onChange={(event) =>
                  setExpenseForm((current) => ({ ...current, amount: event.target.value }))
                }
                placeholder="40.00"
                inputMode="decimal"
                required
              />
            </Field>
            <Field label="Note" error={expenseErrors.note}>
              <TextInput
                value={expenseForm.note}
                onChange={(event) =>
                  setExpenseForm((current) => ({ ...current, note: event.target.value }))
                }
                placeholder="Optional"
              />
            </Field>
            <button
              type="submit"
              disabled={expenseSaving || incomes.length === 0}
              className="rounded-xl bg-clay px-4 py-2.5 font-medium text-white hover:bg-clay/90 disabled:opacity-60"
            >
              {expenseSaving ? "Saving..." : "Add expenditure"}
            </button>
          </form>
        </article>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-serif text-2xl">Income</h2>
          {incomes.length === 0 ? (
            <p className="mt-4 text-ink/60">No income yet.</p>
          ) : (
            <ul className="mt-4 divide-y divide-line">
              {incomes.map((income) => (
                <li key={income.id} className="flex items-start justify-between gap-4 py-3">
                  <div>
                    <p className="font-medium">{income.title}</p>
                    <p className="text-sm text-ink/55">{income.note || "No note"}</p>
                  </div>
                  <div className="text-right">
                    <p>{formatAmount(income.amount)}</p>
                    <p className="text-sm text-pine">{formatAmount(income.remaining)} left</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-3xl border border-line bg-card p-6">
          <h2 className="font-serif text-2xl">Expenditures</h2>
          {expenditures.length === 0 ? (
            <p className="mt-4 text-ink/60">No spending yet.</p>
          ) : (
            <ul className="mt-4 divide-y divide-line">
              {expenditures.map((item) => (
                <li key={item.id} className="flex items-start justify-between gap-4 py-3">
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="text-sm text-ink/55">{item.note || "No note"}</p>
                  </div>
                  <p className="text-clay">{formatAmount(item.amount)}</p>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "pine" | "clay";
}) {
  const valueClass =
    accent === "clay" ? "text-clay" : accent === "pine" ? "text-pine" : "text-ink";
  return (
    <div className="rounded-3xl border border-line bg-card p-5">
      <p className="text-sm text-ink/60">{label}</p>
      <p className={`mt-2 font-serif text-3xl ${valueClass}`}>{value}</p>
    </div>
  );
}
