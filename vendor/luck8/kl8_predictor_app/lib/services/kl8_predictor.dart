import 'dart:math';
import '../models/lottery_draw.dart';
import 'database_service.dart';
import 'dart:async';
import 'dart:developer';

class KL8Predictor {
  final DatabaseService _dbService;
  final Random _random = Random();
  List<LotteryDraw> _allDraws = [];
  DateTime? _lastUpdateTime;

  // 定义号码区间
  static const List<Map<String, int>> _numberRanges = [
    {'start': 1, 'end': 20}, // 第一区间
    {'start': 21, 'end': 40}, // 第二区间
    {'start': 41, 'end': 60}, // 第三区间
    {'start': 61, 'end': 80}, // 第四区间
  ];

  KL8Predictor({DatabaseService? dbService})
      : _dbService = dbService ?? DatabaseService();

  Future<void> _ensureData() async {
    try {
      if (_allDraws.isEmpty ||
          _lastUpdateTime == null ||
          DateTime.now().difference(_lastUpdateTime!) > Duration(hours: 1)) {
        print('开始加载历史数据...');
        _allDraws = await _dbService.getAllDraws();
        print('数据加载完成，共 ${_allDraws.length} 条记录');
        _allDraws.sort((a, b) => b.drawDate.compareTo(a.drawDate)); // 按日期降序排序
        _lastUpdateTime = DateTime.now();
      }
    } catch (e) {
      print('数据加载错误: $e');
      if (_allDraws.isEmpty) {
        throw Exception('无法加载历史数据，且没有缓存数据可用');
      }
      // 如果有缓存数据，继续使用
      print('使用缓存数据继续运行，共 ${_allDraws.length} 条记录');
    }
  }

  // 分析号码频率
  Map<int, double> analyzeFrequency({int? days, bool weightRecent = true}) {
    Map<int, double> frequency = {};
    DateTime? cutoffDate;

    if (days != null) {
      cutoffDate = _allDraws.first.drawDate.subtract(Duration(days: days));
    }

    for (var draw in _allDraws) {
      if (cutoffDate != null && draw.drawDate.isBefore(cutoffDate)) {
        break;
      }

      double weight = 1.0;
      if (weightRecent) {
        // 计算与最新日期的天数差
        int daysDiff =
            _allDraws.first.drawDate.difference(draw.drawDate).inDays;
        weight = 1 / (daysDiff + 1); // 避免除以0
      }

      for (var number in draw.numbers) {
        frequency[number] = (frequency[number] ?? 0) + weight;
      }
    }

    return frequency;
  }

  // 分析号码分布
  Map<String, dynamic> analyzeDistribution({int lookbackCount = 50}) {
    var recentDraws = _allDraws.take(lookbackCount).toList();
    Map<int, int> rangeDistribution = {};
    Map<int, List<int>> consecutiveNumbers = {};
    Map<int, int> gapDistribution = {};

    for (var draw in recentDraws) {
      // 分析区间分布
      for (var number in draw.numbers) {
        for (var range in _numberRanges) {
          if (number >= range['start']! && number <= range['end']!) {
            rangeDistribution[range['start']!] =
                (rangeDistribution[range['start']!] ?? 0) + 1;
            break;
          }
        }
      }

      // 分析连号
      List<int> sortedNumbers = List.from(draw.numbers)..sort();
      for (int i = 0; i < sortedNumbers.length - 1; i++) {
        if (sortedNumbers[i + 1] - sortedNumbers[i] == 1) {
          consecutiveNumbers[sortedNumbers[i]] =
              (consecutiveNumbers[sortedNumbers[i]] ?? [])
                ..add(sortedNumbers[i + 1]);
        }
      }

      // 分析号码间隔
      for (int i = 0; i < sortedNumbers.length - 1; i++) {
        int gap = sortedNumbers[i + 1] - sortedNumbers[i];
        gapDistribution[gap] = (gapDistribution[gap] ?? 0) + 1;
      }
    }

    // 计算每个区间的平均数量
    Map<int, double> rangeAverages = {};
    for (var range in _numberRanges) {
      int total = rangeDistribution[range['start']!] ?? 0;
      rangeAverages[range['start']!] = total / recentDraws.length;
    }

    return {
      'rangeDistribution': Map<int, int>.from(rangeDistribution),
      'rangeAverages': Map<int, double>.from(rangeAverages),
      'consecutiveNumbers': Map<int, List<int>>.from(consecutiveNumbers),
      'gapDistribution': Map<int, int>.from(gapDistribution),
    };
  }

