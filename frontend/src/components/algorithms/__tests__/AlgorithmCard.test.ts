import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AlgorithmCard from '../AlgorithmCard.vue'
import type { Algorithm } from '@/types/algorithm'

const algorithm: Algorithm = {
  id: 'algorithm-1',
  key: 'mock-detector',
  name: 'Mock Detector',
  version: '1.0.0',
  description: 'Contract test algorithm',
  task_type: 'object_detection',
  device: 'cpu',
  framework: 'pytorch',
  status: 'available',
  parameters: {},
  created_at: '2026-08-12T00:00:00Z',
}

describe('AlgorithmCard', () => {
  it('renders metadata and emits selection', async () => {
    const wrapper = mount(AlgorithmCard, { props: { algorithm } })
    expect(wrapper.text()).toContain('Mock Detector')
    expect(wrapper.text()).toContain('目标检测')
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')?.[0]).toEqual([algorithm])
  })
})

