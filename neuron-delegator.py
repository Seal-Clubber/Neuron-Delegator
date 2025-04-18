import asyncio
import aiohttp
import json
import os
import webbrowser
from urllib.parse import quote

# Settings
BATCH_SIZE = 5
SEM = asyncio.Semaphore(BATCH_SIZE)
MAX_WALLETS_PER_URL = 100

def read_ip_ports(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return await response.text()
    except:
        return None

def extract_wallet(api_test_data):
    try:
        parsed = json.loads(api_test_data)
        return parsed.get("data", "")
    except:
        return None

async def process_ip(session, ip_port):
    url = f"http://{ip_port}/api/test"
    data = await fetch(session, url)
    wallet = extract_wallet(data)
    return ip_port, wallet

async def limited_process_ip(session, ip_port):
    async with SEM:
        return await process_ip(session, ip_port)

async def main():
    ip_ports = read_ip_ports("ip.txt")
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{'IP:PORT':<22} | Wallet")
    print("-" * 40)

    wallets = []
    async with aiohttp.ClientSession() as session:
        results = [None] * len(ip_ports)
        for i in range(0, len(ip_ports), BATCH_SIZE):
            batch = ip_ports[i:i + BATCH_SIZE]
            tasks = [limited_process_ip(session, ip) for ip in batch]
            batch_results = await asyncio.gather(*tasks)
            for idx, (ip, wallet) in enumerate(batch_results):
                short = f"{wallet[:4]}..{wallet[-4:]}" if wallet and len(wallet) >= 8 else "N/A"
                print(f"{ip:<22} | {short}")
                if wallet:
                    wallets.append(wallet)

    print("\n")

    # Group wallets and open tabs
    for i in range(0, len(wallets), MAX_WALLETS_PER_URL):
        group = wallets[i:i + MAX_WALLETS_PER_URL]
        print(f"wallets: {len(group)}")
        print(" ".join(group))
        print()

        # Open the corresponding tab
        joined = quote(" ".join(group))  # encode spaces as %20
        url = f"http://127.0.0.1:24601/stake/for/address/{joined}"
        #webbrowser.open_new_tab(url)

    print(f"Total wallets: {len(wallets)}")

if __name__ == "__main__":
    asyncio.run(main())
