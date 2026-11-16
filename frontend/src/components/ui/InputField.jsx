/**
 * InputField.jsx
 * Reusable controlled input component with integrated label,
 * error/success states, and an optional right-side action slot
 * (used for show/hide password toggles).
 */

import React from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react';

/**
 * @param {object}  props
 * @param {string}  props.id          – <input> id (and <label> htmlFor)
 * @param {string}  props.name        – field name
 * @param {string}  props.label       – visible label text
 * @param {string}  props.type        – input type (text | email | password)
 * @param {string}  props.value       – controlled value
 * @param {string}  props.placeholder
 * @param {string}  [props.error]     – error message (empty = no error)
 * @param {boolean} [props.valid]     – show green ring when true
 * @param {boolean} [props.required]  – marks field as required
 * @param {function} props.onChange
 * @param {function} props.onBlur
 * @param {React.ReactNode} [props.rightSlot] – e.g. show/hide button
 * @param {string}  [props.autoComplete]
 */
const InputField = React.forwardRef(function InputField(
  {
    id,
    name,
    label,
    type = 'text',
    value,
    placeholder,
    error,
    valid,
    required,
    onChange,
    onBlur,
    rightSlot,
    autoComplete,
  },
  ref,
) {
  const hasError = Boolean(error);

  return (
    <div className="flex flex-col gap-1.5">
      {/* Label */}
      <label
        htmlFor={id}
        className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400"
      >
        {label}
        {required && (
          <span className="ml-1 text-rose-500 font-bold" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {/* Input wrapper */}
      <div className="relative">
        <input
          ref={ref}
          id={id}
          name={name}
          type={type}
          value={value}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${id}-error` : undefined}
          onChange={onChange}
          onBlur={onBlur}
          className={[
            'input-base',
            rightSlot ? 'pr-11' : '',
            hasError ? 'input-error' : '',
            valid  ? 'border-emerald-500/60 focus:border-emerald-500 focus:ring-emerald-500/20' : '',
          ]
            .filter(Boolean)
            .join(' ')}
        />

        {/* Right slot (show/hide button) */}
        {rightSlot && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {rightSlot}
          </div>
        )}

        {/* Inline status icon (only when no right slot) */}
        {!rightSlot && (hasError || valid) && (
          <div
            className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3"
            aria-hidden="true"
          >
            {hasError ? (
              <AlertCircle className="h-4 w-4 text-rose-400" />
            ) : (
              <CheckCircle className="h-4 w-4 text-emerald-400" />
            )}
          </div>
        )}
      </div>

      {/* Error message */}
      {hasError && (
        <p
          id={`${id}-error`}
          role="alert"
          className="flex items-center gap-1.5 text-xs font-medium text-rose-400 animate-fade-in"
        >
          <AlertCircle className="h-3 w-3 shrink-0" aria-hidden="true" />
          {error}
        </p>
      )}
    </div>
  );
});

export default InputField;
