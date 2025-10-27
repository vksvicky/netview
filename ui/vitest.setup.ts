import '@testing-library/jest-dom/vitest'
import { vi, afterEach, beforeEach } from 'vitest'

// Global cleanup to prevent React scheduler from running after tests
let cleanupFunctions: (() => void)[] = []

beforeEach(() => {
  // Clear any existing cleanup functions
  cleanupFunctions = []
})

afterEach(() => {
  // Run all cleanup functions
  cleanupFunctions.forEach(cleanup => {
    try {
      cleanup()
    } catch (error) {
      // Ignore cleanup errors
    }
  })
  cleanupFunctions = []
  
  // Force garbage collection if available
  if (global.gc) {
    global.gc()
  }
  
  // Clear all timers and intervals
  vi.clearAllTimers()
  
  // Clear all mocks
  vi.clearAllMocks()
})

// Add cleanup function to global registry
export const addCleanup = (cleanup: () => void) => {
  cleanupFunctions.push(cleanup)
}

// Mock canvas for vis-network
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn().mockReturnValue({
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi.fn().mockReturnValue({ data: new Array(4) }),
    putImageData: vi.fn(),
    createImageData: vi.fn().mockReturnValue({ data: new Array(4) }),
    setTransform: vi.fn(),
    drawImage: vi.fn(),
    save: vi.fn(),
    fillText: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    translate: vi.fn(),
    scale: vi.fn(),
    rotate: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    measureText: vi.fn().mockReturnValue({ width: 0 }),
    transform: vi.fn(),
    rect: vi.fn(),
    clip: vi.fn(),
  }),
})

// Mock canvas properties
Object.defineProperty(HTMLCanvasElement.prototype, 'width', {
  value: 800,
  writable: true
})

Object.defineProperty(HTMLCanvasElement.prototype, 'height', {
  value: 600,
  writable: true
})

vi.mock('vis-network/standalone', () => {
  class MockNetwork {
    constructor(container: any, data: any, opts: any) {}
    destroy() {}
    focus() {}
    selectNodes() {}
    on() {}
    setData = vi.fn()
    fit = vi.fn()
    body = { data: { nodes: { get: () => [] } } }
  }
  const DataSet = class {
    constructor(data: any) {}
    add() {}
    update() {}
    remove() {}
    get() { return [] }
  }
  return { Network: MockNetwork, DataSet }
})


