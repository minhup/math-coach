"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import {
  ApiError,
  getContentPreview,
  getContentPreviews,
  type ContentPreview as ContentPreviewData,
  type ContentPreviewList,
} from "../lib/api";
import { ContentPreview } from "./content-preview";

type PreviewState =
  | { kind: "loading" }
  | { kind: "failed"; message: string }
  | { kind: "ready"; list: ContentPreviewList; preview: ContentPreviewData | null };

export function ContentPreviewApp() {
  const [state, setState] = useState<PreviewState>({ kind: "loading" });
  const [loadAttempt, setLoadAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getContentPreviews()
      .then(async (list) => ({
        list,
        preview: list.items.length > 0 ? await getContentPreview(list.items[0].problemId) : null,
      }))
      .then(({ list, preview }) => {
        if (active) {
          setState({ kind: "ready", list, preview });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          const message =
            error instanceof ApiError && error.status === 401
              ? "Sign in to inspect internal content."
              : error instanceof ApiError
                ? error.message
                : "The preview could not be loaded. Check the connection.";
          setState({ kind: "failed", message });
        }
      });
    return () => {
      active = false;
    };
  }, [loadAttempt]);

  return (
    <main className="screen">
      <div className="preview-shell">
        <nav className="preview-navigation" aria-label="Internal content navigation">
          <Link className="text-button preview-link-button" href="/">
            Back to workspace
          </Link>
          <span>Internal content preview</span>
        </nav>

        {state.kind === "loading" ? (
          <div className="recovery-card preview-status" role="status">
            <div className="spinner" aria-hidden="true" />
            <p>Loading validated content…</p>
          </div>
        ) : null}

        {state.kind === "failed" ? (
          <div className="recovery-card preview-status">
            <h1>Content preview unavailable</h1>
            <p role="alert">{state.message}</p>
            <button
              className="primary-button"
              onClick={() => {
                setState({ kind: "loading" });
                setLoadAttempt((attempt) => attempt + 1);
              }}
              type="button"
            >
              Try again
            </button>
          </div>
        ) : null}

        {state.kind === "ready" && state.list.items.length === 0 ? (
          <div className="recovery-card preview-status">
            <h1>No validated content</h1>
            <p>Import a valid versioned package to populate this internal preview.</p>
          </div>
        ) : null}

        {state.kind === "ready" && state.preview ? (
          <>
            {state.list.items.length > 1 ? (
              <label className="preview-picker">
                Problem
                <select
                  onChange={(event) => {
                    const problemId = event.target.value;
                    setState({ kind: "loading" });
                    void getContentPreview(problemId)
                      .then((preview) => setState({ kind: "ready", list: state.list, preview }))
                      .catch((error: unknown) =>
                        setState({
                          kind: "failed",
                          message:
                            error instanceof ApiError
                              ? error.message
                              : "The preview could not be loaded.",
                        }),
                      );
                  }}
                  value={state.preview.problemId}
                >
                  {state.list.items.map((item) => (
                    <option key={item.problemId} value={item.problemId}>
                      {item.externalCode} v{item.version}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <ContentPreview preview={state.preview} />
          </>
        ) : null}
      </div>
    </main>
  );
}
