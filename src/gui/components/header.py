"""
Header Component - Top navigation bar with quick metrics
"""

from nicegui import ui
from src.gui.services.state_manager import StateManager


def create_header(state_manager: StateManager):
    """
    Create header component with logo, quick metrics, and status.

    Args:
        state_manager: Global state manager instance
    """
    # Header container - Floating Glass Panel
    with ui.row().classes('w-[calc(100%-2rem)] glass-panel mx-4 mt-4 px-6 py-4 justify-between items-center z-50'):
        
        # Logo and title
        with ui.row().classes('items-center gap-3'):
            ui.label('🤖').classes('text-3xl filter drop-shadow-[0_0_8px_rgba(0,243,255,0.5)]')
            with ui.column().classes('gap-0'):
                ui.label('NOF1.AI').classes('text-xl font-bold tracking-wider text-white')
                ui.label('ALPHA ARENA').classes('text-[10px] tracking-[0.2em] text-cyan-400 font-light')

        # Quick metrics
        with ui.row().classes('gap-12'):
            # Balance
            with ui.column().classes('items-center gap-0'):
                balance_label = ui.label('$0.00').classes('text-2xl font-light tracking-tight text-white')
                ui.label('TOTAL BALANCE').classes('text-[10px] tracking-widest text-gray-500 font-semibold')

            # 24h PnL
            with ui.column().classes('items-center gap-0'):
                pnl_label = ui.label('+0.00%').classes('text-2xl font-light tracking-tight neon-text-green')
                ui.label('RETURN (24H)').classes('text-[10px] tracking-widest text-gray-500 font-semibold')

            # Sharpe Ratio
            with ui.column().classes('items-center gap-0'):
                sharpe_label = ui.label('0.00').classes('text-2xl font-light tracking-tight text-white')
                ui.label('SHARPE RATIO').classes('text-[10px] tracking-widest text-gray-500 font-semibold')

            # Status indicator
            with ui.row().classes('items-center gap-2 bg-black/30 px-4 py-2 rounded-full border border-white/5'):
                status_dot = ui.label('●').classes('text-xs text-gray-500')
                status_label = ui.label('STOPPED').classes('text-xs font-bold tracking-wider text-gray-400')

        # Auto-refresh metrics
        async def update_header():
            state = state_manager.get_state()

            # Update balance
            balance_label.text = f"${state.balance:,.2f}"

            # Update PnL with color coding
            pnl_pct = state.total_return_pct
            pnl_label.text = f"{pnl_pct:+.2f}%"
            if pnl_pct >= 0:
                pnl_label.classes(remove='text-red-500', add='neon-text-green')
                pnl_label.classes(remove='text-red-400 drop-shadow-[0_0_8px_rgba(248,113,113,0.5)]') 
            else:
                pnl_label.classes(remove='neon-text-green', add='text-red-400')
                # Add red glow manually via style or class if defined, here simple text-red-400

            # Update Sharpe
            sharpe_label.text = f"{state.sharpe_ratio:.2f}"

            # Update status
            if state.is_running:
                status_label.text = 'RUNNING'
                status_label.classes(remove='text-gray-400', add='neon-text-green')
                status_dot.classes(remove='text-gray-500', add='text-green-400')
            else:
                status_label.text = 'STOPPED'
                status_label.classes(remove='neon-text-green', add='text-gray-400')
                status_dot.classes(remove='text-green-400', add='text-gray-500')

            # Error indicator
            if state.error:
                status_label.text = 'ERROR'
                status_label.classes(remove='neon-text-green text-gray-400', add='text-red-500')
                status_dot.classes(remove='text-green-400 text-gray-500', add='text-red-500')

        # Refresh every second
        ui.timer(1.0, update_header)
