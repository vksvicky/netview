import '@testing-library/jest-dom/vitest'
import { vi, afterEach, beforeEach } from 'vitest'

// Global cleanup to prevent React scheduler from running after tests
let cleanupFunctions: (() => void)[] = []

beforeEach(() => {
  // Clear any existing cleanup functions
  cleanupFunctions = []
  
  // Clear all timers before each test
  vi.clearAllTimers()
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
  
  // Clear any remaining timeouts/intervals
  if (typeof window !== 'undefined') {
    // Clear all timeouts and intervals
    const highestTimeoutId = setTimeout(() => {}, 0)
    const highestIntervalId = setInterval(() => {}, 0)
    
    for (let i = 0; i < highestTimeoutId; i++) {
      clearTimeout(i)
    }
    for (let i = 0; i < highestIntervalId; i++) {
      clearInterval(i)
    }
    
    // Clear the test timeouts/intervals
    clearTimeout(highestTimeoutId)
    clearInterval(highestIntervalId)
  }
  
  // Wait for any pending promises to resolve
  return new Promise(resolve => {
    setTimeout(resolve, 0)
  })
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
    canvas: {
      width: 800,
      height: 600,
      offsetWidth: 800,
      offsetHeight: 600,
      clientWidth: 800,
      clientHeight: 600,
      webkitBackingStorePixelRatio: 1
    }
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

// Mock additional canvas properties that vis-network needs
Object.defineProperty(HTMLCanvasElement.prototype, 'offsetWidth', {
  value: 800,
  writable: true
})

Object.defineProperty(HTMLCanvasElement.prototype, 'offsetHeight', {
  value: 600,
  writable: true
})

Object.defineProperty(HTMLCanvasElement.prototype, 'clientWidth', {
  value: 800,
  writable: true
})

Object.defineProperty(HTMLCanvasElement.prototype, 'clientHeight', {
  value: 600,
  writable: true
})

// Mock devicePixelRatio
Object.defineProperty(window, 'devicePixelRatio', {
  value: 1,
  writable: true
})

// Mock webkitBackingStorePixelRatio
Object.defineProperty(HTMLCanvasElement.prototype, 'webkitBackingStorePixelRatio', {
  value: 1,
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


