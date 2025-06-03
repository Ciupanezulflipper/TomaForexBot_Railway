
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_your_finnhub():
    """Test your exact Finnhub setup"""
    
    api_key = os.getenv("FINNHUB_API_KEY")
    
    print("🔑 Checking API Key...")
    if not api_key:
        print("❌ FINNHUB_API_KEY not found in environment!")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test 1: General news endpoint (like your test_finnhub_connection)
    print("\n📰 Testing general news endpoint...")
    url1 = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    
    try:
        resp = requests.get(url1, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ General news working! Got {len(data)} items")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Company news endpoint (like your fetch function)
    print("\n🏢 Testing company news endpoint for TSLA...")
    url2 = f"https://finnhub.io/api/v1/company-news?symbol=TSLA&from=2024-05-01&to=2025-06-01&token={api_key}"
    
    try:
        print(f"URL: {url2}")
        resp = requests.get(url2, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Company news working! Got {len(data)} items")
            
            if data:
                print("\nFirst headline:")
                first = data[0]
                print(f"  Title: {first.get('headline', 'N/A')}")
                print(f"  Source: {first.get('source', 'N/A')}")
                print(f"  Date: {first.get('datetime', 'N/A')}")
            else:
                print("⚠️ No news items returned (might be weekend/no recent news)")
                
        else:
            print(f"❌ Error: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Try a different symbol
    print("\n🍎 Testing with AAPL (Apple)...")
    url3 = f"https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2024-05-01&to=2025-06-01&token={api_key}"
    
    try:
        resp = requests.get(url3, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Apple news: {len(data)} items")
        else:
            print(f"❌ Apple news failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Apple test exception: {e}")

if __name__ == "__main__":
    print("🧪 Testing your Finnhub setup...\n")
    test_your_finnhub()
    print("\n🏁 Test complete!")