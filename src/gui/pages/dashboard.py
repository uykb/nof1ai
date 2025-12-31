"""
Dashboard Page - Main dashboard with metrics and charts
"""

import plotly.graph_objects as go
from nicegui import ui
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager


def create_dashboard(bot_service: BotService, state_manager: StateManager):
    """Create dashboard page with real-time metrics, charts, and controls"""

    ui.label('MISSION CONTROL').classes('text-4xl font-black tracking-tighter text-white mb-6 opacity-90')

    # ===== METRICS CARDS (4 cards in grid) =====
    with ui.grid(columns=4).classes('w-full gap-6 mb-8'):
        # Card 1: Total Balance
        with ui.column().classes('neon-border-panel p-6'):
            ui.label('TOTAL BALANCE').classes('text-[10px] tracking-widest text-gray-500 font-bold mb-2')
            balance_value = ui.label('$0.00').classes('text-4xl font-thin-inter text-white tracking-tight')
            ui.label('≈ 0.00 BTC').classes('text-xs text-gray-600 mt-1')

        # Card 2: Total Return
        with ui.column().classes('glass-panel p-6 border-l-4 border-l-cyan-400'):
            ui.label('TOTAL RETURN').classes('text-[10px] tracking-widest text-gray-500 font-bold mb-2')
            return_value = ui.label('+0.00%').classes('text-4xl font-thin-inter neon-text-green tracking-tight')
            ui.label('24h Performance').classes('text-xs text-gray-600 mt-1')

        # Card 3: Sharpe Ratio
        with ui.column().classes('glass-panel p-6'):
            ui.label('SHARPE RATIO').classes('text-[10px] tracking-widest text-gray-500 font-bold mb-2')
            sharpe_value = ui.label('0.00').classes('text-4xl font-thin-inter neon-text-blue tracking-tight')
            ui.label('Risk-Adjusted Return').classes('text-xs text-gray-600 mt-1')

        # Card 4: Active Positions
        with ui.column().classes('glass-panel p-6'):
            ui.label('ACTIVE POSITIONS').classes('text-[10px] tracking-widest text-gray-500 font-bold mb-2')
            positions_value = ui.label('0').classes('text-4xl font-thin-inter text-white tracking-tight')
            ui.label('Open Trades').classes('text-xs text-gray-600 mt-1')

    # ===== CHARTS ROW =====
    with ui.row().classes('w-full gap-6 mb-8'):
        # Equity Curve Chart (left half)
        with ui.column().classes('flex-1 glass-panel p-6'):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('EQUITY CURVE').classes('text-sm font-bold tracking-widest text-gray-400')
                ui.icon('show_chart').classes('text-gray-600')

            equity_chart = ui.plotly(go.Figure(
                data=[go.Scatter(
                    x=[],
                    y=[],
                    mode='lines',
                    name='Value',
                    line=dict(color='#00f3ff', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 243, 255, 0.1)'
                )],
                layout=go.Layout(
                    template='plotly_dark',
                    height=320,
                    margin=dict(l=40, r=20, t=20, b=40),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#9ca3af', size=10),
                    hovermode='x unified'
                )
            )).classes('w-full')

        # Asset Allocation Pie Chart (right half)
        with ui.column().classes('flex-1 glass-panel p-6'):
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('ALLOCATION').classes('text-sm font-bold tracking-widest text-gray-400')
                ui.icon('pie_chart').classes('text-gray-600')

            allocation_chart = ui.plotly(go.Figure(
                data=[go.Pie(
                    labels=[],
                    values=[],
                    hole=0.7,
                    marker=dict(colors=['#00f3ff', '#bd00ff', '#00ff9d', '#ffffff']),
                    textinfo='none'
                )],
                layout=go.Layout(
                    template='plotly_dark',
                    height=320,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter', color='#9ca3af'),
                    showlegend=True,
                    legend=dict(orientation='v', x=1, y=0.5, font=dict(size=10)),
                    annotations=[dict(text='ASSETS', x=0.5, y=0.5, font_size=12, showarrow=False, font_color='#555')]
                )
            )).classes('w-full')

    # ===== MARKET DATA =====
    with ui.column().classes('w-full glass-panel p-6 mb-8'):
        ui.label('MARKET INTELLIGENCE').classes('text-sm font-bold tracking-widest text-gray-400 mb-4')
        market_data_container = ui.column().classes('w-full gap-4')
        
        with market_data_container:
            ui.label('INITIALIZING FEED...').classes('text-xs tracking-widest text-gray-600 text-center py-8 animate-pulse')

    # ===== ACTIVITY FEED & LOGS =====
    with ui.grid(columns=3).classes('w-full gap-6'):
        # Activity Log (2/3 width)
        with ui.column().classes('col-span-2 glass-panel p-6'):
            ui.label('SYSTEM LOGS').classes('text-sm font-bold tracking-widest text-gray-400 mb-4')
            activity_log = ui.log(max_lines=15).classes('w-full h-48 bg-black/40 text-xs font-mono text-gray-400 p-4 rounded-lg border border-white/5')
            activity_log.push('>> SYSTEM INITIALIZED')
            activity_log.push('>> WAITING FOR COMMAND...')

        # Controls (1/3 width)
        with ui.column().classes('glass-panel p-6 justify-between'):
            ui.label('COMMAND CENTER').classes('text-sm font-bold tracking-widest text-gray-400 mb-4')

            with ui.column().classes('w-full gap-3'):
                # Start Button
                start_btn = ui.button('INITIALIZE BOT', on_click=lambda: start_bot())
                start_btn.classes('w-full bg-cyan-900/30 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/20 tracking-widest font-bold')
                
                # Stop Button
                stop_btn = ui.button('TERMINATE PROCESS', on_click=lambda: stop_bot())
                stop_btn.classes('w-full bg-red-900/20 text-red-500 border border-red-500/30 hover:bg-red-500/10 tracking-widest font-bold')
                stop_btn.props('disable')

                # Refresh Button
                refresh_data_btn = ui.button('REFRESH FEED', on_click=lambda: refresh_market_data())
                refresh_data_btn.classes('w-full text-gray-400 border border-gray-700 hover:bg-gray-800 tracking-widest')
                
                refresh_data_loading = ui.label('').classes('text-xs text-cyan-400 self-center h-4')

            # Status Footer
            with ui.row().classes('w-full justify-between items-center mt-4 border-t border-white/5 pt-4'):
                ui.label('STATUS:').classes('text-[10px] text-gray-600 font-bold')
                status_indicator = ui.label('STANDBY').classes('text-xs font-bold text-gray-500')
            
            last_refresh_label = ui.label('SYNC: PENDING').classes('text-[10px] text-gray-700 self-end')

    # ===== CONTROL FUNCTIONS (Logic Unchanged) =====

    async def start_bot():
        """Start the trading bot"""
        try:
            status_indicator.text = 'INITIALIZING...'
            activity_log.push('>> COMMAND: START_BOT_SEQUENCE')

            await bot_service.start()

            status_indicator.text = 'OPERATIONAL'
            status_indicator.classes(remove='text-gray-500', add='neon-text-green')
            start_btn.props('disable')
            stop_btn.props(remove='disable')

            activity_log.push('>> BOT STARTED SUCCESSFULLY')
            ui.notify('SYSTEM ONLINE', type='positive', classes='glass-panel text-green-400')

        except Exception as e:
            status_indicator.text = 'SYSTEM FAILURE'
            status_indicator.classes(add='text-red-500')
            activity_log.push(f'>> ERROR: {str(e)}')
            ui.notify(f'FAILED: {str(e)}', type='negative')

    async def stop_bot():
        """Stop the trading bot"""
        try:
            status_indicator.text = 'TERMINATING...'
            activity_log.push('>> COMMAND: STOP_BOT_SEQUENCE')

            await bot_service.stop()

            status_indicator.text = 'STANDBY'
            status_indicator.classes(remove='neon-text-green', add='text-gray-500')
            start_btn.props(remove='disable')
            stop_btn.props('disable')

            activity_log.push('>> BOT STOPPED')
            ui.notify('SYSTEM OFFLINE', type='info', classes='glass-panel text-gray-400')

        except Exception as e:
            activity_log.push(f'>> ERROR: {str(e)}')
            ui.notify(f'FAILED: {str(e)}', type='negative')

    # ===== AUTO-REFRESH FUNCTIONS =====

    import time
    import asyncio
    last_refresh_time = None
    refresh_seconds_ago = 0

    async def refresh_market_data():
        """Refresh market data from Hyperliquid without starting bot"""
        nonlocal last_refresh_time, refresh_seconds_ago

        try:
            refresh_data_btn.enabled = False
            refresh_data_loading.text = 'SYNCING...'
            activity_log.push('>> FETCHING MARKET DATA...')

            # Call bot service to refresh data
            success = await bot_service.refresh_market_data()

            if success:
                last_refresh_time = time.time()
                refresh_data_loading.text = 'COMPLETE'
                activity_log.push('>> DATA SYNCED')
                
                # Update dashboard immediately after refresh
                await update_dashboard()
            else:
                refresh_data_loading.text = 'FAILED'
                activity_log.push('>> SYNC FAILED')

        except Exception as e:
            activity_log.push(f'>> EXCEPTION: {str(e)}')
            refresh_data_loading.text = 'ERROR'
        finally:
            refresh_data_btn.enabled = True
            await asyncio.sleep(2.0)
            refresh_data_loading.text = ''

    async def update_dashboard():
        """Update all dashboard components with latest data"""
        nonlocal refresh_seconds_ago

        try:
            state = state_manager.get_state()

            # Update metrics cards
            balance_value.text = f'${state.balance:,.2f}'

            # Return with color coding
            return_pct = state.total_return_pct
            return_value.text = f'{return_pct:+.2f}%'
            if return_pct >= 0:
                return_value.classes(remove='text-red-500', add='neon-text-green')
            else:
                return_value.classes(remove='neon-text-green', add='text-red-500')

            sharpe_value.text = f'{state.sharpe_ratio:.2f}'
            positions_value.text = str(len(state.positions or []))

            # Update equity curve chart
            equity_history = bot_service.get_equity_history()
            if equity_history:
                times = [d['time'] for d in equity_history]
                values = [d['value'] for d in equity_history]

                equity_chart.figure.data[0].x = times
                equity_chart.figure.data[0].y = values
                equity_chart.update()

            # Update asset allocation chart
            positions = state.positions or []
            if positions:
                labels = [p['symbol'] for p in positions]
                values = [abs(p['quantity'] * p['entry_price']) for p in positions]

                allocation_chart.figure.data[0].labels = labels
                allocation_chart.figure.data[0].values = values
                allocation_chart.update()

            # Update market data
            market_data = getattr(state, 'market_data', None)
            market_data_container.clear()
            
            if market_data and isinstance(market_data, list) and len(market_data) > 0:
                with market_data_container:
                    with ui.grid(columns=len(market_data)).classes('w-full gap-6'):
                        for asset_data in market_data:
                            asset = asset_data.get('asset', 'N/A')
                            price = asset_data.get('current_price', 0)
                            
                            # Intraday data
                            intraday = asset_data.get('intraday', {})
                            ema20 = intraday.get('ema20', 0)
                            rsi14 = intraday.get('rsi14', 0)
                            
                            # Long-term data
                            lt = asset_data.get('long_term', {})
                            lt_ema20 = lt.get('ema20', 0)
                            lt_ema50 = lt.get('ema50', 0)
                            
                            with ui.column().classes('p-6 glass-panel relative overflow-hidden group hover:border-cyan-500/30 transition-all'):
                                # Decorative background element
                                ui.label(asset).classes('absolute -right-4 -top-4 text-6xl font-black text-white/5 select-none z-0')
                                
                                # Content
                                ui.label(asset).classes('text-2xl font-light text-white mb-2 z-10')
                                ui.label(f'${price:,.2f}').classes('text-3xl font-thin-inter neon-text-blue mb-4 z-10')
                                
                                with ui.grid(columns=2).classes('w-full gap-4 text-xs z-10'):
                                    with ui.column():
                                        ui.label('5m RSI').classes('text-gray-500 font-bold tracking-wider')
                                        ui.label(f'{rsi14:.1f}' if rsi14 else '-').classes('text-white')
                                    with ui.column():
                                        ui.label('5m EMA').classes('text-gray-500 font-bold tracking-wider')
                                        ui.label(f'{ema20:.1f}' if ema20 else '-').classes('text-white')
            else:
                with market_data_container:
                    ui.label('NO SIGNAL DETECTED').classes('text-xs tracking-widest text-gray-700 text-center py-4')

            # Update activity log with recent events
            recent_events = bot_service.get_recent_events(limit=5)
            for event in recent_events[-5:]:  # Last 5 only
                activity_log.push(f"[{event['time']}] {event['message']}")

            # Update button states
            if state.is_running:
                status_indicator.text = 'OPERATIONAL'
                status_indicator.classes(remove='text-gray-500', add='neon-text-green')
                start_btn.props('disable')
                stop_btn.props(remove='disable')
            else:
                status_indicator.text = 'STANDBY'
                status_indicator.classes(remove='neon-text-green', add='text-gray-500')
                start_btn.props(remove='disable')
                stop_btn.props('disable')

            if state.error:
                status_indicator.text = 'SYSTEM FAILURE'
                status_indicator.classes(add='text-red-500')
                activity_log.push(f'>> CRITICAL: {state.error}')

            # Update refresh timestamp
            if last_refresh_time:
                refresh_seconds_ago = int(time.time() - last_refresh_time)
                last_refresh_label.text = f'SYNC: {refresh_seconds_ago}s AGO'
            else:
                last_refresh_label.text = 'SYNC: PENDING'

        except Exception as e:
            activity_log.push(f'>> UI_THREAD_ERROR: {str(e)}')

    # ===== AUTO-REFRESH TIMER =====
    # Update dashboard every 3 seconds
    ui.timer(3.0, update_dashboard)
