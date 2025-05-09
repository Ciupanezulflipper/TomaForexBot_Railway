# riskmanagement.py

def calculate_position_size(account_balance, risk_per_trade, stop_loss_pips):
    """
    Returns how many lots to trade based on risk per trade and stop loss.
    """
    risk_amount = account_balance * risk_per_trade
    if stop_loss_pips == 0:
        return 0
    lot_size = risk_amount / (stop_loss_pips * 10)  # Simplified formula
    return round(lot_size, 2)


def calculate_stop_loss(entry_price, risk_pips, direction='buy'):
    """
    Returns stop-loss price.
    """
    if direction.lower() == 'buy':
        return entry_price - (risk_pips * 0.0001)
    else:
        return entry_price + (risk_pips * 0.0001)


def calculate_take_profit(entry_price, reward_pips, direction='buy'):
    """
    Returns take-profit price.
    """
    if direction.lower() == 'buy':
        return entry_price + (reward_pips * 0.0001)
    else:
        return entry_price - (reward_pips * 0.0001)
