export interface User {
  id: string
  username: string
  email: string
  full_name: string
  is_admin: boolean
  created_at: string
  updated_at: string
  last_login: string | null
}

export interface Device {
  id: string
  name: string
  device_type: string
  platform: string
  last_seen: string | null
}

export interface Conversation {
  id: string
  title: string
  system_prompt: string | null
  model_provider: string
  model_name: string
  is_archived: boolean
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  tool_calls: ToolCall[] | null
  tool_call_id: string | null
  metadata: Record<string, any> | null
  created_at: string
}

export interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

export interface Tool {
  name: string
  description: string
  permission_level: number
  required_permissions: string[]
  input_schema: Record<string, any>
}

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  progress: number
  current_step: number
  total_steps: number
  plan: TaskStep[] | null
  result: string | null
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export type TaskStatus = 
  | 'queued' 
  | 'planning' 
  | 'waiting_for_approval' 
  | 'running' 
  | 'completed' 
  | 'failed' 
  | 'cancelled'

export interface TaskStep {
  id: string
  task_id: string
  step_number: number
  tool_name: string
  description: string
  input_args: Record<string, any>
  output_result: string | null
  error: string | null
  status: string
  started_at: string | null
  completed_at: string | null
}

export interface ToolCallRecord {
  id: string
  task_id: string
  step_id: string | null
  tool_name: string
  input_args: Record<string, any>
  output_result: string | null
  error: string | null
  permission_level: number
  approval_required: boolean
  execution_time_ms: number
  created_at: string
}

export interface Approval {
  id: string
  title: string
  description: string
  permission_level: number
  details: Record<string, any>
  status: ApprovalStatus
  expires_at: string
  responded_at: string | null
  response_reason: string | null
}

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired'

export interface Automation {
  id: string
  name: string
  description: string | null
  trigger_type: string
  trigger_config: Record<string, any>
  action_type: string
  action_config: Record<string, any>
  conditions: AutomationCondition[] | null
  is_enabled: boolean
  last_run_at: string | null
  next_run_at: string | null
  run_count: number
  success_count: number
  failure_count: number
  last_error: string | null
}

export interface AutomationCondition {
  type: string
  [key: string]: any
}

export interface Memory {
  id: string
  category: string
  key: string
  value: string
  metadata: Record<string, any> | null
  is_sensitive: boolean
  created_at: string
  updated_at: string
}

export interface Notification {
  id: string
  type: string
  title: string
  body: string
  data: Record<string, any> | null
  is_read: boolean
  sent_at: string | null
  read_at: string | null
  created_at: string
}

export interface PCStatus {
  system?: SystemInfo
  cpu?: CPUUsage
  gpu?: GPUUsage
  ram?: RAMUsage
  disk?: DiskUsage
  network?: NetworkInfo
  battery?: BatteryStatus
}

export interface SystemInfo {
  platform: string
  platform_release: string
  platform_version: string
  architecture: string
  processor: string
  hostname: string
  python_version: string
  boot_time: number
}

export interface CPUUsage {
  usage_percent: number | number[]
  core_count: number
  thread_count: number
  frequency_mhz?: number
}

export interface GPUUsage {
  gpus: GPUInfo[]
}

export interface GPUInfo {
  id: number
  name: string
  load_percent: number
  memory_used_mb: number
  memory_total_mb: number
  memory_free_mb: number
  temperature_c: number
}

export interface RAMUsage {
  ram: {
    total_gb: number
    available_gb: number
    used_gb: number
    percent: number
  }
  swap: {
    total_gb: number
    used_gb: number
    free_gb: number
    percent: number
  }
}

export interface DiskUsage {
  path: string
  total_gb: number
  used_gb: number
  free_gb: number
  percent: number
  partitions: PartitionInfo[]
}

export interface PartitionInfo {
  device: string
  mountpoint: string
  fstype: string
  total_gb: number
  used_gb: number
  free_gb: number
  percent: number
}

export interface NetworkInfo {
  interfaces: NetworkInterface[]
}

export interface NetworkInterface {
  name: string
  addresses: NetworkAddress[]
  is_up: boolean
  speed_mbps: number
  bytes_sent: number
  bytes_recv: number
}

export interface NetworkAddress {
  family: string
  address: string
  netmask: string
  broadcast: string
}

export interface BatteryStatus {
  has_battery: boolean
  percent?: number
  power_plugged?: boolean
  time_left_seconds?: number | null
}

export interface GitHubRepository {
  id: number
  name: string
  full_name: string
  description: string | null
  private: boolean
  html_url: string
  default_branch: string
  stars: number
  forks: number
  open_issues: number
  updated_at: string
}

export interface GitHubIssue {
  id: number
  number: number
  title: string
  body: string | null
  state: string
  labels: GitHubLabel[]
  assignees: GitHubUser[]
  created_at: string
  updated_at: string
  html_url: string
}

export interface GitHubPullRequest {
  id: number
  number: number
  title: string
  body: string | null
  state: string
  head: GitHubBranch
  base: GitHubBranch
  draft: boolean
  created_at: string
  updated_at: string
  html_url: string
}

export interface GitHubLabel {
  id: number
  name: string
  color: string
  description: string | null
}

export interface GitHubUser {
  login: string
  id: number
  avatar_url: string
  html_url: string
}

export interface GitHubBranch {
  ref: string
  sha: string
  repo: GitHubRepository | null
}

export interface GitHubWorkflowRun {
  id: number
  name: string
  status: string
  conclusion: string | null
  workflow_id: number
  head_branch: string
  head_sha: string
  run_number: number
  created_at: string
  updated_at: string
  html_url: string
}

export interface FileInfo {
  name: string
  path: string
  is_dir: boolean
  size: number
  modified: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
}

export interface ChatResponse {
  response: string
  conversation_id: string
  tool_calls: ToolCall[] | null
}