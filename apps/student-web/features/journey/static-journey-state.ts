import type { components } from "@math-coach/api-client";

export type JourneyPhase =
  | "onboarding"
  | "planning"
  | "problem_work"
  | "upload"
  | "transcription"
  | "correction"
  | "confirmation"
  | "evaluation"
  | "hint"
  | "retry"
  | "concept"
  | "completion";

export type JourneyStatus =
  | "loading"
  | "ready"
  | "profile_required"
  | "targets_required"
  | "empty"
  | "retryable_failure"
  | "permanent_failure"
  | "invalid_schema"
  | "uncertain";

export type JourneyProfileReference = {
  id: string;
  targetIds: string[];
};

export type JourneyPlanItemReference = {
  conceptVersionId: string | null;
  problemVersionId: string;
  supportedTargetIds: string[];
};

export type JourneyPlanReference = {
  id: string;
  items: JourneyPlanItemReference[];
};

export type JourneyAttemptReference = {
  id: string;
  problemVersionId: string;
  studyProfileId: string;
};

export type JourneyUploadReference = {
  id: string;
  status: "ready";
};

export type JourneyEvaluationReference = {
  confirmedTranscriptVersionId: string;
  evaluationId: string;
  outcome: "ready" | "uncertain";
};

export type JourneyTranscriptVersionReference = {
  hash: string;
  id: string;
  version: number;
};

export type JourneyConfirmationReference = {
  hash: string;
  id: string;
  transcriptVersionId: string;
};

export type JourneyHintReference = {
  hintLevel: number;
};

export type JourneyConceptReference = {
  conceptVersionId: string | null;
};

export type StaticJourneyData = {
  attempts: JourneyAttemptReference[];
  confirmation?: JourneyConfirmationReference;
  concept?: JourneyConceptReference;
  confirmedTranscript?: components["schemas"]["TranscriptDocument"];
  evaluation?: JourneyEvaluationReference;
  hints: JourneyHintReference[];
  plan?: JourneyPlanReference;
  profile?: JourneyProfileReference;
  selectedItem?: JourneyPlanItemReference;
  transcript?: components["schemas"]["TranscriptDocument"];
  transcriptVersion?: JourneyTranscriptVersionReference;
  upload?: JourneyUploadReference;
};

export type StaticJourneyState = {
  data: StaticJourneyData;
  phase: JourneyPhase;
  status: JourneyStatus;
};

export type StaticJourneyEvent =
  | { profile: JourneyProfileReference; type: "onboarding_loaded" }
  | { type: "start_planning" }
  | { plan: JourneyPlanReference; type: "plan_loaded" }
  | { attempt: JourneyAttemptReference; itemIndex: number; type: "problem_started" }
  | { type: "upload_started" }
  | { type: "upload_ready"; upload: JourneyUploadReference }
  | {
      transcript: components["schemas"]["TranscriptDocument"];
      transcriptVersion: JourneyTranscriptVersionReference;
      type: "transcript_received";
    }
  | {
      confirmation: JourneyConfirmationReference;
      transcript: components["schemas"]["TranscriptDocument"];
      transcriptVersion: JourneyTranscriptVersionReference;
      type: "transcript_confirmed";
    }
  | { type: "transcription_uncertain" }
  | { type: "transcription_retake" }
  | { type: "evaluation_requested" }
  | { evaluation: JourneyEvaluationReference; type: "evaluation_received" }
  | { type: "hint_requested" }
  | { hint: JourneyHintReference; type: "hint_received" }
  | { attempt: JourneyAttemptReference; type: "retry_started" }
  | { type: "concept_requested" }
  | { concept: JourneyConceptReference; type: "concept_received" }
  | { type: "session_completed" }
  | { failure: "invalid_schema" | "permanent" | "retryable"; type: "operation_failed" }
  | { type: "operation_retried" };

export type StaticJourneyTransition =
  | { accepted: true; state: StaticJourneyState }
  | { accepted: false; errorCode: "invalid_transition"; state: StaticJourneyState };

export function createInitialStaticJourneyState(): StaticJourneyState {
  return {
    data: { attempts: [], hints: [] },
    phase: "onboarding",
    status: "loading",
  };
}

function accept(state: StaticJourneyState): StaticJourneyTransition {
  return { accepted: true, state };
}

function reject(state: StaticJourneyState): StaticJourneyTransition {
  return { accepted: false, errorCode: "invalid_transition", state };
}

function matchingAttempt(
  attempt: JourneyAttemptReference,
  profile: JourneyProfileReference,
  item: JourneyPlanItemReference,
) {
  return (
    attempt.studyProfileId === profile.id && attempt.problemVersionId === item.problemVersionId
  );
}

