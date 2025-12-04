#!/usr/bin/env python3
"""
SMS Prompt CLI - A powerful CLI tool for sending customized SMS messages
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import questionary
from questionary import Style
import sys
from pathlib import Path
import csv
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config
from core.template_engine import TemplateEngine
from core.sms_gateway import SMSGateway
from db.models import Database

console = Console()
config_manager = Config()

# Custom style for questionary menus
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:cyan bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:gray'),
    ('instruction', 'fg:gray'),
])


def _validate_provider_config(config, provider):
    """Validate SMS provider configuration"""
    if provider == 'twilio':
        creds = config.get('twilio', {})
        if not creds.get('account_sid') or not creds.get('auth_token') or not creds.get('phone_number'):
            console.print("[red]Twilio credentials not configured![/red]")
            console.print("Run: [cyan]sms-prompt config set twilio.account_sid YOUR_SID[/cyan]")
            console.print("     [cyan]sms-prompt config set twilio.auth_token YOUR_TOKEN[/cyan]")
            console.print("     [cyan]sms-prompt config set twilio.phone_number +1234567890[/cyan]")
            return False
    elif provider == 'africas_talking':
        creds = config.get('africas_talking', {})
        if not creds.get('username') or not creds.get('api_key'):
            console.print("[red]Africa's Talking credentials not configured![/red]")
            console.print("Run: [cyan]sms-prompt config set africas_talking.username YOUR_USERNAME[/cyan]")
            console.print("     [cyan]sms-prompt config set africas_talking.api_key YOUR_API_KEY[/cyan]")
            return False
    return True


def _initialize_gateway(config, provider):
    """Initialize SMS gateway with credentials"""
    try:
        if provider == 'twilio':
            creds = config['twilio']
            return SMSGateway(
                provider='twilio',
                account_sid=creds['account_sid'],
                auth_token=creds['auth_token'],
                phone_number=creds['phone_number']
            )
        elif provider == 'africas_talking':
            creds = config['africas_talking']
            return SMSGateway(
                provider='africas_talking',
                username=creds['username'],
                api_key=creds['api_key'],
                sender_id=creds.get('sender_id')
            )
    except Exception as e:
        console.print(f"[red]Failed to initialize SMS gateway: {str(e)}[/red]")
        return None


def interactive_menu():
    """Show interactive menu with arrow key navigation"""
    while True:
        console.clear()
        console.print("\n[cyan bold]📱 SMS Prompt CLI v1.0.0[/cyan bold]")
        console.print("[dim]A powerful CLI tool for sending customized SMS messages[/dim]")
        console.print("[dim]Use ↑↓ arrow keys to navigate, Enter to select[/dim]\n")
        
        # Show status bar
        config = config_manager.load_config()
        provider = config.get('sms_provider', 'twilio')
        template_engine = TemplateEngine(config_manager.templates_dir)
        templates = template_engine.list_templates()
        
        try:
            db = Database(config_manager.db_file)
            stats = db.get_stats(days=30)
            db.close()
            msg_count = stats['total_sent']
        except Exception:
            msg_count = 0
        
        console.print(f"[dim]Provider: {provider} | Templates: {len(templates)} | Messages (30d): {msg_count}[/dim]\n")
        
        # Main menu
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("📤  Send SMS", value="send"),
                questionary.Choice("📊  Bulk Send (CSV)", value="bulk"),
                questionary.Choice("📝  Manage Templates", value="template"),
                questionary.Choice("⚙️   Configuration", value="config"),
                questionary.Choice("📜  Message History", value="history"),
                questionary.Choice("✅  Validate Phone Number", value="validate"),
                questionary.Choice("ℹ️   Tool Information", value="info"),
                questionary.Separator(),
                questionary.Choice("🚪  Exit", value="exit"),
            ],
            style=custom_style,
            qmark="",
        ).ask()
        
        if choice is None or choice == "exit":
            console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
            break
        elif choice == "send":
            interactive_send()
        elif choice == "bulk":
            interactive_bulk()
        elif choice == "template":
            interactive_template_menu()
        elif choice == "config":
            interactive_config_menu()
        elif choice == "history":
            interactive_history_menu()
        elif choice == "validate":
            interactive_validate()
        elif choice == "info":
            interactive_info()
        
        # Wait for user to press Enter before going back to menu
        if choice != "exit":
            console.print("\n[dim]Press Enter to return to menu...[/dim]")
            input()


def interactive_send():
    """Interactive send SMS flow"""
    console.clear()
    console.print("\n[cyan bold]📤 Send SMS[/cyan bold]\n")
    
    config = config_manager.load_config()
    provider = config['sms_provider']
    
    # Choose message source
    msg_type = questionary.select(
        "How would you like to compose the message?",
        choices=[
            questionary.Choice("Use a template", value="template"),
            questionary.Choice("Write direct message", value="direct"),
            questionary.Choice("← Back", value="back"),
        ],
        style=custom_style,
        qmark="",
    ).ask()
    
    if msg_type == "back" or msg_type is None:
        return
    
    message_content = None
    template_name = None
    variables = {}
    
    if msg_type == "template":
        template_engine = TemplateEngine(config_manager.templates_dir)
        templates = template_engine.list_templates()
        
        if not templates:
            console.print("[yellow]No templates found. Create one first![/yellow]")
            return
        
        template_choices = [questionary.Choice(t['name'], value=t['name']) for t in templates]
        template_choices.append(questionary.Choice("← Back", value="back"))
        
        template_name = questionary.select(
            "Select a template:",
            choices=template_choices,
            style=custom_style,
            qmark="",
        ).ask()
        
        if template_name == "back" or template_name is None:
            return
        
        # Get template variables
        content = template_engine.get_template_content(template_name)
        required_vars = template_engine.extract_variables(content)
        
        console.print(f"\n[cyan]Template: {template_name}[/cyan]")
        console.print(Panel(content, border_style="dim"))
        
        if required_vars:
            console.print(f"\n[yellow]Enter values for variables:[/yellow]")
            for var in required_vars:
                value = questionary.text(
                    f"  {var}:",
                    style=custom_style,
                ).ask()
                if value is None:
                    return
                variables[var] = value
        
        message_content = template_engine.render(template_name, variables)
    else:
        message_content = questionary.text(
            "Enter your message:",
            style=custom_style,
        ).ask()
        
        if not message_content:
            return
    
    # Get recipient
    recipient = questionary.text(
        "Recipient phone number (E.164 format, e.g., +1234567890):",
        style=custom_style,
    ).ask()
    
    if not recipient:
        return
    
    # Show preview
    console.print(f"\n[yellow]📱 Preview:[/yellow]")
    console.print(Panel(message_content, border_style="yellow"))
    console.print(f"[dim]To: {recipient}[/dim]")
    
    # Confirm
    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("✓ Send now", value="send"),
            questionary.Choice("👁 Preview only (don't send)", value="preview"),
            questionary.Choice("✗ Cancel", value="cancel"),
        ],
        style=custom_style,
        qmark="",
    ).ask()
    
    if action == "cancel" or action is None:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if action == "preview":
        console.print("[green]✓ Preview mode - no message sent[/green]")
        return
    
    # Validate provider config
    if not _validate_provider_config(config, provider):
        return
    
    # Send
    gateway = _initialize_gateway(config, provider)
    if not gateway:
        return
    
    console.print(f"\n[blue]📤 Sending to {recipient}...[/blue]")
    
    with console.status("[cyan]Sending...[/cyan]"):
        result = gateway.send(recipient, message_content)
    
    # Log to database
    if config['defaults'].get('save_to_history', True):
        db = Database(config_manager.db_file)
        db.log_sms(recipient, message_content, template_name, variables, result)
        db.close()
    
    if result['success']:
        console.print(f"\n[green bold]✓ SMS sent successfully![/green bold]")
        console.print(f"[dim]Message SID: {result.get('message_sid', 'N/A')}[/dim]")
    else:
        console.print(f"\n[red bold]✗ Failed to send SMS[/red bold]")
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")


def interactive_bulk():
    """Interactive bulk send flow"""
    console.clear()
    console.print("\n[cyan bold]📊 Bulk Send SMS[/cyan bold]\n")
    
    config = config_manager.load_config()
    provider = config['sms_provider']
    
    # Select template
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    
    if not templates:
        console.print("[yellow]No templates found. Create one first![/yellow]")
        return
    
    template_choices = [questionary.Choice(t['name'], value=t['name']) for t in templates]
    template_choices.append(questionary.Choice("← Back", value="back"))
    
    template_name = questionary.select(
        "Select a template:",
        choices=template_choices,
        style=custom_style,
        qmark="",
    ).ask()
    
    if template_name == "back" or template_name is None:
        return
    
    # Get CSV file path
    csv_path = questionary.path(
        "Enter path to CSV file:",
        style=custom_style,
    ).ask()
    
    if not csv_path:
        return
    
    # Read CSV and preview
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            recipients = list(reader)
        
        console.print(f"\n[cyan]Loaded {len(recipients)} recipients[/cyan]")
        
        # Preview first few
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Phone", style="cyan")
        table.add_column("Preview", style="white")
        
        for i, recipient in enumerate(recipients[:3], 1):
            phone = recipient.get('phone', 'N/A')
            variables = {k: v for k, v in recipient.items() if k != 'phone'}
            rendered = template_engine.render(template_name, variables)
            preview_msg = rendered[:60] + "..." if len(rendered) > 60 else rendered
            table.add_row(str(i), phone, preview_msg)
        
        console.print(table)
        
        if len(recipients) > 3:
            console.print(f"[dim]... and {len(recipients) - 3} more[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error reading CSV: {str(e)}[/red]")
        return
    
    # Confirm
    if not questionary.confirm(
        f"Send to {len(recipients)} recipients?",
        style=custom_style,
    ).ask():
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if not _validate_provider_config(config, provider):
        return
    
    gateway = _initialize_gateway(config, provider)
    if not gateway:
        return
    
    # Send with progress
    db = Database(config_manager.db_file)
    successful = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Sending...", total=len(recipients))
        
        for recipient in recipients:
            phone = recipient.get('phone')
            variables = {k: v for k, v in recipient.items() if k != 'phone'}
            rendered = template_engine.render(template_name, variables)
            result = gateway.send(phone, rendered)
            
            db.log_sms(phone, rendered, template_name, variables, result)
            
            if result['success']:
                successful += 1
            else:
                failed += 1
            
            progress.update(task, advance=1, description=f"[cyan]✓ {successful} | ✗ {failed}")
    
    db.close()
    
    console.print(f"\n[green bold]✓ Bulk send complete![/green bold]")
    console.print(f"[green]Successful: {successful}[/green]")
    if failed > 0:
        console.print(f"[red]Failed: {failed}[/red]")


def interactive_template_menu():
    """Interactive template management menu"""
    while True:
        console.clear()
        console.print("\n[cyan bold]📝 Template Management[/cyan bold]\n")
        
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("📋  List templates", value="list"),
                questionary.Choice("👁   View template", value="show"),
                questionary.Choice("➕  Create template", value="create"),
                questionary.Choice("🧪  Test template", value="test"),
                questionary.Choice("🗑️   Delete template", value="delete"),
                questionary.Separator(),
                questionary.Choice("← Back", value="back"),
            ],
            style=custom_style,
            qmark="",
        ).ask()
        
        if choice == "back" or choice is None:
            return
        elif choice == "list":
            template_engine = TemplateEngine(config_manager.templates_dir)
            templates = template_engine.list_templates()
            
            if not templates:
                console.print("[yellow]No templates found[/yellow]")
            else:
                table = Table(title="📋 Templates", show_header=True, header_style="bold cyan")
                table.add_column("Name", style="cyan")
                table.add_column("Variables", style="yellow")
                table.add_column("Length", justify="right")
                
                for t in templates:
                    content = template_engine.get_template_content(t['name'])
                    variables = template_engine.extract_variables(content)
                    table.add_row(t['name'], ', '.join(variables) or '-', str(len(content)))
                
                console.print(table)
        elif choice == "show":
            _interactive_template_show()
        elif choice == "create":
            _interactive_template_create()
        elif choice == "test":
            _interactive_template_test()
        elif choice == "delete":
            _interactive_template_delete()
        
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()


def _interactive_template_show():
    """Show template content interactively"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return
    
    choices = [questionary.Choice(t['name'], value=t['name']) for t in templates]
    choices.append(questionary.Choice("← Back", value="back"))
    
    name = questionary.select("Select template:", choices=choices, style=custom_style, qmark="").ask()
    
    if name == "back" or name is None:
        return
    
    content = template_engine.get_template_content(name)
    variables = template_engine.extract_variables(content)
    
    console.print(f"\n[cyan bold]📝 {name}[/cyan bold]")
    console.print(f"[yellow]Variables:[/yellow] {', '.join(variables) if variables else 'None'}")
    console.print(Panel(content, border_style="cyan"))


