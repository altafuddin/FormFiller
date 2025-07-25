import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'FormFiller - AI Voice Agent',
  description: 'Ultra-low latency AI voice-controlled form filling',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}