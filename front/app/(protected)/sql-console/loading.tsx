import { Database, Code, History } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export default function SQLConsoleLoading() {
  return (
    <div className="h-screen flex flex-col">
      {/* Header Skeleton */}
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Database className="h-6 w-6 text-primary animate-pulse" />
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-6 w-20" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-10" />
            <Skeleton className="h-8 w-10" />
          </div>
        </div>
      </header>

      {/* Main Content Skeleton */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Query Editor */}
        <div className="flex-1 flex flex-col border-r border-border">
          <div className="border-b border-border p-4">
            <div className="flex items-center gap-2 mb-3">
              <Code className="h-4 w-4 animate-pulse" />
              <Skeleton className="h-4 w-24" />
            </div>
            <Skeleton className="h-48 w-full mb-3" />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-8 w-20" />
              </div>
              <Skeleton className="h-4 w-48" />
            </div>
          </div>

          <div className="flex-1 p-4">
            <div className="flex items-center justify-between mb-3">
              <Skeleton className="h-6 w-20" />
              <div className="flex items-center gap-2">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-12" />
              </div>
            </div>

            <Card className="h-[400px]">
              <CardContent className="p-4">
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-pulse" />
                    <p className="text-muted-foreground">SQL Console を読み込み中...</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right Panel - History */}
        <div className="w-80 flex flex-col">
          <div className="border-b border-border p-4">
            <div className="flex items-center gap-2 mb-3">
              <History className="h-4 w-4 animate-pulse" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-8" />
            </div>
            <Skeleton className="h-8 w-full" />
          </div>

          <div className="flex-1 p-4">
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Card key={i} className="p-3">
                  <div className="flex items-start justify-between mb-2">
                    <Skeleton className="h-3 w-16" />
                    <div className="flex items-center gap-1">
                      <Skeleton className="h-4 w-12" />
                      <Skeleton className="h-4 w-8" />
                    </div>
                  </div>
                  <Skeleton className="h-12 w-full" />
                </Card>
              ))}
            </div>
          </div>

          <div className="border-t border-border p-4">
            <Skeleton className="h-4 w-20 mb-3" />
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-12" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}