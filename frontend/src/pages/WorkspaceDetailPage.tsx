/**
 * WorkspaceDetailPage — workspace detail with three-column layout.
 *
 * Left:   scrollable execution list (reuses VirtualList + useOffsetVirtualData)
 * Middle: activity placeholder (not yet implemented)
 * Right:  empty placeholder
 */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useOffsetVirtualData } from "../components/virtual-list/useOffsetVirtualData";
import { VirtualList } from "../components/virtual-list/VirtualList";
import { fetchExecutionPage } from "../api/executions";
import { fetchWorkspace } from "../api/workspaces";
import type { Execution } from "../api/executions";
import type { Workspace } from "../api/workspaces";
import styles from "./WorkspaceDetailPage.module.css";

const PAGE_SIZE = 20;
const ESTIMATED_ROW_HEIGHT = 62;

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

function ExecutionCard({ execution }: { execution: Execution }) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(execution.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const shortId = execution.id.slice(0, 8);
  const name = execution.spec.commands[0] ?? execution.spec.kind;

  return (
    <div className={styles.executionCard}>
      <p className={styles.executionType}>{execution.spec.kind}</p>
      <p className={styles.executionName} title={name}>
        {name}
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

export default function WorkspaceDetailPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);

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

  const executionData = useOffsetVirtualData<Execution, void>({
    query: undefined as void,
    fetchPage: fetchExecutionPage,
    pageSize: PAGE_SIZE,
  });

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
          <h3 className={styles.columnHeading}>Executions</h3>
          {executionData.reachedEnd && executionData.totalEstimate === 0 ? (
            <p className={styles.empty}>No executions yet.</p>
          ) : (
            <VirtualList
              data={executionData}
              renderItem={(execution) => (
                <ExecutionCard execution={execution} />
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
          <p>Activity</p>
        </div>

        <div className={styles.rightColumn} />
      </div>
    </div>
  );
}
