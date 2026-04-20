import os
import configparser
from pathlib import Path

def load_config():
    """Load configuration from file or environment variables"""
    config = configparser.ConfigParser()
    config_path = Path.home() / '.nonkyc/config.ini'
    
    if config_path.exists():
        config.read(config_path)
        return {
            'api_key': config.get('nonkyc', 'api_key'),
            'api_secret': config.get('nonkyc', 'api_secret'),
            'base_url': config.get('nonkyc', 'base_url', fallback='https://api.nonkyc.io')
        }
    else:
        # Fallback to environment variables
        return {
            'api_key': os.environ.get('NONKYC_API_KEY'),
            'api_secret': os.environ.get('NONKYC_API_SECRET'),
            'base_url': os.environ.get('NONKYC_BASE_URL', 'https://api.nonkyc.io')
        }

def format_balance(amount, currency='USD'):
    """Format balance with proper colors"""
    if amount > 0:
        return f"[green]{amount:.2f} {currency}[/green]"
    elif amount < 0:
        return f"[red]{amount:.2f} {currency}[/red]"
    else:
        return f"[dim]{amount:.2f} {currency}[/dim]"

def format_price(price, change_24h=None):
    """Format price with 24h change"""
    if change_24h and change_24h > 0:
        change_str = f" [green]▲{change_24h:.2f}%[/green]"
    elif change_24h and change_24h < 0:
        change_str = f" [red]▼{change_24h:.2f}%[/red]"
    else:
        change_str = ""
    
    return f"[bold cyan]${price:.4f}[/bold cyan]{change_str}"
