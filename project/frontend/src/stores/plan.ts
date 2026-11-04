import { defineStore } from 'pinia'
import type { HistoryItem, TravelPlan } from '@/types/plan'

export interface AgentStatus {
  name: string
  status: 'running' | 'completed' | 'failed' | 'waiting'
  timestamp?: string
  details?: string
}

export const usePlanStore = defineStore('plan', {
  state: () => ({
    currentPlan: null as TravelPlan | null,
    history: [] as HistoryItem[],
    agentStatuses: [] as AgentStatus[],
  }),

  actions: {
    loadHistory() {
      const stored = localStorage.getItem('wandergraph_history')
      if (stored) this.history = JSON.parse(stored)
    },

    saveToHistory(item: HistoryItem) {
      this.history.unshift(item)
      if (this.history.length > 50) this.history = this.history.slice(0, 50)
      localStorage.setItem('wandergraph_history', JSON.stringify(this.history))
    },

    deleteHistory(id: string) {
      this.history = this.history.filter((h) => h.id !== id)
      localStorage.setItem('wandergraph_history', JSON.stringify(this.history))
    },

    getHistoryItem(id: string): HistoryItem | undefined {
      return this.history.find((h) => h.id === id)
    },

    // Agent 状态管理
    updateAgentStatus(name: string, status: AgentStatus['status'], timestamp?: string, details?: string) {
      const index = this.agentStatuses.findIndex(s => s.name === name)
      if (index >= 0) {
        this.agentStatuses[index] = { name, status, timestamp, details }
      } else {
        this.agentStatuses.push({ name, status, timestamp, details })
      }
    },

    clearAgentStatuses() {
      this.agentStatuses = []
    },

    clearErrors() {
      this.agentStatuses = this.agentStatuses.filter(s => s.status !== 'failed')
    },

    retryFailedNodes() {
      // 这里可以实现重试逻辑
      console.log('Retrying failed nodes...')
    },
  },
})