def _interactive_template_create():
    """Create template interactively"""
    name = questionary.text("Template name:", style=custom_style).ask()
    if not name:
        return
    
    console.print("[dim]Enter template content (use {{variable}} for variables):[/dim]")
    content = questionary.text("Content:", style=custom_style, multiline=True).ask()
    
    if not content:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    template_engine = TemplateEngine(config_manager.templates_dir)
    template_path = template_engine.create_template(name, content)
    variables = template_engine.extract_variables(content)
    
    console.print(f"\n[green]✓ Template '{name}' created![/green]")
    console.print(f"[yellow]Variables: {', '.join(variables) if variables else 'None'}[/yellow]")


def _interactive_template_test():
    """Test template interactively"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return
    
    choices = [questionary.Choice(t['name'], value=t['name']) for t in templates]
    name = questionary.select("Select template:", choices=choices, style=custom_style, qmark="").ask()
    
    if not name:
        return
    
    content = template_engine.get_template_content(name)
    variables = template_engine.extract_variables(content)
    
    console.print(f"\n[dim]Raw template:[/dim]")
    console.print(Panel(content, border_style="dim"))
    
    values = {}
    if variables:
        console.print(f"\n[yellow]Enter test values:[/yellow]")
        for var in variables:
            val = questionary.text(f"  {var}:", style=custom_style).ask()
            values[var] = val or f"[{var}]"
    
    rendered = template_engine.render(name, values)
    console.print(f"\n[green]Rendered output:[/green]")
    console.print(Panel(rendered, border_style="green"))


def _interactive_template_delete():
    """Delete template interactively"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    
    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return
    
    choices = [questionary.Choice(t['name'], value=t['name']) for t in templates]
    name = questionary.select("Select template to delete:", choices=choices, style=custom_style, qmark="").ask()
    
    if not name:
        return
    
    if questionary.confirm(f"Delete template '{name}'?", default=False, style=custom_style).ask():
        template_engine.delete_template(name)
        console.print(f"[green]✓ Template '{name}' deleted[/green]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


def interactive_config_menu():
    """Interactive configuration menu"""
    while True:
        console.clear()
        console.print("\n[cyan bold]⚙️ Configuration[/cyan bold]\n")
        
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("👁   View configuration", value="show"),
                questionary.Choice("✏️   Set Twilio credentials", value="twilio"),
                questionary.Choice("✏️   Set Africa's Talking credentials", value="africas_talking"),
                questionary.Choice("🔄  Switch SMS provider", value="provider"),
                questionary.Choice("🔧  Edit other settings", value="other"),
                questionary.Separator(),
                questionary.Choice("← Back", value="back"),
            ],
            style=custom_style,
            qmark="",
        ).ask()
        
        if choice == "back" or choice is None:
            return
        elif choice == "show":
            cfg = config_manager.load_config()
            console.print(f"\n[cyan]Config file:[/cyan] {config_manager.config_file}\n")
            
            def print_config(data, indent=0):
                for key, value in data.items():
                    if isinstance(value, dict):
                        console.print("  " * indent + f"[yellow]{key}:[/yellow]")
                        print_config(value, indent + 1)
                    else:
                        # Mask sensitive values
                        if any(s in key.lower() for s in ['token', 'key', 'sid']):
                            if value and len(str(value)) > 4:
                                value = str(value)[:4] + '*' * 8
                        console.print("  " * indent + f"[cyan]{key}:[/cyan] {value}")
            
            print_config(cfg)
        elif choice == "twilio":
            console.print("\n[cyan]Configure Twilio:[/cyan]")
            account_sid = questionary.text("Account SID:", style=custom_style).ask()
            auth_token = questionary.password("Auth Token:", style=custom_style).ask()
            phone_number = questionary.text("Phone Number (e.g., +1234567890):", style=custom_style).ask()
            
            if account_sid:
                config_manager.set_value('twilio.account_sid', account_sid)
            if auth_token:
                config_manager.set_value('twilio.auth_token', auth_token)
            if phone_number:
                config_manager.set_value('twilio.phone_number', phone_number)
            
            console.print("[green]✓ Twilio credentials updated[/green]")
        elif choice == "africas_talking":
            console.print("\n[cyan]Configure Africa's Talking:[/cyan]")
            username = questionary.text("Username:", style=custom_style).ask()
            api_key = questionary.password("API Key:", style=custom_style).ask()
            sender_id = questionary.text("Sender ID (optional):", style=custom_style).ask()
            
            if username:
                config_manager.set_value('africas_talking.username', username)
            if api_key:
                config_manager.set_value('africas_talking.api_key', api_key)
            if sender_id:
                config_manager.set_value('africas_talking.sender_id', sender_id)
            
            console.print("[green]✓ Africa's Talking credentials updated[/green]")
        elif choice == "provider":
            provider = questionary.select(
                "Select SMS provider:",
                choices=["twilio", "africas_talking"],
                style=custom_style,
                qmark="",
            ).ask()
            
            if provider:
                config_manager.set_value('sms_provider', provider)
                console.print(f"[green]✓ Provider set to {provider}[/green]")
        elif choice == "other":
            key = questionary.text("Setting key (e.g., defaults.confirm_before_send):", style=custom_style).ask()
            value = questionary.text("Value:", style=custom_style).ask()
            
            if key and value:
                # Convert types
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                
                config_manager.set_value(key, value)
                console.print(f"[green]✓ Set {key} = {value}[/green]")
        
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()