  // 分析历史同期数据
  Map<String, dynamic> analyzeHistoricalSamePeriod(DateTime targetDate) {
    int targetDay = targetDate.day;
    int targetMonth = targetDate.month;
    int targetWeekday = targetDate.weekday;

    var sameDayData =
        _allDraws.where((draw) => draw.drawDate.day == targetDay).toList();
    var sameWeekdayData = _allDraws
        .where((draw) => draw.drawDate.weekday == targetWeekday)
        .toList();

    // 统计号码出现频率
    Map<int, int> dayFrequency = {};
    Map<int, int> weekdayFrequency = {};

    for (var draw in sameDayData) {
      for (var number in draw.numbers) {
        dayFrequency[number] = (dayFrequency[number] ?? 0) + 1;
      }
    }

    for (var draw in sameWeekdayData) {
      for (var number in draw.numbers) {
        weekdayFrequency[number] = (weekdayFrequency[number] ?? 0) + 1;
      }
    }

    // 获取重合号码
    Set<int> overlapNumbers = {};
    if (sameDayData.length >= 2) {
      var previousNumbers = Set<int>.from(sameDayData[1].numbers);
      var currentNumbers = Set<int>.from(sameDayData[0].numbers);
      overlapNumbers = previousNumbers.intersection(currentNumbers);
    }

    // 分析最后一期的奇偶性和区间分布
    var lastDraw = sameDayData.isNotEmpty ? sameDayData[0].numbers : [];
    int oddCount = lastDraw.where((num) => num % 2 == 1).length;
    int evenCount = lastDraw.length - oddCount;

    // 分析区间分布
    Map<int, int> rangeCount = {};
    for (var number in lastDraw) {
      for (var range in _numberRanges) {
        if (number >= range['start']! && number <= range['end']!) {
          rangeCount[range['start']!] = (rangeCount[range['start']!] ?? 0) + 1;
          break;
        }
      }
    }

    return {
      'sameDayFreq': Map<int, int>.from(dayFrequency),
      'sameWeekdayFreq': Map<int, int>.from(weekdayFrequency),
      'sameDayCount': sameDayData.length,
      'sameWeekdayCount': sameWeekdayData.length,
      'overlapNumbers': overlapNumbers.toList()..sort(),
      'oddEvenRatio': {'odd': oddCount, 'even': evenCount},
      'rangeCount': Map<int, int>.from(rangeCount),
    };
  }

  // 分析和值范围
  Map<String, double> analyzeSumRange({int lookbackCount = 50}) {
    var recentDraws = _allDraws.take(lookbackCount).toList();
    var sums = recentDraws
        .map((draw) => draw.numbers.reduce((a, b) => a + b))
        .toList();

    double mean = sums.reduce((a, b) => a + b) / sums.length;
    double variance =
        sums.map((s) => pow(s - mean, 2)).reduce((a, b) => a + b) / sums.length;
    double std = sqrt(variance);

    return {
      'mean': mean,
      'std': std,
      'min': sums.reduce(min).toDouble(),
      'max': sums.reduce(max).toDouble(),
    };
  }

