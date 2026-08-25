"use client";

import { FormEvent, useState } from "react";

import { ApiError, login, type User } from "../lib/api";

type LoginCardProps = {
  onAuthenticated: (user: User) => void;
};

export function LoginCard({ onAuthenticated }: LoginCardProps) {
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const session = await login(inviteCode.trim());
      onAuthenticated(session.user);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to sign in. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="screen login-screen">
      <section className="login-story" aria-labelledby="story-title">
        <p className="eyebrow">Paper-first mathematics</p>
        <h2 id="story-title">Think deeply. Get feedback that follows your work.</h2>
        <p>
          Solve naturally on paper, confirm what the coach sees, then work through the idea that
          matters most—without turning mathematics into a chat transcript.
        </p>
        <div className="story-steps" aria-label="Coaching workflow">
          <span className="story-step">Solve</span>
          <span className="story-step">Confirm</span>
          <span className="story-step">Understand</span>
          <span className="story-step">Retry</span>
        </div>
      </section>

      <section className="login-card" aria-labelledby="login-title">
        <div className="login-brand">
          <span className="brand-mark" aria-hidden="true">
            ∑
          </span>
          <span>Math Coach</span>
        </div>
        <p className="eyebrow">Internal preview</p>
        <h1 id="login-title">Continue your practice.</h1>
        <p className="login-copy">Enter your invite code to open the paper-solution workspace.</p>
        <form onSubmit={submit}>
          <label className="field-label" htmlFor="invite-code">
            Invite code
          </label>
          <input
            autoComplete="one-time-code"
            className="text-input"
            id="invite-code"
            maxLength={128}
            onChange={(event) => setInviteCode(event.target.value)}
            placeholder="Enter your code"
            required
            value={inviteCode}
          />
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? "Checking invite…" : "Open workspace"}
          </button>
        </form>
        <p className="development-note">
          Internal MVP environment. Upload synthetic or non-personal practice images only.
        </p>
      </section>
    </main>
  );
}
