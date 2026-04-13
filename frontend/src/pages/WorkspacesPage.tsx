/**
 * WorkspacesPage — scrollable card grid of workspaces.
 *
 * This page composes the reusable virtual-list layer with workspace-specific
 * rendering:
 *   1. Data adapter — fetchWorkspacePage (in api/workspaces.ts)
 *   2. Data hook   — useOffsetVirtualData (generic, domain-agnostic)
 *   3. View layer  — VirtualList (generic) + WorkspaceCard (workspace-specific)
 */
import { useOffsetVirtualData } from "../components/virtual-list/useOffsetVirtualData";
import { VirtualList } from "../components/virtual-list/VirtualList";
import { fetchWorkspacePage } from "../api/workspaces";
import type { Workspace } from "../api/workspaces";
import styles from "./WorkspacesPage.module.css";

const PAGE_SIZE = 20;
const COLUMNS = 3;
const ESTIMATED_ROW_HEIGHT = 128; // card height (~88px) + gap (16px) + padding

function WorkspaceCard({ workspace }: { workspace: Workspace }) {
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>{workspace.name}</h3>
      <p className={styles.cardMeta}>
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

  return (
    <div className={styles.page}>
      <h2 className={styles.heading}>Workspaces</h2>

      {data.reachedEnd && data.totalEstimate === 0 ? (
        <p className={styles.empty}>No workspaces yet.</p>
      ) : data.totalEstimate === 0 ? (
        // Initial fetch in progress — no data yet.
        // Show a few skeleton cards so the user sees immediate feedback.
        <div className={styles.skeletonGrid}>
          {Array.from({ length: COLUMNS }, (_, i) => (
            <WorkspacePlaceholder key={i} />
          ))}
        </div>
      ) : (
        <VirtualList
          data={data}
          renderItem={(workspace) => <WorkspaceCard workspace={workspace} />}
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