  // 分析走势模式
  Map<String, List<int>> analyzeTrendPatterns() {
    // 分析最近3期和前3期的频率变化
    var recentFreq = Map<int, int>.fromIterable(List.generate(80, (i) => i + 1),
        key: (i) => i as int,
        value: (i) =>
            _allDraws.take(3).where((draw) => draw.numbers.contains(i)).length);

    var previousFreq = Map<int, int>.fromIterable(
        List.generate(80, (i) => i + 1),
        key: (i) => i as int,
        value: (i) => _allDraws
            .skip(3)
            .take(3)
            .where((draw) => draw.numbers.contains(i))
            .length);

    var trends = {
      'hot_to_cold': <int>[],
      'cold_to_hot': <int>[],
      'stable_numbers': <int>[],
      'volatile_numbers': <int>[]
    };

    for (int num = 1; num <= 80; num++) {
      var recentCount = recentFreq[num] ?? 0;
      var previousCount = previousFreq[num] ?? 0;
      var changeRate = (recentCount - previousCount) / (previousCount + 1);

      if (changeRate <= -0.5) {
        trends['hot_to_cold']!.add(num);
      } else if (changeRate >= 0.5) {
        trends['cold_to_hot']!.add(num);
      } else if (changeRate.abs() < 0.2) {
        trends['stable_numbers']!.add(num);
      } else {
        trends['volatile_numbers']!.add(num);
      }
    }

    return Map<String, List<int>>.from(trends);
  }

  // 验证号码组合
  bool validateCombination(List<int> numbers, Map<String, double> sumStats) {
    print('开始验证号码组合: $numbers');
    if (numbers.length != 10) {
      print('号码数量不符合要求');
      return false;
    }

    // 1. 验证和值范围
    int sum = numbers.reduce((a, b) => a + b);
    double mean = sumStats['mean']!;
    double std = sumStats['std']!;
    print(
        '和值验证 - 当前和值: $sum, 均值: ${mean.toStringAsFixed(2)}, 标准差: ${std.toStringAsFixed(2)}');
    if (sum < mean - 3 * std || sum > mean + 3 * std) {
      // 放宽到3个标准差
      print('和值超出范围');
      return false;
    }

    // 2. 验证区间分布
    var zoneCounts = List.filled(4, 0);
    for (var num in numbers) {
      for (int i = 0; i < _numberRanges.length; i++) {
        if (num >= _numberRanges[i]['start']! &&
            num <= _numberRanges[i]['end']!) {
          zoneCounts[i]++;
          break;
        }
      }
    }
    print('区间分布: $zoneCounts');
    // 每个区间至少1个号码，最多6个号码
    if (zoneCounts.any((count) => count == 0 || count > 6)) {
      // 放宽到6个，但必须每个区间都有数字
      print('区间分布不均匀');
      return false;
    }

    // 3. 验证连号数量
    var sortedNumbers = List<int>.from(numbers)..sort();
    int consecutiveCount = 0;
    int maxConsecutive = 0;
    for (int i = 0; i < sortedNumbers.length - 1; i++) {
      if (sortedNumbers[i + 1] == sortedNumbers[i] + 1) {
        consecutiveCount++;
        maxConsecutive = max(maxConsecutive, consecutiveCount + 1);
      } else {
        consecutiveCount = 0;
      }
    }
    print('最大连号数: $maxConsecutive');
    // 最多允许5个连号
    if (maxConsecutive > 5) {
      // 放宽到5个连号
      print('连号数量过多');
      return false;
    }

    print('验证通过');
    return true;
  }

