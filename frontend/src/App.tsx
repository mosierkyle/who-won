import { useState } from 'react'
import { 
  processScorecard, 
  processScorecardClaude,
  type ProcessScorecardResponse,
  type ProcessScorecardClaudeResponse 
} from './api/processScorecard'

type ProcessingMethod = 'ocr' | 'claude';

function App() {
  const [s3Key, setS3Key] = useState('Raw/ex_scorecard_1.png')
  const [loading, setLoading] = useState(false)
  const [method, setMethod] = useState<ProcessingMethod>('ocr')
  const [ocrResult, setOcrResult] = useState<ProcessScorecardResponse | null>(null)
  const [claudeResult, setClaudeResult] = useState<ProcessScorecardClaudeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async (selectedMethod: ProcessingMethod) => {
    setLoading(true)
    setError(null)
    setOcrResult(null)
    setClaudeResult(null)
    setMethod(selectedMethod)

    try {
      if (selectedMethod === 'ocr') {
        const data = await processScorecard(s3Key)
        setOcrResult(data)
      } else {
        const data = await processScorecardClaude(s3Key)
        setClaudeResult(data)
      }
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
      <h1>Golf Score Helper</h1>
      <p style={{ color: '#666' }}>Choose your processing method</p>

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
        
        {/* Method selection buttons */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
          <button
            onClick={() => handleProcess('ocr')}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: loading && method === 'ocr' ? '#888' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'default' : 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            {loading && method === 'ocr' ? 'Processing...' : '🔧 Process with OCR'}
          </button>
          
          <button
            onClick={() => handleProcess('claude')}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: loading && method === 'claude' ? '#888' : '#8b5cf6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'default' : 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            {loading && method === 'claude' ? 'Processing...' : '🤖 Process with Claude AI'}
          </button>
        </div>
        
        <p style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
          OCR: Free, detailed debugging • Claude AI: Fast, accurate, ~$0.015 per image
        </p>
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

      {/* Claude Results */}
      {claudeResult && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ 
            padding: '15px', 
            backgroundColor: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#0369a1' }}>
              🤖 Claude AI Results
            </h3>
            <p style={{ margin: '5px 0' }}>
              <strong>Scorecard ID:</strong> {claudeResult.scorecard_id}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Filename:</strong> {claudeResult.filename}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Processing Time:</strong> {claudeResult.processing_time_ms}ms
            </p>
            {claudeResult.winner && (
              <p style={{ margin: '5px 0' }}>
                <strong>🏆 Winner:</strong> {claudeResult.winner}
              </p>
            )}
            {claudeResult.course && (
              <p style={{ margin: '5px 0' }}>
                <strong>Course:</strong> {claudeResult.course}
              </p>
            )}
            {claudeResult.date && (
              <p style={{ margin: '5px 0' }}>
                <strong>Date:</strong> {claudeResult.date}
              </p>
            )}
          </div>

          <h3>Players & Scores:</h3>
          {claudeResult.players.map((player, idx) => (
            <div
              key={idx}
              style={{
                marginBottom: '20px',
                padding: '20px',
                border: player.name === claudeResult.winner ? '3px solid #fbbf24' : '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: player.name === claudeResult.winner ? '#fffbeb' : '#fff',
              }}
            >
              <h4 style={{ margin: '0 0 15px 0' }}>
                {player.name === claudeResult.winner && '🏆 '}
                {player.name} - Total: {player.total}
              </h4>
              
              {/* Front 9 */}
              <div style={{ marginBottom: '5px', fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                Front 9
              </div>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(9, 1fr)',
                gap: '8px',
                marginBottom: '20px'
              }}>
                {player.scores.slice(0, 9).map((score, holeIdx) => (
                  <div 
                    key={holeIdx}
                    style={{
                      padding: '8px',
                      textAlign: 'center',
                      backgroundColor: score === null ? '#f3f4f6' : '#dbeafe',
                      border: '1px solid #93c5fd',
                      borderRadius: '4px',
                      fontWeight: 'bold'
                    }}
                  >
                    <div style={{ fontSize: '10px', color: '#666' }}>H{holeIdx + 1}</div>
                    <div>{score ?? '—'}</div>
                  </div>
                ))}
              </div>
              
              {/* Back 9 */}
              <div style={{ marginBottom: '5px', fontSize: '12px', fontWeight: 'bold', color: '#666' }}>
                Back 9
              </div>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(9, 1fr)',
                gap: '8px'
              }}>
                {player.scores.slice(9, 18).map((score, holeIdx) => (
                  <div 
                    key={holeIdx + 9}
                    style={{
                      padding: '8px',
                      textAlign: 'center',
                      backgroundColor: score === null ? '#f3f4f6' : '#dcfce7',
                      border: '1px solid #86efac',
                      borderRadius: '4px',
                      fontWeight: 'bold'
                    }}
                  >
                    <div style={{ fontSize: '10px', color: '#666' }}>H{holeIdx + 10}</div>
                    <div>{score ?? '—'}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* OCR Results */}
      {ocrResult && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ 
            padding: '15px', 
            backgroundColor: ocrResult.status === 'success' ? '#d4edda' : '#fff3cd',
            border: `1px solid ${ocrResult.status === 'success' ? '#c3e6cb' : '#ffeaa7'}`,
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 10px 0' }}>
              {ocrResult.status === 'success' ? '✓ Success!' : '⚠ Partial Success'}
            </h3>
            <p style={{ margin: '5px 0' }}>
              <strong>Scorecard ID:</strong> {ocrResult.scorecard_id}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Filename:</strong> {ocrResult.filename}
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Completed:</strong> {ocrResult.completed_steps} / {ocrResult.total_steps} steps
            </p>
            <p style={{ margin: '5px 0' }}>
              <strong>Total Time:</strong> {ocrResult.total_processing_time_ms}ms
            </p>
          </div>

          <h3>Processing Steps:</h3>
          {ocrResult.steps.map((step, index) => (
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

                    {/* Debug cell images */}
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

                {/* Table detection data */}
                {step.step_name === 'table_detection' && step.data && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '15px', 
                    backgroundColor: '#f0f8ff',
                    borderRadius: '4px',
                    border: '1px solid #b3d9ff'
                  }}>
                    <h5 style={{ margin: '0 0 10px 0' }}>Table Detection:</h5>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Grid:</strong> {step.data.num_rows} rows × {step.data.num_cols} columns
                    </p>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Total Cells:</strong> {step.data.total_cells}
                    </p>
                  </div>
                )}

                {/* Generic data display */}
                {step.data && 
                 step.step_name !== 'scorecard_extraction' && 
                 step.step_name !== 'table_detection' && 
                 Object.keys(step.data).length > 0 && (
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
                      Green boxes = OCR found value, Red boxes = OCR returned nothing
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