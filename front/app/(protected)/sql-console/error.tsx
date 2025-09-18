'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw, Home, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function SQLConsoleError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('SQL Console Error:', error)
  }, [error])

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center gap-4">
          <Database className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold">SQL Console</h1>
          <Badge variant="destructive" className="text-xs">
            <AlertTriangle className="h-3 w-3 mr-1" />
            エラー
          </Badge>
        </div>
      </header>

      {/* Error Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <Card className="w-full max-w-lg">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertTriangle className="h-8 w-8 text-destructive" />
            </div>
            <CardTitle className="text-xl">SQL Console でエラーが発生しました</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center text-muted-foreground">
              <p className="mb-2">
                アプリケーションの読み込み中に予期しないエラーが発生しました。
              </p>
              <p className="text-sm">
                この問題が継続する場合は、システム管理者にお問い合わせください。
              </p>
            </div>

            {/* Error Details (only in development) */}
            {process.env.NODE_ENV === 'development' && (
              <details className="text-sm">
                <summary className="cursor-pointer text-muted-foreground mb-2">
                  エラー詳細 (開発環境のみ)
                </summary>
                <div className="bg-muted p-3 rounded-md font-mono text-xs overflow-auto max-h-32">
                  <p><strong>Message:</strong> {error.message}</p>
                  {error.digest && <p><strong>Digest:</strong> {error.digest}</p>}
                  {error.stack && (
                    <div className="mt-2">
                      <strong>Stack:</strong>
                      <pre className="whitespace-pre-wrap text-xs mt-1">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2 justify-center">
              <Button onClick={reset} className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                再試行
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.href = '/'}
                className="flex items-center gap-2"
              >
                <Home className="h-4 w-4" />
                ホームに戻る
              </Button>
            </div>

            {/* System Status */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-sm font-medium mb-3 text-center">システム状態</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">データベース接続</span>
                  <Badge variant="outline" className="text-xs">
                    確認中...
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">認証状態</span>
                  <Badge variant="outline" className="text-xs">
                    確認中...
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">アプリケーション</span>
                  <Badge variant="destructive" className="text-xs">
                    エラー
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}