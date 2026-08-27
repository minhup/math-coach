"use client";

import katex from "katex";
import { useLayoutEffect, useRef, useState } from "react";

const MAX_LATEX_LENGTH = 2_000;

type MathRendererProps = {
  label: string;
  latex: string;
  mode: "inline" | "display";
};

export function MathRenderer({ label, latex, mode }: MathRendererProps) {
  const hostRef = useRef<HTMLSpanElement>(null);
  const [state, setState] = useState<"rendering" | "rendered" | "failed">("rendering");

  useLayoutEffect(() => {
    const host = hostRef.current;
    if (host === null) {
      return;
    }
    const staging = document.createElement("span");
    let trustedCommandAttempted = false;
    try {
      if (latex.trim().length === 0 || latex.length > MAX_LATEX_LENGTH) {
        throw new Error("Mathematics is outside rendering limits.");
      }
      katex.render(latex, staging, {
        displayMode: mode === "display",
        globalGroup: false,
        macros: {},
        maxExpand: 100,
        maxSize: 10,
        output: "htmlAndMathml",
        strict: "error",
        throwOnError: true,
        trust: () => {
          trustedCommandAttempted = true;
          return false;
        },
      });
      if (trustedCommandAttempted) {
        throw new Error("Trusted KaTeX commands are disabled.");
      }
      host.replaceChildren(...staging.childNodes);
      setState("rendered");
    } catch {
      host.replaceChildren();
      setState("failed");
    }
  }, [latex, mode]);

  return (
    <span className={`math-renderer math-renderer-${mode}`}>
      <span
        aria-label={state === "failed" ? undefined : label}
        data-math-render-state={state}
        hidden={state === "failed"}
        ref={hostRef}
      />
      {state === "failed" ? (
        <span aria-label="Math needs correction" className="math-render-failure" role="img">
          <span aria-hidden="true">Math needs correction</span>
        </span>
      ) : null}
    </span>
  );
}
