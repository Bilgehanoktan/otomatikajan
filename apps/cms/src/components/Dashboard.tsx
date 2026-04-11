import React from 'react'
import { CollectionCards } from '@payloadcms/next/rsc'

const Dashboard = (props: any) => {
  return (
    <div style={{ padding: 'var(--gutter-h)', maxWidth: '1200px', margin: '0 auto' }}>
      <div className="custom-banner" style={{ 
        marginBottom: '3rem', 
        padding: '2.5rem', 
        borderRadius: '24px', 
      }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem', fontWeight: '800' }}>
          Sovereign <span style={{ color: '#6366f1' }}>Cortex</span>
        </h1>
        <p style={{ color: '#888', fontSize: '1.1rem' }}>
          Welcome to your autonomous enterprise operating system control center.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '2rem' }}>
        <CollectionCards {...props} req={{ i18n: props.i18n, payload: props.payload, user: props.user }} />
      </div>
    </div>
  )
}

export default Dashboard
