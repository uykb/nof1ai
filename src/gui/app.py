"""
Main GUI Application - Single Page App with internal navigation
"""

from nicegui import ui
from src.gui.components.header import create_header
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager

# Import pages
from src.gui.pages import dashboard, positions, history, market, reasoning, settings, recommendations

# Global services
bot_service = BotService()
state_manager = StateManager()

# Connect services
bot_service.state_manager = state_manager


def create_app():
    """Initialize and configure the NiceGUI application as single page"""

    # Add Material Icons and Inter Font
    ui.add_head_html('''
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&display=swap" rel="stylesheet">
    ''')
    
    # Add global futuristic styles
    ui.add_head_html('''
        <style>
            :root {
                --bg-obsidian: #050505;
                --glass-bg: rgba(20, 20, 25, 0.7);
                --glass-border: rgba(255, 255, 255, 0.08);
                --neon-blue: #00f3ff;
                --neon-green: #00ff9d;
                --neon-purple: #bd00ff;
                --text-primary: #ffffff;
                --text-secondary: #9ca3af;
            }

            body {
                background-color: var(--bg-obsidian);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
            }

            /* Glassmorphism Panel */
            .glass-panel {
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid var(--glass-border);
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
                border-radius: 16px;
            }

            /* Neon Gradient Border Effect */
            .neon-border-panel {
                position: relative;
                background: linear-gradient(#131313, #131313) padding-box,
                            linear-gradient(135deg, rgba(0,243,255,0.4), rgba(189,0,255,0.4)) border-box;
                border: 1px solid transparent;
                border-radius: 16px;
            }

            /* Typography & Glows */
            .font-thin-inter { font-weight: 200; }
            .font-light-inter { font-weight: 300; }
            
            .neon-text-blue {
                color: var(--neon-blue);
                text-shadow: 0 0 12px rgba(0, 243, 255, 0.4);
            }
            
            .neon-text-green {
                color: var(--neon-green);
                text-shadow: 0 0 12px rgba(0, 255, 157, 0.4);
            }

            .neon-text-purple {
                color: var(--neon-purple);
                text-shadow: 0 0 12px rgba(189, 0, 255, 0.4);
            }

            /* Custom Scrollbar */
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: #0a0a0a; }
            ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #555; }

            /* Navigation Button Overrides */
            .nav-btn {
                color: var(--text-secondary);
                transition: all 0.3s ease;
                border-radius: 8px;
            }
            .nav-btn:hover {
                color: var(--text-primary);
                background: rgba(255, 255, 255, 0.05);
                box-shadow: 0 0 15px rgba(0, 243, 255, 0.1);
            }
        </style>
    ''')

    # Main layout
    with ui.column().classes('w-full h-screen bg-[#050505]'):
        create_header(state_manager)

        with ui.row().classes('w-full flex-grow gap-0'):
            # Sidebar with navigation (Glassmorphic)
            with ui.column().classes('w-64 glass-panel m-4 mt-0 p-4 gap-2 h-[calc(100vh-100px)] border-r-0'):
                # Navigation buttons
                menu_items = [
                    ('Dashboard', '📊 Dashboard', 'Main dashboard with metrics'),
                    ('Recommendations', '🤖 Recommendations', 'AI trade proposals'),
                    ('Positions', '💼 Positions', 'Active positions'),
                    ('History', '📜 History', 'Trade history'),
                    ('Market', '📈 Market', 'Market data'),
                    ('Reasoning', '🧠 Reasoning', 'LLM logic'),
                    ('Settings', '⚙️ Settings', 'Config'),
                ]

                # Create navigation buttons
                for page_id, label, tooltip in menu_items:
                    btn = ui.button(label, on_click=lambda p=page_id: navigate(p))
                    btn.classes('w-full justify-start text-left nav-btn font-light-inter text-base')
                    btn.props('flat dense')
                    with btn:
                        ui.tooltip(tooltip).classes('bg-gray-900 text-xs')

                ui.separator().classes('my-4 opacity-20')

                # Version info
                with ui.column().classes('mt-auto gap-1 w-full items-center opacity-50'):
                    ui.label('v1.0.0 Alpha').classes('text-xs font-thin-inter')
                    ui.label('NOF1.AI').classes('text-[10px] tracking-widest')

            # Main content area
            global content_container
            content_container = ui.column().classes('flex-grow p-6 overflow-auto items-start')

    # Load default page
    with content_container:
        dashboard.create_dashboard(bot_service, state_manager)


def navigate(page: str):
    """Navigate to different page by clearing and recreating content"""
    global content_container

    content_container.clear()

    with content_container:
        if page == 'Dashboard':
            dashboard.create_dashboard(bot_service, state_manager)
        elif page == 'Recommendations':
            recommendations.create_recommendations(bot_service, state_manager)
        elif page == 'Positions':
            positions.create_positions(bot_service, state_manager)
        elif page == 'History':
            history.create_history(bot_service, state_manager)
        elif page == 'Market':
            market.create_market(bot_service, state_manager)
        elif page == 'Reasoning':
            reasoning.create_reasoning(bot_service, state_manager)
        elif page == 'Settings':
            settings.create_settings(bot_service, state_manager)
