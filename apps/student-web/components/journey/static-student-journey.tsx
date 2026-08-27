"use client";

import Image from "next/image";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { summarizeStaticJourney } from "../../features/journey/session-summary";
import {
  createInitialStaticJourneyState,
  transitionStaticJourney,
  type StaticJourneyEvent,
} from "../../features/journey/static-journey-state";
import type {
  ConfirmedTranscriptSnapshot,
  TranscriptBlock,
} from "../../features/transcription/transcript-state";
import { ApiError } from "../../lib/api";
import {
  addExamTarget,
  createAttempt,
  createStudyProfile,
  getAvailableExamCycles,
  getConceptVersion,
  getStaticPlan,
  getStudyProfile,
  requestMockEvaluation,
  requestNextHint,
  type Attempt,
  type AvailableExamCycles,
  type ConceptVersion,
  type MockEvaluation,
  type NextHint,
  type StaticDailyPlan,
  type StudyProfile,
} from "../../lib/static-journey-api";
import {
  confirmTranscriptVersion,
  createTranscriptVersion,
  getUploadDownload,
  requestTranscription,
  type TranscriptConfirmation,
  type TranscriptionRun,
  type TranscriptVersion,
} from "../../lib/transcription-api";
import { GeometryScene } from "../geometry/geometry-scene";
import { TypedContentBlocks } from "../math/content-blocks";
import { MathRenderer } from "../math/math-renderer";
import { TranscriptEditor } from "../transcription/transcript-editor";
import { UploadWorkspace } from "../upload-workspace";

export type StaticJourneyApi = {
  addExamTarget: typeof addExamTarget;
  createAttempt: typeof createAttempt;
  createStudyProfile: typeof createStudyProfile;
  getAvailableExamCycles: typeof getAvailableExamCycles;
  getConceptVersion: typeof getConceptVersion;
  getStaticPlan: typeof getStaticPlan;
  getStudyProfile: typeof getStudyProfile;
  getUploadDownload: typeof getUploadDownload;
  requestMockEvaluation: typeof requestMockEvaluation;
  requestNextHint: typeof requestNextHint;
  requestTranscription: typeof requestTranscription;
  createTranscriptVersion: typeof createTranscriptVersion;
  confirmTranscriptVersion: typeof confirmTranscriptVersion;
};

const defaultApi: StaticJourneyApi = {
  addExamTarget,
  createAttempt,
  createStudyProfile,
  getAvailableExamCycles,
  getConceptVersion,
  getStaticPlan,
  getStudyProfile,
  getUploadDownload,
  requestMockEvaluation,
  requestNextHint,
  requestTranscription,
  createTranscriptVersion,
  confirmTranscriptVersion,
};

type LoadStatus = "loading" | "profile_required" | "ready" | "retryable_failure";

function attemptReference(attempt: Attempt) {
  return {
    id: attempt.id,
    problemVersionId: attempt.problemVersionId,
    studyProfileId: attempt.studyProfileId,
  };
}

function profileReference(profile: StudyProfile) {
  return {
    id: profile.id,
    targetIds: profile.studentExamTargets
      .filter(({ status }) => status === "active")
      .map(({ id }) => id),
  };
}

function planReference(plan: StaticDailyPlan) {
  return {
    id: plan.planId,
    items: plan.items.map((item) => ({
      conceptVersionId: item.conceptVersionId,
      problemVersionId: item.problem.problemVersionId,
      supportedTargetIds: item.supportedTargetIds,
    })),
  };
}

function operationFailure(error: unknown): "invalid_schema" | "permanent" | "retryable" {
  if (error instanceof ApiError) {
    if (error.code === "transcription_invalid_schema" || error.code === "invalid_response") {
      return "invalid_schema";
    }
    if (
      error.code === "mock_payload_invalid" ||
      error.code === "mock_permanent_failure" ||
      error.code === "transcription_provider_rejected" ||
      error.code === "transcription_invalid_media"
    ) {
      return "permanent";
    }
    return error.status >= 500 ? "retryable" : "permanent";
  }
  return "retryable";
}

function safeErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The static journey could not continue. Check the connection and try again.";
}

