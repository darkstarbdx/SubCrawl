import os
import subprocess
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.columns import Columns
import time

# Initialize Rich Console
console = Console()

# Tool Branding
TOOL_NAME = "SubCrawl v1.0"
AUTHOR = "Darkstarbdx"
GITHUB_URL = "https://github.com/darkstarbdx"
TELEGRAM_GROUP = "https://t.me/+mzZ9IrWgXe9jNWNl"

# Tool Banner with Your ASCII Art
BANNER = f"""
[bold cyan]
  _________    ___.   _________                      .__   
 /   _____/__ _\_ |__ \_   ___ \____________ __  _  _|  |  
 \_____  \|  |  \ __ \/    \  \/\_  __ \__  \\ \/ \/ /  |  
 /        \  |  / \_\ \     \____|  | \// __ \\     /|  |__
/_______  /____/|___  /\______  /|__|  (____  /\/\_/ |____/
        \/          \/        \/            \/             
[/bold cyan]
[bold yellow]{TOOL_NAME}[/bold yellow]
[bold green]URL Fetching Tool[/bold green]
[bold magenta][-] Author: {AUTHOR}[/bold magenta]
[bold blue][-] GitHub: {GITHUB_URL}[/bold blue]
[bold cyan][-] Telegram Group: {TELEGRAM_GROUP}[/bold cyan]
"""

# Required Tools
REQUIRED_TOOLS = {
    "subfinder": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "amass": "go install -v github.com/owasp-amass/amass/v3/...@master",
    "waybackurls": "go install -v github.com/tomnomnom/waybackurls@latest",
    "httpx": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
    "jq": "sudo apt install jq" if shutil.which("apt") else "brew install jq",
    "curl": "sudo apt install curl" if shutil.which("apt") else "brew install curl",
}

# Clear Screen Function
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# Check and Install Required Tools
def check_and_install_tools():
    console.print(Panel.fit("[bold yellow]🔧 Checking Required Tools[/bold yellow]"))
    missing_tools = []

    for tool, install_cmd in REQUIRED_TOOLS.items():
        if shutil.which(tool) is None:
            console.print(f"[bold red]❌ {tool} is not installed.[/bold red]")
            missing_tools.append((tool, install_cmd))
        else:
            console.print(f"[bold green]✅ {tool} is installed.[/bold green]")

    if missing_tools:
        console.print(Panel.fit("[bold yellow]🚀 Installing Missing Tools[/bold yellow]"))
        for tool, install_cmd in missing_tools:
            console.print(f"[bold cyan]Installing {tool}...[/bold cyan]")
            try:
                subprocess.run(install_cmd, shell=True, check=True)
                console.print(f"[bold green]✅ {tool} installed successfully![/bold green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]❌ Failed to install {tool}. Please install it manually:[/bold red]")
                console.print(f"[bold yellow]{install_cmd}[/bold yellow]")
                exit(1)
    else:
        console.print("[bold green]🎉 All required tools are installed![/bold green]")

# Create Directory
def create_directory():
    console.print(Panel.fit("[bold magenta]📂 Create a directory to save results:[/bold magenta]"))
    dir_name = console.input("[bold]Enter directory name: [/bold]")
    dir_path = console.input("[bold]Enter directory path (leave blank for current directory): [/bold]")
    
    if dir_path:
        save_path = Path(dir_path) / dir_name
    else:
        save_path = Path.cwd() / dir_name
    
    save_path.mkdir(exist_ok=True)
    console.print(f"[bold green]✅ Directory created at: {save_path}[/bold green]")
    return save_path

# Run Command with Enhanced Progress Animation
def run_command(command, description):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]{description}...", total=100)
        try:
            # Use universal_newlines=False to avoid automatic decoding
            result = subprocess.run(command, shell=True, capture_output=True, universal_newlines=False)
            # Decode the output manually, ignoring errors
            stdout = result.stdout.decode("utf-8", errors="ignore")
            stderr = result.stderr.decode("utf-8", errors="ignore")
            progress.update(task, completed=100)
            return subprocess.CompletedProcess(args=command, returncode=result.returncode, stdout=stdout, stderr=stderr)
        except Exception as e:
            console.print(f"[bold red]❌ Error running command: {e}[/bold red]")
            progress.update(task, completed=100)
            return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr=str(e))

