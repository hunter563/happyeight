import 'package:flutter_test/flutter_test.dart';
import 'package:kl8_predictor_app/services/data_initializer.dart';
import 'package:kl8_predictor_app/services/database_service.dart';
import 'package:kl8_predictor_app/services/api_service.dart';
import 'package:kl8_predictor_app/models/lottery_draw.dart';
import 'package:flutter/services.dart';
import 'dart:convert';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late DataInitializer dataInitializer;
  late DatabaseService dbService;
  late ApiService apiService;

  // 模拟CSV数据
  final String mockCsvData = '''期号,开奖日期,开奖号码
20240321-001,2024-03-21,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
20240322-001,2024-03-22,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21
20240323-001,2024-03-23,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22''';

  // 模拟API返回数据
  final List<LotteryDraw> mockApiData = [
    LotteryDraw(
      drawDate: DateTime.parse('2024-03-24'),
      numbers: List.generate(20, (i) => i + 4),
    ),
    LotteryDraw(
      drawDate: DateTime.parse('2024-03-25'),
      numbers: List.generate(20, (i) => i + 5),
    ),
  ];

  setUp(() {
    // 设置资源绑定
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/assets', (ByteData? message) async {
      return Uint8List.fromList(utf8.encode(mockCsvData)).buffer.asByteData();
    });

    dbService = DatabaseService();
    apiService = ApiService();
    dataInitializer = DataInitializer();
  });

  group('DataInitializer Tests', () {
    test('Should import CSV data when database is empty', () async {
      // 清空数据库
      await dbService.clearAllDraws();

      // 执行数据初始化
      await dataInitializer.initializeData();

      // 验证数据是否正确导入
      final allDraws = await dbService.getAllDraws();
      expect(allDraws.length, 3); // CSV中有3条记录

      // 验证第一条记录
      expect(allDraws.first.drawDate, DateTime.parse('2024-03-21'));
      expect(allDraws.first.numbers.length, 20);
    });

    test('Should only import missing data when database is incomplete',
        () async {
      // 先插入部分数据
      await dbService.insertDraw(LotteryDraw(
        drawDate: DateTime.parse('2024-03-22'),
        numbers: List.generate(20, (i) => i + 1),
      ));

      // 执行数据初始化
      await dataInitializer.initializeData();

      // 验证是否只导入了缺失的数据
      final allDraws = await dbService.getAllDraws();
      expect(allDraws.length, 3);

      // 验证数据范围
      final dates = allDraws.map((d) => d.drawDate.toIso8601String()).toList();
      expect(dates.contains('2024-03-21'), true);
      expect(dates.contains('2024-03-22'), true);
      expect(dates.contains('2024-03-23'), true);
    });

    test('Should update with new data from API', () async {
      // Mock API response
      apiService = MockApiService(mockApiData);
      dataInitializer = DataInitializer(
        dbService: dbService,
        apiService: apiService,
      );

      // 先导入历史数据
      await dataInitializer.initializeData();

      // 验证新数据是否被添加
      final allDraws = await dbService.getAllDraws();
      expect(allDraws.length, 5); // 3条CSV数据 + 2条API数据

      // 验证最新的数据
      final latestDraw = await dbService.getLatestDraw();
      expect(latestDraw?.drawDate, DateTime.parse('2024-03-25'));
    });
  });
}

// Mock API Service
class MockApiService extends ApiService {
  final List<LotteryDraw> mockData;

  MockApiService(this.mockData);

  @override
  Future<List<LotteryDraw>> fetchLatestDraws() async {
    return mockData;
  }
}
