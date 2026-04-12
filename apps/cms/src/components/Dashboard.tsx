import React from 'react'
import { CollectionCards } from '@payloadcms/next/rsc'

const Dashboard = (props: any) => {
  return (
    <div style={{ padding: 'var(--gutter-h)', maxWidth: '1400px', margin: '0 auto' }}>
      <header className="custom-banner" style={{ 
        marginBottom: '3rem', 
        padding: '3rem', 
        borderRadius: '32px',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        position: 'relative'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ 
            width: '12px', 
            height: '12px', 
            borderRadius: '50%', 
            backgroundColor: '#10b981',
            boxShadow: '0 0 12px #10b981'
          }} />
          <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: '#10b981', letterSpacing: '0.1em' }}>
            System Operational
          </span>
        </div>

        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', margin: 0, fontWeight: '900', letterSpacing: '-0.02em', lineHeight: '1.1' }}>
          Sovereign <span style={{ 
            background: 'linear-gradient(to right, #6366f1, #a855f7)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>Cortex</span>
        </h1>
        
        <p style={{ color: '#94a3b8', fontSize: '1.25rem', maxWidth: '600px', margin: 0, lineHeight: '1.6' }}>
          Autonomous enterprise intelligence orchestration. Seamlessly managing cognitive cycles and strategic assets.
        </p>
      </header>

      <div className="dashboard__collections">
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', fontWeight: '700', color: '#f8fafc' }}>
          Management Modules
        </h2>
        <CollectionCards {...props} req={{ i18n: props.i18n, payload: props.payload, user: props.user }} />
      </div>
    </div>
  )
}

export default Dashboard