# Subdomain Enumeration with Enhanced Animations
def enumerate_subdomains(target, save_path):
    console.print(Panel.fit(f"[bold yellow]🔍 Enumerating Subdomains for {target}[/bold yellow]"))
    
    # Subfinder
    run_command(f"subfinder -d {target} -o {save_path}/subdomains.txt", "Running Subfinder")
    
    # Amass
    run_command(f"amass enum -d {target} -o {save_path}/amass_subdomains.txt", "Running Amass")
    
    # crt.sh
    run_command(f'curl -s "https://crt.sh/?q=%25.{target}&output=json" | jq -r \'.[].name_value\' | sort -u > {save_path}/crt_subdomains.txt', "Fetching crt.sh Data")
    
    # Merge and Sort Subdomains
    run_command(f"cat {save_path}/subdomains.txt {save_path}/amass_subdomains.txt {save_path}/crt_subdomains.txt | sort -u > {save_path}/all_subdomains.txt", "Merging Subdomains")
    
    with open(f"{save_path}/all_subdomains.txt", "r") as file:
        subdomains = file.readlines()
        console.print(f"[bold green]✅ Total Subdomains Found: {len(subdomains)}[/bold green]")

# Fetch URLs from Wayback Machine with Enhanced Animations
def fetch_urls(save_path):
    console.print(Panel.fit("[bold yellow]🌐 Fetching URLs from Wayback Machine[/bold yellow]"))
    run_command(f"cat {save_path}/all_subdomains.txt | waybackurls > {save_path}/wayback_data.txt", "Fetching URLs")
    
    with open(f"{save_path}/wayback_data.txt", "r") as file:
        urls = file.readlines()
        console.print(f"[bold green]✅ Total URLs Fetched: {len(urls)}[/bold green]")

# Check Live Domains with Enhanced Animations
def check_live_domains(save_path):
    console.print(Panel.fit("[bold yellow]🌍 Checking Live Domains[/bold yellow]"))
    run_command(f"cat {save_path}/wayback_data.txt | httpx -silent -o {save_path}/alive_domains.txt", "Checking Live Domains")
    
    with open(f"{save_path}/alive_domains.txt", "r") as file:
        alive_domains = file.readlines()
        console.print(f"[bold green]✅ Total Alive Domains: {len(alive_domains)}[/bold green]")

# Display Results with Enhanced Dashboard UI
def display_results(save_path):
    console.print(Panel.fit("[bold yellow]📊 Results Summary[/bold yellow]"))
    
    with open(f"{save_path}/all_subdomains.txt", "r") as file:
        subdomains = file.readlines()
    
    with open(f"{save_path}/wayback_data.txt", "r") as file:
        urls = file.readlines()
    
    with open(f"{save_path}/alive_domains.txt", "r") as file:
        alive_domains = file.readlines()
    
    # Create a Table for Results
    table = Table(title="[bold cyan]Results[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="bold green")
    table.add_column("Count", style="bold yellow")
    
    table.add_row("Total Subdomains", str(len(subdomains)))
    table.add_row("Total URLs Fetched", str(len(urls)))
    table.add_row("Total Alive Domains", str(len(alive_domains)))
    
    # Create Panels for Each Section
    subdomains_panel = Panel.fit(
        f"[bold green]{len(subdomains)}[/bold green] subdomains found.",
        title="[bold cyan]Subdomains[/bold cyan]",
        border_style="blue"
    )
    
    urls_panel = Panel.fit(
        f"[bold green]{len(urls)}[/bold green] URLs fetched.",
        title="[bold cyan]URLs[/bold cyan]",
        border_style="blue"
    )
    
    alive_panel = Panel.fit(
        f"[bold green]{len(alive_domains)}[/bold green] alive domains detected.",
        title="[bold cyan]Alive Domains[/bold cyan]",
        border_style="blue"
    )
    
    # Display Panels in Columns
    console.print(Columns([subdomains_panel, urls_panel, alive_panel]))
    
    # Display Table
    console.print(table)

# Main Function
def main():
    clear_screen()
    console.print(Panel.fit(BANNER, style="bold blue"))
    
    # Check and Install Required Tools
    check_and_install_tools()
    
    # Create Directory
    save_path = create_directory()
    
    # Get Target Domain
    target = console.input("[bold]🎯 Enter target domain (without http/https): [/bold]")
    
    # Clear the terminal before starting work
    clear_screen()
    console.print(Panel.fit(f"[bold yellow]🚀 Starting SubCrawl for {target}[/bold yellow]"))
    
    # Enumerate Subdomains
    enumerate_subdomains(target, save_path)
    
    # Fetch URLs
    fetch_urls(save_path)
    
    # Check Live Domains
    check_live_domains(save_path)
    
    # Display Results
    display_results(save_path)
    
    console.print(Panel.fit("[bold green]🎉 Tool execution completed![/bold green]", style="bold green"))

if __name__ == "__main__":
    main()