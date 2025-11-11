import { useState } from 'react'
import { processScorecard, type ProcessScorecardResponse } from './api/processScorecard'

function App() {
  const [s3Key, setS3Key] = useState('Raw/ex_scorecard_1.png')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProcessScorecardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await processScorecard(s3Key)
      setResult(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message
      setError(errorMsg)
      console.error('Error processing scorecard:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px' }}>
      <h1>Golf Score Helper - OCR Pipeline</h1>
      <p style={{ color: '#666' }}>Preprocessing visualization</p>

      <div style={{ marginTop: '30px', marginBottom: '30px' }}>
        <label htmlFor="s3key" style={{ fontWeight: 'bold' }}>S3 Key</label>
        <br />
        <input
          id="s3key"
          type="text"
          value={s3Key}
          onChange={(e) => setS3Key(e.target.value)}
          disabled={loading}
          placeholder="Enter the S3 key (e.g., Raw/your-scorecard.jpg)"
          style={{
            width: '100%',
            padding: '10px',
            marginTop: '8px',
            marginBottom: '12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            fontSize: '14px'
          }}
        />
        <button
          onClick={handleProcess}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: loading ? '#888' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'default' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          {loading ? 'Processing...' : 'Process Scorecard'}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ 
            padding: '15px', 
            backgroundColor: result.status === 'success' ? '#d4edda' : '#fff3cd',
            border: `1px solid ${result.status === 'success' ? '#c3e6cb' : '#ffeaa7'}`,
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 10px 0' }}>
              {result.status === 'success' ? '✓ Success!' : '⚠ Partial Success'}
            </h3>
            <p style={{ margin: '5px 0' }}>
              <strong>Scorecard ID:</strong> {result.scorecard_id}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Filename:</strong> {result.filename}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Completed:</strong> {result.completed_steps} / {result.total_steps} steps
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Total Time:</strong> {result.total_processing_time_ms}ms
            </p>
          </div>

          <h3>Processing Steps:</h3>
          {result.steps.map((step, index) => (
            <div
              key={index}
              style={{
                marginBottom: '30px',
                padding: '20px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: step.status === 'error' ? '#fff5f5' : '#fff',
              }}
            >
              <div style={{ marginBottom: '15px' }}>
                <h4 style={{ margin: '0 0 10px 0' }}>
                  {index}. {step.step_name.replace(/_/g, ' ').toUpperCase()}
                </h4>
                <p style={{ margin: '5px 0', color: '#666', fontSize: '14px' }}>
                  Status: <strong style={{ 
                    color: step.status === 'success' ? 'green' : 'red' 
                  }}>{step.status}</strong> | 
                  Time: {step.processing_time_ms}ms
                  {step.s3_path && ` | S3: ${step.s3_path}`}
                </p>
                
                {step.error && (
                  <p style={{ color: 'red', marginTop: '10px' }}>
                    <strong>Error:</strong> {step.error}
                  </p>
                )}

                {step.data && Object.keys(step.data).length > 0 && (
                  <details style={{ marginTop: '10px' }}>
                    <summary style={{ cursor: 'pointer', color: '#007bff' }}>
                      View metadata
                    </summary>
                    <pre
                      style={{
                        backgroundColor: '#f5f5f5',
                        padding: '10px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        marginTop: '10px',
                        overflowX: 'auto'
                      }}
                    >
                      {JSON.stringify(step.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>

              {step.image_base64 && (
                <div>
                  <img
                    src={step.image_base64}
                    alt={step.step_name}
                    style={{
                      maxWidth: '100%',
                      border: '2px solid #ddd',
                      borderRadius: '4px',
                      display: 'block'
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App