export function transitionStaticJourney(
  state: StaticJourneyState,
  event: StaticJourneyEvent,
): StaticJourneyTransition {
  if (event.type === "onboarding_loaded" && state.phase === "onboarding") {
    return accept({
      data: { ...state.data, profile: event.profile },
      phase: "onboarding",
      status: event.profile.targetIds.length >= 2 ? "ready" : "targets_required",
    });
  }
  if (event.type === "start_planning" && state.phase === "onboarding" && state.status === "ready") {
    return accept({ ...state, phase: "planning", status: "loading" });
  }
  if (event.type === "plan_loaded" && state.phase === "planning" && state.status === "loading") {
    return accept({
      data: { ...state.data, plan: event.plan },
      phase: "planning",
      status: event.plan.items.length === 0 ? "empty" : "ready",
    });
  }
  if (event.type === "problem_started" && state.phase === "planning" && state.status === "ready") {
    const profile = state.data.profile;
    const item = state.data.plan?.items[event.itemIndex];
    if (
      profile === undefined ||
      item === undefined ||
      !matchingAttempt(event.attempt, profile, item)
    ) {
      return reject(state);
    }
    return accept({
      data: {
        ...state.data,
        attempts: [event.attempt],
        selectedItem: item,
      },
      phase: "problem_work",
      status: "ready",
    });
  }
  if (event.type === "upload_started" && state.phase === "problem_work") {
    return accept({ ...state, phase: "upload", status: "ready" });
  }
  if (event.type === "upload_ready" && state.phase === "upload") {
    return accept({
      data: { ...state.data, upload: event.upload },
      phase: "transcription",
      status: "loading",
    });
  }
  if (
    event.type === "transcript_received" &&
    state.phase === "transcription" &&
    state.status === "loading" &&
    event.transcript.attemptId === state.data.attempts.at(-1)?.id &&
    event.transcriptVersion.id.length > 0 &&
    event.transcriptVersion.hash.length === 64 &&
    event.transcriptVersion.version >= 1
  ) {
    return accept({
      data: {
        ...state.data,
        transcript: event.transcript,
        transcriptVersion: event.transcriptVersion,
      },
      phase: "correction",
      status: "ready",
    });
  }
  if (
    event.type === "transcription_uncertain" &&
    state.phase === "transcription" &&
    state.status === "loading"
  ) {
    return accept({ ...state, status: "uncertain" });
  }
  if (
    event.type === "transcription_retake" &&
    state.phase === "transcription" &&
    state.status === "uncertain"
  ) {
    return accept({
      data: { ...state.data, upload: undefined },
      phase: "upload",
      status: "ready",
    });
  }
  if (
    event.type === "transcript_confirmed" &&
    state.phase === "correction" &&
    event.transcript.attemptId === state.data.attempts.at(-1)?.id &&
    event.confirmation.transcriptVersionId === event.transcriptVersion.id &&
    event.confirmation.hash === event.transcriptVersion.hash
  ) {
    return accept({
      data: {
        ...state.data,
        confirmation: event.confirmation,
        confirmedTranscript: event.transcript,
        transcriptVersion: event.transcriptVersion,
      },
      phase: "confirmation",
      status: "ready",
    });
  }
  if (event.type === "evaluation_requested" && state.phase === "confirmation") {
    return accept({ ...state, phase: "evaluation", status: "loading" });
  }
  if (
    event.type === "evaluation_received" &&
    state.phase === "evaluation" &&
    state.status === "loading" &&
    event.evaluation.confirmedTranscriptVersionId ===
      state.data.confirmation?.transcriptVersionId &&
    event.evaluation.evaluationId.length > 0
  ) {
    return accept({
      data: { ...state.data, evaluation: event.evaluation },
      phase: "evaluation",
      status: event.evaluation.outcome === "uncertain" ? "uncertain" : "ready",
    });
  }
  if (
    event.type === "hint_requested" &&
    ((state.phase === "evaluation" && (state.status === "ready" || state.status === "uncertain")) ||
      (state.phase === "hint" && state.status === "ready"))
  ) {
    return accept({ ...state, phase: "hint", status: "loading" });
  }
  if (
    event.type === "hint_received" &&
    state.phase === "hint" &&
    state.status === "loading" &&
    event.hint.hintLevel === state.data.hints.length + 1
  ) {
    return accept({
      data: { ...state.data, hints: [...state.data.hints, event.hint] },
      phase: "hint",
      status: "ready",
    });
  }
  if (event.type === "retry_started" && state.phase === "hint" && state.status === "ready") {
    const profile = state.data.profile;
    const item = state.data.selectedItem;
    const previousAttempt = state.data.attempts.at(-1);
    if (
      profile === undefined ||
      item === undefined ||
      previousAttempt === undefined ||
      !matchingAttempt(event.attempt, profile, item) ||
      event.attempt.id === previousAttempt.id
    ) {
      return reject(state);
    }
    return accept({
      data: { ...state.data, attempts: [...state.data.attempts, event.attempt] },
      phase: "retry",
      status: "ready",
    });
  }
  if (event.type === "concept_requested" && state.phase === "retry") {
    return accept({ ...state, phase: "concept", status: "loading" });
  }
  if (
    event.type === "concept_received" &&
    state.phase === "concept" &&
    state.status === "loading" &&
    event.concept.conceptVersionId === state.data.selectedItem?.conceptVersionId
  ) {
    return accept({
      data: { ...state.data, concept: event.concept },
      phase: "concept",
      status: "ready",
    });
  }
  if (event.type === "session_completed" && state.phase === "concept" && state.status === "ready") {
    return accept({ ...state, phase: "completion", status: "ready" });
  }
  if (
    event.type === "operation_failed" &&
    ["planning", "transcription", "evaluation", "hint", "concept"].includes(state.phase)
  ) {
    return accept({
      ...state,
      status:
        event.failure === "retryable"
          ? "retryable_failure"
          : event.failure === "invalid_schema"
            ? "invalid_schema"
            : "permanent_failure",
    });
  }
  if (event.type === "operation_retried" && state.status === "retryable_failure") {
    return accept({ ...state, status: "loading" });
  }
  return reject(state);
}
