"use client";

import { useEffect, useState } from "react";

import { ApiError, getCurrentUser, type User } from "../lib/api";
import { InteractionShell } from "./interaction-shell";
import { LoginCard } from "./login-card";

type AppState =
  | { status: "checking" }
  | { status: "signed-out" }
  | { status: "signed-in"; user: User }
  | { status: "unavailable" };

export function MathCoachApp() {
  const [state, setState] = useState<AppState>({ status: "checking" });
  const [checkAttempt, setCheckAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((user) => {
        if (active) {
          setState({ status: "signed-in", user });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState(
            error instanceof ApiError && error.status === 401
              ? { status: "signed-out" }
              : { status: "unavailable" },
          );
        }
      });
    return () => {
      active = false;
    };
  }, [checkAttempt]);

  if (state.status === "checking") {
    return (
      <main className="screen boot-screen">
        <div className="boot-card" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <strong>Opening your workspace…</strong>
        </div>
      </main>
    );
  }

  if (state.status === "signed-out") {
    return <LoginCard onAuthenticated={(user) => setState({ status: "signed-in", user })} />;
  }

  if (state.status === "unavailable") {
    return (
      <main className="screen boot-screen">
        <section className="recovery-card" aria-labelledby="recovery-title">
          <p className="eyebrow">Connection interrupted</p>
          <h1 id="recovery-title">Your workspace could not open.</h1>
          <p>Your work is unchanged. Check the local services and try again.</p>
          <button
            className="primary-button"
            onClick={() => {
              setState({ status: "checking" });
              setCheckAttempt((attempt) => attempt + 1);
            }}
            type="button"
          >
            Retry connection
          </button>
        </section>
      </main>
    );
  }

  return (
    <InteractionShell
      initialUser={state.user}
      onSignedOut={() => setState({ status: "signed-out" })}
    />
  );
}
