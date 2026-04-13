/**
 * ActivityViewer — live event stream rendered as chat-message-like cards.
 *
 * Connects to the SSE event stream, groups contiguous events by source,
 * and renders them through VirtualList for efficient scrolling.
 */
import { useState } from "react";
import { useEventStreamData } from "../virtual-list/useEventStreamData";
import { VirtualList } from "../virtual-list/VirtualList";
import type { EventGroup } from "../virtual-list/useEventStreamData";
import styles from "./ActivityViewer.module.css";

const ESTIMATED_ROW_HEIGHT = 80;

function EventGroupCard({
  group,
  executionName,
}: {
  group: EventGroup;
  executionName: string | undefined;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(group.sourceId);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lines = group.events.map((e) => e.payload.line).join("\n");

  return (
    <div className={styles.eventGroupCard}>
      <div className={styles.eventGroupHeader}>
        <span className={styles.eventGroupName}>
          {executionName ?? group.shortId}
        </span>
        <span
          className={styles.eventGroupId}
          onClick={handleCopyId}
          title={copied ? "Copied!" : `Click to copy: ${group.sourceId}`}
        >
          {copied ? "Copied!" : group.shortId}
        </span>
      </div>
      <pre className={styles.eventGroupBody}>{lines}</pre>
    </div>
  );
}

function EventGroupPlaceholder() {
  return <div className={styles.eventGroupPlaceholder} />;
}

export function ActivityViewer({
  executionNames,
}: {
  executionNames: Map<string, string>;
}) {
  const data = useEventStreamData();

  return (
    <div className={styles.container}>
      <h3 className={styles.heading}>Activity</h3>
      {data.totalEstimate === 0 && !data.isLoading ? (
        <p className={styles.empty}>No activity yet.</p>
      ) : (
        <VirtualList
          data={data}
          renderItem={(group) => (
            <EventGroupCard
              group={group}
              executionName={executionNames.get(group.sourceId)}
            />
          )}
          renderPlaceholder={() => <EventGroupPlaceholder />}
          getItemKey={(group) => group.firstEventId}
          estimatedItemHeight={ESTIMATED_ROW_HEIGHT}
          overscan={5}
          columns={1}
          className={styles.list}
        />
      )}
    </div>
  );
}
