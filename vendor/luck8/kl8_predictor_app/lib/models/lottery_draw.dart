import 'package:intl/intl.dart';

class LotteryDraw {
  final String drawNumber;
  final DateTime drawDate;
  final List<int> numbers;

  LotteryDraw({
    required this.drawNumber,
    required this.drawDate,
    required this.numbers,
  });

  // 从JSON映射创建实例
  factory LotteryDraw.fromJson(Map<String, dynamic> json) {
    final dateStr = json['开奖日期'] as String;
    final numbersStr = json['开奖号码'] as String;

    // 处理号码字符串
    final numbers = parseNumbers(numbersStr);
    print('从JSON解析到的号码: $numbers'); // 添加日志

    return LotteryDraw(
      drawNumber: json['期号'] as String,
      drawDate: DateFormat('yyyy-MM-dd').parse(dateStr),
      numbers: numbers,
    );
  }

  // 从数据库映射创建实例
  factory LotteryDraw.fromMap(Map<String, dynamic> map) {
    final dateStr = map['drawDate'] as String;
    final numbersStr = map['numbers'] as String;

    print('从数据库读取的原始号码字符串: $numbersStr'); // 添加调试日志

    // 处理号码字符串
    final numbers = parseNumbers(numbersStr);
    print('从数据库解析到的号码: $numbers'); // 添加日志

    return LotteryDraw(
      drawNumber: map['drawNumber'] as String,
      drawDate: DateFormat('yyyy-MM-dd').parse(dateStr),
      numbers: numbers,
    );
  }

  // 统一的号码解析方法
  static List<int> parseNumbers(String numbersStr) {
    print('开始解析号码字符串: $numbersStr'); // 添加调试日志

    // 移除引号和多余的空格
    numbersStr = numbersStr.replaceAll('"', '').trim();
    print('移除引号后: $numbersStr'); // 添加调试日志

    // 分割字符串（支持逗号和空格分隔）
    final numberStrings = numbersStr.split(RegExp(r'[,\s]+'));
    print('分割后的字符串数组: $numberStrings'); // 添加调试日志

    // 过滤空字符串并转换为整数
    final numbers = numberStrings.where((s) => s.isNotEmpty).map((s) {
      // print('正在解析数字: "$s"'); // 添加调试日志
      return int.parse(s.trim());
    }).toList();

    print('转换后的数字数组: $numbers'); // 添加调试日志

    // 排序并确保正好有20个号码
    numbers.sort();
    if (numbers.length != 20) {
      print('号码数量不正确: ${numbers.length}个，期望20个'); // 添加调试日志
      throw FormatException(
          '号码数量必须为20个，当前为: ${numbers.length}，原始字符串: $numbersStr');
    }

    return numbers;
  }

  // 转换为数据库映射
  Map<String, dynamic> toMap() {
    final numbersStr = numbers.join(',');
    print('转换为数据库映射，号码字符串: $numbersStr'); // 添加调试日志
    return {
      'drawNumber': drawNumber,
      'drawDate': DateFormat('yyyy-MM-dd').format(drawDate),
      'numbers': numbersStr,
    };
  }

  @override
  String toString() {
    return 'LotteryDraw(drawNumber: $drawNumber, date: ${DateFormat('yyyy-MM-dd').format(drawDate)}, numbers: $numbers)';
  }
}