  // 预测下一期号码
  Future<List<List<int>>> predictNextNumbers({int groupCount = 5}) async {
    try {
      print('开始预测号码 predictNextNumbers - groupCount: $groupCount');
      final stopwatch = Stopwatch()..start();
      final timeoutDuration = Duration(seconds: 30);

      print('步骤1/4: 确保数据已加载');
      await _ensureData();
      if (_allDraws.isEmpty) {
        print('历史数据为空，无法预测');
        return [];
      }

      print('步骤2/4: 开始数据分析');
      // 异步并行处理分析计算
      final analysisResults = await Future.wait([
        Future(() {
          print('分析全时段频率...');
          return analyzeFrequency(weightRecent: true);
        }),
        Future(() {
          print('分析近期频率...');
          return analyzeFrequency(days: 30, weightRecent: false);
        }),
        Future(() {
          print('分析历史同期数据...');
          return analyzeHistoricalSamePeriod(
              _allDraws.first.drawDate.add(Duration(days: 1)));
        }),
        Future(() {
          print('分析和值范围...');
          return analyzeSumRange(lookbackCount: 50);
        }),
        Future(() {
          print('分析走势模式...');
          return analyzeTrendPatterns();
        }),
        Future(() {
          print('分析热门模式...');
          return analyzeHotPatterns(lookbackCount: 100);
        })
      ]);

      var allTimeFreq = analysisResults[0];
      var recentFreq = analysisResults[1];
      var historicalData = analysisResults[2];
      var sumStats = analysisResults[3];
      var trendPatterns = analysisResults[4];
      var hotPatterns = analysisResults[5];

      print('步骤3/4: 生成预测组合');
      List<List<int>> predictions = [];

      // 计算号码得分
      Map<int, double> numberScores = {};
      for (int num = 1; num <= 80; num++) {
        double score = 0.0;

        // 基础分数计算
        score += (allTimeFreq[num] ?? 0) * 0.15;
        score += (recentFreq[num] ?? 0) * 0.15;

        // 同期数据分数
        var dayFreq = historicalData['sameDayFreq'][num] ?? 0;
        var weekdayFreq = historicalData['sameWeekdayFreq'][num] ?? 0;
        score += (dayFreq / (historicalData['sameDayCount'] ?? 1) +
                weekdayFreq / (historicalData['sameWeekdayCount'] ?? 1)) *
            0.10;

        // 走势分数
        if (trendPatterns['cold_to_hot']!.contains(num)) {
          score += 0.20;
        } else if (trendPatterns['stable_numbers']!.contains(num)) {
          score += 0.15;
        } else if (trendPatterns['volatile_numbers']!.contains(num)) {
          score += 0.10;
        }

        // 热门号码分数
        var hotNumbersMap = hotPatterns['hotNumbers'] as Map<int, int>;
        if (hotNumbersMap.containsKey(num)) {
          score += 0.20 * (hotNumbersMap[num]! / hotNumbersMap.values.first);
        }

        // 重合号码分数
        if (historicalData['overlapNumbers'].contains(num)) {
          score += 0.10;
        }

        // 奇偶平衡分数
        var oddEvenRatio = historicalData['oddEvenRatio'];
        if ((num % 2 == 1 && oddEvenRatio['odd'] < 5) ||
            (num % 2 == 0 && oddEvenRatio['even'] < 5)) {
          score += 0.10;
        }

        // 添加随机波动
        score *= 0.95 + (_random.nextDouble() * 0.10);
        numberScores[num] = score;
      }

      int maxAttempts = 100;
      int currentAttempts = 0;
      double validationThreshold = 3.0;
      List<int> selectedNumbers = [];

      while (predictions.length < groupCount &&
          currentAttempts < maxAttempts &&
          stopwatch.elapsed < timeoutDuration) {
        currentAttempts++;

        // 使用轮盘赌选择法
        var sortedNumbers = numberScores.entries.toList()
          ..sort((a, b) => b.value.compareTo(a.value));

        var topNumbers = sortedNumbers.take(20).toList();
        var totalScore = topNumbers.map((e) => e.value).reduce((a, b) => a + b);
        selectedNumbers = <int>[];

        // 选择号码
        while (selectedNumbers.length < 10) {
          double randomPoint = _random.nextDouble() * totalScore;
          double currentSum = 0;

          for (var entry in topNumbers) {
            currentSum += entry.value;
            if (currentSum >= randomPoint &&
                !selectedNumbers.contains(entry.key)) {
              selectedNumbers.add(entry.key);
              break;
            }
          }

          // 如果没有选中号码，随机选择一个未使用的号码
          if (selectedNumbers.length < 10 &&
              selectedNumbers.length == selectedNumbers.toSet().length) {
            var unusedNumbers = topNumbers
                .where((e) => !selectedNumbers.contains(e.key))
                .toList();
            if (unusedNumbers.isNotEmpty) {
              selectedNumbers.add(
                  unusedNumbers[_random.nextInt(unusedNumbers.length)].key);
            }
          }
        }

        selectedNumbers.sort();

        // 首先验证和值
        int sum = selectedNumbers.reduce((a, b) => a + b);
        double mean = sumStats['mean']!;
        double std = sumStats['std']!;

        bool isValid = sum >= mean - validationThreshold * std &&
            sum <= mean + validationThreshold * std;

        // 如果和值验证通过，进行完整验证
        if (isValid) {
          // 创建sumStats的副本，确保类型正确
          Map<String, double> validationStats = {
            'mean': sumStats['mean']!,
            'std': sumStats['std']!,
            'min': sumStats['min']!,
            'max': sumStats['max']!
          };
          isValid = validateCombination(selectedNumbers, validationStats);
        }

        if (isValid) {
          predictions.add(selectedNumbers);
          print('成功生成第 ${predictions.length} 组预测: $selectedNumbers');
          validationThreshold = 3.0; // 重置阈值
        } else if (currentAttempts % 20 == 0) {
          // 每20次尝试放宽一次验证条件
          validationThreshold += 0.5;
          print('放宽验证条件，新的标准差阈值: $validationThreshold');
        }

        // 如果运行时间过长，适当放宽条件
        if (stopwatch.elapsed > Duration(seconds: 15) && predictions.isEmpty) {
          validationThreshold += 0.5;
          print('运行时间较长，放宽验证条件到: $validationThreshold');
        }
      }

      print('步骤4/4: 完成预测');
      // 如果没有生成足够的预测，使用最后一组号码
      if (predictions.isEmpty && currentAttempts >= maxAttempts) {
        print('达到最大尝试次数，使用最后一次生成的号码');
        predictions.add(selectedNumbers);
      }

      print(
          '预测生成完成，共生成 ${predictions.length} 组预测，总尝试次数: $currentAttempts，用时: ${stopwatch.elapsed.inSeconds}秒');
      return predictions;
    } catch (e, stackTrace) {
      print('预测过程中发生错误: $e');
      print('错误堆栈: $stackTrace');
      return [];
    }
  }

