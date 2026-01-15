import { useEffect, useRef, useState } from 'react'
import { Stage, Layer, Line, Circle, Text, Rect, Group } from 'react-konva'
import { ZoomIn, ZoomOut, Move, RotateCcw } from 'lucide-react'

interface Point {
  x: number
  y: number
}

interface Entity {
  type: string
  points?: Point[]
  start?: Point
  end?: Point
  center?: Point
  radius?: number
  text?: string
  layer?: string
  closed?: boolean
}

interface PlanCanvasProps {
  bounds?: {
    min_x: number
    min_y: number
    max_x: number
    max_y: number
    width: number
    height: number
  }
  contours?: Entity[]
  openings?: Entity[]
  elements?: any[]
  width?: number
  height?: number
}

export default function PlanCanvas({
  bounds,
  contours = [],
  openings = [],
  elements = [],
  width = 800,
  height = 600,
}: PlanCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [stageSize, setStageSize] = useState({ width, height })

  // Calculate scale to fit content
  useEffect(() => {
    if (bounds && bounds.width && bounds.height) {
      const padding = 50
      const scaleX = (stageSize.width - padding * 2) / bounds.width
      const scaleY = (stageSize.height - padding * 2) / bounds.height
      const newScale = Math.min(scaleX, scaleY, 2) // Max scale 2x

      setScale(newScale)

      // Center the drawing
      const centerX = stageSize.width / 2 - (bounds.width * newScale) / 2 - bounds.min_x * newScale
      const centerY = stageSize.height / 2 + (bounds.height * newScale) / 2 + bounds.min_y * newScale

      setPosition({ x: centerX, y: centerY })
    }
  }, [bounds, stageSize])

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setStageSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        })
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleWheel = (e: any) => {
    e.evt.preventDefault()
    const scaleBy = 1.1
    const stage = e.target.getStage()
    const oldScale = scale
    const mousePointTo = {
      x: stage.getPointerPosition().x / oldScale - position.x / oldScale,
      y: stage.getPointerPosition().y / oldScale - position.y / oldScale,
    }
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
    setScale(Math.max(0.1, Math.min(10, newScale)))
    setPosition({
      x: -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale,
      y: -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale,
    })
  }

  const handleZoomIn = () => setScale((s) => Math.min(s * 1.2, 10))
  const handleZoomOut = () => setScale((s) => Math.max(s / 1.2, 0.1))
  const handleReset = () => {
    if (bounds && bounds.width && bounds.height) {
      const scaleX = (stageSize.width - 100) / bounds.width
      const scaleY = (stageSize.height - 100) / bounds.height
      const newScale = Math.min(scaleX, scaleY, 2)
      setScale(newScale)
      const centerX = stageSize.width / 2 - (bounds.width * newScale) / 2 - bounds.min_x * newScale
      const centerY = stageSize.height / 2 + (bounds.height * newScale) / 2 + bounds.min_y * newScale
      setPosition({ x: centerX, y: centerY })
    }
  }

  // Convert DXF coordinates to canvas (flip Y axis)
  const toCanvasY = (y: number) => -y

  // Render polyline/polygon
  const renderPolyline = (entity: Entity, index: number, color: string, strokeWidth: number = 2) => {
    if (!entity.points || entity.points.length < 2) return null

    const points = entity.points.flatMap((p) => [p.x, toCanvasY(p.y)])

    return (
      <Line
        key={`poly-${index}`}
        points={points}
        stroke={color}
        strokeWidth={strokeWidth / scale}
        closed={entity.closed}
        fill={entity.closed ? `${color}20` : undefined}
      />
    )
  }

  // Render line
  const renderLine = (entity: Entity, index: number, color: string) => {
    if (!entity.start || !entity.end) return null

    return (
      <Line
        key={`line-${index}`}
        points={[entity.start.x, toCanvasY(entity.start.y), entity.end.x, toCanvasY(entity.end.y)]}
        stroke={color}
        strokeWidth={1 / scale}
      />
    )
  }

  // Render circle
  const renderCircle = (entity: Entity, index: number, color: string, fill?: string) => {
    if (!entity.center || !entity.radius) return null

    return (
      <Circle
        key={`circle-${index}`}
        x={entity.center.x}
        y={toCanvasY(entity.center.y)}
        radius={entity.radius}
        stroke={color}
        strokeWidth={2 / scale}
        fill={fill}
      />
    )
  }

  // Render element (poutrelle, predalle, etc.)
  const renderElement = (elem: any, index: number) => {
    const pos = elem.position || {}
    const dims = elem.dimensions || {}

    const x = pos.x || 0
    const y = toCanvasY(pos.y || 0)
    const rotation = pos.rotation || 0
    const length = dims.length_mm || 1000
    const width = dims.width_mm || 600

    return (
      <Group key={`elem-${index}`} x={x} y={y} rotation={-rotation}>
        <Rect
          x={-length / 2}
          y={-width / 2}
          width={length}
          height={width}
          fill="#3b82f620"
          stroke="#3b82f6"
          strokeWidth={2 / scale}
        />
        <Text
          x={-length / 2 + 10}
          y={-8}
          text={elem.reference || `E${index + 1}`}
          fontSize={14 / scale}
          fill="#1e40af"
        />
      </Group>
    )
  }

  return (
    <div ref={containerRef} className="relative bg-white border rounded-lg overflow-hidden" style={{ height }}>
      {/* Toolbar */}
      <div className="absolute top-2 right-2 z-10 flex gap-1 bg-white rounded-lg shadow p-1">
        <button
          onClick={handleZoomIn}
          className="p-2 hover:bg-gray-100 rounded"
          title="Zoom avant"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 hover:bg-gray-100 rounded"
          title="Zoom arrière"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={handleReset}
          className="p-2 hover:bg-gray-100 rounded"
          title="Réinitialiser"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Scale indicator */}
      <div className="absolute bottom-2 left-2 z-10 bg-white/80 px-2 py-1 rounded text-xs text-gray-600">
        Échelle: {(scale * 100).toFixed(0)}%
      </div>

      {/* Canvas */}
      <Stage
        width={stageSize.width}
        height={stageSize.height}
        scaleX={scale}
        scaleY={scale}
        x={position.x}
        y={position.y}
        draggable
        onWheel={handleWheel}
        onDragEnd={(e) => {
          setPosition({
            x: e.target.x(),
            y: e.target.y(),
          })
        }}
      >
        <Layer>
          {/* Grid background */}
          {bounds && (
            <Rect
              x={bounds.min_x - 100}
              y={toCanvasY(bounds.max_y) - 100}
              width={bounds.width + 200}
              height={bounds.height + 200}
              fill="#f9fafb"
            />
          )}

          {/* Contours (main outlines) */}
          {contours.map((entity, i) => {
            if (entity.type === 'polyline') {
              return renderPolyline(entity, i, '#1e40af', 3)
            }
            if (entity.type === 'line') {
              return renderLine(entity, i, '#1e40af')
            }
            return null
          })}

          {/* Openings (tremies) */}
          {openings.map((entity, i) => {
            if (entity.type === 'polyline') {
              return renderPolyline(entity, i, '#dc2626', 2)
            }
            if (entity.type === 'circle') {
              return renderCircle(entity, i, '#dc2626', '#dc262620')
            }
            return null
          })}

          {/* Elements (poutrelles, predalles, etc.) */}
          {elements.map((elem, i) => renderElement(elem, i))}
        </Layer>
      </Stage>

      {/* Empty state */}
      {contours.length === 0 && openings.length === 0 && elements.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <Move className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Aucune géométrie à afficher</p>
            <p className="text-sm">Importez un fichier DXF</p>
          </div>
        </div>
      )}
    </div>
  )
}
