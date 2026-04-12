import React from 'react'
import { CollectionCards } from '@payloadcms/next/rsc'

const Dashboard = (props: any) => {
  return (
    <div className="dashboard-wrapper">
      <div className="custom-banner focus-ring">
        <h1 style={{ fontSize: '3rem', marginBottom: '0.75rem', fontWeight: '900', letterSpacing: '-0.025em' }}>
          Sovereign <span style={{ color: '#818cf8', textShadow: '0 0 20px rgba(129, 140, 248, 0.3)' }}>Cortex</span>
        </h1>
        <p style={{ color: '#cbd5e1', fontSize: '1.25rem', fontWeight: '500' }}>
          Autonomous enterprise intelligence orchestration.
        </p>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <CollectionCards {...props} />
      </div>
    </div>
  )
}

export default Dashboard
