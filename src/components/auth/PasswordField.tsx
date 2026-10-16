import React, { useCallback, useState } from 'react';

interface PasswordFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  touched?: boolean;
  describedBy?: string;
  autoFocus?: boolean;
  disabled?: boolean;
  inputRef?: React.Ref<HTMLInputElement>;
  capsLockHint?: boolean;
}

export function PasswordField({
  id,
  label,
  value,
  onChange,
  onBlur,
  error,
  touched,
  describedBy,
  disabled,
  inputRef,
  capsLockHint = true,
}: PasswordFieldProps) {
  const [show, setShow] = useState(false);
  const [capsOn, setCapsOn] = useState(false);

  const handleKey = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (capsLockHint) {
      setCapsOn(e.getModifierState ? e.getModifierState('CapsLock') : false);
    }
  }, [capsLockHint]);

  const toggle = useCallback(() => setShow((s) => !s), []);

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="password-row">
        <input
          id={id}
          ref={inputRef}
          type={show ? 'text' : 'password'}
          value={value}
          autoComplete="current-password"
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          onKeyDown={handleKey}
          onKeyUp={handleKey}
          aria-invalid={touched && !!error ? true : undefined}
          aria-describedby={describedBy}
          disabled={disabled}
          style={{ flex: 1 }}
        />
        <button
          type="button"
          className="toggle"
          onClick={toggle}
          aria-pressed={show}
          aria-label={show ? 'Hide password' : 'Show password'}
          disabled={disabled}
        >
          {show ? 'Hide' : 'Show'}
        </button>
      </div>
      {capsLockHint && capsOn && !disabled && (
        <small style={{ color: 'var(--emerald-800)', fontSize: 13 }} role="status">
          Caps Lock is on.
        </small>
      )}
      {touched && error && <span className="err" id={`${id}-error`}>{error}</span>}
    </div>
  );
}