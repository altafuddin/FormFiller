import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Voice Form Filler',
  description: 'Fill forms using voice commands',
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