  // 生成预测报告
  Future<Map<String, dynamic>> generatePredictionReport() async {
    print('开始生成预测报告');
    await _ensureData();
    if (_allDraws.isEmpty) {
      print('历史数据为空，无法生成报告');
      return {};
    }

    print('开始获取预测数据');
    var predictions = await predictNextNumbers();
    print('预测号码生成完成');
    var nextDrawDate = _allDraws.first.drawDate.add(Duration(days: 1));
    var historicalData = analyzeHistoricalSamePeriod(nextDrawDate);
    var distributionData = analyzeDistribution();
    var sumStats = analyzeSumRange();
    var trendPatterns = analyzeTrendPatterns();
    print('所有分析数据获取完成');

    return {
      'predictedNumbers': predictions,
      'predictionTime': DateTime.now(),
      'nextDrawDate': nextDrawDate,
      'lastDrawDate': _allDraws.first.drawDate,
      'lastDrawNumbers': _allDraws.first.numbers,
      'historicalData': historicalData,
      'distributionData': distributionData,
      'sumStats': sumStats,
      'trendPatterns': trendPatterns,
    };
  }

  Future<List<int>> generatePrediction() async {
    try {
      print('开始生成预测...');
      await _ensureData();
      if (_allDraws.isEmpty) {
        throw Exception('无法获取历史开奖数据');
      }

      // 获取下一期日期
      DateTime nextDrawDate = _allDraws.first.drawDate.add(Duration(days: 1));
      print('开始分析历史同期数据');
      var historicalData = analyzeHistoricalSamePeriod(nextDrawDate);
      print('历史同期数据分析完成');

      print('开始分析全量数据');
      var allTimeFreq = analyzeFrequency(weightRecent: true);
      print('全量数据分析完成');

      print('开始分析近期数据');
      var recentFreq = analyzeFrequency(days: 30, weightRecent: false);
      var sumStats = analyzeSumRange(lookbackCount: 50);
      var trendPatterns = analyzeTrendPatterns();
      print('近期数据分析完成');

      print('开始选号...');
      var predictions = await predictNextNumbers(groupCount: 1);
      if (predictions.isEmpty) {
        throw Exception('无法生成预测号码');
      }

      print('预测号码生成完成: ${predictions.first}');
      return predictions.first;
    } catch (e) {
      print('生成预测失败: $e');
      rethrow;
    }
  }

