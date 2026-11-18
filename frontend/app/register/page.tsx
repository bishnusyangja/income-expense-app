"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { Field, TextInput } from "@/components/Field";
import { ApiError, register } from "@/lib/api";

const initial = {
  first_name: "",
  last_name: "",
  email: "",
  address: "",
  phone: "",
  password: "",
};

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function update(name: keyof typeof initial, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    event.stopPropagation();
    setSubmitting(true);
    setErrors({});
    const data = new FormData(event.currentTarget);
    const payload = {
      first_name: String(data.get("first_name") ?? form.first_name),
      last_name: String(data.get("last_name") ?? form.last_name),
      email: String(data.get("email") ?? form.email),
      address: String(data.get("address") ?? form.address),
      phone: String(data.get("phone") ?? form.phone),
      password: String(data.get("password") ?? form.password),
    };
    try {
      await register(payload);
      router.push("/login?registered=1");
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
    <AuthShell title="Create an account" subtitle="Start tracking what comes in and what goes out.">
      <form onSubmit={onSubmit} method="post" action="" className="space-y-4">
        {errors.non_field ? (
          <p className="rounded-xl bg-clay/10 px-3 py-2 text-sm text-clay">{errors.non_field}</p>
        ) : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="First name" error={errors.first_name}>
            <TextInput
              name="first_name"
              value={form.first_name}
              onChange={(event) => update("first_name", event.target.value)}
              error={errors.first_name}
              autoComplete="given-name"
              required
            />
          </Field>
          <Field label="Last name" error={errors.last_name}>
            <TextInput
              name="last_name"
              value={form.last_name}
              onChange={(event) => update("last_name", event.target.value)}
              error={errors.last_name}
              autoComplete="family-name"
              required
            />
          </Field>
        </div>
        <Field label="Email" error={errors.email}>
          <TextInput
            name="email"
            type="email"
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            error={errors.email}
            autoComplete="email"
            required
          />
        </Field>
        <Field label="Address" error={errors.address}>
          <TextInput
            name="address"
            value={form.address}
            onChange={(event) => update("address", event.target.value)}
            error={errors.address}
            autoComplete="street-address"
            required
          />
        </Field>
        <Field label="Phone" error={errors.phone}>
          <TextInput
            name="phone"
            type="tel"
            value={form.phone}
            onChange={(event) => update("phone", event.target.value)}
            error={errors.phone}
            autoComplete="tel"
            required
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <TextInput
            name="password"
            type="password"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            error={errors.password}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </Field>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 w-full rounded-xl bg-pine px-4 py-3 font-medium text-white transition hover:bg-pine-dark disabled:opacity-60"
        >
          {submitting ? "Creating account..." : "Register"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-ink/70">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-pine hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
