import 'package:flutter/material.dart';
import '../services/database_service.dart';
import '../services/api_service.dart';
import '../services/data_initializer.dart';
import 'home_page.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final DatabaseService _databaseService = DatabaseService();
  final ApiService _apiService = ApiService();
  final DataInitializer _dataInitializer = DataInitializer();

  bool _isLoading = true;
  String _status = '正在初始化...';
  int _drawCount = 0;
  int _predictionCount = 0;

  @override
  void initState() {
    super.initState();
    _initializeData();
  }

  Future<void> _initializeData() async {
    try {
      // 使用 DataInitializer 初始化数据
      await _dataInitializer.initializeData(
        onProgress: (status) {
          setState(() {
            _status = status;
          });
        },
      );

      // 获取数据统计
      final draws = await _databaseService.getAllDraws();
      final predictions = await _databaseService.getAllPredictions();

      setState(() {
        _drawCount = draws.length;
        _predictionCount = predictions.length;
        _status = '初始化完成\n开奖记录: $_drawCount 条\n预测记录: $_predictionCount 条';
        _isLoading = false;
      });

      // 延迟一会儿以显示完整状态
      await Future.delayed(const Duration(seconds: 2));

      // 导航到主页
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const HomePage()),
        );
      }
    } catch (e) {
      setState(() {
        _status = '初始化失败: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                '快乐8助手',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 48),
              if (_isLoading) const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                _status,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
