import re
import subprocess
import sys
from collections import defaultdict

since = sys.argv[1] if len(sys.argv) > 1 else "7 days ago"
until = sys.argv[2] if len(sys.argv) > 2 else "now"

result = subprocess.run(
    ["journalctl", "-u", "kis-bot", "--since", since, "--until", until, "--no-pager"],
    capture_output=True, text=True
)
lines = result.stdout.splitlines()
print(f"조회 범위: {since} ~ {until} (로그 {len(lines)}줄)")
print()

pattern = re.compile(r"\[(.+?)\] 현재가: ([\d,]+)원 \| 보유수량: (\d+)주 \| 매수기준: ([\d,]+)원 이하")

min_price = {}
buy_threshold = {}
buy_hits = defaultdict(int)
total_lines = defaultdict(int)

for line in lines:
    m = pattern.search(line)
    if not m:
        continue
    name, price_s, qty_s, buy_s = m.groups()
    price = int(price_s.replace(",", ""))
    buy_price = int(buy_s.replace(",", ""))
    buy_threshold[name] = buy_price
    total_lines[name] += 1
    if name not in min_price or price < min_price[name]:
        min_price[name] = price
    if price <= buy_price:
        buy_hits[name] += 1

print(f"{'종목':10} {'조회횟수':>8} {'기간중 최저가':>14} {'매수기준':>14} {'조건충족횟수':>10}")
for name in min_price:
    print(f"{name:10} {total_lines[name]:>8} {min_price[name]:>14,} {buy_threshold.get(name, 0):>14,} {buy_hits[name]:>10}")

print()
print("매수 체결 기록:")
buy_lines = [l for l in lines if "매수 체결" in l]
print(f"  {len(buy_lines)}건")
for l in buy_lines:
    print(" ", l)

print()
error_count = sum(1 for l in lines if "처리 중 오류" in l)
print(f"에러 발생 횟수: {error_count}건")

print()
print("서비스 (재)시작 횟수 (하루 1번씩은 정상):")
start_count = sum(1 for l in lines if "자동매매 시작" in l)
print(f"  {start_count}건")
