"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  syntheticGeometryActions,
  syntheticGeometryScene,
} from "../../features/geometry/synthetic-fixtures";
import { ApiError, getCurrentUser, type User } from "../../lib/api";
import { GeometryScene } from "./geometry-scene";

type AccessState =
  | { status: "checking" }
  | { status: "authentication-required" }
  | { status: "ready"; user: User }
  | { status: "unavailable" };

export function GeometrySpikeApp() {
  const [access, setAccess] = useState<AccessState>({ status: "checking" });
  const [checkAttempt, setCheckAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((user) => {
        if (active) {
          setAccess({ status: "ready", user });
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setAccess(
          error instanceof ApiError && error.status === 401
            ? { status: "authentication-required" }
            : { status: "unavailable" },
        );
      });
    return () => {
      active = false;
    };
  }, [checkAttempt]);

  if (access.status === "checking") {
    return (
      <main className="screen boot-screen">
        <div className="boot-card" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <strong>Checking geometry-spike access…</strong>
        </div>
      </main>
    );
  }

  if (access.status === "authentication-required") {
    return (
      <main className="screen boot-screen">
        <section className="recovery-card" aria-labelledby="geometry-auth-title">
          <p className="eyebrow">Internal route</p>
          <h1 id="geometry-auth-title">Authentication required</h1>
          <p>Sign in through the workspace before opening the geometry spike.</p>
          <Link className="primary-button correction-link-button" href="/">
            Return to workspace
          </Link>
        </section>
      </main>
    );
  }

  if (access.status === "unavailable") {
    return (
      <main className="screen boot-screen">
        <section className="recovery-card" aria-labelledby="geometry-unavailable-title">
          <p className="eyebrow">Connection interrupted</p>
          <h1 id="geometry-unavailable-title">Geometry spike unavailable</h1>
          <p>The synthetic fixture has not been opened. Check the local services and try again.</p>
          <button
            className="primary-button"
            onClick={() => {
              setAccess({ status: "checking" });
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
    <main className="screen geometry-spike-screen">
      <div className="geometry-spike-shell">
        <nav className="preview-navigation" aria-label="Internal geometry navigation">
          <Link className="text-button preview-link-button" href="/">
            Back to workspace
          </Link>
          <span>{access.user.displayName}</span>
        </nav>
        <header className="geometry-spike-header">
          <div>
            <p className="eyebrow">Milestone 4 · internal only</p>
            <h1>Interactive geometry engine</h1>
            <p className="correction-synthetic-label">
              Synthetic curated construction — not examination content
            </p>
          </div>
          <p>
            This device surface exercises every approved primitive, typed action, accessible
            selection path, free-point drag, and deterministic constraint monitor.
          </p>
        </header>
        <GeometryScene
          actions={syntheticGeometryActions}
          scene={syntheticGeometryScene}
          showConstraintSnapshot
        />
      </div>
    </main>
  );
}
