/**
 * WorkspaceDetailPage — workspace detail with two-column layout.
 *
 * Left:   sidebar with inline create form + compact execution list
 * Middle: live activity viewer (SSE event stream)
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useOffsetVirtualData } from "../components/virtual-list/useOffsetVirtualData";
import { VirtualList } from "../components/virtual-list/VirtualList";
import { ActivityViewer } from "../components/activity-viewer/ActivityViewer";
import {
  fetchExecutionPage,
  createExecution,
  dispatchExecution,
  deleteExecution,
} from "../api/executions";
import { fetchSandboxes } from "../api/sandboxes";
import { fetchWorkspace } from "../api/workspaces";
import type { Execution } from "../api/executions";
import type { Sandbox } from "../api/sandboxes";
import type { Workspace } from "../api/workspaces";
import styles from "./WorkspaceDetailPage.module.css";

const PAGE_SIZE = 20;
const ESTIMATED_ROW_HEIGHT = 32;

const EXECUTION_COLORS = [
  "#2dd4bf", "#f97066", "#a78bfa", "#84cc16", "#f59e0b", "#e879a8",
  "#38bdf8", "#f97316", "#34d399", "#f472b6", "#818cf8", "#fbbf24",
];

/* ------------------------------------------------------------------ */
/*  Icons                                                              */
/* ------------------------------------------------------------------ */

function BackArrow() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 12L6 8l4-4" />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 16 16"
      fill="currentColor"
      stroke="none"
    >
      <path d="M4 2l10 6-10 6V2z" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 4h12" />
      <path d="M5.333 4V2.667a1.333 1.333 0 0 1 1.334-1.334h2.666a1.333 1.333 0 0 1 1.334 1.334V4" />
      <path d="M12.667 4v9.333a1.333 1.333 0 0 1-1.334 1.334H4.667a1.333 1.333 0 0 1-1.334-1.334V4" />
      <path d="M6.667 7.333v4" />
      <path d="M9.333 7.333v4" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Color helpers                                                      */
/* ------------------------------------------------------------------ */

function getExecutionColor(execution: Execution): string {
  const stored = execution.metadata?.color;
  if (typeof stored === "string" && stored.length > 0) return stored;
  return "var(--accent)";
}

function pickNextColor(existingExecutions: Execution[]): string {
  // Count how many executions use each color to round-robin.
  const usedCounts = new Map<string, number>();
  for (const ex of existingExecutions) {
    const c = typeof ex.metadata?.color === "string" ? ex.metadata.color : null;
    if (c) usedCounts.set(c, (usedCounts.get(c) ?? 0) + 1);
  }
  // Pick the least-used color from the palette.
  let best = EXECUTION_COLORS[0];
  let bestCount = Infinity;
  for (const c of EXECUTION_COLORS) {
    const count = usedCounts.get(c) ?? 0;
    if (count < bestCount) {
      best = c;
      bestCount = count;
    }
  }
  return best;
}

/* ------------------------------------------------------------------ */
/*  ExecutionCard (compact, expandable)                                 */
/* ------------------------------------------------------------------ */

