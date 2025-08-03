import React, { useState, useRef, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:5000';

// Enhanced Slider Component with proper 50% centering
const AutotuneSlider = ({ value, onChange }) => {
  const sliderRef = useRef(null);
  
  const handleSliderChange = (e) => {
    onChange(parseFloat(e.target.value));
  };
  
  // Calculate thumb position (50% should be at center)
  const thumbPosition = ((value - 0.1) / (1.0 - 0.1)) * 100;
  
  return (
    <div className="slider-container">
      <div className="slider-track">
        <div 
          className="slider-progress" 
          style={{ width: `${thumbPosition}%` }}
        />
        <input
          ref={sliderRef}
          type="range"
          min="0.1"
          max="1.0"
          step="0.1"
          value={value}
          onChange={handleSliderChange}
          className="slider-input"
        />
        <div 
          className="slider-thumb" 
          style={{ left: `${thumbPosition}%` }}
        />
      </div>
      <style jsx>{`
        .slider-container {
          position: relative;
          width: 100%;
          height: 40px;
          display: flex;
          align-items: center;
        }
        
        .slider-track {
          position: relative;
          width: 100%;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .slider-progress {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
          border-radius: 4px;
          transition: width 0.2s ease;
        }
        
        .slider-input {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          opacity: 0;
          cursor: pointer;
          z-index: 2;
        }
        
        .slider-thumb {
          position: absolute;
          top: 50%;
          width: 20px;
          height: 20px;
          background: white;
          border: 3px solid #3b82f6;
          border-radius: 50%;
          transform: translate(-50%, -50%);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          transition: left 0.2s ease, transform 0.2s ease;
          pointer-events: none;
          z-index: 1;
        }
        
        .slider-input:hover + .slider-thumb {
          transform: translate(-50%, -50%) scale(1.1);
          border-color: #8b5cf6;
        }
        
        .slider-input:active + .slider-thumb {
          transform: translate(-50%, -50%) scale(1.2);
          border-color: #ec4899;
        }
      `}</style>
    </div>
  );
};

function Homepage() {
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [processedFile, setProcessedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [autotuneStrength, setAutotuneStrength] = useState(0.5); // Start at 50%

  const fileInputRef = useRef(null);

  useEffect(() => {
    let interval;
    if (isUploading) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);
    } else if (isProcessing) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 3;
        });
      }, 300);
    } else {
      setProgress(0);
    }
    return () => clearInterval(interval);
  }, [isUploading, isProcessing]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.type === 'audio/mp3' || file.type === 'audio/wav' || 
        file.name.toLowerCase().endsWith('.mp3') || file.name.toLowerCase().endsWith('.wav')) {
      setUploadedFile(file);
      setError(null);
    } else {
      setError('Please upload an MP3 or WAV file only');
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const processAudio = async () => {
    if (!uploadedFile) return;
    
    setIsProcessing(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('strength', autotuneStrength.toString());
    
    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process file');
      }
      
      const result = await response.json();
      setProgress(100);
      
      setProcessedFile({
        name: result.processed_name,
        fileId: result.file_id,
        originalName: result.original_name,
        strengthUsed: result.strength_used
      });
      
    } catch (error) {
      console.error('Error processing audio:', error);
      setError(error.message || 'Failed to process audio. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadProcessedFile = async () => {
    if (!processedFile) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/download/${processedFile.fileId}`);
      
      if (!response.ok) {
        throw new Error('Failed to download file');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = processedFile.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Error downloading file:', error);
      setError('Failed to download file. Please try again.');
    }
  };

  const removeFile = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadedFile(null);
    setProcessedFile(null);
    setIsUploading(false);
    setIsProcessing(false);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        maxWidth: '800px',
        width: '100%',
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: '3rem',
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #3b82f6, #8b5cf6, #ec4899)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          color: 'transparent',
          marginBottom: '0.5rem'
        }}>
          AutoTune Pro
        </h1>
        <p style={{
          fontSize: '1.2rem',
          color: '#94a3b8',
          marginBottom: '2rem'
        }}>
          Transform your audio with AI-powered pitch correction
        </p>
        
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            padding: '1rem',
            margin: '1rem 0',
            color: '#ef4444',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}
        
        <div style={{ marginBottom: '2rem' }}>
          <div 
            style={{
              background: dragActive ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(40px)',
              border: dragActive ? '2px dashed #3b82f6' : uploadedFile ? '2px solid #10b981' : '2px dashed rgba(255, 255, 255, 0.2)',
              borderRadius: '20px',
              padding: '2rem',
              cursor: !uploadedFile ? 'pointer' : 'default',
              transition: 'all 0.3s ease',
              minHeight: '200px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => !uploadedFile && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp3,.wav,audio/mp3,audio/wav"
              onChange={handleFileInput}
              style={{ display: 'none' }}
            />
            
            {!uploadedFile && (
              <div style={{ textAlign: 'center', color: '#cbd5e1' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎵</div>
                <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>Upload Audio File</h3>
                <p style={{ marginBottom: '1rem' }}>Drag and drop your audio file here, or click to browse</p>
                <span style={{ 
                  padding: '0.5rem 1rem',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '20px',
                  fontSize: '0.9rem'
                }}>
                  Supports: MP3, WAV
                </span>
              </div>
            )}
            
            {uploadedFile && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                width: '100%',
                background: 'rgba(255, 255, 255, 0.1)',
                padding: '1rem',
                borderRadius: '15px'
              }}>
                <div style={{ fontSize: '2rem' }}>🎵</div>
                <div style={{ flex: 1, textAlign: 'left' }}>
                  <h4 style={{ color: 'white', margin: 0 }}>{uploadedFile.name}</h4>
                  <p style={{ color: '#94a3b8', margin: '0.25rem 0 0 0' }}>
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button 
                  onClick={removeFile}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '8px',
                    color: '#ef4444',
                    padding: '0.5rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title="Remove file"
                >
                  ✕
                </button>
              </div>
            )}
          </div>
          
          {uploadedFile && !processedFile && (
            <>
              <div style={{
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(40px)',
                borderRadius: '15px',
                padding: '1.5rem',
                margin: '1.5rem 0',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <h3 style={{ 
                  color: '#ffffff', 
                  margin: '0 0 1rem 0', 
                  fontSize: '1.1rem',
                  textAlign: 'center'
                }}>
                  Autotune Strength: {Math.round(autotuneStrength * 100)}%
                </h3>
                
                <div style={{ margin: '1rem 0' }}>
                  <AutotuneSlider 
                    value={autotuneStrength}
                    onChange={setAutotuneStrength}
                  />
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  fontSize: '0.85rem', 
                  color: '#94a3b8',
                  marginTop: '0.5rem'
                }}>
                  <span>10% - Subtle</span>
                  <span>50% - Balanced</span>
                  <span>100% - Heavy</span>
                </div>
              </div>

              <button 
                onClick={processAudio}
                disabled={isProcessing}
                style={{
                  background: isProcessing ? '#6b7280' : 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
                  border: 'none',
                  borderRadius: '15px',
                  color: 'white',
                  padding: '1rem 2rem',
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  transform: isProcessing ? 'none' : 'translateY(0)',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)'
                }}
                onMouseEnter={(e) => {
                  if (!isProcessing) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 20px rgba(59, 130, 246, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isProcessing) {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 4px 15px rgba(59, 130, 246, 0.3)';
                  }
                }}
              >
                {isProcessing ? '🎵 Processing Audio...' : '🎤 Apply AutoTune'}
              </button>
              
              {isProcessing && (
                <div style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(40px)',
                  borderRadius: '15px',
                  padding: '1.5rem',
                  margin: '1rem 0',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    marginBottom: '1rem'
                  }}>
                    <div style={{
                      width: `${progress}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                      borderRadius: '4px',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <p style={{ color: '#cbd5e1', margin: 0, textAlign: 'center' }}>
                    Processing with AI pitch correction... {progress}%
                  </p>
                </div>
              )}
            </>
          )}
          
          {processedFile && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '15px',
              padding: '1.5rem',
              margin: '1rem 0',
              textAlign: 'center'
            }}>
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ color: '#10b981', margin: '0 0 0.5rem 0' }}>
                  ✅ AutoTune Complete!
                </h3>
                <p style={{ color: '#cbd5e1', margin: 0 }}>
                  Your audio has been processed with {Math.round((processedFile.strengthUsed || 0.5) * 100)}% autotune strength
                </p>
              </div>
              
              <div style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '10px',
                padding: '1rem',
                margin: '1rem 0',
                textAlign: 'left'
              }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#94a3b8' }}>Original: </span>
                  <span style={{ color: 'white' }}>{processedFile.originalName}</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Processed: </span>
                  <span style={{ color: 'white' }}>{processedFile.name}</span>
                </div>
              </div>
              
              <button 
                onClick={downloadProcessedFile}
                style={{
                  background: 'linear-gradient(45deg, #10b981, #059669)',
                  border: 'none',
                  borderRadius: '10px',
                  color: 'white',
                  padding: '0.75rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  margin: '0 auto',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 15px rgba(16, 185, 129, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }}
              >
                <span>⬇️</span>
                Download Processed File
              </button>
            </div>
          )}
        </div>
        
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(40px)',
          borderRadius: '20px',
          padding: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          marginTop: '2rem'
        }}>
          <h2 style={{
            color: 'white',
            marginBottom: '2rem',
            fontSize: '1.8rem'
          }}>
            How It Works
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem'
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '15px',
              padding: '1.5rem',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                color: 'white',
                fontSize: '1.5rem',
                fontWeight: 'bold'
              }}>
                1
              </div>
              <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>Upload Audio</h3>
              <p style={{ color: '#94a3b8', margin: 0 }}>
                Upload your audio file in MP3 or WAV format
              </p>
            </div>
            
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '15px',
              padding: '1.5rem',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(45deg, #8b5cf6, #ec4899)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                color: 'white',
                fontSize: '1.5rem',
                fontWeight: 'bold'
              }}>
                2
              </div>
              <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>AI Processing</h3>
              <p style={{ color: '#94a3b8', margin: 0 }}>
                Our AI analyzes pitch and applies intelligent correction
              </p>
            </div>
            
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '15px',
              padding: '1.5rem',
              textAlign: 'center',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(45deg, #ec4899, #10b981)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem auto',
                color: 'white',
                fontSize: '1.5rem',
                fontWeight: 'bold'
              }}>
                3
              </div>
              <h3 style={{ color: 'white', marginBottom: '0.5rem' }}>Download</h3>
              <p style={{ color: '#94a3b8', margin: 0 }}>
                Get your perfectly tuned audio file instantly
              </p>
            </div>
          </div>
        </div>
        
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '10px',
          textAlign: 'center'
        }}>
          <p style={{ color: '#3b82f6', margin: 0, fontSize: '0.9rem' }}>
            💡 <strong>Pro Tip:</strong> Start with 50% strength for balanced results. Use lower values for subtle correction, higher for dramatic effect.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Homepage;