export interface AgentStatus {
  name: string
  status: 'running' | 'completed' | 'failed' | 'degraded'
  timestamp: string
}

export interface Location {
  lat: number
  lng: number
}

export interface Activity {
  time: string
  name: string
  description: string
  duration_hours: number
  ticket_price: number | null
  location: Location | null
  transport_to_next: string | null
}

export interface Meal {
  type: string
  time: string
  restaurant: string
  dishes: string[]
  estimated_cost: number
}

export interface DayPlan {
  day: number
  date: string
  theme: string
  weather_note: string
  activities: Activity[]
  meals: Meal[]
  accommodation: string
  daily_budget_estimate: number
  tips: string[]
}

export interface BudgetEstimate {
  hotel: number
  food: number
  transport: number
  tickets: number
  total: number
  per_person: number
}

export interface TravelPlan {
  user_query: string
  task_id: string
  destination: string
  travel_dates: { start: string; end: string }
  traveler_count: number
  budget: number | null
  preferences: string[]
  attractions: any[]
  weather_info: any
  hotel_recommendations: any[]
  food_plan: any
  transport_plan: any
  budget_estimate: BudgetEstimate
  image_urls: string[]
  itinerary: DayPlan[]
  summary: string
  errors: Array<{ node: string; error: string }>
}

export interface HistoryItem {
  id: string
  query: string
  destination: string
  date: string
  plan: TravelPlan
}
