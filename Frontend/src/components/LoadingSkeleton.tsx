import { Skeleton } from "@/components/ui/skeleton";

export const CardSkeleton = () => (
  <div className="rounded-lg border border-border bg-card p-6 space-y-4">
    <Skeleton className="h-5 w-1/2 bg-muted" />
    <Skeleton className="h-3 w-1/3 bg-muted" />
    <div className="space-y-2">
      <Skeleton className="h-2 w-full bg-muted" />
      <Skeleton className="h-2 w-full bg-muted" />
      <Skeleton className="h-2 w-full bg-muted" />
    </div>
    <div className="flex gap-2">
      <Skeleton className="h-8 w-20 bg-muted" />
      <Skeleton className="h-8 w-16 bg-muted" />
      <Skeleton className="h-8 w-16 bg-muted" />
    </div>
  </div>
);

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="space-y-2">
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} className="h-10 w-full bg-muted rounded" />
    ))}
  </div>
);
