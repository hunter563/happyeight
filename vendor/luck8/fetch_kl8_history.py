import requests
import json
import csv
import time
from datetime import datetime

def fetch_kl8_data(page_num):
    url = "https://jc.zhcw.com/port/client_json.php"
    
    params = {
        'callback': f'jQuery1122039414901311157857_{int(time.time()*1000)}',
        'transactionType': '10001001',
        'lotteryId': '6',
        'issueCount': '2000',  # 增加获取期数
        'startIssue': '',
        'endIssue': '',
        'startDate': '2020-10-28',  # 快乐8开始日期
        'endDate': datetime.now().strftime('%Y-%m-%d'),  # 当前日期
        'type': '2',  # 修改type参数
        'pageNum': str(page_num),
        'pageSize': '2000',  # 增加每页数量
        'tt': str(time.time()),
        '_': str(int(time.time()*1000))
    }
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,vi;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': 'https://www.zhcw.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    
    try:
        print(f"Requesting URL: {url}")
        print(f"Parameters: {json.dumps(params, indent=2)}")
        
        response = requests.get(url, params=params, headers=headers)
        print(f"Response status code: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        
        # 检查响应状态码
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return None
            
        # 从JSONP响应中提取JSON数据
        try:
            json_str = response.text[response.text.index('(') + 1:response.text.rindex(')')]
            data = json.loads(json_str)
            
            # 检查返回的数据结构
            if 'data' not in data or 'pages' not in data or 'total' not in data:
                print("Error: Invalid data structure")
                print(f"Data keys: {data.keys()}")
                return None
                
            print(f"Total records in response: {len(data['data'])}")
            return data
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            return None
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_to_csv(data_list, filename='kl8_history.csv'):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['期号', '开奖日期', '开奖号码'])
            # 写入数据
            for row in data_list:
                writer.writerow(row)
        print(f"Successfully saved {len(data_list)} records to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    all_data = []
    page = 1
    total_pages = None
    max_retries = 3
    
    while True:
        print(f"\nFetching page {page}...")
        
        # 添加重试机制
        for retry in range(max_retries):
            response_data = fetch_kl8_data(page)
            if response_data:
                break
            print(f"Retry {retry + 1}/{max_retries}")
            time.sleep(2)  # 重试前等待2秒
        
        if not response_data:
            print("Failed to fetch data after retries")
            break
            
        if total_pages is None:
            total_pages = int(response_data['pages'])
            total_records = int(response_data['total'])
            print(f"Total pages: {total_pages}")
            print(f"Total records: {total_records}")
        
        try:
            for item in response_data['data']:
                # 获取期号
                issue = item['issue']
                # 格式化日期（只保留日期部分）
                date = item['openTime']
                # 获取开奖号码并处理
                numbers = item['frontWinningNum'].strip().split()  # 用空格分割
                numbers = [int(n) for n in numbers]
                numbers.sort()  # 对号码排序
                numbers = ','.join(map(str, numbers))
                
                all_data.append([issue, date, numbers])
            
            print(f"Processed {len(response_data['data'])} records from page {page}")
        except Exception as e:
            print(f"Error processing data: {e}")
            print(f"Problematic item: {item}")
            continue
        
        if page >= total_pages:
            break
            
        page += 1
        time.sleep(1)  # 添加延迟，避免请求过快
    
    # 保存数据到CSV文件
    if all_data:
        # 按期号降序排序（最新的在前面）
        all_data.sort(key=lambda x: int(x[0]), reverse=True)
        save_to_csv(all_data)
        print(f"Total records saved: {len(all_data)}")
    else:
        print("No data collected")

if __name__ == "__main__":
    main() 