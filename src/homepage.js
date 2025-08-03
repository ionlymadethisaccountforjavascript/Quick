import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import Silk from './Silk';
import ShinyText from './ShinyText';

function Homepage() {
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [processedFile, setProcessedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);

  const fileInputRef = useRef(null);

  useEffect(() => {
    let interval;
    if (isUploading) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 4;
        });
      }, 60);
    } else if (isProcessing) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 2;
        });
      }, 60);
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
      setIsUploading(true);
      // Simulate upload delay
      setTimeout(() => {
        setUploadedFile(file);
        setIsUploading(false);
      }, 1500);
    } else {
      alert('Please upload an MP3 or WAV file only');
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const processAudio = () => {
    if (!uploadedFile) return;
    
    setIsProcessing(true);
    // Simulate processing delay
    setTimeout(() => {
      setProcessedFile({
        name: uploadedFile.name.replace(/\.[^/.]+$/, '') + '_autotuned.mp3',
        url: URL.createObjectURL(uploadedFile) // In real app, this would be the processed file
      });
      setIsProcessing(false);
    }, 3000);
  };

  const downloadProcessedFile = () => {
    if (processedFile) {
      const link = document.createElement('a');
      link.href = processedFile.url;
      link.download = processedFile.name;
      link.click();
    }
  };

  const removeFile = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadedFile(null);
    setProcessedFile(null);
    setIsUploading(false);
    setIsProcessing(false);
    // Reset the file input so future uploads work
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="homepage">
      <div className="silk-background">
        <Silk
          speed={5}
          scale={1}
          color="#374151"
          noiseIntensity={1.5}
          rotation={0}
        />
      </div>
      <div className="homepage-container">
        <ShinyText 
          text="AutoTune Pro" 
          disabled={false} 
          speed={3} 
          className="homepage-title"
        />
        <p className="homepage-subtitle">Transform your audio with AI-powered pitch correction</p>
        
        <div className="upload-section">
          <div 
            className={`upload-area ${dragActive ? 'drag-active' : ''} ${uploadedFile ? 'has-file' : ''}`}
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
              <div className="upload-content">
                <div className="upload-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7,10 12,15 17,10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </div>
                <h3>Upload Audio File</h3>
                <p>Drag and drop your audio file here, or click to browse</p>
                <span className="file-types">Supports: MP3, WAV</span>
              </div>
            )}
            
            {uploadedFile && (
              <div className="file-info">
                <div className="file-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10,9 9,9 8,9"/>
                  </svg>
                </div>
                <div className="file-details">
                  <h4>{uploadedFile.name}</h4>
                  <p>{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button className="remove-button" onClick={removeFile} title="Remove file">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            )}
            
            {isUploading && (
              <div style={{ width: '100%', marginTop: '2rem', marginBottom: '1rem' }}>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${progress}%`
                    }}
                  ></div>
                </div>
                <p style={{ color: '#cbd5e1', margin: 0 }}>Uploading... {progress}%</p>
              </div>
            )}
          </div>
          
          {uploadedFile && !processedFile && (
            <>
              <button 
                className="process-button"
                onClick={processAudio}
                disabled={isProcessing}
              >
                AutoTune Audio
              </button>
              
              {isProcessing && (
                <div style={{ width: '100%', marginTop: '2rem', marginBottom: '1rem' }}>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${progress}%`
                      }}
                    ></div>
                  </div>
                  <p style={{ color: '#cbd5e1', margin: 0 }}>Processing Audio... {progress}%</p>
                </div>
              )}
            </>
          )}
          
          {processedFile && (
            <div className="result-section">
              <div className="result-card">
                <div className="result-header">
                  <h3>✅ Processing Complete</h3>
                  <p>Your audio has been autotuned successfully!</p>
                </div>
                <div className="result-details">
                  <div className="detail-item">
                    <span className="detail-label">Original:</span>
                    <span className="detail-value">{uploadedFile.name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Processed:</span>
                    <span className="detail-value">{processedFile.name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Pitch Correction:</span>
                    <span className="detail-value">Applied</span>
                  </div>
                </div>
                <button className="download-button" onClick={downloadProcessedFile}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7,10 12,15 17,10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Download Processed File
                </button>
              </div>
            </div>
          )}
        </div>
        
        <div className="features-section">
          <h2>How It Works</h2>
          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-number">1</div>
              <h3>Upload</h3>
              <p>Upload your audio file in any common format</p>
            </div>
            <div className="feature-item">
              <div className="feature-number">2</div>
              <h3>Process</h3>
              <p>Our AI analyzes and corrects pitch automatically</p>
            </div>
            <div className="feature-item">
              <div className="feature-number">3</div>
              <h3>Download</h3>
              <p>Get your perfectly tuned audio file instantly</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Homepage;
