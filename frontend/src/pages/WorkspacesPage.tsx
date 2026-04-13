/**
 * WorkspacesPage — scrollable list of workspace cards.
 *
 * This page composes the reusable virtual-list layer with workspace-specific
 * rendering:
 *   1. Data adapter — fetchWorkspacePage / deleteWorkspace (in api/workspaces.ts)
 *   2. Data hook   — useOffsetVirtualData (generic, domain-agnostic)
 *   3. View layer  — VirtualList (generic) + WorkspaceCard (workspace-specific)
 */
import { useCallback, useState } from "react";
import { useOffsetVirtualData } from "../components/virtual-list/useOffsetVirtualData";
import { VirtualList } from "../components/virtual-list/VirtualList";
import { fetchWorkspacePage, deleteWorkspace } from "../api/workspaces";
import type { Workspace } from "../api/workspaces";
import styles from "./WorkspacesPage.module.css";

const PAGE_SIZE = 20;
const COLUMNS = 1;
const ESTIMATED_ROW_HEIGHT = 110; // card height (~82px) + 12px gap + padding

function TrashIcon() {
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
      <path d="M2 4h12" />
      <path d="M5.333 4V2.667a1.333 1.333 0 0 1 1.334-1.334h2.666a1.333 1.333 0 0 1 1.334 1.334V4" />
      <path d="M12.667 4v9.333a1.333 1.333 0 0 1-1.334 1.334H4.667a1.333 1.333 0 0 1-1.334-1.334V4" />
      <path d="M6.667 7.333v4" />
      <path d="M9.333 7.333v4" />
    </svg>
  );
}

function WorkspaceCard({
  workspace,
  onDelete,
}: {
  workspace: Workspace;
  onDelete: (id: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (deleting) return;
    setDeleting(true);
    onDelete(workspace.id);
  };

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(workspace.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const shortId = workspace.id.slice(0, 8);

  return (
    <div className={styles.card}>
      <button
        className={styles.deleteButton}
        onClick={handleDelete}
        disabled={deleting}
        aria-label="Delete workspace"
        type="button"
      >
        <TrashIcon />
      </button>
      <h3 className={styles.cardTitle}>{workspace.name}</h3>
      <p className={styles.cardMeta}>
        <span
          className={styles.workspaceId}
          onClick={handleCopyId}
          title={copied ? "Copied!" : `Click to copy: ${workspace.id}`}
        >
          {copied ? "Copied!" : shortId}
        </span>
        <span className={styles.metaSep}>&middot;</span>
        Created {new Date(workspace.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}

function WorkspacePlaceholder() {
  return <div className={styles.placeholder} />;
}

export default function WorkspacesPage() {
  const data = useOffsetVirtualData<Workspace, void>({
    query: undefined as void,
    fetchPage: fetchWorkspacePage,
    pageSize: PAGE_SIZE,
  });

  const { invalidate } = data;

  const handleDelete = useCallback(
    async (workspaceId: string) => {
      try {
        await deleteWorkspace(workspaceId);
        invalidate();
      } catch (err) {
        console.error("Failed to delete workspace:", err);
      }
    },
    [invalidate],
  );

  return (
    <div className={styles.page}>
      <h2 className={styles.heading}>Workspaces</h2>

      {data.reachedEnd && data.totalEstimate === 0 ? (
        <p className={styles.empty}>No workspaces yet.</p>
      ) : data.totalEstimate === 0 ? (
        <div className={styles.skeletonGrid}>
          <WorkspacePlaceholder />
        </div>
      ) : (
        <VirtualList
          data={data}
          renderItem={(workspace) => (
            <WorkspaceCard workspace={workspace} onDelete={handleDelete} />
          )}
          renderPlaceholder={() => <WorkspacePlaceholder />}
          getItemKey={(workspace) => workspace.id}
          estimatedItemHeight={ESTIMATED_ROW_HEIGHT}
          overscan={3}
          columns={COLUMNS}
          className={styles.listContainer}
        />
      )}
    </div>
  );
}
