"use client";

import { useState } from "react";
import Link from "next/link";

import { ApiError, logout, type User } from "../lib/api";
import { StaticStudentJourney } from "./journey/static-student-journey";

type InteractionShellProps = {
  initialUser: User;
  onSignedOut: () => void;
};

export function InteractionShell({ initialUser, onSignedOut }: InteractionShellProps) {
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  async function signOut() {
    setSignOutError(null);
    setSigningOut(true);
    try {
      await logout();
      onSignedOut();
    } catch (error) {
      setSignOutError(
        error instanceof ApiError ? error.message : "Could not sign out. Check the connection.",
      );
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <main className="screen">
      <div className="app-shell">
        <header className="app-header">
          <div className="header-brand">
            <span className="brand-mark" aria-hidden="true">
              ∑
            </span>
            <div>
              <strong>Math Coach</strong>
              <span>Static student journey</span>
            </div>
          </div>
          <div className="header-account">
            <div className="header-user">
              <div className="header-user-copy">
                <strong>{initialUser.displayName}</strong>
                <span>Internal learner</span>
              </div>
              <Link className="text-button preview-link-button" href="/internal/content-preview">
                Content preview
              </Link>
              <Link className="text-button preview-link-button" href="/internal/math-correction">
                Correction spike
              </Link>
              <Link className="text-button preview-link-button" href="/internal/geometry-spike">
                Geometry spike
              </Link>
              <button className="text-button" disabled={signingOut} onClick={signOut} type="button">
                {signingOut ? "Signing out…" : "Sign out"}
              </button>
            </div>
            {signOutError ? (
              <p className="header-error" role="alert">
                {signOutError}
              </p>
            ) : null}
          </div>
        </header>
        <div className="workspace">
          <StaticStudentJourney />
        </div>
      </div>
    </main>
  );
}
