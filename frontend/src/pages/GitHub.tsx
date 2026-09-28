import { useEffect, useState } from 'react'
import { Tab, Tabs, TabList, TabTrigger, TabContent } from '../components/ui/Tabs'
import { Github, RefreshCw, Loader2, ExternalLink, FileText, GitBranch, AlertTriangle, CheckCircle, Clock, Zap } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { GitHubRepository, GitHubIssue, GitHubPullRequest, GitHubWorkflowRun } from '../types'
import { clsx } from 'clsx'

export function GitHub() {
  const [repo, setRepo] = useState<GitHubRepository | null>(null)
  const [issues, setIssues] = useState<GitHubIssue[]>([])
  const [prs, setPRs] = useState<GitHubPullRequest[]>([])
  const [workflows, setWorkflows] = useState<GitHubWorkflowRun[]>([])
  const [loading, setLoading] = useState({ repo: true, issues: true, prs: true, workflows: true })
  const [repoInput, setRepoInput] = useState('')
  const [activeTab, setActiveTab] = useState<'repo' | 'issues' | 'prs' | 'workflows'>('repo')

  useEffect(() => {
    if (repoInput) {
      fetchAll()
    }
  }, [repoInput])

  const fetchAll = async () => {
    const [owner, name] = repoInput.split('/')
    if (!owner || !name) return

    setLoading({ repo: true, issues: true, prs: true, workflows: true })

    try {
      const [repoRes, issuesRes, prsRes, workflowsRes] = await Promise.allSettled([
        api.post('/github/repository', { owner, repo: name }),
        api.post('/github/issues', { owner, repo: name, state: 'open', limit: 20 }),
        api.post('/github/pull-requests', { owner, repo: name, state: 'open', limit: 20 }),
        api.get('/github/workflows?limit=10'),
      ])

      if (repoRes.status === 'fulfilled') setRepo(repoRes.value)
      if (issuesRes.status === 'fulfilled') setIssues(issuesRes.value.issues || [])
      if (prsRes.status === 'fulfilled') setPRs(prsRes.value.pull_requests || [])
      if (workflowsRes.status === 'fulfilled') setWorkflows(workflowsRes.value.workflow_runs || [])
    } catch (error) {
      console.error('Failed to fetch GitHub data:', error)
    } finally {
      setLoading({ repo: false, issues: false, prs: false, workflows: false })
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString()
  }

  const getStatusBadge = (status: string, conclusion?: string | null) => {
    if (conclusion === 'success') return <Badge variant="success" dot>Success</Badge>
    if (conclusion === 'failure') return <Badge variant="error" dot>Failed</Badge>
    if (status === 'in_progress') return <Badge variant="info" dot><Clock className="w-3 h-3 mr-1 animate-spin" />Running</Badge>
    if (status === 'queued') return <Badge variant="warning" dot>Queued</Badge>
    return <Badge variant="gray" dot>{status}</Badge>
  }

  const IssueRow = ({ issue }: { issue: GitHubIssue }) => (
    <div className="p-3 rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800/50 border-b border-dark-100 dark:border-dark-800 last:border-0">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-dark-900 dark:text-white truncate">#{issue.number}</span>
            <span className="text-primary-600 dark:text-primary-400 font-mono text-sm">{issue.title}</span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-dark-500 dark:text-dark-400">
            {issue.labels?.map((l: any) => (
              <Badge key={l.id} variant="gray" className="text-xs" style={{ backgroundColor: `#${l.color}20`, color: `#${l.color}` }}>
                {l.name}
              </Badge>
            ))}
            <span>by {issue.user?.login}</span>
            <span>{formatDate(issue.created_at)}</span>
          </div>
        </div>
        <Button variant="ghost" size="sm" asChild>
          <a href={issue.html_url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="w-4 h-4" />
          </a>
        </Button>
      </div>
    </div>
  )

  const PRRow = ({ pr }: { pr: GitHubPullRequest }) => (
    <div className="p-3 rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800/50 border-b border-dark-100 dark:border-dark-800 last:border-0">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-dark-900 dark:text-white truncate">#{pr.number}</span>
            <span className="text-primary-600 dark:text-primary-400 font-mono text-sm">{pr.title}</span>
            {pr.draft && <Badge variant="gray" size="sm">Draft</Badge>}
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-dark-500 dark:text-dark-400">
            <span className="font-mono">{pr.head.ref} → {pr.base.ref}</span>
            <span>by {pr.user?.login}</span>
            <span>{formatDate(pr.created_at)}</span>
          </div>
        </div>
        <Button variant="ghost" size="sm" asChild>
          <a href={pr.html_url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="w-4 h-4" />
          </a>
        </Button>
      </div>
    </div>
  )

  const WorkflowRow = ({ wf }: { wf: GitHubWorkflowRun }) => (
    <div className="p-3 rounded-lg hover:bg-dark-50 dark:hover:bg-dark-800/50 border-b border-dark-100 dark:border-dark-800 last:border-0">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-dark-900 dark:text-white truncate">{wf.name}</span>
            <Badge variant="gray" size="sm">#{wf.run_number}</Badge>
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-dark-500 dark:text-dark-400">
            <span className="font-mono">{wf.head_branch}</span>
            <span>{wf.head_sha.slice(0, 7)}</span>
            <span>{formatDate(wf.created_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge(wf.status, wf.conclusion)}
          <Button variant="ghost" size="sm" asChild>
            <a href={wf.html_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">GitHub</h1>
          <p className="text-dark-500 dark:text-dark-400">Repository management and monitoring</p>
        </div>
        <div className="flex gap-2">
          <Input
            value={repoInput}
            onChange={(e) => setRepoInput(e.target.value)}
            placeholder="owner/repo (e.g., facebook/react)"
            className="w-64"
          />
          <Button onClick={fetchAll} disabled={loading.repo || !repoInput}>
            <RefreshCw className={clsx('w-4 h-4', loading.repo && 'animate-spin')} />
          </Button>
        </div>
      </div>

      {repo && (
        <Card>
          <CardHeader
            title={repo.full_name}
            subtitle={repo.description || 'No description'}
            action={
              <Button variant="ghost" size="sm" asChild>
                <a href={repo.html_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-4 h-4" /> View on GitHub
                </a>
              </Button>
            }
          />
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="p-4 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                <p className="text-sm text-dark-500 dark:text-dark-400">Stars</p>
                <p className="text-2xl font-bold text-dark-900 dark:text-white">{repo.stargazers_count?.toLocaleString() || 0}</p>
              </div>
              <div className="p-4 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                <p className="text-sm text-dark-500 dark:text-dark-400">Forks</p>
                <p className="text-2xl font-bold text-dark-900 dark:text-white">{repo.forks_count?.toLocaleString() || 0}</p>
              </div>
              <div className="p-4 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                <p className="text-sm text-dark-500 dark:text-dark-400">Open Issues</p>
                <p className="text-2xl font-bold text-dark-900 dark:text-white">{repo.open_issues_count?.toLocaleString() || 0}</p>
              </div>
              <div className="p-4 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                <p className="text-sm text-dark-500 dark:text-dark-400">Default Branch</p>
                <p className="text-2xl font-bold text-dark-900 dark:text-white">{repo.default_branch}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabList className="w-full">
          <TabTrigger value="repo" className="flex-1">
            <Github className="w-4 h-4 mr-2" /> Repository
          </TabTrigger>
          <TabTrigger value="issues" className="flex-1">
            <FileText className="w-4 h-4 mr-2" /> Issues ({issues.length})
          </TabTrigger>
          <TabTrigger value="prs" className="flex-1">
            <GitBranch className="w-4 h-4 mr-2" /> Pull Requests ({prs.length})
          </TabTrigger>
          <TabTrigger value="workflows" className="flex-1">
            <Zap className="w-4 h-4 mr-2" /> Workflows ({workflows.length})
          </TabTrigger>
        </TabList>

        <TabContent value="repo">
          {repo ? (
            <Card>
              <CardHeader title="Repository Details" />
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Visibility</p>
                    <p className="font-medium">{repo.private ? 'Private' : 'Public'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Language</p>
                    <p className="font-medium">{repo.language || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Created</p>
                    <p className="font-medium">{formatDate(repo.created_at)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Updated</p>
                    <p className="font-medium">{formatDate(repo.updated_at)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">License</p>
                    <p className="font-medium">{repo.license?.name || 'None'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Topics</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {repo.topics?.map((t: string) => (
                        <Badge key={t} variant="gray" size="sm">{t}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="text-center py-12">
              <Github className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">Enter a repository</h3>
              <p className="text-dark-500 dark:text-dark-400 mt-1">Type owner/repo above to get started</p>
            </Card>
          )}
        </TabContent>

        <TabContent value="issues">
          {loading.issues ? (
            <div className="p-8 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600" /></div>
          ) : issues.length === 0 ? (
            <Card className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">No open issues</h3>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <ScrollArea className="max-h-[500px]">
                  {issues.map(issue => <IssueRow key={issue.id} issue={issue} />)}
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabContent>

        <TabContent value="prs">
          {loading.prs ? (
            <div className="p-8 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600" /></div>
          ) : prs.length === 0 ? (
            <Card className="text-center py-12">
              <GitBranch className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">No open PRs</h3>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <ScrollArea className="max-h-[500px]">
                  {prs.map(pr => <PRRow key={pr.id} pr={pr} />)}
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabContent>

        <TabContent value="workflows">
          {loading.workflows ? (
            <div className="p-8 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600" /></div>
          ) : workflows.length === 0 ? (
            <Card className="text-center py-12">
              <Zap className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">No recent workflows</h3>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <ScrollArea className="max-h-[500px]">
                  {workflows.map(wf => <WorkflowRow key={wf.id} wf={wf} />)}
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabContent>
      </Tabs>
    </div>
  )
}