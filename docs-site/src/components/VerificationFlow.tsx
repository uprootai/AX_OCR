import React from 'react';

const ARROW = '\u2193';

export default function VerificationFlow() {
  return (
    <div style={{ padding: '16px', border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: '8px' }}>
      {/* Input */}
      <div style={{ textAlign: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'inline-block', padding: '8px 24px', background: '#eceff1', borderRadius: '8px', fontWeight: 600 }}>
          Detection Result
        </div>
      </div>
      <div style={{ textAlign: 'center', fontSize: '1.2rem', color: '#999', marginBottom: '8px' }}>{ARROW}</div>

      {/* Confidence check */}
      <div style={{ textAlign: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'inline-block', padding: '8px 20px', background: '#fff9c4', border: '2px solid #f9a825', borderRadius: '8px', fontWeight: 600 }}>
          Confidence Check
        </div>
      </div>

      {/* Three levels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '12px' }}>
        {/* L1 */}
        <div style={{ padding: '16px', background: '#e8f5e9', border: '2px solid #4caf50', borderRadius: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#2e7d32', textTransform: 'uppercase', marginBottom: '4px' }}>Level 1</div>
          <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#1b5e20' }}>Auto-Approve</div>
          <div style={{ margin: '8px 0', padding: '4px 12px', background: 'white', borderRadius: '16px', display: 'inline-block', fontSize: '0.85rem', fontWeight: 600 }}>
            conf &ge; 0.85
          </div>
          <div style={{ fontSize: '0.8rem', color: '#388e3c', marginTop: '6px' }}>~80% of items</div>
          <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#666' }}>No human needed</div>
        </div>

        {/* L2 */}
        <div style={{ padding: '16px', background: '#e3f2fd', border: '2px solid #2196f3', borderRadius: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#1565c0', textTransform: 'uppercase', marginBottom: '4px' }}>Level 2</div>
          <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#0d47a1' }}>Agent Review</div>
          <div style={{ margin: '8px 0', padding: '4px 12px', background: 'white', borderRadius: '16px', display: 'inline-block', fontSize: '0.85rem', fontWeight: 600 }}>
            0.5 - 0.85
          </div>
          <div style={{ fontSize: '0.8rem', color: '#1976d2', marginTop: '6px' }}>Claude Sonnet Vision</div>
          <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#666' }}>Accept / Reject / Escalate</div>
        </div>

        {/* L3 */}
        <div style={{ padding: '16px', background: '#fff3e0', border: '2px solid #ff9800', borderRadius: '12px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#e65100', textTransform: 'uppercase', marginBottom: '4px' }}>Level 3</div>
          <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#bf360c' }}>Human Review</div>
          <div style={{ margin: '8px 0', padding: '4px 12px', background: 'white', borderRadius: '16px', display: 'inline-block', fontSize: '0.85rem', fontWeight: 600 }}>
            conf &lt; 0.5
          </div>
          <div style={{ fontSize: '0.8rem', color: '#e65100', marginTop: '6px' }}>Complex / Uncertain</div>
          <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#666' }}>Keyboard shortcuts (A/R/S)</div>
        </div>
      </div>

      {/* Result */}
      <div style={{ textAlign: 'center', marginTop: '12px', fontSize: '1.2rem', color: '#999' }}>{ARROW}</div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '8px' }}>
        <div style={{ padding: '8px 20px', background: '#e8f5e9', border: '2px solid #4caf50', borderRadius: '8px', fontWeight: 600, color: '#1b5e20' }}>
          Approved
        </div>
        <div style={{ padding: '8px 20px', background: '#ffebee', border: '2px solid #ef5350', borderRadius: '8px', fontWeight: 600, color: '#c62828' }}>
          Rejected
        </div>
      </div>
    </div>
  );
}
