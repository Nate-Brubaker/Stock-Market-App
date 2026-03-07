import yfinance as yf
import asciichartpy as asciichart
import pandas as pd

def plot_stock(symbol, period="1mo", interval="1d"):
    # Parameters
    chart_width = 50  # constant width
    chart_height = 10  # constant height
    # Returned String of Graph
    finalstring = ""

    # Accept either a symbol string (download via yfinance) or a DataFrame passed in
    if isinstance(symbol, pd.DataFrame):
        df = symbol.copy()
        # prefer a Date column, else allow a 'time' column that may already be formatted
        if 'Date' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime("%m/%d/%y")
            except Exception:
                df['Date'] = df['Date'].astype(str)
        elif 'time' in df.columns:
            # use the 'time' column (already formatted in data.get_daily_history)
            df['Date'] = df['time'].astype(str)
        prices = [p.item() if hasattr(p, 'item') else float(p) for p in df['Close'].values]
        dates = df['Date'].tolist()
    else:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime("%m/%d/%y")
        prices = [p.item() for p in df['Close'].values]
        dates = df['Date'].tolist()

    # Compute basic metrics: current price and percent change across the period
    current_price = prices[-1] if len(prices) > 0 else 0.0
    start_price = prices[0] if len(prices) > 0 else current_price
    pct_change = ((current_price / start_price) - 1.0) * 100 if start_price != 0 else 0.0

    # Sample prices/dates to the chart width
    # For shorter periods (2 months or less), use linear interpolation of indices for even date spacing
    factor = max(1, len(prices) / chart_width) if len(prices) > 0 else 1
    
    # Determine if period is 2 months or shorter
    is_short_period = period in ["1mo", "2mo", "5d", "1d", "3d"]
    
    sampled_prices = []
    sampled_dates = []
    for i in range(chart_width):
        if is_short_period and len(prices) > 1:
            # For short periods, use linear interpolation for even visual spacing
            idx = (i * (len(prices) - 1)) / (chart_width - 1) if chart_width > 1 else 0
            # Interpolate between two prices if needed
            idx_low = int(idx)
            idx_high = min(idx_low + 1, len(prices) - 1)
            t = idx - idx_low
            
            if idx_low == idx_high:
                sampled_prices.append(prices[idx_low])
                sampled_dates.append(dates[idx_low])
            else:
                # Linear interpolation for smooth curve
                price = prices[idx_low] * (1 - t) + prices[idx_high] * t
                sampled_prices.append(price)
                # Use the later date for display
                sampled_dates.append(dates[idx_high] if t > 0.5 else dates[idx_low])
        else:
            # For longer periods, use regular sampling
            idx = int(i * factor)
            if idx >= len(prices):
                idx = len(prices) - 1
            sampled_prices.append(prices[idx])
            sampled_dates.append(dates[idx])


    # Plot chart
    config = {
        'height': chart_height,
        'format': '{:.2f}',
        'offset': 3
    }
    chart_lines = asciichart.plot(sampled_prices, config).split('\n')
    
    # Find the maximum length of the price labels
    max_label_length = 0
    for line in chart_lines:
        # Find where the graph starts (looking for both ┤ and ┼)
        graph_start = -1
        for char in ['┤', '┼']:
            pos = line.find(char)
            if pos != -1:
                graph_start = pos if graph_start == -1 else min(graph_start, pos)
        
        if graph_start != -1:
            # Extract the price label and find its length
            label = line[:graph_start].strip()
            if label and label[0].isdigit():  # Make sure it's a number
                max_label_length = max(max_label_length, len(label))

    # Right-align all lines
    aligned_lines = []
    for line in chart_lines:
        # Find where the graph starts (looking for both ┤ and ┼)
        graph_start = -1
        for char in ['┤', '┼']:
            pos = line.find(char)
            if pos != -1:
                graph_start = pos if graph_start == -1 else min(graph_start, pos)
                
        if graph_start != -1:
            label = line[:graph_start].strip()
            graph = line[graph_start:]
            if label and label[0].isdigit():
                # Right align the label to max_label_length
                aligned_line = label.rjust(max_label_length) + graph
            else:
                # For lines without numbers, just pad with spaces
                aligned_line = " " * max_label_length + graph
            aligned_lines.append(aligned_line)
        else:
            aligned_lines.append(line)

    # Print chart with dates below
    for line in aligned_lines:
        finalstring += line + "\n"
    # Sets the right number of spaces before the date labels
    label_line = ""
    if aligned_lines:
        try:
            end_idx = aligned_lines[-1].find("┤")
        except Exception:
            end_idx = 0
    else:
        end_idx = 0
    for i in range(max(0, end_idx)):
        label_line += " "
    # Strip off extra spaces to align with chart width
    if chart_width:
        label_line = label_line[:-round(chart_width/11.5)] if len(label_line) > 0 else label_line

    # Print dates at roughly equal intervals under the chart
    num_labels = 5  # how many dates to show
    step = max(1, int(chart_width) // num_labels)
    for i in range(chart_width):
        if i % step == 0 and i < len(sampled_dates):
            label_line += sampled_dates[i][:5].center(step)  # first 5 chars (MM/DD)
        else:
            label_line += ''
        if i == chart_width - 1 and i < len(sampled_dates):
            label_line += sampled_dates[i][:5].center(step)
    finalstring += label_line

    # Return chart string and the computed metrics so callers can display them
    # Also return the start price so callers can recompute percent change from a live price
    return finalstring, start_price, current_price, pct_change, period