function ExecutionCard({
  execution,
  expanded,
  onToggle,
  onDispatch,
  onDelete,
}: {
  execution: Execution;
  expanded: boolean;
  onToggle: () => void;
  onDispatch: (execution: Execution) => void;
  onDelete: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const color = getExecutionColor(execution);
  const hasDispatch = execution.dispatch_id !== null;

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(execution.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const shortId = execution.id.slice(0, 8);

  return (
    <div>
      <div className={styles.executionCard} onClick={onToggle}>
        <span
          className={styles.executionDot}
          style={{ color: hasDispatch ? color : "var(--text)" }}
        >
          {"\u25CF"}
        </span>
        <span className={styles.executionLabel} title={execution.name}>
          {execution.name}
        </span>
        <div className={styles.cardActions}>
          <button
            className={styles.cardActionButton}
            onClick={(e) => {
              e.stopPropagation();
              onDispatch(execution);
            }}
            disabled={hasDispatch}
            title={hasDispatch ? "Already dispatched" : "Dispatch execution"}
            type="button"
          >
            <PlayIcon />
          </button>
          <button
            className={`${styles.cardActionButton} ${styles.deleteCardButton}`}
            onClick={(e) => {
              e.stopPropagation();
              onDelete(execution.id);
            }}
            title="Delete execution"
            type="button"
          >
            <TrashIcon />
          </button>
        </div>
      </div>
      {expanded && (
        <div className={styles.executionDetails}>
          <p className={styles.executionType}>{execution.spec.kind}</p>
          <pre className={styles.executionCommand}>
            {execution.spec.command}
          </pre>
          <span
            className={styles.executionId}
            onClick={handleCopyId}
            title={copied ? "Copied!" : `Click to copy: ${execution.id}`}
          >
            {copied ? "Copied!" : shortId}
          </span>
        </div>
      )}
    </div>
  );
}

function ExecutionPlaceholder() {
  return <div className={styles.executionPlaceholder} />;
}

/* ------------------------------------------------------------------ */
/*  DispatchDialog                                                     */
/* ------------------------------------------------------------------ */

function DispatchDialog({
  open,
  execution,
  sandboxes,
  onClose,
  onDispatch,
}: {
  open: boolean;
  execution: Execution | null;
  sandboxes: Sandbox[];
  onClose: () => void;
  onDispatch: (sandboxId: string | null) => Promise<void>;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [sandboxId, setSandboxId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const prevOpen = useRef(false);
  if (open !== prevOpen.current) {
    prevOpen.current = open;
    if (open) {
      setSandboxId("");
      setError("");
      queueMicrotask(() => dialogRef.current?.showModal());
    } else {
      dialogRef.current?.close();
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await onDispatch(sandboxId || null);
      onClose();
    } catch {
      setError("Failed to dispatch execution.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <dialog ref={dialogRef} className={styles.dialog} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <h3 className={styles.dialogTitle}>
          Dispatch: {execution?.name ?? "execution"}
        </h3>
        <label className={styles.dialogLabel} htmlFor="dispatch-sandbox">
          Sandbox
        </label>
        <select
          id="dispatch-sandbox"
          className={styles.dialogSelect}
          value={sandboxId}
          onChange={(e) => setSandboxId(e.target.value)}
        >
          <option value="">None</option>
          {sandboxes.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        {error && <p className={styles.dialogError}>{error}</p>}
        <div className={styles.dialogActions}>
          <button
            type="button"
            className={styles.dialogCancel}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className={styles.dialogSubmit}
            disabled={submitting}
          >
            {submitting ? "Dispatching..." : "Dispatch"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

/* ------------------------------------------------------------------ */
/*  Inline create execution form                                       */
/* ------------------------------------------------------------------ */

function CreateExecutionForm({
  sandboxes,
  allExecutions,
  onCreated,
}: {
  sandboxes: Sandbox[];
  allExecutions: Execution[];
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("command");
  const [commandText, setCommandText] = useState("");
  const [sandboxId, setSandboxId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const trimmedName = name.trim();
  const trimmedCommand = commandText.trim();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trimmedName || !trimmedCommand) return;
    setSubmitting(true);
    setError("");
    try {
      const color = pickNextColor(allExecutions);
      const execution = await createExecution({
        name: trimmedName,
        spec: { kind, command: trimmedCommand },
        metadata: { color },
      });
      await dispatchExecution(execution.id, {
        sandbox_id: sandboxId || null,
        callback: {
          execution_id: execution.id,
          execution_name: execution.name,
          execution_color: color,
        },
      });
      setName("");
      setCommandText("");
      onCreated();
    } catch {
      setError("Failed to create & dispatch execution.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className={styles.inlineForm} onSubmit={handleSubmit}>
      <div className={styles.formRow}>
        <label className={styles.formLabel} htmlFor="exec-name">
          Name
        </label>
        <input
          id="exec-name"
          className={styles.formInput}
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Build backend image"
          required
        />
      </div>

      <div className={styles.formRow}>
        <label className={styles.formLabel} htmlFor="exec-kind">
          Type
        </label>
        <select
          id="exec-kind"
          className={styles.formSelect}
          value={kind}
          onChange={(e) => setKind(e.target.value)}
        >
          <option value="command">command</option>
        </select>
      </div>

      <div className={styles.formRow}>
        <label className={styles.formLabel} htmlFor="exec-commands">
          Command
        </label>
        <textarea
          id="exec-commands"
          className={styles.formTextarea}
          value={commandText}
          onChange={(e) => setCommandText(e.target.value)}
          placeholder={"echo hello\nls -la"}
          rows={4}
        />
      </div>

      <div className={styles.formRow}>
        <label className={styles.formLabel} htmlFor="exec-sandbox">
          Sandbox
        </label>
        <select
          id="exec-sandbox"
          className={styles.formSelect}
          value={sandboxId}
          onChange={(e) => setSandboxId(e.target.value)}
        >
          <option value="">None</option>
          {sandboxes.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {error && <p className={styles.formError}>{error}</p>}

      <button
        type="submit"
        className={styles.submitButton}
        disabled={submitting || !trimmedName || !trimmedCommand}
      >
        {submitting ? "Dispatching..." : "Create & Dispatch"}
      </button>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function WorkspaceDetailPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [sandboxes, setSandboxes] = useState<Sandbox[]>([]);
  const [dispatchTarget, setDispatchTarget] = useState<Execution | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [expandedExecutions, setExpandedExecutions] = useState<Set<string>>(
    new Set(),
  );

  useEffect(() => {
    if (!workspaceId) return;
    const controller = new AbortController();
    fetchWorkspace(workspaceId, controller.signal)
      .then(setWorkspace)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        console.error("Failed to fetch workspace:", err);
      });
    return () => controller.abort();
  }, [workspaceId]);

  useEffect(() => {
    const controller = new AbortController();
    fetchSandboxes(controller.signal)
      .then(setSandboxes)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        console.error("Failed to fetch sandboxes:", err);
      });
    return () => controller.abort();
  }, []);

  const executionData = useOffsetVirtualData<Execution, void>({
    query: undefined as void,
    fetchPage: fetchExecutionPage,
    pageSize: PAGE_SIZE,
  });

  const { invalidate } = executionData;

  // Collect all loaded executions for color assignment.
  const allExecutions = useMemo(() => {
    const items: Execution[] = [];
    for (let i = 0; i < executionData.totalEstimate; i++) {
      const item = executionData.getItem(i);
      if (item) items.push(item);
    }
    return items;
  }, [executionData]);

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteExecution(id);
        invalidate();
      } catch (err) {
        console.error("Failed to delete execution:", err);
      }
    },
    [invalidate],
  );

  const handleCardDispatch = useCallback((execution: Execution) => {
    setDispatchTarget(execution);
  }, []);

  const handleConfirmDispatch = useCallback(
    async (sandboxId: string | null) => {
      if (!dispatchTarget) return;
      const color = getExecutionColor(dispatchTarget);
      await dispatchExecution(dispatchTarget.id, {
        sandbox_id: sandboxId,
        callback: {
          execution_id: dispatchTarget.id,
          execution_name: dispatchTarget.name,
          execution_color: color,
        },
      });
      setDispatchTarget(null);
      invalidate();
    },
    [dispatchTarget, invalidate],
  );

  const toggleExpanded = useCallback((id: string) => {
    setExpandedExecutions((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleFormCreated = useCallback(() => {
    invalidate();
    setShowForm(false);
  }, [invalidate]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button
          className={styles.backButton}
          onClick={() => navigate("/workspaces")}
          type="button"
        >
          <BackArrow />
          Back
        </button>
        <span className={styles.headerSep}>/</span>
        <h2 className={styles.workspaceName}>
          {workspace?.name ?? "\u00A0"}
        </h2>
      </div>

      <div className={styles.columns}>
        <div className={styles.leftColumn}>
          <div className={styles.columnHeadingRow}>
            <h3 className={styles.columnHeading}>Executions</h3>
          </div>

          <button
            className={styles.newExecutionButton}
            onClick={() => setShowForm((v) => !v)}
            type="button"
          >
            {showForm ? "\u2715 Close" : "+ New"}
          </button>

          {showForm && (
            <CreateExecutionForm
              sandboxes={sandboxes}
              allExecutions={allExecutions}
              onCreated={handleFormCreated}
            />
          )}

          {executionData.reachedEnd && executionData.totalEstimate === 0 ? (
            <p className={styles.empty}>No executions yet.</p>
          ) : (
            <VirtualList
              data={executionData}
              renderItem={(execution) => (
                <ExecutionCard
                  execution={execution}
                  expanded={expandedExecutions.has(execution.id)}
                  onToggle={() => toggleExpanded(execution.id)}
                  onDispatch={handleCardDispatch}
                  onDelete={handleDelete}
                />
              )}
              renderPlaceholder={() => <ExecutionPlaceholder />}
              getItemKey={(execution) => execution.id}
              estimatedItemHeight={ESTIMATED_ROW_HEIGHT}
              overscan={3}
              columns={1}
              className={styles.executionListContainer}
            />
          )}
        </div>

        <div className={styles.middleColumn}>
          <ActivityViewer />
        </div>
      </div>

      <DispatchDialog
        open={dispatchTarget !== null}
        execution={dispatchTarget}
        sandboxes={sandboxes}
        onClose={() => setDispatchTarget(null)}
        onDispatch={handleConfirmDispatch}
      />
    </div>
  );
}
