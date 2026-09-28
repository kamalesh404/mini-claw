from typing import List, Optional, Dict, Any
import httpx
from githubkit import GitHub
from githubkit.versions.latest import models
from githubkit.exception import GitHubError

from app.config import settings
from app.database.models import GitHubAccount
from app.database.session import get_session
from app.security.auth import verify_password, get_password_hash


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.client = GitHub(self.token) if self.token else None
    
    async def _get_client(self, user_id: Optional[str] = None) -> GitHub:
        if self.client:
            return self.client
        
        if user_id:
            async with get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(GitHubAccount).where(
                        GitHubAccount.user_id == user_id,
                        GitHubAccount.is_active == True
                    )
                )
                account = result.scalar_one_or_none()
                if account:
                    return GitHub(account.access_token_encrypted)
        
        raise ValueError("No GitHub token available")
    
    async def get_repository(self, owner: str, repo: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.repos.async_get(owner=owner, repo=repo)
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        limit: int = 30,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        client = await self._get_client(user_id)
        try:
            params = {"state": state, "per_page": limit}
            if labels:
                params["labels"] = ",".join(labels)
            
            response = await client.rest.issues.async_list_for_repo(owner=owner, repo=repo, **params)
            return [issue.to_dict() for issue in response.parsed_data]
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.issues.async_get(owner=owner, repo=repo, issue_number=issue_number)
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            data = {"title": title}
            if body:
                data["body"] = body
            if labels:
                data["labels"] = labels
            if assignees:
                data["assignees"] = assignees
            
            response = await client.rest.issues.async_create(owner=owner, repo=repo, data=data)
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.issues.async_create_comment(
                owner=owner, repo=repo, issue_number=issue_number, data={"body": body}
            )
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 30,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.pulls.async_list(
                owner=owner, repo=repo, state=state, per_page=limit
            )
            return [pr.to_dict() for pr in response.parsed_data]
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.pulls.async_get(owner=owner, repo=repo, pull_number=pr_number)
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            base_ref = await client.rest.git.async_get_ref(owner=owner, repo=repo, ref=f"heads/{from_branch}")
            base_sha = base_ref.parsed_data.object.sha
            
            response = await client.rest.git.async_create_ref(
                owner=owner,
                repo=repo,
                data={"ref": f"refs/heads/{branch_name}", "sha": base_sha}
            )
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def create_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        message: str,
        files: Dict[str, str],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            # Get latest commit on branch
            ref_response = await client.rest.git.async_get_ref(owner=owner, repo=repo, ref=f"heads/{branch}")
            latest_sha = ref_response.parsed_data.object.sha
            
            # Get tree of latest commit
            commit_response = await client.rest.git.async_get_commit(owner=owner, repo=repo, commit_sha=latest_sha)
            base_tree_sha = commit_response.parsed_data.tree.sha
            
            # Create blobs for new files
            blobs = []
            for path, content in files.items():
                blob_response = await client.rest.git.async_create_blob(
                    owner=owner, repo=repo, data={"content": content, "encoding": "utf-8"}
                )
                blobs.append({
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_response.parsed_data.sha,
                })
            
            # Create new tree
            tree_response = await client.rest.git.async_create_tree(
                owner=owner,
                repo=repo,
                data={"base_tree": base_tree_sha, "tree": blobs}
            )
            new_tree_sha = tree_response.parsed_data.sha
            
            # Create commit
            commit_response = await client.rest.git.async_create_commit(
                owner=owner,
                repo=repo,
                data={
                    "message": message,
                    "tree": new_tree_sha,
                    "parents": [latest_sha],
                }
            )
            new_commit_sha = commit_response.parsed_data.sha
            
            # Update branch reference
            await client.rest.git.async_update_ref(
                owner=owner,
                repo=repo,
                ref=f"heads/{branch}",
                data={"sha": new_commit_sha, "force": False}
            )
            
            return {"sha": new_commit_sha, "message": message}
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        head: str = "",
        base: str = "main",
        draft: bool = False,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            data = {"title": title, "head": head, "base": base, "draft": draft}
            if body:
                data["body"] = body
            
            response = await client.rest.pulls.async_create(owner=owner, repo=repo, data=data)
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            data = {"ref": ref}
            if inputs:
                data["inputs"] = inputs
            
            response = await client.rest.actions.async_create_workflow_dispatch(
                owner=owner, repo=repo, workflow_id=workflow_id, data=data
            )
            return {"status": "triggered", "workflow_id": workflow_id}
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.actions.async_get_workflow_run(
                owner=owner, repo=repo, run_id=run_id
            )
            return response.parsed_data.to_dict()
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def download_artifact(
        self,
        owner: str,
        repo: str,
        artifact_id: int,
        path: str = ".",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._get_client(user_id)
        try:
            response = await client.rest.actions.async_download_artifact(
                owner=owner, repo=repo, artifact_id=artifact_id, archive_format="zip"
            )
            import os
            os.makedirs(path, exist_ok=True)
            file_path = os.path.join(path, f"artifact_{artifact_id}.zip")
            with open(file_path, "wb") as f:
                f.write(response.content)
            return {"path": file_path, "size": len(response.content)}
        except GitHubError as e:
            raise Exception(f"GitHub API error: {e}")
    
    async def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        import hmac
        import hashlib
        
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)