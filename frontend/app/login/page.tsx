"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { Field, TextInput } from "@/components/Field";
import { ApiError, login } from "@/lib/api";
import { setSession } from "@/lib/auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const registered = searchParams.get("registered") === "1";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    event.stopPropagation();
    setSubmitting(true);
    setErrors({});
    const formData = new FormData(event.currentTarget);
    const submittedEmail = String(formData.get("email") ?? email);
    const submittedPassword = String(formData.get("password") ?? password);
    try {
      const response = await login({
        email: submittedEmail,
        password: submittedPassword,
      });
      setSession(response.data.access_token, response.data.user);
      router.replace("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        const next = { ...error.errors };
        if (next.csrf && !next.non_field) {
          next.non_field = next.csrf;
        }
        setErrors(next);
      } else {
        setErrors({ non_field: "Something went wrong. Try again." });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Log in to add income and track spending.">
      {registered ? (
        <p className="mb-6 rounded-xl bg-pine/10 px-3 py-2 text-sm text-pine-dark">
          Account created. You can log in now.
        </p>
      ) : null}
      <form onSubmit={onSubmit} method="post" action="" className="space-y-4">
        {errors.non_field ? (
          <p className="rounded-xl bg-clay/10 px-3 py-2 text-sm text-clay">{errors.non_field}</p>
        ) : null}
        <Field label="Email" error={errors.email}>
          <TextInput
            name="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={errors.email}
            autoComplete="email"
            required
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <TextInput
            name="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={errors.password}
            autoComplete="current-password"
            required
          />
        </Field>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 w-full rounded-xl bg-pine px-4 py-3 font-medium text-white transition hover:bg-pine-dark disabled:opacity-60"
        >
          {submitting ? "Signing in..." : "Log in"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-ink/70">
        New here?{" "}
        <Link href="/register" className="font-medium text-pine hover:underline">
          Create an account
        </Link>
      </p>
    </AuthShell>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