def interactive_history_menu():
    """Interactive history menu"""
    while True:
        console.clear()
        console.print("\n[cyan bold]📜 Message History[/cyan bold]\n")
        
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("📋  View recent messages", value="list"),
                questionary.Choice("📊  View statistics", value="stats"),
                questionary.Choice("📤  Export history", value="export"),
                questionary.Choice("🗑️   Clear old messages", value="clear"),
                questionary.Separator(),
                questionary.Choice("← Back", value="back"),
            ],
            style=custom_style,
            qmark="",
        ).ask()
        
        if choice == "back" or choice is None:
            return
        elif choice == "list":
            db = Database(config_manager.db_file)
            logs = db.get_history(limit=20)
            db.close()
            
            if not logs:
                console.print("[yellow]No messages found[/yellow]")
            else:
                table = Table(title="📜 Recent Messages", show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim", width=5)
                table.add_column("Recipient", style="cyan")
                table.add_column("Template", style="yellow")
                table.add_column("Status", justify="center")
                table.add_column("Sent At", style="dim")
                
                for log in logs:
                    status = "[green]✓[/green]" if log.success else "[red]✗[/red]"
                    sent_at = log.sent_at.strftime("%Y-%m-%d %H:%M") if log.sent_at else "-"
                    table.add_row(str(log.id), log.recipient, log.template_name or "-", status, sent_at)
                
                console.print(table)
        elif choice == "stats":
            db = Database(config_manager.db_file)
            stats = db.get_stats(days=30)
            db.close()
            
            console.print(f"\n[cyan bold]📊 Statistics (Last 30 days)[/cyan bold]\n")
            console.print(f"[cyan]Total Sent:[/cyan] {stats['total_sent']}")
            console.print(f"[green]Successful:[/green] {stats['successful']}")
            console.print(f"[red]Failed:[/red] {stats['failed']}")
            console.print(f"[cyan]Success Rate:[/cyan] {stats['success_rate']:.1f}%")
            console.print(f"[cyan]Total Cost:[/cyan] ${stats['total_cost']:.2f}")
        elif choice == "export":
            fmt = questionary.select("Export format:", choices=["csv", "json"], style=custom_style, qmark="").ask()
            output = questionary.path("Output file path:", style=custom_style).ask()
            
            if fmt and output:
                db = Database(config_manager.db_file)
                if fmt == 'csv':
                    data = db.export_logs(format='csv', limit=1000)
                    with open(output, 'w', encoding='utf-8') as f:
                        f.write(data)
                else:
                    data = db.export_logs(format='dict', limit=1000)
                    with open(output, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, default=str)
                db.close()
                console.print(f"[green]✓ Exported to {output}[/green]")
        elif choice == "clear":
            days = questionary.text("Delete messages older than (days):", default="90", style=custom_style).ask()
            if days and questionary.confirm(f"Delete messages older than {days} days?", default=False, style=custom_style).ask():
                db = Database(config_manager.db_file)
                deleted = db.delete_old_logs(days=int(days))
                db.close()
                console.print(f"[green]✓ Deleted {deleted} old messages[/green]")
        
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()


def interactive_validate():
    """Interactive phone number validation"""
    console.clear()
    console.print("\n[cyan bold]✅ Validate Phone Number[/cyan bold]\n")
    
    phone = questionary.text(
        "Enter phone number to validate:",
        style=custom_style,
    ).ask()
    
    if not phone:
        return
    
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone, None)
        is_valid = phonenumbers.is_valid_number(parsed)
        
        if is_valid:
            formatted_e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            formatted_intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            country = phonenumbers.region_code_for_number(parsed)
            
            console.print(f"\n[green]✓ Valid phone number[/green]")
            console.print(f"[cyan]E.164 Format:[/cyan] {formatted_e164}")
            console.print(f"[cyan]International:[/cyan] {formatted_intl}")
            console.print(f"[cyan]Country:[/cyan] {country}")
        else:
            console.print(f"\n[red]✗ Invalid phone number[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


def interactive_info():
    """Show tool information"""
    console.clear()
    console.print("\n[cyan bold]ℹ️ Tool Information[/cyan bold]\n")
    
    console.print(f"[cyan]Version:[/cyan] 1.0.0")
    console.print(f"[cyan]Config Directory:[/cyan] {config_manager.config_dir}")
    console.print(f"[cyan]Config File:[/cyan] {config_manager.config_file}")
    console.print(f"[cyan]Templates Directory:[/cyan] {config_manager.templates_dir}")
    console.print(f"[cyan]Database File:[/cyan] {config_manager.db_file}")
    
    config = config_manager.load_config()
    provider = config.get('sms_provider', 'twilio')
    console.print(f"\n[cyan]Active Provider:[/cyan] {provider}")
    
    if _validate_provider_config(config, provider):
        console.print("[green]✓ Provider configured[/green]")
    
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    console.print(f"\n[cyan]Available Templates:[/cyan] {len(templates)}")
    
    try:
        db = Database(config_manager.db_file)
        stats = db.get_stats(days=30)
        db.close()
        console.print(f"[cyan]Messages (Last 30 days):[/cyan] {stats['total_sent']}")
    except Exception:
        pass


@click.group(invoke_without_command=True)
@click.version_option(version='1.0.0', prog_name='sms-prompt')
@click.pass_context
def cli(ctx):
    """SMS Prompt CLI - Send customized SMS messages at scale 📱
    
    \b
    A powerful command-line tool for:
    • Sending personalized SMS using templates
    • Bulk messaging with CSV data
    • Template management
    • Message history and analytics
    
    Get started:
      sms-prompt config set twilio.account_sid YOUR_SID
      sms-prompt template list
      sms-prompt send --template welcome --to +1234567890 -v name=John
    """
    if ctx.invoked_subcommand is None:
        # Show interactive menu
        interactive_menu()


# =============================================================================
# SEND COMMANDS
# =============================================================================

@cli.command()
@click.option('--template', '-t', help='Template name to use')
@click.option('--message', '-m', help='Direct message (no template)')
@click.option('--to', required=True, help='Recipient phone number (E.164 format)')
@click.option('--vars', '-v', multiple=True, help='Variables as key=value pairs')
@click.option('--preview', is_flag=True, help='Preview without sending')
@click.option('--no-confirm', is_flag=True, help='Skip confirmation prompt')
def send(template, message, to, vars, preview, no_confirm):
    """Send SMS to a single recipient
    
    \b
    Examples:
      sms-prompt send --template welcome --to +1234567890 -v name=John -v company=Acme
      sms-prompt send --message "Hello World!" --to +1234567890
      sms-prompt send --template promo --to +1234567890 -v name=Jane -v discount=20 --preview
    """
    
    # Load config
    config = config_manager.load_config()
    
    # Validate SMS provider configuration (skip for preview mode)
    provider = config['sms_provider']
    if not preview and not _validate_provider_config(config, provider):
        return
    
    # Parse variables
    variables = {}
    for var in vars:
        try:
            key, value = var.split('=', 1)
            variables[key.strip()] = value.strip()
        except ValueError:
            console.print(f"[red]Invalid variable format: {var}. Use key=value[/red]")
            return
    
    # Get message content
    if template:
        # Use template
        template_engine = TemplateEngine(config_manager.templates_dir)
        try:
            preview_data = template_engine.preview_template(template, variables)
            message_content = preview_data['rendered']
            
            # Check for missing variables
            validation = template_engine.validate_template(template, variables)
            if not validation['valid']:
                console.print(f"[red]Missing variables: {', '.join(validation['missing_variables'])}[/red]")
                console.print(f"[dim]Required: {', '.join(validation['required_variables'])}[/dim]")
                return
            
            # Show template info
            console.print(f"\n[cyan]📝 Template:[/cyan] {template}")
            console.print(f"[cyan]Variables:[/cyan] {', '.join(preview_data['variables_used']) if preview_data['variables_used'] else 'None'}")
            
        except FileNotFoundError:
            console.print(f"[red]Template '{template}' not found. Use 'sms-prompt template list' to see available templates.[/red]")
            return
        except Exception as e:
            console.print(f"[red]Error rendering template: {str(e)}[/red]")
            return
    elif message:
        # Direct message
        message_content = message
        template = None
    else:
        console.print("[red]Either --template or --message must be provided[/red]")
        return
    
    # Show preview
    length = len(message_content)
    has_unicode = any(ord(char) > 127 for char in message_content)
    chars_per_segment = 70 if has_unicode else 160
    segments = (length // chars_per_segment) + (1 if length % chars_per_segment > 0 else 0)
    
    console.print(f"\n[yellow]📱 Preview:[/yellow]")
    console.print(Panel(message_content, border_style="yellow"))
    console.print(f"[dim]Length: {length} chars | Segments: {segments} | Estimated cost: ~${segments * 0.0079:.4f}[/dim]")
    if has_unicode:
        console.print("[dim]⚠️  Message contains Unicode characters (70 chars/segment)[/dim]")
    
    if preview:
        console.print("\n[green]✓ Preview mode - no message sent[/green]")
        return
    
    # Confirm sending
    if not no_confirm and config['defaults'].get('confirm_before_send', True):
        if not Confirm.ask(f"\n[yellow]Send SMS to {to}?[/yellow]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Initialize SMS gateway
    gateway = _initialize_gateway(config, provider)
    if not gateway:
        return
    
    # Send SMS
    console.print(f"\n[blue]📤 Sending to {to}...[/blue]")
    
    with console.status("[cyan]Sending...[/cyan]"):
        result = gateway.send(to, message_content)
    
    # Log to database
    if config['defaults'].get('save_to_history', True):
        db = Database(config_manager.db_file)
        db.log_sms(to, message_content, template, variables, result)
        db.close()
    
    # Show result
    if result['success']:
        console.print(f"\n[green bold]✓ SMS sent successfully![/green bold]")
        console.print(f"[dim]Message SID: {result.get('message_sid', 'N/A')}[/dim]")
        console.print(f"[dim]Status: {result.get('status', 'N/A')}[/dim]")
        if result.get('price'):
            console.print(f"[dim]Cost: {result.get('price')} {result.get('price_unit', 'USD')}[/dim]")
    else:
        console.print(f"\n[red bold]✗ Failed to send SMS[/red bold]")
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
        if result.get('error_code'):
            console.print(f"[red]Error Code: {result.get('error_code')}[/red]")


@cli.command()
@click.option('--template', '-t', required=True, help='Template name to use')
@click.option('--file', '-f', required=True, type=click.Path(exists=True), help='CSV file with recipients')
@click.option('--preview', is_flag=True, help='Preview first 5 without sending')
@click.option('--no-confirm', is_flag=True, help='Skip confirmation prompt')
@click.option('--rate-limit', '-r', default=10, help='Messages per second (default: 10)')
def bulk(template, file, preview, no_confirm, rate_limit):
    """Send SMS to multiple recipients from CSV file
    
    \b
    CSV format: phone,name,var1,var2,...
    First row should be headers matching template variables.
    
    \b
    Example CSV:
      phone,name,discount,code
      +1234567890,John,20,SAVE20
      +0987654321,Jane,15,SAVE15
    
    \b
    Examples:
      sms-prompt bulk --template promo --file contacts.csv
      sms-prompt bulk --template promo --file contacts.csv --preview
      sms-prompt bulk --template welcome --file users.csv --rate-limit 5
    """
    
    config = config_manager.load_config()
    provider = config['sms_provider']
    
    if not preview and not _validate_provider_config(config, provider):
        return
    
    # Read CSV
    try:
        with open(file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            recipients = list(reader)
    except Exception as e:
        console.print(f"[red]Error reading CSV: {str(e)}[/red]")
        return
    
    if not recipients:
        console.print("[red]No recipients found in CSV[/red]")
        return
    
    # Validate phone column exists
    if 'phone' not in recipients[0]:
        console.print("[red]CSV must have a 'phone' column[/red]")
        return
    
    console.print(f"\n[cyan]📊 Loaded {len(recipients)} recipients from {file}[/cyan]")
    
    # Initialize template engine
    template_engine = TemplateEngine(config_manager.templates_dir)
    
    # Validate template exists
    try:
        template_content = template_engine.get_template_content(template)
        required_vars = template_engine.extract_variables(template_content)
    except FileNotFoundError:
        console.print(f"[red]Template '{template}' not found[/red]")
        return
    
    # Check if CSV has all required variables
    csv_columns = set(recipients[0].keys()) - {'phone'}
    missing_vars = set(required_vars) - csv_columns
    if missing_vars:
        console.print(f"[yellow]⚠️  Warning: CSV may be missing columns for: {', '.join(missing_vars)}[/yellow]")
    
    # Preview mode
    if preview:
        console.print("\n[yellow]📱 Preview (first 5 recipients):[/yellow]")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Phone", style="cyan")
        table.add_column("Message Preview", style="white")
        
        for i, recipient in enumerate(recipients[:5], 1):
            phone = recipient.get('phone')
            variables = {k: v for k, v in recipient.items() if k != 'phone'}
            
            try:
                rendered = template_engine.render(template, variables)
                preview_msg = rendered[:80] + "..." if len(rendered) > 80 else rendered
                table.add_row(str(i), phone, preview_msg)
            except Exception as e:
                table.add_row(str(i), phone, f"[red]Error: {str(e)}[/red]")
        
        console.print(table)
        
        if len(recipients) > 5:
            console.print(f"\n[dim]... and {len(recipients) - 5} more recipients[/dim]")
        
        console.print("\n[green]✓ Preview mode - no messages sent[/green]")
        return
    
    # Estimate cost
    sample_variables = {k: v for k, v in recipients[0].items() if k != 'phone'}
    try:
        sample_rendered = template_engine.render(template, sample_variables)
        has_unicode = any(ord(char) > 127 for char in sample_rendered)
        chars_per_segment = 70 if has_unicode else 160
        segments = (len(sample_rendered) // chars_per_segment) + 1
        total_cost = len(recipients) * segments * 0.0079
        
        console.print(f"\n[yellow]💰 Estimated cost: ${total_cost:.2f} for {len(recipients)} recipients ({segments} segment(s) each)[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not estimate cost: {str(e)}[/yellow]")
    
    # Confirm
    if not no_confirm:
        if not Confirm.ask(f"\n[yellow]Send {len(recipients)} SMS messages?[/yellow]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Initialize gateway
    gateway = _initialize_gateway(config, provider)
    if not gateway:
        return
    
    # Send to all recipients
    db = Database(config_manager.db_file)
    successful = 0
    failed = 0
    errors = []
    
    console.print(f"\n[blue]📤 Sending to {len(recipients)} recipients...[/blue]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Sending messages...", total=len(recipients))
        
        delay = 1.0 / rate_limit if rate_limit > 0 else 0
        
        for i, recipient in enumerate(recipients, 1):
            phone = recipient.get('phone')
            variables = {k: v for k, v in recipient.items() if k != 'phone'}
            
            try:
                rendered = template_engine.render(template, variables)
                result = gateway.send(phone, rendered)
                
                # Log
                db.log_sms(phone, rendered, template, variables, result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    errors.append({'phone': phone, 'error': result.get('error')})
                
                progress.update(task, advance=1, description=f"[cyan]Sent {i}/{len(recipients)} (✓ {successful} | ✗ {failed})")
                
                # Rate limiting
                if delay > 0 and i < len(recipients):
                    import time
                    time.sleep(delay)
                    
            except Exception as e:
                console.print(f"[red]Error for {phone}: {str(e)}[/red]")
                failed += 1
                errors.append({'phone': phone, 'error': str(e)})
                progress.update(task, advance=1)
    
    db.close()
    
    # Summary
    console.print(f"\n[bold]{'=' * 50}[/bold]")
    console.print(f"[green bold]✓ Bulk send complete![/green bold]")
    console.print(f"[green]Successful: {successful}[/green]")
    if failed > 0:
        console.print(f"[red]Failed: {failed}[/red]")
        
        if errors and Confirm.ask("\n[yellow]Show failed recipients?[/yellow]"):
            table = Table(title="Failed Messages", show_header=True, header_style="bold red")
            table.add_column("Phone", style="cyan")
            table.add_column("Error", style="red")
            
            for error in errors[:20]:
                table.add_row(error['phone'], error['error'][:50] if error['error'] else 'Unknown')
            
            console.print(table)
            
            if len(errors) > 20:
                console.print(f"[dim]... and {len(errors) - 20} more errors[/dim]")


# =============================================================================
# TEMPLATE COMMANDS
# =============================================================================

@cli.group()
def template():
    """Manage SMS templates
    
    \b
    Templates use Jinja2 syntax: {{variable}}
    
    Example template:
      Hi {{name}}! Your order #{{order_id}} is ready for pickup.
    """
    pass


@template.command('list')
def template_list():
    """List all available templates"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    
    if not templates:
        console.print("[yellow]No templates found. Create one with 'sms-prompt template create'[/yellow]")
        console.print(f"[dim]Templates directory: {config_manager.templates_dir}[/dim]")
        return
    
    table = Table(title="📋 Available Templates", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("File", style="dim")
    table.add_column("Variables", style="yellow")
    table.add_column("Length", style="dim", justify="right")
    
    for t in templates:
        content = template_engine.get_template_content(t['name'])
        variables = template_engine.extract_variables(content)
        table.add_row(
            t['name'],
            t['file'],
            ', '.join(variables) if variables else '-',
            str(len(content))
        )
    
    console.print(table)
    console.print(f"\n[dim]Templates directory: {config_manager.templates_dir}[/dim]")


@template.command('show')
@click.argument('name')
def template_show(name):
    """Show template content and details"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    
    try:
        content = template_engine.get_template_content(name)
        variables = template_engine.extract_variables(content)
        
        # Calculate message info
        length = len(content)
        has_unicode = any(ord(char) > 127 for char in content)
        chars_per_segment = 70 if has_unicode else 160
        segments = (length // chars_per_segment) + (1 if length % chars_per_segment > 0 else 0)
        
        console.print(f"\n[cyan bold]📝 Template: {name}[/cyan bold]")
        console.print(f"[yellow]Variables:[/yellow] {', '.join(variables) if variables else 'None'}")
        console.print(f"[dim]Length: {length} chars | Estimated segments: {segments}[/dim]")
        if has_unicode:
            console.print("[dim]Contains Unicode characters[/dim]")
        
        console.print("\n[yellow]Content:[/yellow]")
        console.print(Panel(content, border_style="cyan"))
        
        # Show example usage
        if variables:
            example_vars = ' '.join([f'-v {v}=value' for v in variables])
            console.print(f"\n[dim]Example usage:[/dim]")
            console.print(f"[cyan]sms-prompt send --template {name} --to +1234567890 {example_vars}[/cyan]")
        
    except FileNotFoundError:
        console.print(f"[red]Template '{name}' not found[/red]")
        console.print(f"[dim]Use 'sms-prompt template list' to see available templates[/dim]")


@template.command('create')
@click.option('--name', '-n', required=True, help='Template name (without .txt extension)')
@click.option('--content', '-c', help='Template content')
@click.option('--file', '-f', type=click.Path(exists=True), help='Load content from file')
@click.option('--interactive', '-i', is_flag=True, help='Create interactively')
def template_create(name, content, file, interactive):
    """Create a new template
    
    \b
    Examples:
      sms-prompt template create -n greeting -c "Hello {{name}}!"
      sms-prompt template create -n welcome --file welcome_template.txt
      sms-prompt template create -n notification --interactive
    """
    template_engine = TemplateEngine(config_manager.templates_dir)
    
    # Check if template already exists
    existing = [t['name'] for t in template_engine.list_templates()]
    if name in existing:
        if not Confirm.ask(f"[yellow]Template '{name}' already exists. Overwrite?[/yellow]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Get content
    if interactive:
        console.print("\n[cyan]Enter template content (use {{variable}} for variables):[/cyan]")
        console.print("[dim]Press Enter twice when done[/dim]\n")
        lines = []
        empty_count = 0
        try:
            while True:
                line = input()
                if line == '':
                    empty_count += 1
                    if empty_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_count = 0
                    lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        content = '\n'.join(lines).strip()
    elif file:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif not content:
        console.print("[red]Provide content via --content, --file, or --interactive[/red]")
        return
    
    if not content:
        console.print("[red]Template content cannot be empty[/red]")
        return
    
    # Create template
    try:
        template_path = template_engine.create_template(name, content)
        variables = template_engine.extract_variables(content)
        
        console.print(f"\n[green]✓ Template '{name}' created successfully![/green]")
        console.print(f"[dim]Location: {template_path}[/dim]")
        console.print(f"[yellow]Variables detected: {', '.join(variables) if variables else 'None'}[/yellow]")
        
        # Show preview
        console.print("\n[cyan]Preview:[/cyan]")
        console.print(Panel(content, border_style="cyan"))
        
    except Exception as e:
        console.print(f"[red]Error creating template: {str(e)}[/red]")


@template.command('delete')
@click.argument('name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def template_delete(name, yes):
    """Delete a template"""
    template_engine = TemplateEngine(config_manager.templates_dir)
    
    # Check if template exists
    try:
        content = template_engine.get_template_content(name)
    except FileNotFoundError:
        console.print(f"[red]Template '{name}' not found[/red]")
        return
    
    # Show template content
    console.print(f"\n[yellow]Template to delete: {name}[/yellow]")
    console.print(Panel(content, border_style="red"))
    
    # Confirm deletion
    if not yes:
        if not Confirm.ask(f"[red]Are you sure you want to delete template '{name}'?[/red]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Delete template
    if template_engine.delete_template(name):
        console.print(f"[green]✓ Template '{name}' deleted[/green]")
    else:
        console.print(f"[red]Failed to delete template '{name}'[/red]")


@template.command('test')
@click.argument('name')
@click.option('--vars', '-v', multiple=True, help='Variables as key=value pairs')
def template_test(name, vars):
    """Test a template with sample variables
    
    \b
    Example:
      sms-prompt template test welcome -v name=John -v company=Acme
    """
    template_engine = TemplateEngine(config_manager.templates_dir)
    
    # Parse variables
    variables = {}
    for var in vars:
        try:
            key, value = var.split('=', 1)
            variables[key.strip()] = value.strip()
        except ValueError:
            console.print(f"[red]Invalid variable format: {var}. Use key=value[/red]")
            return
    
    try:
        preview_data = template_engine.preview_template(name, variables)
        
        console.print(f"\n[cyan bold]📝 Template Test: {name}[/cyan bold]")
        
        # Show validation
        validation = template_engine.validate_template(name, variables)
        if not validation['valid']:
            console.print(f"\n[red]⚠️  Missing variables: {', '.join(validation['missing_variables'])}[/red]")
        
        console.print(f"\n[yellow]Raw Template:[/yellow]")
        console.print(Panel(preview_data['raw'], border_style="dim"))
        
        console.print(f"\n[green]Rendered Output:[/green]")
        console.print(Panel(preview_data['rendered'], border_style="green"))
        
        # Stats
        console.print(f"\n[dim]Length: {preview_data['length']} chars[/dim]")
        console.print(f"[dim]SMS Segments: {preview_data['segments']}[/dim]")
        console.print(f"[dim]Has Unicode: {'Yes' if preview_data['has_unicode'] else 'No'}[/dim]")
        console.print(f"[dim]Variables Used: {', '.join(preview_data['variables_used'])}[/dim]")
        console.print(f"[dim]Variables Provided: {', '.join(preview_data['variables_provided'])}[/dim]")
        
    except FileNotFoundError:
        console.print(f"[red]Template '{name}' not found[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


# =============================================================================
# CONFIG COMMANDS
# =============================================================================

@cli.group()
def config():
    """Manage configuration settings
    
    \b
    Configuration is stored in ~/.sms-prompt/config.yaml
    """
    pass


@config.command('show')
@click.option('--reveal', is_flag=True, help='Show sensitive values (tokens, keys)')
def config_show(reveal):
    """Show current configuration"""
    cfg = config_manager.load_config()
    
    console.print("\n[cyan bold]⚙️  SMS Prompt Configuration[/cyan bold]")
    console.print(f"[dim]Config file: {config_manager.config_file}[/dim]\n")
    
    # Mask sensitive values unless --reveal is used
    def mask_value(value, key):
        sensitive_keys = ['auth_token', 'api_key', 'account_sid']
        if not reveal and any(k in key.lower() for k in sensitive_keys):
            if value and len(str(value)) > 4:
                return str(value)[:4] + '*' * (len(str(value)) - 4)
        return value
    
    def print_config(cfg, prefix=''):
        for key, value in cfg.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                console.print(f"[yellow]{key}:[/yellow]")
                print_config(value, full_key)
            else:
                masked = mask_value(value, full_key)
                console.print(f"  [cyan]{key}:[/cyan] {masked}")
    
    print_config(cfg)
    
    if not reveal:
        console.print("\n[dim]Use --reveal to show sensitive values[/dim]")


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value
    
    \b
    Use dot notation for nested values.
    
    Examples:
      sms-prompt config set twilio.account_sid YOUR_SID
      sms-prompt config set twilio.auth_token YOUR_TOKEN
      sms-prompt config set twilio.phone_number +1234567890
      sms-prompt config set sms_provider twilio
      sms-prompt config set defaults.confirm_before_send false
    """
    # Convert string values to appropriate types
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif value.isdigit():
        value = int(value)
    
    try:
        config_manager.set_value(key, value)
        console.print(f"[green]✓ Set {key} = {value}[/green]")
    except Exception as e:
        console.print(f"[red]Error setting configuration: {str(e)}[/red]")


@config.command('get')
@click.argument('key')
def config_get(key):
    """Get a configuration value
    
    \b
    Example:
      sms-prompt config get twilio.account_sid
    """
    value = config_manager.get_value(key)
    if value is not None:
        console.print(f"[cyan]{key}:[/cyan] {value}")
    else:
        console.print(f"[yellow]Key '{key}' not found[/yellow]")


@config.command('init')
def config_init():
    """Initialize/reset configuration to defaults"""
    if Confirm.ask("[yellow]Reset configuration to defaults? This will overwrite current settings.[/yellow]"):
        import os
        if config_manager.config_file.exists():
            os.remove(config_manager.config_file)
        
        # Re-initialize
        config_manager._ensure_config_exists()
        console.print("[green]✓ Configuration reset to defaults[/green]")
        console.print(f"[dim]Config file: {config_manager.config_file}[/dim]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


# =============================================================================
# HISTORY COMMANDS
# =============================================================================

@cli.group()
def history():
    """View message history and analytics"""
    pass


@history.command('list')
@click.option('--limit', '-l', default=20, help='Number of messages to show (default: 20)')
@click.option('--recipient', '-r', help='Filter by recipient phone number')
@click.option('--template', '-t', help='Filter by template name')
@click.option('--success', is_flag=True, help='Show only successful messages')
@click.option('--failed', is_flag=True, help='Show only failed messages')
def history_list(limit, recipient, template, success, failed):
    """List recent messages"""
    db = Database(config_manager.db_file)
    
    success_filter = None
    if success:
        success_filter = True
    elif failed:
        success_filter = False
    
    logs = db.get_history(
        limit=limit,
        recipient=recipient,
        template=template,
        success_only=success_filter
    )
    db.close()
    
    if not logs:
        console.print("[yellow]No messages found[/yellow]")
        return
    
    table = Table(title="📜 Message History", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Recipient", style="cyan")
    table.add_column("Template", style="yellow")
    table.add_column("Status", justify="center")
    table.add_column("Segments", justify="right")
    table.add_column("Sent At", style="dim")
    
    for log in logs:
        status = "[green]✓[/green]" if log.success else "[red]✗[/red]"
        sent_at = log.sent_at.strftime("%Y-%m-%d %H:%M") if log.sent_at else "-"
        table.add_row(
            str(log.id),
            log.recipient,
            log.template_name or "-",
            status,
            str(log.segments) if log.segments else "-",
            sent_at
        )
    
    console.print(table)


@history.command('show')
@click.argument('message_id', type=int)
def history_show(message_id):
    """Show details of a specific message"""
    db = Database(config_manager.db_file)
    logs = db.get_history(limit=1000)  # Get all to find by ID
    
    log = None
    for l in logs:
        if l.id == message_id:
            log = l
            break
    
    db.close()
    
    if not log:
        console.print(f"[red]Message ID {message_id} not found[/red]")
        return
    
    data = log.to_dict()
    
    console.print(f"\n[cyan bold]📧 Message #{message_id}[/cyan bold]")
    console.print(f"[{'green' if data['success'] else 'red'}]Status: {'Sent' if data['success'] else 'Failed'}[/]")
    console.print(f"[cyan]Recipient:[/cyan] {data['recipient']}")
    console.print(f"[cyan]Template:[/cyan] {data['template'] or 'Direct message'}")
    console.print(f"[cyan]Sent at:[/cyan] {data['sent_at']}")
    
    if data['variables']:
        console.print(f"[cyan]Variables:[/cyan] {json.dumps(data['variables'], indent=2)}")
    
    if data['message_sid']:
        console.print(f"[cyan]Message SID:[/cyan] {data['message_sid']}")
    
    if data['segments']:
        console.print(f"[cyan]Segments:[/cyan] {data['segments']}")
    
    if data['cost']:
        console.print(f"[cyan]Cost:[/cyan] ${data['cost']:.4f}")
    
    if data['error']:
        console.print(f"[red]Error:[/red] {data['error']}")
    
    console.print(f"\n[yellow]Message Content:[/yellow]")
    console.print(Panel(data['message'], border_style="cyan"))


@history.command('stats')
@click.option('--days', '-d', default=30, help='Number of days to analyze (default: 30)')
def history_stats(days):
    """Show sending statistics"""
    db = Database(config_manager.db_file)
    stats = db.get_stats(days=days)
    db.close()
    
    console.print(f"\n[cyan bold]📊 SMS Statistics (Last {days} days)[/cyan bold]\n")
    
    # Summary
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Total Sent", str(stats['total_sent']))
    table.add_row("Successful", f"[green]{stats['successful']}[/green]")
    table.add_row("Failed", f"[red]{stats['failed']}[/red]")
    table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
    table.add_row("Total Segments", str(stats['total_segments']))
    table.add_row("Total Cost", f"${stats['total_cost']:.2f}")
    
    console.print(table)
    
    # Top templates
    if stats['top_templates']:
        console.print(f"\n[yellow]Top Templates:[/yellow]")
        for i, t in enumerate(stats['top_templates'], 1):
            console.print(f"  {i}. {t['name']}: {t['count']} messages")
    
    # Daily breakdown (last 7 days)
    if stats['daily_breakdown']:
        console.print(f"\n[yellow]Daily Breakdown (Last 7 days):[/yellow]")
        for day in stats['daily_breakdown'][-7:]:
            console.print(f"  {day['date']}: {day['count']} messages (${day['cost']:.2f})")


@history.command('export')
@click.option('--format', '-f', type=click.Choice(['csv', 'json']), default='csv', help='Export format')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output file path')
@click.option('--limit', '-l', default=1000, help='Maximum records to export')
def history_export(format, output, limit):
    """Export message history"""
    db = Database(config_manager.db_file)
    
    if format == 'csv':
        data = db.export_logs(format='csv', limit=limit)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(data)
    else:
        data = db.export_logs(format='dict', limit=limit)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    db.close()
    
    console.print(f"[green]✓ Exported to {output}[/green]")


@history.command('clear')
@click.option('--days', '-d', default=90, help='Delete logs older than N days')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def history_clear(days, yes):
    """Clear old message history"""
    if not yes:
        if not Confirm.ask(f"[red]Delete all logs older than {days} days?[/red]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    db = Database(config_manager.db_file)
    deleted = db.delete_old_logs(days=days)
    db.close()
    
    console.print(f"[green]✓ Deleted {deleted} old log entries[/green]")


# =============================================================================
# UTILITY COMMANDS
# =============================================================================

@cli.command()
@click.argument('phone_number')
def validate(phone_number):
    """Validate a phone number format
    
    \b
    Example:
      sms-prompt validate +1234567890
    """
    try:
        import phonenumbers
        parsed = phonenumbers.parse(phone_number, None)
        is_valid = phonenumbers.is_valid_number(parsed)
        
        if is_valid:
            formatted_e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            formatted_intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            country = phonenumbers.region_code_for_number(parsed)
            
            console.print(f"\n[green]✓ Valid phone number[/green]")
            console.print(f"[cyan]E.164 Format:[/cyan] {formatted_e164}")
            console.print(f"[cyan]International:[/cyan] {formatted_intl}")
            console.print(f"[cyan]Country:[/cyan] {country}")
        else:
            console.print(f"[red]✗ Invalid phone number[/red]")
    except Exception as e:
        console.print(f"[red]Error parsing phone number: {str(e)}[/red]")


@cli.command()
def info():
    """Show tool information and paths"""
    console.print("\n[cyan bold]📱 SMS Prompt CLI[/cyan bold]")
    console.print("[dim]A powerful CLI tool for sending customized SMS messages[/dim]\n")
    
    console.print(f"[cyan]Config Directory:[/cyan] {config_manager.config_dir}")
    console.print(f"[cyan]Config File:[/cyan] {config_manager.config_file}")
    console.print(f"[cyan]Templates Directory:[/cyan] {config_manager.templates_dir}")
    console.print(f"[cyan]Database File:[/cyan] {config_manager.db_file}")
    
    # Check config status
    config = config_manager.load_config()
    provider = config.get('sms_provider', 'twilio')
    console.print(f"\n[cyan]Active Provider:[/cyan] {provider}")
    
    if _validate_provider_config(config, provider):
        console.print("[green]✓ Provider configured[/green]")
    
    # Count templates
    template_engine = TemplateEngine(config_manager.templates_dir)
    templates = template_engine.list_templates()
    console.print(f"\n[cyan]Available Templates:[/cyan] {len(templates)}")
    
    # Database stats
    try:
        db = Database(config_manager.db_file)
        stats = db.get_stats(days=30)
        db.close()
        console.print(f"[cyan]Messages (Last 30 days):[/cyan] {stats['total_sent']}")
    except Exception:
        pass


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
