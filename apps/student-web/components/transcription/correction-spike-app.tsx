"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";

import { SYNTHETIC_CORRECTION_TRANSCRIPT } from "../../features/transcription/synthetic-fixture";
import { ApiError, getCurrentUser, type User } from "../../lib/api";
import { MathRenderer } from "../math/math-renderer";
import { TranscriptEditor } from "./transcript-editor";

type AccessState =
  | { status: "checking" }
  | { status: "authentication-required" }
  | { status: "ready"; user: User }
  | { status: "unavailable" };

type PhonePanel = "photo" | "transcript";

function useTabletLayout() {
  const [tablet, setTablet] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") {
      return;
    }
    const query = window.matchMedia("(min-width: 768px)");
    const update = () => setTablet(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return tablet;
}

export function CorrectionSpikeApp() {
  const [access, setAccess] = useState<AccessState>({ status: "checking" });
  const [checkAttempt, setCheckAttempt] = useState(0);
  const [phonePanel, setPhonePanel] = useState<PhonePanel>("photo");
  const photoTabRef = useRef<HTMLButtonElement>(null);
  const transcriptTabRef = useRef<HTMLButtonElement>(null);
  const tablet = useTabletLayout();

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

  function selectPhonePanel(panel: PhonePanel, focus = false) {
    setPhonePanel(panel);
    if (focus) {
      const target = panel === "photo" ? photoTabRef.current : transcriptTabRef.current;
      target?.focus();
    }
  }

  if (access.status === "checking") {
    return (
      <main className="screen boot-screen">
        <div className="boot-card" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <strong>Checking correction-spike access…</strong>
        </div>
      </main>
    );
  }

  if (access.status === "authentication-required") {
    return (
      <main className="screen boot-screen">
        <section className="recovery-card" aria-labelledby="correction-auth-title">
          <p className="eyebrow">Internal route</p>
          <h1 id="correction-auth-title">Authentication required</h1>
          <p>Sign in through the workspace before opening the correction spike.</p>
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
        <section className="recovery-card" aria-labelledby="correction-unavailable-title">
          <p className="eyebrow">Connection interrupted</p>
          <h1 id="correction-unavailable-title">Correction spike unavailable</h1>
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

  const photoPanel = (
    <div className="correction-panel correction-photo-panel">
      <div className="correction-panel-heading">
        <p className="eyebrow">Photo</p>
        <h2>Synthetic paper fixture</h2>
      </div>
      <figure className="synthetic-paper">
        <Image
          alt="Original synthetic handwritten algebra solution; no student data"
          height={920}
          priority
          src="/fixtures/synthetic-correction-sheet.svg"
          width={720}
        />
        <figcaption>
          Original repository fixture. No student image or AI output is shown.
        </figcaption>
      </figure>
    </div>
  );
  const transcriptPanel = (
    <div className="correction-panel correction-transcript-panel">
      <TranscriptEditor initialState={SYNTHETIC_CORRECTION_TRANSCRIPT} />
    </div>
  );

  return (
    <main className="screen correction-screen">
      <div className="correction-shell">
        <nav className="preview-navigation" aria-label="Internal correction navigation">
          <Link className="text-button preview-link-button" href="/">
            Back to workspace
          </Link>
          <span>{access.user.displayName}</span>
        </nav>

        <header className="correction-header">
          <div>
            <p className="eyebrow">Milestone 3 · internal only</p>
            <h1>Mathematical correction spike</h1>
            <p className="correction-synthetic-label">Synthetic fixture — not student work</p>
          </div>
          <p className="correction-header-copy">
            Compare the fixture with its typed transcript. A valid inline factor such as{" "}
            <MathRenderer label="Inline synthetic factor" latex="x-2" mode="inline" /> renders
            through the same controlled boundary used by every preview.
          </p>
        </header>

        {tablet ? (
          <div className="correction-split" data-layout="tablet-split">
            <section aria-label="Synthetic photo" role="region">
              {photoPanel}
            </section>
            <section aria-label="Transcript correction" role="region">
              {transcriptPanel}
            </section>
          </div>
        ) : (
          <div className="correction-phone" data-layout="phone-tabs">
            <div aria-label="Correction view" className="correction-tabs" role="tablist">
              <button
                aria-controls="correction-photo-tabpanel"
                aria-selected={phonePanel === "photo"}
                id="correction-photo-tab"
                onClick={() => selectPhonePanel("photo")}
                onKeyDown={(event) => {
                  if (event.key === "ArrowRight") {
                    event.preventDefault();
                    selectPhonePanel("transcript", true);
                  }
                }}
                ref={photoTabRef}
                role="tab"
                tabIndex={phonePanel === "photo" ? 0 : -1}
                type="button"
              >
                PHOTO
              </button>
              <button
                aria-controls="correction-transcript-tabpanel"
                aria-selected={phonePanel === "transcript"}
                id="correction-transcript-tab"
                onClick={() => selectPhonePanel("transcript")}
                onKeyDown={(event) => {
                  if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    selectPhonePanel("photo", true);
                  }
                }}
                ref={transcriptTabRef}
                role="tab"
                tabIndex={phonePanel === "transcript" ? 0 : -1}
                type="button"
              >
                TRANSCRIPT
              </button>
            </div>
            <section
              aria-label="PHOTO"
              aria-labelledby="correction-photo-tab"
              hidden={phonePanel !== "photo"}
              id="correction-photo-tabpanel"
              role="tabpanel"
              tabIndex={0}
            >
              {photoPanel}
            </section>
            <section
              aria-label="TRANSCRIPT"
              aria-labelledby="correction-transcript-tab"
              hidden={phonePanel !== "transcript"}
              id="correction-transcript-tabpanel"
              role="tabpanel"
              tabIndex={0}
            >
              {transcriptPanel}
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
