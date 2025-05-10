import asyncio
import aiohttp
import json
import os

# Settings
BATCH_SIZE = 5
SEM = asyncio.Semaphore(BATCH_SIZE)

# Global counters
total_neurons = 0
total_ok_response = 0

def read_ip_ports(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return await response.text()
    except Exception:
        return None

def extract_wallet(api_test_data):
    try:
        parsed = json.loads(api_test_data)
        return parsed.get("data", "")
    except Exception:
        return None

async def stake_wallet(session, wallet):
    stake_url = f"http://127.0.0.1:24601/stake/for/address/{wallet}"
    try:
        async with session.get(stake_url) as response:
            return await response.text()
    except Exception as e:
        return f"Failed to stake for wallet {wallet}: {e}"

async def process_ip(session, ip_port):
    global total_neurons, total_ok_response

    url = f"http://{ip_port}/api/test"
    data = await fetch(session, url)
    wallet = extract_wallet(data)

    total_neurons += 1  # Always increment neurons even if wallet is missing

    if wallet and len(wallet) == 34:
        stake_response = await stake_wallet(session, wallet)

        if stake_response and stake_response.strip() == "OK":
            total_ok_response += 1

        return f"{ip_port:<22} | {wallet:<34} | {stake_response}"
    else:
        return f"{ip_port:<22} | Wallet not found"

async def limited_process_ip(session, ip_port):
    async with SEM:
        return await process_ip(session, ip_port)

async def main():
    global total_neurons, total_ok_response

    ip_ports = read_ip_ports("ip.txt")
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{'IP:PORT':<22} | {'Wallet':<34} | Stake Response")
    print("-----------------------+------------------------------------+----------------")

    async with aiohttp.ClientSession() as session:
        results = []
        for i in range(0, len(ip_ports), BATCH_SIZE):
            batch = ip_ports[i:i + BATCH_SIZE]
            tasks = [limited_process_ip(session, ip) for ip in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            for result in batch_results:
                print(result)

    print("\nSummary:")
    print(f"Total Neurons      : {total_neurons}")
    print(f"Total OK Responses : {total_ok_response}")

if __name__ == "__main__":
    asyncio.run(main())
