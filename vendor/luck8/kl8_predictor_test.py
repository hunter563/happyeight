import pandas as pd
from datetime import datetime
from kl8_predictor import KL8Predictor
import copy

class KL8PredictorTester:
    def __init__(self, data_file='kl8_history.csv'):
        """初始化测试器"""
        self.original_df = pd.read_csv(data_file)
        # 转换日期和号码格式
        self.original_df['开奖日期'] = pd.to_datetime(self.original_df['开奖日期'])
        self.original_df['numbers_list'] = self.original_df['开奖号码'].apply(lambda x: [int(n) for n in x.split(',')])
        # 按日期降序排序
        self.original_df = self.original_df.sort_values('开奖日期', ascending=False)
        
    def test_single_draw(self, test_date, predictor):
        """测试单期预测结果"""
        # 获取实际开奖号码
        actual_numbers = self.original_df[self.original_df['开奖日期'] == test_date]['numbers_list'].iloc[0]
        actual_numbers_set = set(actual_numbers)
        
        # 生成5组预测号码
        predictions = []
        hit_counts = []
        for _ in range(5):
            predicted = predictor.predict_next_numbers(10)
            predictions.append(predicted)
            # 计算命中数
            hits = len(set(predicted) & actual_numbers_set)
            hit_counts.append(hits)
            
        return {
            'date': test_date,
            'actual_numbers': actual_numbers,
            'predictions': predictions,
            'hit_counts': hit_counts,
            'max_hits': max(hit_counts),
            'avg_hits': sum(hit_counts) / len(hit_counts)
        }
    
    def test_multiple_draws(self, num_draws=100):
        """测试多期预测结果"""
        results = []
        total_dates = min(num_draws, len(self.original_df)-1)  # -1确保有前期数据可用
        
        print(f"\n开始测试最近{total_dates}期预测准确性...")
        print("="*50)
        
        for i in range(total_dates):
            test_date = pd.Timestamp(self.original_df.iloc[i]['开奖日期'])
            print(f"\r测试进度: {i+1}/{total_dates}", end="")
            
            # 创建仅包含测试日期之前数据的DataFrame
            test_df = self.original_df[self.original_df['开奖日期'] < test_date].copy()
            
            if len(test_df) == 0:
                print(f"\n警告：{test_date}之前没有历史数据，跳过该期测试")
                continue
                
            # 创建新的预测器实例
            predictor = KL8Predictor()
            predictor.df = test_df  # 替换数据源
            # 重新初始化日期相关特征
            predictor.df['day_of_week'] = predictor.df['开奖日期'].dt.dayofweek.astype(int)
            predictor.df['day_of_month'] = predictor.df['开奖日期'].dt.day.astype(int)
            predictor.df['month'] = predictor.df['开奖日期'].dt.month.astype(int)
            
            # 测试该期预测结果
            result = self.test_single_draw(test_date, predictor)
            results.append(result)
        
        print("\n\n测试完成！生成测试报告...")
        self.generate_test_report(results)
        
    def generate_test_report(self, results):
        """生成测试报告"""
        print("\n=== 快乐8预测算法测试报告 ===")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试期数: {len(results)}期")
        print("\n详细命中统计:")
        print("-" * 50)
        
        # 统计总体情况
        total_predictions = len(results) * 5  # 每期5组预测
        total_max_hits = sum(r['max_hits'] for r in results)
        total_avg_hits = sum(r['avg_hits'] for r in results) / len(results)
        
        # 统计各命中数量的次数
        hit_distribution = {i: 0 for i in range(11)}  # 0-10个命中的分布
        for result in results:
            for hits in result['hit_counts']:
                hit_distribution[hits] += 1
        
        # 输出每期详细信息
        for result in results:
            print(f"\n日期: {result['date'].strftime('%Y-%m-%d')}")
            print(f"实际开奖: {result['actual_numbers']}")
            print("预测号码及命中数:")
            for i, (pred, hits) in enumerate(zip(result['predictions'], result['hit_counts']), 1):
                print(f"第{i}组 {pred} (命中: {hits}个)")
            print(f"最大命中: {result['max_hits']}个, 平均命中: {result['avg_hits']:.1f}个")
        
        print("\n=== 统计摘要 ===")
        print(f"总预测组数: {total_predictions}组")
        print(f"平均每期最大命中数: {total_max_hits/len(results):.2f}")
        print(f"总体平均命中数: {total_avg_hits:.2f}")
        print("\n命中分布:")
        for hits, count in hit_distribution.items():
            percentage = (count / total_predictions) * 100
            print(f"{hits}个号码命中: {count}次 ({percentage:.1f}%)")
        
        # 计算实用价值
        print("\n=== 实用价值分析 ===")
        hit_5_plus = sum(count for hits, count in hit_distribution.items() if hits >= 5)
        hit_5_plus_rate = (hit_5_plus / total_predictions) * 100
        print(f"命中5个及以上号码概率: {hit_5_plus_rate:.1f}%")
        
        print("\n注意：本测试结果仅供参考，购彩需理性，请注意控制投注金额。")

def main():
    # 创建测试器实例
    tester = KL8PredictorTester()
    # 执行测试
    tester.test_multiple_draws(500)

if __name__ == "__main__":
    main() 