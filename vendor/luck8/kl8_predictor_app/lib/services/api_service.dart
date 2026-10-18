import 'package:dio/dio.dart';
import '../models/lottery_draw.dart';
import 'dart:convert';

class ApiService {
  final Dio _dio = Dio();
  final String _baseUrl = 'https://jc.zhcw.com/port/client_json.php';

  Future<List<LotteryDraw>> fetchLatestDraws() async {
    try {
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final response = await _dio.get(
        _baseUrl,
        queryParameters: {
          'callback': 'jQuery1122039414901311157857_$timestamp',
          'transactionType': '10001001',
          'lotteryId': '6',
          'issueCount': '50', // 只获取最近50期数据
          'startIssue': '',
          'endIssue': '',
          'startDate': '', // 不限制开始日期
          'endDate': DateTime.now().toString().split(' ')[0], // 当前日期
          'type': '2',
          'pageNum': '1',
          'pageSize': '50',
          'tt': (timestamp / 1000).toString(),
          '_': timestamp.toString(),
        },
        options: Options(
          headers: {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.zhcw.com/',
            'User-Agent':
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
          },
        ),
      );

      // 从JSONP响应中提取JSON数据
      String jsonStr = response.data.toString();
      print('API原始响应: $jsonStr'); // 添加调试日志

      jsonStr =
          jsonStr.substring(jsonStr.indexOf('(') + 1, jsonStr.lastIndexOf(')'));
      print('提取的JSON字符串: $jsonStr'); // 添加调试日志

      Map<String, dynamic> jsonData = json.decode(jsonStr);
      print('解析后的JSON数据: $jsonData'); // 添加调试日志

      if (jsonData['data'] != null) {
        return (jsonData['data'] as List).map((item) {
          print('处理开奖记录: $item'); // 添加调试日志

          // 将号码字符串转换为标准格式
          final numbersStr = item['frontWinningNum'].toString().trim();
          print('原始号码字符串: $numbersStr'); // 添加调试日志

          // 分割号码字符串并过滤空字符串
          final numbersList = numbersStr
              .split(RegExp(r'[,\s]+'))
              .where((s) => s.isNotEmpty)
              .map((s) => int.parse(s.trim()))
              .toList();

          print('解析后的号码列表: $numbersList'); // 添加调试日志

          // 验证号码数量
          if (numbersList.length != 20) {
            throw Exception(
                '号码数量错误: ${numbersList.length}，期望20个，原始字符串: $numbersStr');
          }

          // 排序号码
          numbersList.sort();
          print('排序后的号码列表: $numbersList'); // 添加调试日志

          return LotteryDraw(
            drawNumber: item['issue'].toString(),
            drawDate: DateTime.parse(item['openTime']),
            numbers: numbersList,
          );
        }).toList();
      }
      throw Exception('API返回数据为空');
    } catch (e) {
      print('获取最新数据失败: $e');
      throw Exception('获取最新数据失败: $e');
    }
  }

  // 移除 fetchDrawsByDate 方法，因为我们只需要获取最新数据
}
