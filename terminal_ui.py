import curses, plotting, data, orders, account, time, util

def main(stdscr):

    curses.start_color()
    # define color pairs for percent change (green positive, red negative) and labels
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    # Clear screen
    util.clear()
    stdscr.clear()
    stdscr.refresh()
    
    # Use fixed-size variables for layout (not relative to terminal size)
    INFO_H = 3
    GRAPH_H = 16
    DEFAULT_GRAPH_W = 67  # preferred graph width
    STATS_W = 28  # width of the right-side stats box
    
    # Available time periods for arrow key navigation
    PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
    period_index = PERIODS.index("6mo") if "6mo" in PERIODS else 3
    
    # Default view shows a ticker graph
    symbol = "AAPL"
    period = PERIODS[period_index]
    interval = "1d"
    plot, start_price, price, pct_change, period = plotting.plot_stock(symbol, period=period, interval=interval)
    try:
        hist_df = data.get_daily_history(symbol, period=period, interval=interval)
    except Exception:
        hist_df = None
    holdings = account.get_holdings()
    lines = plot.split("\n")

    # Build content strings for the info boxes
    def make_contents(price_val, pct_val):
        return [f"Ticker: {symbol}", f"Price: ${price_val:,.2f}", f"Change: {pct_val:+.2f}%", f"Period: {period}"]

    contents = make_contents(price, pct_change)

    # determine terminal size early so compute_positions can use GRAPH_W
    term_h, term_w = stdscr.getmaxyx()
    GRAPH_W = DEFAULT_GRAPH_W

    def compute_positions(contents):
        # minimal width for a box (including padding/borders)
        min_w = 12
        needed = [max(min_w, len(s) + 4) for s in contents]
        rows = []
        cur_row = []
        cur_sum = 0
        for w in needed:
            if cur_row and cur_sum + w > GRAPH_W:
                rows.append(cur_row)
                cur_row = [w]
                cur_sum = w
            else:
                cur_row.append(w)
                cur_sum += w
        if cur_row:
            rows.append(cur_row)

        # positions: list of tuples (row_i, x, width, content_index)
        positions = []
        idx = 0
        for row_i, row in enumerate(rows):
            x = 0
            for w in row:
                positions.append((row_i, x, w, idx))
                x += w
                idx += 1
        return positions, len(rows)

    positions, rows_count = compute_positions(contents)

    required_h = rows_count * INFO_H + GRAPH_H + 4
    required_w = GRAPH_W + STATS_W + 1
    if term_h < required_h or term_w < required_w:
        stdscr.addstr(0, 0, f"Terminal too small: need {required_w}x{required_h}. Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return

    # Create info windows according to computed positions
    info_windows = [None] * len(contents)
    for row_i, x, w, idx in positions:
        y = row_i * INFO_H
        win = curses.newwin(INFO_H, w, y, x)
        win.box()
        info_windows[idx] = win

    # graphWin placed below the info rows (left side)
    graph_y = rows_count * INFO_H
    graphWin = curses.newwin(GRAPH_H, GRAPH_W, graph_y, 0)
    graphWin.box()

    # stats window on the right of the graph
    stats_x = GRAPH_W + 1
    statsWin = curses.newwin(GRAPH_H+3, STATS_W, 0, stats_x)
    statsWin.box()

    # input prompt window below graph and stats (single row)
    input_y = graph_y + GRAPH_H
    input_w = GRAPH_W + 1 + STATS_W
    inputWin = curses.newwin(3, input_w, input_y, 0)
    inputWin.box()

    def set_input_message(msg):
        inputWin.erase()
        inputWin.box()
        try:
            inputWin.addstr(1, 2, msg[: term_w - 4])
        except curses.error:
            pass
        inputWin.refresh()

    #draw info windows and graph
    def draw_all(current_price, current_pct, lines, hist_df=None):
        contents = make_contents(current_price, current_pct)
        # draw info boxes
        for idx, text in enumerate(contents):
            try:
                w = info_windows[idx]
                w.erase()
                w.box()
                if idx == 0:
                    w.addstr(1, 2, text, curses.color_pair(3))
                elif idx == 2:
                    color = curses.color_pair(1) if current_pct >= 0 else curses.color_pair(2)
                    w.addstr(1, 2, text, color)
                else:
                    w.addstr(1, 2, text)
                w.refresh()
            except (curses.error, TypeError):
                pass

        # draw graph
        graphWin.erase()
        graphWin.box()
        for i, line in enumerate(lines):
            if 0 <= i < GRAPH_H - 2:
                try:
                    graphWin.addstr(i+1, 1, line[:GRAPH_W-2])
                except curses.error:
                    pass
        graphWin.refresh()
        # draw stats on the right
        statsWin.erase()
        statsWin.box()
        try:
            # Basic stats
            statsWin.addstr(1, 2, f"Symbol: {symbol}")
            statsWin.addstr(2, 2, f"Period: {period}")
            statsWin.addstr(3, 2, f"Start: ${start_price:,.2f}")
            statsWin.addstr(4, 2, f"Now:   ${current_price:,.2f}")
            color = curses.color_pair(1) if current_pct >= 0 else curses.color_pair(2)
            statsWin.addstr(5, 2, f"Change: {current_pct:+.2f}%", color)
            # If history dataframe provided, show high/low/volume
            if hist_df is not None and not hist_df.empty:
                try:
                    high = hist_df['High'].max()
                    low = hist_df['Low'].min()
                    vol = int(hist_df['Volume'].iloc[-1]) if 'Volume' in hist_df.columns else None
                    statsWin.addstr(6, 2, f"High: ${high:,.2f}")
                    statsWin.addstr(7, 2, f"Low:  ${low:,.2f}")
                    if vol is not None:
                        statsWin.addstr(8, 2, f"Vol: {vol:,}")
                except Exception:
                    pass
            # Portfolio summary section
            try:
                acc = account.get_account_info()
                statsWin.addstr(7, 2, "Portfolio:", curses.color_pair(3))
                statsWin.addstr(8, 2, f"Eq: ${float(acc.get('portfolio_value', 0)) :,.0f}")
                statsWin.addstr(9, 2, f"Cash: ${float(acc.get('cash', 0)) :,.0f}")

            except Exception:
                pass
            # Holdings section
            try:
                statsWin.addstr(11, 2, "Holdings:", curses.color_pair(3))
                row = 12
                # Show all holdings that fit, starting from the most recent
                available_rows = GRAPH_H - row + 2
                start_idx = max(0, len(holdings) - available_rows)
                for holding in holdings[start_idx:]:
                    if row >= GRAPH_H + 2:
                        break
                    sym = holding['symbol']
                    qty = holding['qty']
                    price = holding['current_price']
                    pl = holding['unrealized_pl']
                    pl_color = curses.color_pair(1) if pl >= 0 else curses.color_pair(2)
                    label = f"{sym}: {qty:.0f}@{price:.2f}"
                    pl_text = f"${pl:+,.0f}"
                    try:
                        statsWin.addstr(row, 2, label)
                        statsWin.addstr(row, 20, pl_text, pl_color)
                    except curses.error:
                        pass
                    row += 1
            except Exception:
                pass
        except curses.error:
            pass
        statsWin.refresh()

    # Try to load history for stats
    try:
        hist_df = data.get_daily_history(symbol, period=period, interval=interval)
    except Exception:
        hist_df = None

    # Initial draw
    draw_all(price, pct_change, lines, hist_df)
    # Input hint
    set_input_message("Press 's' to change symbol, LEFT/RIGHT arrows to change period, 't' to trade, 'q' to quit.")

    # Now enter an update loop: poll for latest price every 5 seconds and update boxes
    stdscr.nodelay(True)
    UPDATE_INTERVAL = 5.0
    last_update = time.time()
    try:
        while True:
            ch = stdscr.getch()
            if ch != -1:
                # handle keys: 'q' to quit, 's' to change symbol/period
                if ch in (ord('q'), ord('Q')):
                    break
                if ch in (ord('s'), ord('S')):
                    # prompt user for new symbol only
                    curses.echo()
                    curses.curs_set(1)
                    inputWin.erase()
                    inputWin.box()
                    prompt = "Enter SYMBOL (e.g. AAPL). Blank to cancel: "
                    try:
                        inputWin.addstr(1, 2, prompt)
                        inputWin.refresh()
                        # getstr with max length
                        user_input = inputWin.getstr(1, 2 + len(prompt), 32).decode().strip()
                    except Exception:
                        user_input = ''
                    curses.noecho()
                    curses.curs_set(0)
                    # restore input window box
                    set_input_message("Press 's' to change symbol, LEFT/RIGHT arrows to change period, 't' to trade, 'q' to quit.")

                    if user_input:
                        new_symbol = user_input.upper()
                        try:
                            plot, start_price, price, pct_change, period = plotting.plot_stock(new_symbol, period=period, interval=interval)
                            symbol = new_symbol
                            lines = plot.split('\n')
                            try:
                                hist_df = data.get_daily_history(symbol, period=period, interval=interval)
                            except Exception:
                                hist_df = None
                            draw_all(price, pct_change, lines, hist_df)
                        except Exception:
                            set_input_message("Invalid symbol; press 's' to try again or 't' to trade.")
                    last_update = time.time()
                    continue
                if ch in (ord('t'), ord('T')):
                    curses.echo()
                    curses.curs_set(1)
                    inputWin.erase()
                    inputWin.box()
                    prompt = "Order: SIDE SYMBOL QTY (e.g. buy AAPL 1). Blank to cancel: "
                    try:
                        inputWin.addstr(1, 2, prompt)
                        inputWin.refresh()
                        user_input = inputWin.getstr(1, 2 + len(prompt), 48).decode().strip()
                    except Exception:
                        user_input = ''
                    curses.noecho()
                    curses.curs_set(0)

                    if user_input:
                        parts = user_input.split()
                        if len(parts) >= 3:
                            side = parts[0].lower()
                            symbol_in = parts[1].upper()
                            qty_part = parts[2]
                            try:
                                qty_val = float(qty_part)
                            except ValueError:
                                qty_val = None
                            if side in ("buy", "sell") and qty_val and qty_val > 0:
                                try:
                                    order = orders.place_market_order(symbol_in, qty_val, side)
                                    time.sleep(0.5)  # give API time to process the order
                                    holdings = account.get_holdings()
                                    draw_all(price, pct_change, lines, hist_df)
                                    set_input_message(f"OK: {side.upper()} {qty_val} {symbol_in} submitted (id {order.id}).")
                                except Exception:
                                    set_input_message("Order failed; check API keys and funds.")
                            else:
                                set_input_message("Invalid input. Format: buy AAPL 1")
                        else:
                            set_input_message("Invalid input. Format: buy AAPL 1")
                    else:
                        set_input_message("Trade canceled. Press 's' to change symbol, 't' to trade, 'q' to quit.")
                    last_update = time.time()
                    continue
                # Left arrow: previous period
                if ch == 260:
                    period_index = (period_index - 1) % len(PERIODS)
                    period = PERIODS[period_index]
                    try:
                        plot, start_price, price, pct_change, period = plotting.plot_stock(symbol, period=period, interval=interval)
                        lines = plot.split('\n')
                        try:
                            hist_df = data.get_daily_history(symbol, period=period, interval=interval)
                        except Exception:
                            hist_df = None
                        draw_all(price, pct_change, lines, hist_df)
                    except Exception:
                        set_input_message(f"Failed to load period {period}. Try another period.")
                    last_update = time.time()
                    continue
                # Right arrow: next period
                if ch == 261:
                    period_index = (period_index + 1) % len(PERIODS)
                    period = PERIODS[period_index]
                    try:
                        plot, start_price, price, pct_change, period = plotting.plot_stock(symbol, period=period, interval=interval)
                        lines = plot.split('\n')
                        try:
                            hist_df = data.get_daily_history(symbol, period=period, interval=interval)
                        except Exception:
                            hist_df = None
                        draw_all(price, pct_change, lines, hist_df)
                    except Exception:
                        set_input_message(f"Failed to load period {period}. Try another period.")
                    last_update = time.time()
                    continue
                # any other key: ignore
                else:
                    pass

            now = time.time()
            if now - last_update >= UPDATE_INTERVAL:
                new_price = data.get_latest_price(symbol)
                if new_price is not None:
                    price = new_price
                    pct_change = ((price / start_price) - 1.0) * 100 if start_price != 0 else 0.0
                    draw_all(price, pct_change, lines, hist_df)
                last_update = now

            time.sleep(0.1)
    finally:
        # restore blocking getch behavior
        stdscr.nodelay(False)

curses.wrapper(main)