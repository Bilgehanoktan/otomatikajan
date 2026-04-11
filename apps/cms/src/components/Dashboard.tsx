import React from 'react'
import { CollectionCards } from '@payloadcms/next/rsc'

const Dashboard = (props: any) => {
  return (
    <div style={{ padding: 'var(--gutter-h)', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ 
        marginBottom: '3rem', 
        padding: '2rem', 
        borderRadius: '24px', 
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)'
      }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem', fontWeight: '800' }}>
          Sovereign <span style={{ color: '#6366f1' }}>Cortex</span>
        </h1>
        <p style={{ color: '#888', fontSize: '1.1rem' }}>
          Welcome to your autonomous enterprise operating system control center.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '2rem' }}>
        <CollectionCards {...props} />
      </div>
    </div>
  )
}

export default Dashboard
