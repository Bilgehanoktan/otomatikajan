import React from 'react'

export const metadata = {
  title: 'Sovereign AGI CMS',
  description: 'Payload CMS for Sovereign AGI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
