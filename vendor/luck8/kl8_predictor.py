import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import warnings
import math
warnings.filterwarnings('ignore')

class KL8Predictor:
    def __init__(self, data_file='kl8_history.csv'):
        # 读取历史数据
        self.df = pd.read_csv(data_file)
        # 将开奖号码字符串转换为数字列表
        self.df['numbers_list'] = self.df['开奖号码'].apply(lambda x: [int(n) for n in x.split(',')])
        # 转换日期
        self.df['开奖日期'] = pd.to_datetime(self.df['开奖日期'])
        # 添加日期相关特征
        self.df['day_of_week'] = self.df['开奖日期'].dt.dayofweek
        self.df['day_of_month'] = self.df['开奖日期'].dt.day
        self.df['month'] = self.df['开奖日期'].dt.month
        # 按日期降序排序
        self.df = self.df.sort_values('开奖日期', ascending=False)
        
        # 中文数字映射
        self.chinese_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        # 奖金设置
        self.prize_settings = {
            '选一': {'中1': 4.6},
            '选二': {'中2': 19},
            '选三': {'中3': 53, '中2': 3},
            '选四': {'中4': 100, '中3': 5, '中2': 3},
            '选五': {'中5': 1000, '中4': 21, '中3': 3},
            '选六': {'中6': 2000, '中5': 50, '中4': 8, '中3': 3},
            '选七': {'中7': 4000, '中6': 100, '中5': 15, '中4': 4, '中3': 3},
            '选八': {'中8': 8000, '中7': 200, '中6': 30, '中5': 8, '中4': 3},
            '选九': {'中9': 15000, '中8': 400, '中7': 60, '中6': 15, '中5': 5, '中4': 3},
            '选十': {'中10': 50000, '中9': 800, '中8': 120, '中7': 30, '中6': 8, '中5': 4}
        }
        
    def get_number_from_play_type(self, play_type):
        """从玩法名称中获取选号数量"""
        chinese_num = play_type[1:]  # 去掉'选'字
        return self.chinese_nums[chinese_num]
        
    def analyze_frequency(self, days=None, weight_recent=True):
        """分析号码频率，支持全量数据分析和加权分析"""
        if days:
            recent_date = self.df['开奖日期'].max() - timedelta(days=days)
            data = self.df[self.df['开奖日期'] >= recent_date]
        else:
            data = self.df
            
        # 统计所有号码出现次数
        frequency = Counter()
        for idx, row in data.iterrows():
            numbers = row['numbers_list']
            if weight_recent:
                # 根据距离当前日期的天数计算权重
                days_diff = (data['开奖日期'].max() - row['开奖日期']).days
                weight = 1 / (days_diff + 1)  # 避免除以0
            else:
                weight = 1
                
            for num in numbers:
                frequency[num] += weight
                
        return frequency
    
    def analyze_cold_numbers(self, days=None):
        """分析未出现的号码"""
        frequency = self.analyze_frequency(days)
        cold_numbers = [num for num in range(1, 81) if frequency.get(num, 0) == 0]
        return cold_numbers
    
    def analyze_historical_same_period(self, target_date=None):
        """分析历史同期数据"""
        if target_date is None or pd.isna(target_date):
            target_date = self.df['开奖日期'].max() + timedelta(days=1)
            
        # 获取目标日期的特征
        if isinstance(target_date, pd.Timestamp):
            target_day = target_date.day
            target_month = target_date.month
            target_weekday = int(target_date.dayofweek)
        else:
            try:
                timestamp = pd.Timestamp(target_date)
                target_day = timestamp.day
                target_month = timestamp.month
                target_weekday = int(timestamp.dayofweek)
            except:
                # 如果转换失败，使用当前日期
                current_date = pd.Timestamp.now()
                target_day = current_date.day
                target_month = current_date.month
                target_weekday = int(current_date.dayofweek)
        
        # 分析同一日期的历史数据
        same_day_data = self.df[self.df['day_of_month'] == target_day]
        same_weekday_data = self.df[self.df['day_of_week'] == target_weekday]
        
        # 统计号码出现频率
        day_frequency = Counter()
        weekday_frequency = Counter()
        
        for numbers in same_day_data['numbers_list']:
            for num in numbers:
                day_frequency[num] += 1
                
        for numbers in same_weekday_data['numbers_list']:
            for num in numbers:
                weekday_frequency[num] += 1
                
        # 获取最常出现的号码
        top_day_numbers = sorted(day_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        top_weekday_numbers = sorted(weekday_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 计算平均出现次数
        day_avg = sum(day_frequency.values()) / (len(day_frequency) if day_frequency else 1)
        weekday_avg = sum(weekday_frequency.values()) / (len(weekday_frequency) if weekday_frequency else 1)
        
        # 分析重合点
        overlap_numbers = set()
        if len(same_day_data) >= 2:
            previous_numbers = set(same_day_data.iloc[1]['numbers_list'])
            current_numbers = set(same_day_data.iloc[0]['numbers_list'])
            overlap_numbers = previous_numbers.intersection(current_numbers)
        
        # 分析相邻数据的奇偶性
        last_draw = same_day_data.iloc[0]['numbers_list'] if not same_day_data.empty else []
        odd_count = sum(1 for num in last_draw if num % 2 == 1)
        even_count = len(last_draw) - odd_count
        
        # 分析数字间隔
        gaps = []
        if last_draw:
            sorted_nums = sorted(last_draw)
            gaps = [sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)]
        
        # 分析号码分区
        zones = {'1-20': 0, '21-40': 0, '41-60': 0, '61-80': 0}
        for num in last_draw:
            if 1 <= num <= 20:
                zones['1-20'] += 1
            elif 21 <= num <= 40:
                zones['21-40'] += 1
            elif 41 <= num <= 60:
                zones['41-60'] += 1
            else:
                zones['61-80'] += 1
        
        # 分析连号
        consecutive_count = 0
        max_consecutive = 0
        if last_draw:
            sorted_nums = sorted(last_draw)
            current_consecutive = 1
            for i in range(len(sorted_nums)-1):
                if sorted_nums[i+1] == sorted_nums[i] + 1:
                    current_consecutive += 1
                else:
                    max_consecutive = max(max_consecutive, current_consecutive)
                    current_consecutive = 1
            max_consecutive = max(max_consecutive, current_consecutive)
        
        return {
            'same_day_freq': day_frequency,
            'same_weekday_freq': weekday_frequency,
            'same_day_count': len(same_day_data),
            'same_weekday_count': len(same_weekday_data),
            'top_day_numbers': top_day_numbers,
            'top_weekday_numbers': top_weekday_numbers,
            'day_avg_freq': day_avg,
            'weekday_avg_freq': weekday_avg,
            'target_day': target_day,
            'target_weekday': ['一', '二', '三', '四', '五', '六', '日'][target_weekday],
            'overlap_numbers': sorted(list(overlap_numbers)),
            'odd_even_ratio': {'odd': odd_count, 'even': even_count},
            'number_gaps': gaps,
            'zone_distribution': zones,
            'max_consecutive': max_consecutive
        }
    
    def calculate_expected_value(self, play_type):
        """计算某种玩法的期望值"""
        numbers_count = self.get_number_from_play_type(play_type)
        total_draws = self.df.shape[0]  # 总开奖次数
        prize_info = self.prize_settings[play_type]
        
        # 计算各种中奖情况的概率和期望值
        expected_value = 0
        cost = 2  # 每注2元
        
        # 计算组合数
        def nCr(n, r):
            return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
        
        # 计算理论概率和实际概率的加权平均
        for hit_count, prize in prize_info.items():
            hit_num = int(hit_count[1:])  # 提取中奖个数
            
            # 理论概率
            theoretical_prob = (nCr(20, hit_num) * nCr(60, numbers_count - hit_num)) / nCr(80, numbers_count)
            
            # 实际概率（基于历史数据）
            hit_times = 0
            for numbers in self.df['numbers_list']:
                if len(set(numbers[:numbers_count]).intersection(set(numbers))) == hit_num:
                    hit_times += 1
            empirical_prob = hit_times / total_draws
            
            # 使用加权平均（给予历史数据更高的权重）
            probability = 0.3 * theoretical_prob + 0.7 * empirical_prob
            expected_value += probability * prize
        
        return expected_value - cost
    
    def find_best_strategy(self):
        """找出期望值最高的玩法"""
        strategies = []
        for play_type in self.prize_settings.keys():
            ev = self.calculate_expected_value(play_type)
            strategies.append({
                'play_type': play_type,
                'expected_value': ev,
                'numbers_count': self.get_number_from_play_type(play_type)
            })
        
        return sorted(strategies, key=lambda x: x['expected_value'], reverse=True)
    
    def analyze_number_patterns(self, days=30):
        """分析号码组合模式"""
        recent_date = self.df['开奖日期'].max() - timedelta(days=days)
        recent_data = self.df[self.df['开奖日期'] >= recent_date]
        
        patterns = {
            'consecutive_pairs': defaultdict(int),  # 连号对
            'number_pairs': defaultdict(int),       # 常见号码对
            'sum_range': [],                        # 和值范围
            'max_gaps': [],                         # 最大间隔
            'zone_combinations': defaultdict(int)   # 分区组合
        }
        
        for numbers in recent_data['numbers_list']:
            sorted_nums = sorted(numbers)
            
            # 分析连号对
            for i in range(len(sorted_nums)-1):
                if sorted_nums[i+1] == sorted_nums[i] + 1:
                    patterns['consecutive_pairs'][(sorted_nums[i], sorted_nums[i+1])] += 1
            
            # 分析常见号码对
            for i in range(len(sorted_nums)):
                for j in range(i+1, len(sorted_nums)):
                    patterns['number_pairs'][(sorted_nums[i], sorted_nums[j])] += 1
            
            # 分析和值范围
            numbers_sum = sum(sorted_nums)
            patterns['sum_range'].append(numbers_sum)
            
            # 分析最大间隔
            gaps = [sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)]
            patterns['max_gaps'].append(max(gaps))
            
            # 分析分区组合
            zone_counts = [0] * 4  # 4个分区的计数
            for num in sorted_nums:
                if num <= 20:
                    zone_counts[0] += 1
                elif num <= 40:
                    zone_counts[1] += 1
                elif num <= 60:
                    zone_counts[2] += 1
                else:
                    zone_counts[3] += 1
            patterns['zone_combinations'][tuple(zone_counts)] += 1
        
        # 处理统计结果
        result = {
            'common_consecutive_pairs': sorted(patterns['consecutive_pairs'].items(), key=lambda x: x[1], reverse=True)[:5],
            'common_number_pairs': sorted(patterns['number_pairs'].items(), key=lambda x: x[1], reverse=True)[:10],
            'sum_range_stats': {
                'mean': np.mean(patterns['sum_range']),
                'std': np.std(patterns['sum_range']),
                'min': min(patterns['sum_range']),
                'max': max(patterns['sum_range'])
            },
            'max_gap_stats': {
                'mean': np.mean(patterns['max_gaps']),
                'std': np.std(patterns['max_gaps'])
            },
            'common_zone_combinations': sorted(patterns['zone_combinations'].items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        return result

    def analyze_trend_patterns(self):
        """分析号码走势模式"""
        trends = {
            'hot_to_cold': [],  # 热号转冷号
            'cold_to_hot': [],  # 冷号转热号
            'stable_numbers': [],  # 稳定号码
            'volatile_numbers': []  # 波动号码
        }
        
        # 分析最近3期和前3期的频率变化
        recent_freq = self.analyze_frequency(days=3)
        previous_freq = self.analyze_frequency(days=6)
        
        for num in range(1, 81):
            recent_count = recent_freq.get(num, 0)
            previous_count = previous_freq.get(num, 0) - recent_count
            
            # 计算变化率
            change_rate = (recent_count - previous_count) / (previous_count + 1)  # 加1避免除以0
            
            if change_rate <= -0.5:  # 热转冷
                trends['hot_to_cold'].append(num)
            elif change_rate >= 0.5:  # 冷转热
                trends['cold_to_hot'].append(num)
            elif abs(change_rate) < 0.2:  # 稳定
                trends['stable_numbers'].append(num)
            else:  # 波动
                trends['volatile_numbers'].append(num)
        
        return trends

    def predict_next_numbers(self, predict_count=10):
        """预测下一期可能出现的号码"""
        next_draw_date = self.df['开奖日期'].max() + timedelta(days=1)
        
        # 1. 分析全量数据（带权重）
        all_time_freq = self.analyze_frequency(weight_recent=True)
        
        # 2. 分析最近30天数据
        recent_freq = self.analyze_frequency(days=30, weight_recent=False)
        
        # 3. 分析历史同期数据
        historical_same_period = self.analyze_historical_same_period(next_draw_date)
        
        # 4. 获取上期开奖号码
        last_draw = self.df['numbers_list'].iloc[0]
        last_draw_set = set(last_draw)
        
        # 5. 分析号码组合模式
        number_patterns = self.analyze_number_patterns()
        
        # 6. 分析走势模式
        trend_patterns = self.analyze_trend_patterns()
        
        # 综合评分
        number_scores = defaultdict(float)
        
        # 基础分数计算（调整权重）
        # 全量数据权重
        for num, freq in all_time_freq.items():
            number_scores[num] += freq * 0.15
            
        # 最近数据权重
        for num, freq in recent_freq.items():
            number_scores[num] += freq * 0.15
            
        # 同期数据权重
        day_freq = historical_same_period['same_day_freq']
        weekday_freq = historical_same_period['same_weekday_freq']
        
        for num in range(1, 81):
            day_score = day_freq.get(num, 0) / max(historical_same_period['same_day_count'], 1)
            weekday_score = weekday_freq.get(num, 0) / max(historical_same_period['same_weekday_count'], 1)
            number_scores[num] += (day_score + weekday_score) * 0.1
        
        # 号码组合模式分析（权重0.2）
        common_pairs = set()
        for (num1, num2), _ in number_patterns['common_number_pairs']:
            common_pairs.add(num1)
            common_pairs.add(num2)
        
        for num in range(1, 81):
            if num in common_pairs:
                number_scores[num] += 0.2
                
            # 考虑和值范围
            for potential_combination in self.generate_potential_combinations(num, number_patterns['sum_range_stats']):
                number_scores[num] += 0.1 * len(potential_combination) / 20
        
        # 走势模式分析（权重0.2）
        for num in range(1, 81):
            if num in trend_patterns['cold_to_hot']:
                number_scores[num] += 0.2
            elif num in trend_patterns['stable_numbers']:
                number_scores[num] += 0.15
            elif num in trend_patterns['volatile_numbers']:
                number_scores[num] += 0.1
        
        # 保留原有的其他分析逻辑
        overlap_numbers = set(historical_same_period['overlap_numbers'])
        for num in range(1, 81):
            if num in overlap_numbers:
                number_scores[num] += 0.1
        
        odd_even_ratio = historical_same_period['odd_even_ratio']
        target_odd_count = odd_even_ratio['odd']
        for num in range(1, 81):
            if (num % 2 == 1 and target_odd_count > 10) or (num % 2 == 0 and target_odd_count < 10):
                number_scores[num] += 0.1
                
        # 添加随机波动（±5%，减小随机性）
        for num in range(1, 81):
            number_scores[num] *= np.random.uniform(0.95, 1.05)
        
        # 选择得分最高的号码
        sorted_numbers = sorted(number_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 从前20个高分号码中随机选择predict_count个（减少随机范围）
        top_20_numbers = [num for num, _ in sorted_numbers[:20]]
        predicted_numbers = sorted(np.random.choice(top_20_numbers, size=predict_count, replace=False))
        
        return predicted_numbers
        
    def generate_potential_combinations(self, num, sum_stats):
        """生成潜在的号码组合"""
        combinations = []
        mean_sum = sum_stats['mean']
        std_sum = sum_stats['std']
        
        # 生成可能的组合（简化版）
        base_numbers = list(range(max(1, num-10), min(81, num+11)))
        np.random.shuffle(base_numbers)
        
        # 尝试生成3个符合和值范围的组合
        for _ in range(3):
            combination = [num]
            current_sum = num
            
            while len(combination) < 10 and current_sum < mean_sum + std_sum:
                for n in base_numbers:
                    if n not in combination and current_sum + n <= mean_sum + std_sum:
                        combination.append(n)
                        current_sum += n
                        break
                        
            if abs(current_sum - mean_sum) <= std_sum:
                combinations.append(combination)
                
        return combinations
    
    def generate_prediction_report(self):
        """生成预测报告"""
        next_draw_date = self.df['开奖日期'].max() + timedelta(days=1)
        
        # 1. 预测号码
        predicted_numbers = self.predict_next_numbers(10)
        
        # 2. 分析最优策略
        best_strategies = self.find_best_strategy()
        
        # 3. 获取历史同期数据
        historical_data = self.analyze_historical_same_period(next_draw_date)
        
        # 4. 生成报告
        report = {
            'predicted_numbers': predicted_numbers,
            'best_strategies': best_strategies[:3],  # 前三个最优策略
            'prediction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'next_draw_date': next_draw_date.strftime('%Y-%m-%d'),
            'last_draw_date': self.df['开奖日期'].iloc[0].strftime('%Y-%m-%d'),
            'last_draw_numbers': self.df['numbers_list'].iloc[0],
            'historical_data': historical_data
        }
        
        return report

def main():
    # 创建预测器实例
    predictor = KL8Predictor()
    
    # 生成多组预测号码
    print("\n=== 快乐8预测报告 ===")
    print(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"上期开奖号码: {predictor.df['numbers_list'].iloc[0]}")
    
    print("\n生成5组预测号码:")
    for i in range(5):
        predicted_numbers = predictor.predict_next_numbers(10)
        print(f"第{i+1}组: {predicted_numbers}")
    
    print("\n注意：本预测仅供参考，购彩需理性，请注意控制投注金额。")

if __name__ == "__main__":
    main() 