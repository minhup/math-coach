"use client";

import katex from "katex";
import { useLayoutEffect, useRef } from "react";

const MAX_LATEX_LENGTH = 2_000;

type MathRendererProps = {
  label: string;
  latex: string;
  mode: "inline" | "display";
};

export function MathRenderer({ label, latex, mode }: MathRendererProps) {
  const hostRef = useRef<HTMLSpanElement>(null);

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
      host.className = "math-render-output";
      host.dataset.mathRenderState = "rendered";
      host.setAttribute("aria-label", label);
      host.removeAttribute("role");
    } catch {
      const message = document.createElement("span");
      message.ariaHidden = "true";
      message.textContent = "Math needs correction";
      host.replaceChildren(message);
      host.className = "math-render-output math-render-failure";
      host.dataset.mathRenderState = "failed";
      host.setAttribute("aria-label", "Math needs correction");
      host.setAttribute("role", "img");
    }
  }, [label, latex, mode]);

  return (
    <span className={`math-renderer math-renderer-${mode}`}>
      <span
        aria-label={label}
        className="math-render-output"
        data-math-render-state="rendering"
        ref={hostRef}
      />
    </span>
  );
}
