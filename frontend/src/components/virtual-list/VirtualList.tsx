/**
 * VirtualList — generic virtualized list/grid component.
 *
 * ABSTRACTION BOUNDARY: This component knows nothing about what it renders.
 * It receives data from useOffsetVirtualData and delegates item rendering
 * to the consumer's renderItem / renderPlaceholder callbacks.
 *
 * Grid support: when `columns > 1`, the virtualizer tracks *rows* (each
 * containing `columns` items). Row N maps to items [N*columns, (N+1)*columns).
 * This keeps virtualization one-dimensional (vertical) while producing a
 * multi-column card grid.
 */
import { useEffect, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { VirtualListProps } from "./types";
import styles from "./VirtualList.module.css";

function DefaultPlaceholder() {
  return <div className={styles.placeholder} />;
}

export function VirtualList<T>({
  data,
  renderItem,
  renderPlaceholder,
  getItemKey,
  estimatedItemHeight,
  overscan = 5,
  columns = 1,
  className,
}: VirtualListProps<T>) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const rowCount = Math.ceil(data.totalEstimate / columns);

  const virtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => estimatedItemHeight,
    overscan,
  });

  const virtualRows = virtualizer.getVirtualItems();

  // Tell the data layer which item indexes the viewport needs.
  // This fires whenever the visible row range changes (scroll, resize).
  useEffect(() => {
    if (virtualRows.length === 0) return;
    const firstRow = virtualRows[0].index;
    const lastRow = virtualRows[virtualRows.length - 1].index;
    const startIndex = firstRow * columns;
    const endIndex = (lastRow + 1) * columns;
    data.ensureRangeLoaded(startIndex, endIndex);
  }, [virtualRows, columns, data]);

  return (
    <div
      ref={scrollRef}
      className={`${styles.scrollContainer} ${className ?? ""}`}
    >
      {/* Spacer div whose height matches the total virtualized content.
          This gives the browser an accurate scrollbar thumb size. */}
      <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
        {virtualRows.map((virtualRow) => {
          const rowStartIndex = virtualRow.index * columns;

          const rowStyle: React.CSSProperties = {
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            transform: `translateY(${virtualRow.start}px)`,
            ...(columns > 1 && {
              display: "grid",
              gridTemplateColumns: `repeat(${columns}, 1fr)`,
              gap: "16px",
            }),
          };

          return (
            <div
              key={virtualRow.index}
              ref={virtualizer.measureElement}
              data-index={virtualRow.index}
              style={rowStyle}
            >
              {Array.from({ length: columns }, (_, colIdx) => {
                const itemIndex = rowStartIndex + colIdx;

                // Past the end of known items — don't render a cell.
                if (itemIndex >= data.totalEstimate) return null;

                const item = data.getItem(itemIndex);

                if (item != null) {
                  return (
                    <div key={getItemKey(item, itemIndex)}>
                      {renderItem(item, itemIndex)}
                    </div>
                  );
                }

                // Item not loaded yet — show placeholder.
                return (
                  <div key={`placeholder-${itemIndex}`}>
                    {renderPlaceholder
                      ? renderPlaceholder(itemIndex)
                      : <DefaultPlaceholder />}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
