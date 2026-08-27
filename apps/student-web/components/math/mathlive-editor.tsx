"use client";

import { createElement, useEffect, useRef, useState } from "react";

type MathLiveEditorProps = {
  label: string;
  onInput: (value: string) => void;
  value: string;
};

export function MathLiveEditor({ label, onInput, value }: MathLiveEditorProps) {
  const fieldRef = useRef<HTMLElement>(null);
  const initialValueRef = useRef(value);
  const onInputRef = useRef(onInput);
  const [loadState, setLoadState] = useState<"failed" | "loading" | "ready">("loading");

  useEffect(() => {
    onInputRef.current = onInput;
  }, [onInput]);

  useEffect(() => {
    let active = true;
    const field = fieldRef.current;
    if (field === null) {
      return;
    }

    const handleInput = () => {
      const nextValue = Reflect.get(field, "value");
      if (typeof nextValue === "string") {
        onInputRef.current(nextValue);
      }
    };

    void import("mathlive")
      .then(() => {
        if (!active) {
          return;
        }
        Reflect.set(field, "mathVirtualKeyboardPolicy", "auto");
        Reflect.set(field, "value", initialValueRef.current);
        field.addEventListener("input", handleInput);
        setLoadState("ready");
      })
      .catch(() => {
        if (active) {
          setLoadState("failed");
        }
      });

    return () => {
      active = false;
      field.removeEventListener("input", handleInput);
    };
  }, []);

  useEffect(() => {
    const field = fieldRef.current;
    if (loadState === "ready" && field !== null && Reflect.get(field, "value") !== value) {
      Reflect.set(field, "value", value);
    }
  }, [loadState, value]);

  return (
    <div className="mathlive-editor" data-editor-state={loadState}>
      {createElement("math-field", {
        "aria-label": label,
        className: "mathlive-field",
        hidden: loadState !== "ready",
        ref: fieldRef,
      })}
      {loadState === "loading" ? (
        <span className="mathlive-editor-status" role="status">
          Loading visual math editor…
        </span>
      ) : null}
      {loadState === "failed" ? (
        <span className="mathlive-editor-status" role="alert">
          Visual math editor unavailable. Reload this page to retry.
        </span>
      ) : null}
    </div>
  );
}
