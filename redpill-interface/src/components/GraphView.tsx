import React, { useEffect, useRef, useState } from "react";
import axios from "axios";

interface Node {
  id: string;
  label: string;
  type: string;
  description: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Edge {
  source: string;
  target: string;
  label: string;
  description: string;
}

interface GraphViewProps {
  sessionId: number;
}

export const GraphView: React.FC<GraphViewProps> = ({ sessionId }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dragNodeRef = useRef<Node | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Fetch graph data from backend
  useEffect(() => {
    if (!sessionId) return;
    
    const fetchGraphData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`http://localhost:8001/sessions/${sessionId}/graph`);
        const { nodes: fetchedNodes, edges: fetchedEdges } = res.data;
        
        // Initialize positions randomly near center
        const width = containerRef.current?.clientWidth || 600;
        const height = containerRef.current?.clientHeight || 450;
        
        const initializedNodes = fetchedNodes.map((n: Node) => ({
          ...n,
          x: width / 2 + (Math.random() - 0.5) * 100,
          y: height / 2 + (Math.random() - 0.5) * 100,
          vx: 0,
          vy: 0,
          fx: null,
          fy: null
        }));
        
        setNodes(initializedNodes);
        setEdges(fetchedEdges);
      } catch (err) {
        console.error("Error loading graph:", err);
        setError("Failed to initialize neural link graph data.");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [sessionId]);

  // Force-directed simulation loop
  useEffect(() => {
    if (nodes.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const runSimulation = () => {
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      // 1. Force Parameters
      const kRepulsion = 1500; // Repulsion constant
      const kAttraction = 0.05; // Spring force constant
      const friction = 0.85;    // Velocity damping
      const gravity = 0.015;     // Center attraction force
      const minDistance = 45;   // Minimizes overlapping

      // 2. Compute Repulsion Forces (Node vs Node)
      for (let i = 0; i < nodes.length; i++) {
        const u = nodes[i];
        if (u.fx !== undefined && u.fx !== null) continue; // Pinned
        
        let fx = 0;
        let fy = 0;

        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          const v = nodes[j];
          
          const dx = (u.x || 0) - (v.x || 0);
          const dy = (u.y || 0) - (v.y || 0);
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);

          if (dist < 300) {
            // Coulomb's repulsion
            const force = kRepulsion / distSq;
            fx += (dx / dist) * force;
            fy += (dy / dist) * force;
          }
        }

        u.vx = ((u.vx || 0) + fx) * friction;
        u.vy = ((u.vy || 0) + fy) * friction;
      }

      // 3. Compute Attraction Forces (Edges)
      edges.forEach((edge) => {
        const sourceNode = nodes.find((n) => n.id === edge.source);
        const targetNode = nodes.find((n) => n.id === edge.target);

        if (!sourceNode || !targetNode) return;

        const dx = (targetNode.x || 0) - (sourceNode.x || 0);
        const dy = (targetNode.y || 0) - (sourceNode.y || 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        if (dist > minDistance) {
          const force = kAttraction * (dist - minDistance);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (sourceNode.fx === undefined || sourceNode.fx === null) {
            sourceNode.vx = (sourceNode.vx || 0) + fx;
            sourceNode.vy = (sourceNode.vy || 0) + fy;
          }
          if (targetNode.fy === undefined || targetNode.fy === null) {
            targetNode.vx = (targetNode.vx || 0) - fx;
            targetNode.vy = (targetNode.vy || 0) - fy;
          }
        }
      });

      // 4. Center Gravity & Position Updates
      nodes.forEach((u) => {
        if (u.fx !== undefined && u.fx !== null) {
          u.x = u.fx;
          u.y = u.fy;
          u.vx = 0;
          u.vy = 0;
          return;
        }

        // Pull toward center
        const dx = centerX - (u.x || 0);
        const dy = centerY - (u.y || 0);
        u.vx = (u.vx || 0) + dx * gravity;
        u.vy = (u.vy || 0) + dy * gravity;

        // Apply positions
        u.x = (u.x || 0) + (u.vx || 0);
        u.y = (u.y || 0) + (u.vy || 0);

        // Keep inside boundaries
        const padding = 20;
        u.x = Math.max(padding, Math.min(width - padding, u.x));
        u.y = Math.max(padding, Math.min(height - padding, u.y));
      });

      // 5. Drawing Step
      ctx.clearRect(0, 0, width, height);

      // Draw edges (lines)
      ctx.lineWidth = 1.2;
      edges.forEach((edge) => {
        const sourceNode = nodes.find((n) => n.id === edge.source);
        const targetNode = nodes.find((n) => n.id === edge.target);

        if (!sourceNode || !targetNode) return;

        // Draw connections in dim matrix green or cyan for docs
        const isDocEdge = edge.source.startsWith("doc:") || edge.target.startsWith("doc:");
        ctx.strokeStyle = isDocEdge ? "rgba(0, 180, 216, 0.25)" : "rgba(34, 197, 94, 0.25)";
        
        ctx.beginPath();
        ctx.moveTo(sourceNode.x || 0, sourceNode.y || 0);
        ctx.lineTo(targetNode.x || 0, targetNode.y || 0);
        ctx.stroke();
      });

      // Draw nodes (glowing dots)
      nodes.forEach((u) => {
        const isHovered = hoveredNode?.id === u.id;
        const isDoc = u.type === "Document";
        
        // Node coloring
        let baseColor = "#22c55e"; // bright neon green
        let glowColor = "rgba(34, 197, 94, 0.7)";
        
        if (isDoc) {
          baseColor = "#00b4d8"; // Cyan for docs
          glowColor = "rgba(0, 180, 216, 0.7)";
        } else if (u.type === "Person") {
          baseColor = "#86efac"; // Mint green for people
          glowColor = "rgba(134, 239, 172, 0.7)";
        }

        // Draw outer glow shadow
        ctx.save();
        ctx.shadowBlur = isHovered ? 15 : 6;
        ctx.shadowColor = glowColor;

        ctx.fillStyle = baseColor;
        ctx.beginPath();
        ctx.arc(u.x || 0, u.y || 0, isHovered ? 9 : 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.restore();

        // Draw node labels
        ctx.font = isHovered ? "bold 11px monospace" : "9px monospace";
        ctx.fillStyle = isHovered ? "#ffffff" : "rgba(255, 255, 255, 0.65)";
        ctx.textAlign = "center";
        ctx.fillText(u.label, u.x || 0, (u.y || 0) - 12);
      });

      animationFrameRef.current = requestAnimationFrame(runSimulation);
    };

    animationFrameRef.current = requestAnimationFrame(runSimulation);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [nodes, edges, hoveredNode]);

  // Adjust canvas size to parent container
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (!canvas || !container) return;
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [nodes]);

  // Mouse Interaction Handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find node under mouse
    const clickedNode = nodes.find((n) => {
      const dx = (n.x || 0) - x;
      const dy = (n.y || 0) - y;
      return Math.sqrt(dx * dx + dy * dy) < 15;
    });

    if (clickedNode) {
      dragNodeRef.current = clickedNode;
      clickedNode.fx = x;
      clickedNode.fy = y;
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (dragNodeRef.current) {
      // Dragging node
      dragNodeRef.current.fx = x;
      dragNodeRef.current.fy = y;
    } else {
      // Hover detection
      const hovered = nodes.find((n) => {
        const dx = (n.x || 0) - x;
        const dy = (n.y || 0) - y;
        return Math.sqrt(dx * dx + dy * dy) < 15;
      });
      setHoveredNode(hovered || null);
    }
  };

  const handleMouseUp = () => {
    if (dragNodeRef.current) {
      dragNodeRef.current.fx = null;
      dragNodeRef.current.fy = null;
      dragNodeRef.current = null;
    }
  };

  return (
    <div ref={containerRef} className="relative w-full h-[500px] border border-green-500/20 bg-black/40 rounded-md overflow-hidden flex flex-col crt-monitor">
      {/* Scanline Grid */}
      <div className="absolute inset-0 pointer-events-none bg-scanlines z-10 opacity-30" />
      
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-20">
          <div className="text-green-500 font-mono text-sm animate-pulse">
            INITIALIZING NEURAL LINK GRAPH...
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-20">
          <div className="text-red-500 font-mono text-xs text-center px-4">
            {error}
          </div>
        </div>
      )}

      <div className="p-2 border-b border-green-500/20 bg-green-950/20 flex justify-between items-center z-10">
        <span className="text-[10px] text-green-500 font-mono tracking-widest uppercase">
          Neural Subgraph Visualization (Obsidian Mode)
        </span>
        <span className="text-[9px] text-green-500/60 font-mono">
          Entities: {nodes.filter(n => n.type !== "Document").length} | Docs: {nodes.filter(n => n.type === "Document").length}
        </span>
      </div>

      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="w-full flex-grow cursor-crosshair"
      />

      {/* Dynamic HUD Details panel on hover */}
      {hoveredNode && (
        <div className="absolute bottom-2 left-2 right-2 p-2 border border-green-500/30 bg-black/95 rounded font-mono text-[10px] text-green-400 z-20 pointer-events-none shadow-lg">
          <div className="flex justify-between border-b border-green-500/20 pb-1 mb-1">
            <span className="font-bold text-white uppercase">{hoveredNode.label}</span>
            <span className="text-[9px] uppercase px-1 rounded bg-green-900/40 text-green-300 border border-green-500/30">
              {hoveredNode.type}
            </span>
          </div>
          <div className="text-[9px] text-green-300/80 leading-normal">
            {hoveredNode.description || "Syntactic node representing extracted entity details."}
          </div>
        </div>
      )}
    </div>
  );
};
