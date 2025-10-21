import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

vi.mock('vis-network/standalone', () => {
  class MockNetwork {
    constructor(container: any, data: any, opts: any) {}
    destroy() {}
    focus() {}
    selectNodes() {}
    on() {}
    setData() {}
    fit() {}
    body = { data: { nodes: { get: () => [] } } }
  }
  const DataSet = class {}
  return { Network: MockNetwork, DataSet }
})


