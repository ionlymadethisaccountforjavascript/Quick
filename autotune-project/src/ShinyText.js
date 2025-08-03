const ShinyText = ({ text, disabled = false, speed = 5, className = '' }) => {
  const animationDuration = `${speed}s`;

  return (
    <div
      className={`inline-block ${className}`}
      style={{
        position: 'relative',
      }}
    >
      {/* Base text - always visible */}
      <span 
        style={{ 
          background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {text}
      </span>
      
      {/* Shine effect - layered on top */}
      {!disabled && (
        <span
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(120deg, transparent 40%, rgba(255, 255, 255, 0.8) 50%, transparent 60%)',
            backgroundSize: '200% 100%',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            animation: `shine ${animationDuration} linear infinite`,
            zIndex: 2,
            pointerEvents: 'none',
          }}
        >
          {text}
        </span>
      )}
    </div>
  );
};

export default ShinyText; 