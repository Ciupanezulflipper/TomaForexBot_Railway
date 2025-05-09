import MetaTrader5 as mt5

# Try connecting without path (assuming MT5 is already open)
if not mt5.initialize():
    print("❌ Initialize() failed, error code =", mt5.last_error())
else:
    print("✅ MT5 initialized successfully")

    # Show MT5 version
    print("MetaTrader5 version:", mt5.__version__)

    # Check if logged in
    account_info = mt5.account_info()
    if account_info is None:
        print("❌ Not logged into any trading account.")
    else:
        print("👤 Logged in to account:", account_info.login)
        print(account_info)

    mt5.shutdown()
