import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/lottery_draw.dart';
import 'database_service.dart';
import 'api_service.dart';
import 'package:csv/csv.dart';

class DataInitializer {
  final DatabaseService _dbService;
  final ApiService _apiService;

  DataInitializer({
    DatabaseService? dbService,
    ApiService? apiService,
  })  : _dbService = dbService ?? DatabaseService(),
        _apiService = apiService ?? ApiService();

  Future<void> initializeData(
      {void Function(String status)? onProgress}) async {
    try {
      onProgress?.call('检查数据库状态...');
      final draws = await _dbService.getAllDraws();
      print('当前数据库中有 ${draws.length} 条记录');

      if (draws.isEmpty) {
        onProgress?.call('数据库为空，开始导入历史数据...');
        await _importHistoricalData(onProgress);
      } else {
        print('数据库已有数据，跳过历史数据导入');
      }

      onProgress?.call('正在获取最新数据...');
      await _updateLatestData(onProgress);
    } catch (e, stackTrace) {
      print('数据初始化失败: $e');
      print('错误堆栈: $stackTrace');
      rethrow;
    }
  }

  Future<void> _importHistoricalData(
      void Function(String status)? onProgress) async {
    try {
      onProgress?.call('读取历史数据文件...');
      print('开始读取CSV文件...');
      final String csvData =
          await rootBundle.loadString('assets/data/kl8_history.csv');
      print('CSV文件读取成功，长度: ${csvData.length}');

      // 使用CSV解析器
      final csvConverter = CsvToListConverter(
        shouldParseNumbers: false,
        fieldDelimiter: ',',
      );
      final List<List<dynamic>> rows = csvConverter.convert(csvData);
      print('CSV文件行数: ${rows.length}');

      if (rows.isEmpty) {
        throw Exception('历史数据文件为空');
      }

      onProgress?.call('解析历史数据...');
      print('开始解析CSV数据...');

      // 跳过标题行
      final records = rows.skip(1).map((row) {
        print('正在处理行: $row'); // 添加调试日志

        if (row.length < 3) {
          print('数据行格式错误: $row');
          throw Exception('数据格式错误: $row');
        }

        final drawNumber = row[0].toString().trim();
        final drawDate = row[1].toString().trim();
        final numbersStr = row[2].toString().trim();

        print('原始号码字符串: $numbersStr'); // 添加调试日志

        // 验证号码格式
        final numbersList = numbersStr
            .replaceAll('"', '')
            .split(',')
            .where((s) => s.isNotEmpty)
            .map((s) => int.parse(s.trim()))
            .toList();

        print('解析后的号码列表: $numbersList'); // 添加调试日志

        if (numbersList.length != 20) {
          throw Exception('号码数量错误: ${numbersList.length}，期望20个，行: $row');
        }

        return {
          '期号': drawNumber,
          '开奖日期': drawDate,
          '开奖号码': numbersList.join(','),
        };
      }).toList();

      print('成功解析记录数: ${records.length}');
      onProgress?.call('成功读取CSV文件，共 ${records.length} 条记录');

      onProgress?.call('导入数据到数据库...');
      print('开始转换为LotteryDraw对象...');
      final draws = records.map((record) {
        try {
          print('转换记录: $record'); // 添加调试日志
          return LotteryDraw.fromJson(record);
        } catch (e) {
          print('转换记录失败: $record, 错误: $e');
          rethrow;
        }
      }).toList();

      print('开始批量插入数据库...');
      await _dbService.insertMultipleDraws(draws);
      print('数据库插入完成');

      onProgress?.call('成功导入 ${draws.length} 条记录');
    } catch (e, stackTrace) {
      print('导入历史数据失败: $e');
      print('错误堆栈: $stackTrace');
      throw Exception('导入历史数据失败: $e');
    }
  }

  Future<void> _updateLatestData(
      void Function(String status)? onProgress) async {
    try {
      onProgress?.call('获取最新开奖数据...');
      print('开始从API获取最新数据...');
      final latestDraws = await _apiService.fetchLatestDraws();
      print('API返回 ${latestDraws.length} 条记录');

      if (latestDraws.isEmpty) {
        onProgress?.call('没有新的数据需要更新');
        return;
      }

      final dbLatestDraw = await _dbService.getLatestDraw();
      if (dbLatestDraw == null) {
        onProgress?.call('导入最新数据...');
        await _dbService.insertMultipleDraws(latestDraws);
        onProgress?.call('成功导入 ${latestDraws.length} 条最新记录');
        return;
      }

      print('数据库最新记录日期: ${dbLatestDraw.drawDate}');
      final newDraws = latestDraws
          .where((draw) => draw.drawDate.isAfter(dbLatestDraw.drawDate))
          .toList();

      print('发现 ${newDraws.length} 条新数据');
      if (newDraws.isNotEmpty) {
        onProgress?.call('更新最新数据...');
        await _dbService.insertMultipleDraws(newDraws);
        onProgress?.call('成功更新 ${newDraws.length} 条最新记录');
      } else {
        onProgress?.call('数据已是最新');
      }
    } catch (e, stackTrace) {
      print('更新最新数据失败: $e');
      print('错误堆栈: $stackTrace');
      throw Exception('更新最新数据失败: $e');
    }
  }
}
