import React from 'react'

export const Logo = () => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '24px',
      fontWeight: 'bold',
      background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      letterSpacing: '-0.5px'
    }}>
      <span style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        width: '32px',
        height: '32px',
        background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
        borderRadius: '8px',
        color: 'white',
        WebkitTextFillColor: 'white',
        fontSize: '18px'
      }}>S</span>
      SOVEREIGN
    </div>
  )
}
