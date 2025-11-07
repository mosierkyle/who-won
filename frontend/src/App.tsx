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
    <div style={{ maxWidth: '700px', margin: '0 auto', padding: '40px' }}>
      <h1>Golf Score Helper</h1>
      <p>OCR Pipeline - Step 1: S3 Fetch</p>

      <div style={{ marginTop: '20px' }}>
        <label htmlFor="s3key">S3 Key</label>
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
            padding: '8px',
            marginTop: '6px',
            marginBottom: '12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        />
        <br />
        <button
          onClick={handleProcess}
          disabled={loading}
          style={{
            width: '100%',
            padding: '10px',
            backgroundColor: loading ? '#888' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'default' : 'pointer',
          }}
        >
          {loading ? 'Loading...' : 'Fetch from S3'}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginTop: '20px',
            padding: '10px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div
          style={{
            marginTop: '20px',
            padding: '15px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            backgroundColor: '#f9f9f9',
          }}
        >
          <h3>Success! ✓</h3>
          <p>{result.message}</p>
          <pre
            style={{
              backgroundColor: '#eee',
              padding: '10px',
              borderRadius: '4px',
              overflowX: 'auto',
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default App
