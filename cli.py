"""CLI tool for testing the Autonomous PM System."""
import asyncio
import sys
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

app = typer.Typer(help="Autonomous PM System CLI")
console = Console()

BASE_URL = "http://localhost:8000/api/v1"


@app.command()
def health() -> None:
    """Check API health status."""
    try:
        response = httpx.get("http://localhost:8000/health")
        response.raise_for_status()
        data = response.json()
        rprint(f"[green]✓[/green] API is {data['status']}")
        rprint(f"  Environment: {data['environment']}")
        rprint(f"  Database: {data['database']}")
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] API health check failed: {e}")
        sys.exit(1)


@app.command()
def create_project(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, help="Project description"),
    github_org: Optional[str] = typer.Option(None, help="GitHub organization"),
) -> None:
    """Create a new project."""
    payload = {"name": name, "github_org": github_org or ""}
    if description:
        payload["description"] = description
    
    try:
        response = httpx.post(f"{BASE_URL}/projects", json=payload)
        response.raise_for_status()
        project = response.json()
        
        rprint(f"[green]✓[/green] Created project: {project['name']}")
        rprint(f"  ID: {project['id']}")
        rprint(f"  Status: {project['status']}")
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Failed to create project: {e}")
        sys.exit(1)


@app.command()
def list_projects() -> None:
    """List all projects."""
    try:
        response = httpx.get(f"{BASE_URL}/projects")
        response.raise_for_status()
        projects = response.json()
        
        if not projects:
            rprint("[yellow]No projects found[/yellow]")
            return
        
        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("GitHub Org", style="blue")
        
        for project in projects:
            table.add_row(
                str(project["id"]),
                project["name"],
                project["status"],
                project.get("github_org", "N/A"),
            )
        
        console.print(table)
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Failed to list projects: {e}")
        sys.exit(1)


@app.command()
def create_epic(
    title: str = typer.Argument(..., help="Epic title"),
    project_id: int = typer.Option(..., help="Project ID"),
    description: Optional[str] = typer.Option(None, help="Epic description"),
    priority: int = typer.Option(0, help="Priority (higher = more important)"),
) -> None:
    """Create a new epic."""
    payload = {
        "title": title,
        "project_id": project_id,
        "priority": priority,
    }
    if description:
        payload["description"] = description
    
    try:
        response = httpx.post(f"{BASE_URL}/epics", json=payload)
        response.raise_for_status()
        epic = response.json()
        
        rprint(f"[green]✓[/green] Created epic: {epic['title']}")
        rprint(f"  ID: {epic['id']}")
        rprint(f"  Status: {epic['status']}")
        rprint(f"  Priority: {epic['priority']}")
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Failed to create epic: {e}")
        sys.exit(1)


@app.command()
def create_task(
    title: str = typer.Argument(..., help="Task title"),
    epic_id: int = typer.Option(..., help="Epic ID"),
    description: Optional[str] = typer.Option(None, help="Task description"),
    priority: str = typer.Option("medium", help="Priority (critical/high/medium/low)"),
    story_points: Optional[int] = typer.Option(None, help="Story points"),
) -> None:
    """Create a new task."""
    payload = {
        "title": title,
        "epic_id": epic_id,
        "priority": priority,
    }
    if description:
        payload["description"] = description
    if story_points:
        payload["story_points"] = story_points
    
    try:
        response = httpx.post(f"{BASE_URL}/tasks", json=payload)
        response.raise_for_status()
        task = response.json()
        
        rprint(f"[green]✓[/green] Created task: {task['title']}")
        rprint(f"  ID: {task['id']}")
        rprint(f"  Status: {task['status']}")
        rprint(f"  Priority: {task['priority']}")
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Failed to create task: {e}")
        sys.exit(1)


@app.command()
def kanban(
    epic_id: Optional[int] = typer.Option(None, help="Filter by epic ID"),
) -> None:
    """Display kanban board."""
    try:
        url = f"{BASE_URL}/tasks/kanban/board"
        if epic_id:
            url += f"?epic_id={epic_id}"
        
        response = httpx.get(url)
        response.raise_for_status()
        board = response.json()
        
        for column, tasks in board.items():
            if tasks:
                table = Table(title=column.upper().replace("_", " "))
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Priority", style="yellow")
                
                for task in tasks:
                    table.add_row(
                        str(task["id"]),
                        task["title"],
                        task["priority"],
                    )
                
                console.print(table)
                console.print()
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Failed to get kanban board: {e}")
        sys.exit(1)


@app.command()
def sync(
    project_id: int = typer.Argument(..., help="Project ID"),
    repo_owner: str = typer.Option(..., help="GitHub repo owner"),
    repo_name: str = typer.Option(..., help="GitHub repo name"),
) -> None:
    """Sync project with GitHub."""
    try:
        response = httpx.post(
            f"{BASE_URL}/sync/projects/{project_id}",
            params={"repo_owner": repo_owner, "repo_name": repo_name},
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()
        
        rprint(f"[green]✓[/green] Sync completed!")
        rprint(f"  Direction: {result['direction']}")
        rprint(f"  Epics synced: {result['epics_synced']}")
        rprint(f"  GitHub items synced: {result['github_sync']['synced_count']}")
        rprint(f"  New items created: {result['github_sync']['created_count']}")
    except httpx.HTTPError as e:
        rprint(f"[red]✗[/red] Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
