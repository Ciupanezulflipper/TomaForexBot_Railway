# confirmation_filter.py

def confirmation_filter(*args):
    """
    Returns True only if all passed arguments are True.
    Example usage:
        if confirmation_filter(news_signal, pattern_signal, volume_signal):
            # send alert
    """
    return all(bool(x) for x in args)

# Example usage/test
if __name__ == "__main__":
    print("Test 1: All True →", confirmation_filter(True, True, True))          # True
    print("Test 2: Some False →", confirmation_filter(True, False, True))       # False
    print("Test 3: Mixed →", confirmation_filter(True, None, 1))                # False
    print("Test 4: All Empty →", confirmation_filter())                         # True (no filter)