function ConfirmedTranscriptView({ transcript }: { transcript: ConfirmedTranscriptSnapshot }) {
  return (
    <div className="journey-transcript" aria-label="Confirmed authoritative transcript">
      {transcript.blocks.map((block, index) =>
        block.type === "text" ? (
          <span key={block.id}>{block.text}</span>
        ) : (
          <MathRenderer
            key={block.id}
            label={`Confirmed formula ${index + 1}`}
            latex={block.latex}
            mode="inline"
          />
        ),
      )}
    </div>
  );
}

export function StaticStudentJourney({ api = defaultApi }: { api?: StaticJourneyApi }) {
  const [journey, setJourney] = useState(createInitialStaticJourneyState);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("loading");
  const [profile, setProfile] = useState<StudyProfile | null>(null);
  const [cycles, setCycles] = useState<AvailableExamCycles["items"]>([]);
  const [plan, setPlan] = useState<StaticDailyPlan | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [currentAttempt, setCurrentAttempt] = useState<Attempt | null>(null);
  const [evaluation, setEvaluation] = useState<MockEvaluation | null>(null);
  const [hints, setHints] = useState<NextHint[]>([]);
  const [concept, setConcept] = useState<ConceptVersion | null>(null);
  const [transcriptVersion, setTranscriptVersion] = useState<TranscriptVersion | null>(null);
  const [confirmation, setConfirmation] = useState<TranscriptConfirmation | null>(null);
  const [transcriptionRun, setTranscriptionRun] = useState<TranscriptionRun | null>(null);
  const [transcriptionWarnings, setTranscriptionWarnings] = useState<string[]>([]);
  const [selectedSourceRegion, setSelectedSourceRegion] = useState<NonNullable<
    TranscriptBlock["sourceRegion"]
  > | null>(null);
  const [sourceImageUrl, setSourceImageUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transitionMessage, setTransitionMessage] = useState<string | null>(null);
  const retryOperation = useRef<(() => Promise<void>) | null>(null);

  const dispatch = useCallback((event: StaticJourneyEvent) => {
    setJourney((current) => {
      const result = transitionStaticJourney(current, event);
      if (!result.accepted) {
        setTransitionMessage("That step is not available until the required earlier steps finish.");
      } else {
        setTransitionMessage(null);
      }
      return result.state;
    });
  }, []);

  const loadOnboarding = useCallback(async () => {
    setLoadStatus("loading");
    setErrorMessage(null);
    try {
      const available = await api.getAvailableExamCycles();
      setCycles(available.items);
      try {
        const loadedProfile = await api.getStudyProfile();
        setProfile(loadedProfile);
        dispatch({ profile: profileReference(loadedProfile), type: "onboarding_loaded" });
        setLoadStatus("ready");
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          setLoadStatus("profile_required");
          return;
        }
        throw error;
      }
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
      setLoadStatus("retryable_failure");
    }
  }, [api, dispatch]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => void loadOnboarding(), 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadOnboarding]);

  const activeTargets = useMemo(
    () => profile?.studentExamTargets.filter(({ status }) => status === "active") ?? [],
    [profile],
  );
  const missingCycles = useMemo(() => {
    const existing = new Set(profile?.studentExamTargets.map(({ examCycleId }) => examCycleId));
    return cycles.filter(({ id }) => !existing.has(id));
  }, [cycles, profile]);
  const selectedItem = plan?.items[selectedIndex] ?? null;

  async function createProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    const form = new FormData(event.currentTarget);
    try {
      const created = await api.createStudyProfile({
        name: String(form.get("profileName") ?? "Synthetic preparation"),
        weeklyStudyMinutes: Number(form.get("weeklyStudyMinutes") ?? 240),
      });
      setProfile(created);
      dispatch({ profile: profileReference(created), type: "onboarding_loaded" });
      setLoadStatus("ready");
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
    }
  }

  async function addTarget(cycleId: string) {
    if (profile === null) {
      return;
    }
    setErrorMessage(null);
    try {
      const target = await api.addExamTarget({
        examCycleId: cycleId,
        priorityRank: activeTargets.length + 1,
        targetScore: activeTargets.length === 0 ? "16.00" : "15.00",
      });
      const updated = {
        ...profile,
        studentExamTargets: [...profile.studentExamTargets, target],
      };
      setProfile(updated);
      dispatch({ profile: profileReference(updated), type: "onboarding_loaded" });
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
    }
  }

  function recordOperationFailure(error: unknown, retry: () => Promise<void>) {
    setErrorMessage(safeErrorMessage(error));
    retryOperation.current = retry;
    dispatch({ failure: operationFailure(error), type: "operation_failed" });
  }

  async function loadPlan() {
    try {
      const loaded = await api.getStaticPlan();
      setPlan(loaded);
      dispatch({ plan: planReference(loaded), type: "plan_loaded" });
    } catch (error) {
      recordOperationFailure(error, loadPlan);
    }
  }

  function startPlanning() {
    setErrorMessage(null);
    dispatch({ type: "start_planning" });
    void loadPlan();
  }

  async function startProblem(itemIndex: number) {
    const item = plan?.items[itemIndex];
    if (item === undefined) {
      return;
    }
    setErrorMessage(null);
    try {
      const attempt = await api.createAttempt(item.problem.problemVersionId);
      setSelectedIndex(itemIndex);
      setCurrentAttempt(attempt);
      dispatch({ attempt: attemptReference(attempt), itemIndex, type: "problem_started" });
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
    }
  }

  async function transcribe(uploadId: string, idempotencyKey = crypto.randomUUID()) {
    if (currentAttempt === null) {
      return;
    }
    try {
      const source = await api.getUploadDownload(uploadId);
      setSourceImageUrl(source.downloadUrl);
      const response = await api.requestTranscription(currentAttempt.id, uploadId, idempotencyKey);
      setTranscriptionRun(response.run);
      if (response.outcome === "uncertain") {
        setTranscriptionWarnings(response.warnings.map(({ message }) => message));
        dispatch({ type: "transcription_uncertain" });
        return;
      }
      setSelectedSourceRegion(null);
      setTranscriptVersion(response.transcriptVersion);
      setTranscriptionWarnings(
        response.transcriptVersion.document.warnings.map(({ message }) => message),
      );
      dispatch({
        transcript: response.transcriptVersion.document,
        transcriptVersion: {
          hash: response.transcriptVersion.transcriptHash,
          id: response.transcriptVersion.id,
          version: response.transcriptVersion.version,
        },
        type: "transcript_received",
      });
    } catch (error) {
      recordOperationFailure(error, () => transcribe(uploadId));
    }
  }

  function useUpload(upload: { id: string; status: "pending" | "ready" | "rejected" }) {
    if (upload.status !== "ready") {
      setTransitionMessage("The upload must be verified before transcription.");
      return;
    }
    dispatch({ type: "upload_ready", upload: { id: upload.id, status: "ready" } });
    setSourceImageUrl(null);
    setTranscriptionWarnings([]);
    void transcribe(upload.id);
  }

  async function confirmCorrectedTranscript(transcript: ConfirmedTranscriptSnapshot) {
    if (currentAttempt === null || transcriptVersion === null) {
      throw new Error("No validated transcript version is available.");
    }
    try {
      const selectedVersion =
        JSON.stringify(transcript) === JSON.stringify(transcriptVersion.document)
          ? transcriptVersion
          : await api.createTranscriptVersion(currentAttempt.id, transcriptVersion.id, transcript);
      const confirmed = await api.confirmTranscriptVersion(
        currentAttempt.id,
        selectedVersion.id,
        selectedVersion.transcriptHash,
      );
      setTranscriptVersion(selectedVersion);
      setConfirmation(confirmed);
      dispatch({
        confirmation: {
          hash: confirmed.transcriptHash,
          id: confirmed.id,
          transcriptVersionId: confirmed.transcriptVersionId,
        },
        transcript,
        transcriptVersion: {
          hash: selectedVersion.transcriptHash,
          id: selectedVersion.id,
          version: selectedVersion.version,
        },
        type: "transcript_confirmed",
      });
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
      throw error;
    }
  }

  async function evaluate() {
    const confirmed = journey.data.confirmation;
    if (currentAttempt === null || confirmed === undefined) {
      dispatch({ type: "evaluation_requested" });
      return;
    }
    try {
      const response = await api.requestMockEvaluation(
        currentAttempt.id,
        confirmed.transcriptVersionId,
      );
      setEvaluation(response);
      dispatch({
        evaluation: {
          outcome: response.outcome,
          transcriptFingerprint: response.transcriptFingerprint,
        },
        type: "evaluation_received",
      });
    } catch (error) {
      recordOperationFailure(error, evaluate);
    }
  }

  function startEvaluation() {
    setErrorMessage(null);
    dispatch({ type: "evaluation_requested" });
    void evaluate();
  }

  async function loadNextHint() {
    if (currentAttempt === null) {
      return;
    }
    try {
      const hint = await api.requestNextHint(currentAttempt.id, hints.length);
      setHints((current) => [...current, hint]);
      dispatch({ hint: { hintLevel: hint.hintLevel }, type: "hint_received" });
    } catch (error) {
      recordOperationFailure(error, loadNextHint);
    }
  }

  function requestHint() {
    setErrorMessage(null);
    dispatch({ type: "hint_requested" });
    void loadNextHint();
  }

  async function retryProblem() {
    if (selectedItem === null) {
      return;
    }
    setErrorMessage(null);
    try {
      const attempt = await api.createAttempt(selectedItem.problem.problemVersionId);
      setCurrentAttempt(attempt);
      dispatch({ attempt: attemptReference(attempt), type: "retry_started" });
    } catch (error) {
      setErrorMessage(safeErrorMessage(error));
    }
  }

  async function loadConcept() {
    const conceptVersionId = selectedItem?.conceptVersionId;
    if (conceptVersionId === null || conceptVersionId === undefined) {
      recordOperationFailure(
        new ApiError("concept_unavailable", "No linked concept is available.", 404),
        loadConcept,
      );
      return;
    }
    try {
      const loaded = await api.getConceptVersion(conceptVersionId);
      setConcept(loaded);
      dispatch({
        concept: { conceptVersionId: loaded.conceptVersionId },
        type: "concept_received",
      });
    } catch (error) {
      recordOperationFailure(error, loadConcept);
    }
  }

  function requestConcept() {
    setErrorMessage(null);
    dispatch({ type: "concept_requested" });
    void loadConcept();
  }

  function retryFailedOperation() {
    if (retryOperation.current === null) {
      return;
    }
    setErrorMessage(null);
    dispatch({ type: "operation_retried" });
    void retryOperation.current();
  }

  if (loadStatus === "loading") {
    return (
      <p className="journey-status" role="status">
        Loading your study profile…
      </p>
    );
  }
  if (loadStatus === "retryable_failure") {
    return (
      <section className="journey-card journey-status-card" aria-labelledby="journey-load-error">
        <p className="eyebrow">Retryable failure</p>
        <h2 id="journey-load-error">Your study profile could not load.</h2>
        <p role="alert">{errorMessage}</p>
        <button className="primary-button" onClick={() => void loadOnboarding()} type="button">
          Retry profile loading
        </button>
      </section>
    );
  }
  if (loadStatus === "profile_required") {
    return (
      <section className="journey-card" aria-labelledby="create-profile-title">
        <p className="eyebrow">Onboarding</p>
        <h2 id="create-profile-title">Create your study profile</h2>
        <p>One profile keeps every active examination target together.</p>
        <form className="journey-form" onSubmit={createProfile}>
          <label>
            Profile name
            <input className="text-input" defaultValue="Synthetic preparation" name="profileName" />
          </label>
          <label>
            Weekly study minutes
            <input
              className="text-input"
              defaultValue="240"
              min="30"
              name="weeklyStudyMinutes"
              step="30"
              type="number"
            />
          </label>
          <button className="primary-button" type="submit">
            Create study profile
          </button>
        </form>
        {errorMessage ? (
          <p className="form-error" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </section>
    );
  }

  if (
    journey.status === "retryable_failure" ||
    journey.status === "permanent_failure" ||
    journey.status === "invalid_schema"
  ) {
    const retryable = journey.status === "retryable_failure";
    const invalidSchema = journey.status === "invalid_schema";
    return (
      <section
        className="journey-card journey-status-card"
        aria-labelledby="journey-operation-error"
      >
        <p className="eyebrow">
          {retryable
            ? "Retryable failure"
            : invalidSchema
              ? "Invalid provider response"
              : "Permanent failure"}
        </p>
        <h2 id="journey-operation-error">
          {invalidSchema ? "No transcript was accepted." : "This step could not finish."}
        </h2>
        <p role="alert">{errorMessage}</p>
        {retryable ? (
          <button className="primary-button" onClick={retryFailedOperation} type="button">
            Retry this step
          </button>
        ) : (
          <p>The application did not fabricate a replacement result.</p>
        )}
      </section>
    );
  }

  let panel;
  if (journey.phase === "onboarding") {
    panel = (
      <section className="journey-card" aria-labelledby="profile-title">
        <p className="eyebrow">Onboarding</p>
        <h2 id="profile-title">Your study profile</h2>
        <p>{profile?.name}</p>
        <ul className="target-list">
          {activeTargets.map((target) => (
            <li key={target.id}>
              <span>Priority {target.priorityRank}</span>
              <strong>{target.examName}</strong>
              <small>
                {target.examDate} · target {target.targetScore}
              </small>
            </li>
          ))}
        </ul>
        {activeTargets.length < 2 ? (
          <div className="journey-onboarding-action">
            <h3>Add at least two active examination targets</h3>
            {missingCycles.map((cycle) => (
              <button
                className="secondary-button"
                key={cycle.id}
                onClick={() => void addTarget(cycle.id)}
                type="button"
              >
                Add {cycle.examName}
              </button>
            ))}
            {missingCycles.length === 0 ? (
              <p>No synthetic examination cycles are available.</p>
            ) : null}
          </div>
        ) : (
          <button className="primary-button" onClick={startPlanning} type="button">
            {"Build today's combined plan"}
          </button>
        )}
        {errorMessage ? (
          <p className="form-error" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </section>
    );
  } else if (journey.phase === "planning" && journey.status === "loading") {
    panel = (
      <p className="journey-status" role="status">
        Building the deterministic combined plan…
      </p>
    );
  } else if (journey.phase === "planning" && journey.status === "empty") {
    panel = (
      <section className="journey-card journey-status-card">
        <p className="eyebrow">Empty plan</p>
        <h2>No planned problems are available.</h2>
        <p>Your examination targets remain unchanged.</p>
      </section>
    );
  } else if (journey.phase === "planning" && plan !== null) {
    panel = (
      <section className="journey-card" aria-labelledby="plan-title">
        <p className="eyebrow">Deterministic plan · {plan.planDate}</p>
        <h2 id="plan-title">{"Today's combined plan"}</h2>
        <div className="journey-target-chips" aria-label="Active examination targets">
          {plan.targets.map((target) => (
            <span key={target.targetId}>{target.examName}</span>
          ))}
        </div>
        <ol className="journey-plan-list">
          {plan.items.map((item, index) => {
            const names = plan.targets
              .filter(({ targetId }) => item.supportedTargetIds.includes(targetId))
              .map(({ examName }) => examName);
            return (
              <li key={item.problem.problemVersionId}>
                <div>
                  <span>
                    Item {item.position} · {item.problem.estimatedMinutes} min
                  </span>
                  <h3>{item.problem.externalCode}</h3>
                  <strong>
                    Supports {names.length} {names.length === 1 ? "target" : "targets"}
                  </strong>
                  <small>{names.join(" · ")}</small>
                </div>
                <button
                  className="secondary-button"
                  onClick={() => void startProblem(index)}
                  type="button"
                >
                  Open {item.problem.externalCode}
                </button>
              </li>
            );
          })}
        </ol>
      </section>
    );
  } else if (journey.phase === "problem_work" && selectedItem !== null) {
    panel = (
      <section className="journey-card problem-card" aria-labelledby="problem-title">
        <p className="eyebrow">Typed math and geometry problem</p>
        <h2 id="problem-title">{selectedItem.problem.externalCode}</h2>
        <p className="version-badge">Pinned content version {selectedItem.problem.version}</p>
        <TypedContentBlocks
          blocks={selectedItem.problem.statement}
          resolveGeometry={(sceneVersionId) =>
            selectedItem.problem.geometryScene?.id === sceneVersionId
              ? { actions: [], scene: selectedItem.problem.geometryScene }
              : null
          }
        />
        <button
          className="primary-button"
          onClick={() => dispatch({ type: "upload_started" })}
          type="button"
        >
          Upload a synthetic solution
        </button>
      </section>
    );
  } else if (journey.phase === "upload") {
    panel = <UploadWorkspace onContinue={useUpload} />;
  } else if (journey.phase === "transcription" && journey.status === "loading") {
    panel = (
      <p className="journey-status" role="status">
        Loading and validating the complete image transcription…
      </p>
    );
  } else if (journey.phase === "transcription" && journey.status === "uncertain") {
    panel = (
      <section className="journey-card journey-status-card" aria-labelledby="uncertain-transcript">
        <p className="eyebrow">Transcription uncertainty</p>
        <h2 id="uncertain-transcript">No transcript was created.</h2>
        <p>The service could not produce a faithful complete document from this image.</p>
        <ul className="transcription-warning-list">
          {transcriptionWarnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
        <button
          className="primary-button"
          onClick={() => dispatch({ type: "transcription_retake" })}
          type="button"
        >
          Upload a clearer synthetic image
        </button>
      </section>
    );
  } else if (journey.phase === "correction" && journey.data.transcript !== undefined) {
    panel = (
      <section className="transcription-review-layout" aria-label="Image and transcript review">
        <figure className="transcription-source-card">
          <p className="eyebrow">Owned verified upload</p>
          {sourceImageUrl === null ? (
            <p role="status">Loading the synthetic source image…</p>
          ) : (
            <div className="transcription-source-image-frame">
              <Image
                alt="Clearly synthetic uploaded mathematics solution"
                height={900}
                src={sourceImageUrl}
                unoptimized
                width={1200}
              />
              {selectedSourceRegion === null ? null : (
                <span
                  aria-label="Selected transcript source region"
                  className="transcription-source-region-overlay"
                  role="img"
                  style={{
                    height: `${selectedSourceRegion.height * 100}%`,
                    left: `${selectedSourceRegion.x * 100}%`,
                    top: `${selectedSourceRegion.y * 100}%`,
                    width: `${selectedSourceRegion.width * 100}%`,
                  }}
                />
              )}
            </div>
          )}
          <figcaption>
            Compare every visible line. Mathematical mistakes must stay as written.
          </figcaption>
        </figure>
        <div>
          {transcriptionRun === null ? null : (
            <p className="transcription-run-note">
              Validated with {transcriptionRun.provider} · {transcriptionRun.modelSnapshot} · schema{" "}
              {transcriptionRun.schemaVersion}
            </p>
          )}
          <TranscriptEditor
            initialState={journey.data.transcript}
            key={journey.data.transcript.attemptId}
            onConfirm={confirmCorrectedTranscript}
            onSourceRegionChange={setSelectedSourceRegion}
            sourceLabel="Validated image transcription"
          />
        </div>
      </section>
    );
  } else if (journey.phase === "confirmation" && journey.data.confirmedTranscript !== undefined) {
    panel = (
      <section className="journey-card" aria-labelledby="authoritative-title">
        <p className="eyebrow">Explicitly confirmed</p>
        <h2 id="authoritative-title">Authoritative evaluation input</h2>
        <p>
          This locked snapshot—and no earlier draft—is sent to the deterministic mock evaluation.
        </p>
        <p className="identifier">
          Transcript version {transcriptVersion?.version} · {confirmation?.transcriptVersionId}
        </p>
        <p className="identifier">SHA-256 {confirmation?.transcriptHash}</p>
        <ConfirmedTranscriptView transcript={journey.data.confirmedTranscript} />
        <button className="primary-button" onClick={startEvaluation} type="button">
          Run clearly mocked evaluation
        </button>
      </section>
    );
  } else if (journey.phase === "mock_evaluation" && journey.status === "loading") {
    panel = (
      <p className="journey-status" role="status">
        Evaluating the confirmed transcript…
      </p>
    );
  } else if (journey.phase === "mock_evaluation" && evaluation !== null) {
    panel = (
      <section className="journey-card" aria-labelledby="evaluation-title">
        <p className="eyebrow">Structured mock evaluation</p>
        <h2 id="evaluation-title">
          {journey.status === "uncertain" ? "Evaluation is uncertain" : "Deterministic feedback"}
        </h2>
        {journey.status === "uncertain" ? (
          <p className="uncertain-callout">
            No correctness claim is made for this uncertain result.
          </p>
        ) : null}
        <TypedContentBlocks blocks={evaluation.feedback} />
        <h3>Next steps</h3>
        <TypedContentBlocks blocks={evaluation.nextSteps} />
        <p className="reference-note">
          Reference solutions are non-exhaustive; valid alternative methods may also be correct.
        </p>
        <button className="primary-button" onClick={requestHint} type="button">
          Request hint 1
        </button>
      </section>
    );
  } else if (journey.phase === "hint" && journey.status === "loading") {
    panel = (
      <p className="journey-status" role="status">
        Loading the next curated hint…
      </p>
    );
  } else if (journey.phase === "hint") {
    const latestHint = hints.at(-1);
    panel = (
      <section className="journey-card" aria-labelledby="hint-title">
        <p className="eyebrow">Progressive typed help</p>
        <h2 id="hint-title">Curated hints</h2>
        <ol className="journey-hint-list">
          {hints.map((hint) => (
            <li key={hint.hintId}>
              <strong>Hint {hint.hintLevel}</strong>
              <TypedContentBlocks blocks={hint.content} />
            </li>
          ))}
        </ol>
        {latestHint && selectedItem?.problem.geometryScene ? (
          <GeometryScene
            actions={latestHint.geometryActions}
            scene={selectedItem.problem.geometryScene}
          />
        ) : null}
        {!latestHint?.revealsCompleteSolution ? (
          <button className="secondary-button" onClick={requestHint} type="button">
            Request hint {hints.length + 1}
          </button>
        ) : null}
        <button className="primary-button" onClick={() => void retryProblem()} type="button">
          Retry this problem
        </button>
      </section>
    );
  } else if (journey.phase === "retry" && selectedItem !== null) {
    panel = (
      <section className="journey-card" aria-labelledby="retry-title">
        <p className="eyebrow">Retry</p>
        <h2 id="retry-title">New attempt ready</h2>
        <p>
          Attempt {journey.data.attempts.length} · same immutable content version{" "}
          {selectedItem.problem.version}
        </p>
        <p className="identifier">Attempt ID {currentAttempt?.id}</p>
        <button className="primary-button" onClick={requestConcept} type="button">
          Study the linked concept
        </button>
      </section>
    );
  } else if (journey.phase === "concept" && journey.status === "loading") {
    panel = (
      <p className="journey-status" role="status">
        Loading typed concept content…
      </p>
    );
  } else if (journey.phase === "concept" && concept !== null) {
    panel = (
      <section className="journey-card" aria-labelledby="concept-title">
        <p className="eyebrow">Typed concept · version {concept.version}</p>
        <h2 id="concept-title">{concept.name}</h2>
        <TypedContentBlocks blocks={concept.content} />
        {concept.geometryScene ? <GeometryScene scene={concept.geometryScene} /> : null}
        <button
          className="primary-button"
          onClick={() => dispatch({ type: "session_completed" })}
          type="button"
        >
          Complete session
        </button>
      </section>
    );
  } else {
    const summary = summarizeStaticJourney(journey);
    panel = (
      <section className="journey-card" aria-labelledby="summary-title">
        <p className="eyebrow">Application-owned summary</p>
        <h2 id="summary-title">Session complete</h2>
        <dl className="journey-summary">
          <div>
            <dt>Targets</dt>
            <dd>{summary.targetCount} active targets</dd>
          </div>
          <div>
            <dt>Plan</dt>
            <dd>{summary.plannedItemCount} planned items</dd>
          </div>
          <div>
            <dt>Attempts</dt>
            <dd>{summary.attemptCount} attempts</dd>
          </div>
          <div>
            <dt>Hints</dt>
            <dd>Hints {summary.hintLevelsUsed.join(", ")}</dd>
          </div>
          <div>
            <dt>Evaluation</dt>
            <dd>{summary.evaluationOutcome}</dd>
          </div>
        </dl>
        <p className="identifier">Problem version {summary.problemVersionId}</p>
      </section>
    );
  }

  return (
    <div className="static-journey">
      <nav className="journey-progress" aria-label="Student journey progress">
        <span>{journey.phase.replaceAll("_", " ")}</span>
        <strong>{journey.status}</strong>
      </nav>
      {transitionMessage ? (
        <p className="form-error" role="alert">
          {transitionMessage}
        </p>
      ) : null}
      {panel}
    </div>
  );
}