  // 分析热门号码组合模式
  Map<String, dynamic> analyzeHotPatterns({int lookbackCount = 100}) {
    print('开始分析热门号码组合模式 - lookbackCount: $lookbackCount');
    var recentDraws = _allDraws.take(lookbackCount).toList();

    // 分析号码组合特征
    Map<String, int> patternFrequency = {};
    Map<int, int> hotNumbers = {};
    Map<int, List<int>> commonPairs = {};

    for (var draw in recentDraws) {
      var numbers = draw.numbers;

      // 统计单个号码出现频率
      for (var num in numbers) {
        hotNumbers[num] = (hotNumbers[num] ?? 0) + 1;
      }

      // 分析号码对
      for (int i = 0; i < numbers.length; i++) {
        for (int j = i + 1; j < numbers.length; j++) {
          var pair = [numbers[i], numbers[j]]..sort();
          var pairKey = '${pair[0]}-${pair[1]}';
          patternFrequency[pairKey] = (patternFrequency[pairKey] ?? 0) + 1;

          commonPairs[pair[0]] = (commonPairs[pair[0]] ?? [])..add(pair[1]);
          commonPairs[pair[1]] = (commonPairs[pair[1]] ?? [])..add(pair[0]);
        }
      }

      // 分析奇偶组合
      int oddCount = numbers.where((n) => n % 2 == 1).length;
      String oddEvenPattern = '$oddCount-${numbers.length - oddCount}';
      patternFrequency[oddEvenPattern] =
          (patternFrequency[oddEvenPattern] ?? 0) + 1;

      // 分析区间组合
      var zonePattern = List.filled(4, 0);
      for (var num in numbers) {
        for (int i = 0; i < _numberRanges.length; i++) {
          if (num >= _numberRanges[i]['start']! &&
              num <= _numberRanges[i]['end']!) {
            zonePattern[i]++;
            break;
          }
        }
      }
      String zoneKey = zonePattern.join('-');
      patternFrequency[zoneKey] = (patternFrequency[zoneKey] ?? 0) + 1;
    }

    // 处理常见配对
    Map<int, List<int>> topPairs = {};
    for (var entry in commonPairs.entries) {
      var pairs = entry.value;
      var frequency = Map<int, int>();
      for (var num in pairs) {
        frequency[num] = (frequency[num] ?? 0) + 1;
      }
      var sortedPairs = frequency.entries.toList()
        ..sort((MapEntry<int, int> a, MapEntry<int, int> b) =>
            b.value.compareTo(a.value));
      topPairs[entry.key] = sortedPairs.take(3).map((e) => e.key).toList();
    }

    // 对热门号码进行排序和处理
    var sortedEntries = hotNumbers.entries.toList()
      ..sort((MapEntry<int, int> a, MapEntry<int, int> b) =>
          b.value.compareTo(a.value));
    var topHotNumbers = Map<int, int>.fromEntries(sortedEntries.take(20));

    // 对模式频率进行排序和处理
    var sortedPatternEntries = patternFrequency.entries.toList()
      ..sort((MapEntry<String, int> a, MapEntry<String, int> b) =>
          b.value.compareTo(a.value));
    var topPatterns =
        Map<String, int>.fromEntries(sortedPatternEntries.take(10));

    print('热门号码分析完成');
    return {
      'hotNumbers': Map<int, int>.from(topHotNumbers),
      'topPatterns': Map<String, int>.from(topPatterns),
      'commonPairs': Map<int, List<int>>.from(topPairs),
    };
  }
}
