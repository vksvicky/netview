import '@testing-library/jest-dom'

vi.mock('vis-network/standalone', () => {
  class MockNetwork {
    constructor(container: any, data: any, opts: any) {}
    destroy() {}
    focus() {}
    selectNodes() {}
    on() {}
    setData() {}
    body = { data: { nodes: { get: () => [] } } }
  }
  const DataSet = class {}
  return { Network: MockNetwork, DataSet }
})


