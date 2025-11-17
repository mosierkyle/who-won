import { useState } from 'react'
import { processScorecard, type ProcessScorecardResponse } from './api/processScorecard'

function App() {
  const [s3Key, setS3Key] = useState('Raw/ex_scorecard_1.png')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProcessScorecardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // TODO: Replace with your actual S3 bucket name or use env variable
  const S3_BUCKET_URL = 'https://who-won-development.s3.amazonaws.com'

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
      <p style={{ color: '#666' }}>Preprocessing + OCR visualization</p>

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

                {/* Scorecard extraction results */}
                {step.step_name === 'scorecard_extraction' && step.data && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '15px', 
                    backgroundColor: '#f0f8ff',
                    borderRadius: '4px',
                    border: '1px solid #b3d9ff'
                  }}>
                    <h5 style={{ margin: '0 0 10px 0' }}>Scorecard Extraction Results:</h5>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Players Found:</strong> {step.data.total_players}
                    </p>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Grid Size:</strong> {step.data.grid_size}
                    </p>
                    
                    {/* Player data */}
                    <details style={{ marginTop: '15px' }}>
                      <summary style={{ cursor: 'pointer', color: '#007bff', fontWeight: 'bold' }}>
                        View Player Data
                      </summary>
                      <div style={{ 
                        marginTop: '10px',
                        backgroundColor: '#fff',
                        padding: '10px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        maxHeight: '400px',
                        overflowY: 'auto'
                      }}>
                        {step.data.players.map((player: any, idx: number) => (
                          <div key={idx} style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #eee' }}>
                            <h6 style={{ margin: '0 0 8px 0' }}>
                              Player {idx + 1}: {player.name} (Row {player.row})
                            </h6>
                            <div style={{ 
                              display: 'grid', 
                              gridTemplateColumns: 'repeat(auto-fill, minmax(40px, 1fr))',
                              gap: '5px',
                              fontSize: '12px'
                            }}>
                              {player.all_values.map((val: string | null, colIdx: number) => (
                                <div 
                                  key={colIdx}
                                  style={{
                                    padding: '4px',
                                    textAlign: 'center',
                                    backgroundColor: val ? '#d4edda' : '#f8f9fa',
                                    border: '1px solid #ddd',
                                    borderRadius: '3px',
                                    fontFamily: 'monospace'
                                  }}
                                  title={`Col ${colIdx}`}
                                >
                                  {val || '—'}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>

                      {/* Debug cell images - now using presigned URLs directly */}
                      {step.data.debug_images && step.data.debug_images.length > 0 && (
                        <details style={{ marginTop: '15px' }}>
                          <summary style={{ cursor: 'pointer', color: '#007bff', fontWeight: 'bold' }}>
                            🔍 View Debug Cell Images ({step.data.debug_images.length} images)
                          </summary>
                          <div style={{ 
                            marginTop: '10px',
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                            gap: '15px',
                            maxHeight: '600px',
                            overflowY: 'auto',
                            padding: '10px',
                            backgroundColor: '#fafafa',
                            borderRadius: '4px'
                          }}>
                            {step.data.debug_images.map((url: string, idx: number) => {
                              // Extract filename from URL for display
                              const filename = url.split('/').pop()?.split('?')[0] || `image-${idx}`;
                              return (
                                <div key={idx} style={{ 
                                  textAlign: 'center',
                                  padding: '10px',
                                  backgroundColor: '#fff',
                                  borderRadius: '4px',
                                  border: '1px solid #ddd'
                                }}>
                                  <img
                                    src={url}
                                    alt={filename}
                                    style={{
                                      width: '100%',
                                      border: '2px solid #007bff',
                                      borderRadius: '4px',
                                      imageRendering: 'pixelated',
                                      minHeight: '60px',
                                      backgroundColor: '#f0f0f0'
                                    }}
                                  />
                                  <div style={{ 
                                    fontSize: '10px', 
                                    color: '#666', 
                                    marginTop: '8px',
                                    wordBreak: 'break-all',
                                    fontFamily: 'monospace'
                                  }}>
                                    {filename}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </details>
                      )}
                  </div>
                )}

                {/* OCR-specific data display (legacy - keeping for compatibility) */}
                {step.step_name === 'ocr' && step.data && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '15px', 
                    backgroundColor: '#f0f8ff',
                    borderRadius: '4px',
                    border: '1px solid #b3d9ff'
                  }}>
                    <h5 style={{ margin: '0 0 10px 0' }}>OCR Results:</h5>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Words Detected:</strong> {step.data.total_words}
                    </p>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Average Confidence:</strong> {step.data.avg_confidence}%
                    </p>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Low Confidence Words:</strong> {step.data.low_confidence_count} (below 70%)
                    </p>
                    
                    <details style={{ marginTop: '15px' }}>
                      <summary style={{ cursor: 'pointer', color: '#007bff', fontWeight: 'bold' }}>
                        View Full Text
                      </summary>
                      <pre style={{ 
                        whiteSpace: 'pre-wrap',
                        backgroundColor: '#fff',
                        padding: '10px',
                        marginTop: '10px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}>
                        {step.data.full_text}
                      </pre>
                    </details>

                    <details style={{ marginTop: '10px' }}>
                      <summary style={{ cursor: 'pointer', color: '#007bff', fontWeight: 'bold' }}>
                        View All Words (with confidence)
                      </summary>
                      <div style={{ 
                        maxHeight: '300px', 
                        overflowY: 'auto',
                        marginTop: '10px',
                        backgroundColor: '#fff',
                        padding: '10px',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}>
                        {step.data.words.map((word: any, idx: number) => (
                          <div 
                            key={idx}
                            style={{ 
                              padding: '5px',
                              marginBottom: '5px',
                              backgroundColor: word.confidence < 70 ? '#ffe6e6' : '#e6ffe6',
                              borderRadius: '3px',
                              fontSize: '12px'
                            }}
                          >
                            <strong>{word.text}</strong> - {word.confidence.toFixed(1)}%
                            <span style={{ color: '#666', marginLeft: '10px' }}>
                              @ ({word.bbox[0]}, {word.bbox[1]})
                            </span>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}

                {step.data && step.step_name !== 'ocr' && step.step_name !== 'scorecard_extraction' && Object.keys(step.data).length > 0 && (
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
                  {step.step_name === 'scorecard_extraction' && (
                    <p style={{ 
                      fontSize: '12px', 
                      color: '#666', 
                      marginTop: '10px',
                      fontStyle: 'italic'
                    }}>
                      Green boxes = OCR found value, Red boxes = OCR returned nothing, Cell dimensions shown in gray
                    </p>
                  )}
                  {step.step_name === 'ocr' && (
                    <p style={{ 
                      fontSize: '12px', 
                      color: '#666', 
                      marginTop: '10px',
                      fontStyle: 'italic'
                    }}>
                      Green boxes = high confidence (≥70%), Red boxes = low confidence (&lt;70%)
                    </p>
                  )}
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