/**
 * WorkspaceDetailPage — workspace detail with three-column layout.
 *
 * Left:   scrollable execution list (reuses VirtualList + useOffsetVirtualData)
 * Middle: live activity viewer (SSE event stream)
 * Right:  empty placeholder
 */
import { useCallback, useEffect, useRef, useState } from "react";
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
const ESTIMATED_ROW_HEIGHT = 76;

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
      width="14"
      height="14"
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
      width="14"
      height="14"
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
/*  ExecutionCard                                                      */
/* ------------------------------------------------------------------ */

function ExecutionCard({
  execution,
  onDispatch,
  onDelete,
}: {
  execution: Execution;
  onDispatch: (execution: Execution) => void;
  onDelete: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(execution.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const shortId = execution.id.slice(0, 8);
  const commandPreview = execution.spec.command.replace(/\s+/g, " ").trim();
  const hasDispatch = execution.dispatch_id !== null;

  return (
    <div className={styles.executionCard}>
      <div className={styles.cardActions}>
        <button
          className={styles.cardActionButton}
          onClick={() => onDispatch(execution)}
          disabled={hasDispatch}
          title={hasDispatch ? "Already dispatched" : "Dispatch execution"}
          type="button"
        >
          <PlayIcon />
        </button>
        <button
          className={`${styles.cardActionButton} ${styles.deleteCardButton}`}
          onClick={() => onDelete(execution.id)}
          title="Delete execution"
          type="button"
        >
          <TrashIcon />
        </button>
      </div>
      <p className={styles.executionType}>{execution.spec.kind}</p>
      <p className={styles.executionName} title={execution.name}>
        {execution.name}
      </p>
      <p className={styles.executionCommand} title={commandPreview}>
        {commandPreview}
      </p>
      <span
        className={styles.executionId}
        onClick={handleCopyId}
        title={copied ? "Copied!" : `Click to copy: ${execution.id}`}
      >
        {copied ? "Copied!" : shortId}
      </span>
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
  sandboxes,
  onClose,
  onDispatch,
}: {
  open: boolean;
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
        <h3 className={styles.dialogTitle}>Dispatch execution</h3>
        <label className={styles.dialogLabel} htmlFor="dispatch-sandbox">
          Sandbox
        </label>
        <select
          id="dispatch-sandbox"
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
/*  CreateExecutionForm                                                */
/* ------------------------------------------------------------------ */

function CreateExecutionForm({
  sandboxes,
  onCreated,
}: {
  sandboxes: Sandbox[];
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
      const execution = await createExecution({
        name: trimmedName,
        spec: { kind, command: trimmedCommand },
      });
      await dispatchExecution(execution.id, {
        sandbox_id: sandboxId || null,
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
    <form onSubmit={handleSubmit}>
      <h3 className={styles.formHeading}>New Execution</h3>

      <div className={styles.formSection}>
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

      <div className={styles.formSection}>
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

      <div className={styles.formSection}>
        <label className={styles.formLabel} htmlFor="exec-commands">
          Command
        </label>
        <textarea
          id="exec-commands"
          className={styles.formTextarea}
          value={commandText}
          onChange={(e) => setCommandText(e.target.value)}
          placeholder={"echo hello\nls -la\nprintf 'done\\n' > proof.txt"}
          rows={6}
        />
      </div>

      <div className={styles.formSection}>
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
/*  CreateExecutionDialog                                              */
/* ------------------------------------------------------------------ */

function CreateExecutionDialog({
  open,
  sandboxes,
  onClose,
  onCreated,
}: {
  open: boolean;
  sandboxes: Sandbox[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  const prevOpen = useRef(false);
  if (open !== prevOpen.current) {
    prevOpen.current = open;
    if (open) {
      queueMicrotask(() => dialogRef.current?.showModal());
    } else {
      dialogRef.current?.close();
    }
  }

  const handleCreated = () => {
    onCreated();
    onClose();
  };

  return (
    <dialog ref={dialogRef} className={styles.dialog} onClose={onClose}>
      <CreateExecutionForm sandboxes={sandboxes} onCreated={handleCreated} />
    </dialog>
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
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [executionNames, setExecutionNames] = useState<Map<string, string>>(
    () => new Map(),
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

  // Build dispatch_id → execution name lookup for the activity viewer.
  useEffect(() => {
    const controller = new AbortController();
    fetchExecutionPage({ offset: 0, limit: 100, query: undefined as void, signal: controller.signal })
      .then((result) => {
        const names = new Map<string, string>();
        for (const exec of result.items) {
          if (exec.dispatch_id) {
            names.set(exec.dispatch_id, exec.name);
          }
        }
        setExecutionNames(names);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        console.error("Failed to fetch execution names:", err);
      });
    return () => controller.abort();
  }, []);

  const executionData = useOffsetVirtualData<Execution, void>({
    query: undefined as void,
    fetchPage: fetchExecutionPage,
    pageSize: PAGE_SIZE,
  });

  const { invalidate } = executionData;

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
      const result = await dispatchExecution(dispatchTarget.id, { sandbox_id: sandboxId });
      setExecutionNames((prev) => {
        const next = new Map(prev);
        next.set(result.id, dispatchTarget.name);
        return next;
      });
      setDispatchTarget(null);
      invalidate();
    },
    [dispatchTarget, invalidate],
  );

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
        <h2 className={styles.workspaceName}>
          {workspace?.name ?? "\u00A0"}
        </h2>
      </div>

      <div className={styles.columns}>
        <div className={styles.leftColumn}>
          <div className={styles.columnHeadingRow}>
            <h3 className={styles.columnHeading}>Executions</h3>
            <button
              className={styles.createExecutionButton}
              onClick={() => setCreateDialogOpen(true)}
              title="Create execution"
              type="button"
            >
              +
            </button>
          </div>
          {executionData.reachedEnd && executionData.totalEstimate === 0 ? (
            <p className={styles.empty}>No executions yet.</p>
          ) : (
            <VirtualList
              data={executionData}
              renderItem={(execution) => (
                <ExecutionCard
                  execution={execution}
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
          <ActivityViewer executionNames={executionNames} />
        </div>

        <div className={styles.rightColumn} />
      </div>

      <DispatchDialog
        open={dispatchTarget !== null}
        sandboxes={sandboxes}
        onClose={() => setDispatchTarget(null)}
        onDispatch={handleConfirmDispatch}
      />

      <CreateExecutionDialog
        open={createDialogOpen}
        sandboxes={sandboxes}
        onClose={() => setCreateDialogOpen(false)}
        onCreated={invalidate}
      />
    </div>
  );
}
