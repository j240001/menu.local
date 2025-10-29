# nhl_routes/__init__.py
from flask import Blueprint

# Create a blueprint for all NHL-related routes
nhl_bp = Blueprint("nhl", __name__)

# Import submodules so their routes automatically register
from . import scoreboard, standings, stats, updater, updater_page, more

from . import results_menu
from .months import oct2025, nov2025, dec2025, jan2026, feb2026, mar2026, apr2026
