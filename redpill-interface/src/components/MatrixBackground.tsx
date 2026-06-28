import { useEffect, useRef } from 'react';

export const MatrixBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Actual Matrix half-width Katakana + numeric digits
    const matrix = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ1234567890:+-*<>=[]_";
    const matrixArray = matrix.split("");

    const font_size = 14;
    const columns = Math.floor(canvas.width / font_size) + 1;
    
    // Array for drops - one per column
    const drops: number[] = [];
    // Track drop speed variations
    const speeds: number[] = [];
    
    for (let x = 0; x < columns; x++) {
      drops[x] = Math.random() * -100; // Initialize off-screen at different heights
      speeds[x] = 1 + Math.random() * 1.5; // Random fall speeds
    }

    // Drawing the characters
    const draw = () => {
      // Semi-transparent black block to create trailing fade effect
      ctx.fillStyle = 'rgba(0, 0, 0, 0.06)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      ctx.font = font_size + 'px monospace';
      
      // Looping over drops
      for (let i = 0; i < drops.length; i++) {
        // Only draw if the drop has entered the visible canvas
        if (drops[i] >= 0) {
          const text = matrixArray[Math.floor(Math.random() * matrixArray.length)];
          const x = i * font_size;
          const y = Math.floor(drops[i]) * font_size;

          // Draw the leading head of the stream in bright white with a green glow
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#00FF41';
          ctx.shadowBlur = 8;
          ctx.fillText(text, x, y);

          // Draw the trail character immediately above it in standard neon green
          if (drops[i] > 1) {
            ctx.fillStyle = '#00FF41';
            ctx.shadowBlur = 2;
            const trailText = matrixArray[Math.floor(Math.random() * matrixArray.length)];
            ctx.fillText(trailText, x, y - font_size);
          }

          // Draw a dim green character further up for tail length definition
          if (drops[i] > 3) {
            ctx.fillStyle = '#005f18';
            ctx.shadowBlur = 0;
            const dimText = matrixArray[Math.floor(Math.random() * matrixArray.length)];
            ctx.fillText(dimText, x, y - (font_size * 3));
          }
        }
        
        // Reset drop back to top after it goes below canvas
        if (drops[i] * font_size > canvas.height) {
          if (Math.random() > 0.98) {
            drops[i] = 0;
            speeds[i] = 1 + Math.random() * 1.5;
          }
        }
        
        // Move the drop down based on its speed
        drops[i] += speeds[i] * 0.4;
      }
    };

    const interval = setInterval(draw, 33);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed top-0 left-0 w-full h-full pointer-events-none z-0"
      style={{ opacity: 0.22 }} // Increased opacity slightly for standard matrix immersion
    />
  );
};