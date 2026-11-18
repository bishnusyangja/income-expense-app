import type { InputHTMLAttributes, ReactNode } from "react";

const inputClass =
  "w-full rounded-xl border border-ink/15 bg-white px-3.5 py-2.5 text-ink shadow-sm outline-none transition placeholder:text-ink/35 focus:border-pine focus:ring-2 focus:ring-pine/20";

type FieldProps = {
  label: string;
  error?: string;
  children: ReactNode;
};

export function Field({ label, error, children }: FieldProps) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-ink/75">{label}</span>
      {children}
      {error ? <span className="block text-sm text-clay">{error}</span> : null}
    </label>
  );
}

export function TextInput(
  props: InputHTMLAttributes<HTMLInputElement> & { error?: string },
) {
  const { error, className, ...rest } = props;
  return (
    <input
      {...rest}
      className={`${inputClass} ${error ? "border-clay/60" : ""} ${className ?? ""}`}
    />
  );
}

export { inputClass };
