import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/prediction_record.dart';
import '../services/kl8_predictor.dart';
import '../services/database_service.dart';
import '../services/api_service.dart';
import '../services/data_initializer.dart';

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  final KL8Predictor _predictor = KL8Predictor();
  final DatabaseService _databaseService = DatabaseService();
  final ApiService _apiService = ApiService();
  final DataInitializer _dataInitializer = DataInitializer();
  bool _isLoading = false;
  Map<String, List<PredictionRecord>> _groupedPredictions = {};
  List<String> _expandedDrawNumbers = [];
  String? _latestDrawNumber;
  List<int>? _latestDrawNumbers;
  DateTime? _latestDrawDate;

  @override
  void initState() {
    super.initState();
    _loadLatestDraw();
    _loadPredictions();
    _checkAndUpdateDrawnNumbers();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _checkAndUpdateDrawnNumbers() async {
    try {
      // 获取所有预测记录
      final predictions = await _databaseService.getAllPredictions();

      // 获取所有开奖记录
      final draws = await _databaseService.getAllDraws();

      // 创建开奖记录映射，方便查找
      final drawsMap = {for (var draw in draws) draw.drawNumber: draw};

      // 检查每个未开奖的预测
      for (var prediction in predictions) {
        if (!prediction.isDrawn &&
            drawsMap.containsKey(prediction.drawNumber)) {
          // 找到对应的开奖记录，更新预测记录
          final draw = drawsMap[prediction.drawNumber]!;
          await _databaseService.updateDrawnPredictions(
            prediction.drawNumber,
            draw.numbers,
          );
        }
      }

      // 重新加载预测记录以显示更新后的结果
      await _loadPredictions();
    } catch (e) {
      print('更新开奖结果失败: $e');
    }
  }

  Future<void> _loadPredictions() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // 加载所有预测记录
      final predictions = await _databaseService.getAllPredictions();

      // 按期号分组
      final grouped = <String, List<PredictionRecord>>{};
      for (var prediction in predictions) {
        grouped.putIfAbsent(prediction.drawNumber, () => []).add(prediction);
      }

      setState(() {
        _groupedPredictions = grouped;
        _isLoading = false;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('加载预测失败: $e')),
      );
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _generateSinglePrediction() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final latestDraw = await _databaseService.getLatestDraw();
      if (latestDraw == null) {
        throw Exception('无法获取最新开奖信息');
      }

      final nextDrawNumber = (int.parse(latestDraw.drawNumber) + 1).toString();
      final prediction = await _predictor.generatePrediction();

      // 创建并保存预测记录
      final predictionRecord = PredictionRecord(
        drawNumber: nextDrawNumber,
        predictionTime: DateTime.now(),
        numbers: prediction,
      );

      await _databaseService.insertPrediction(predictionRecord);

      // 重新加载预测记录
      await _loadPredictions();

      // 展开最新预测的期号
      setState(() {
        if (!_expandedDrawNumbers.contains(nextDrawNumber)) {
          _expandedDrawNumbers.add(nextDrawNumber);
        }
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('生成预测失败: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _refreshData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // 使用DataInitializer获取最新数据
      await _dataInitializer.initializeData(
        onProgress: (status) {
          print('更新数据: $status');
        },
      );

      // 更新最新开奖信息
      await _loadLatestDraw();

      // 更新开奖结果并重新加载预测
      await _checkAndUpdateDrawnNumbers();

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('数据更新成功')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('更新数据失败: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadLatestDraw() async {
    try {
      final latestDraw = await _databaseService.getLatestDraw();
      if (latestDraw != null) {
        setState(() {
          _latestDrawNumber = latestDraw.drawNumber;
          _latestDrawNumbers = latestDraw.numbers;
          _latestDrawDate = latestDraw.drawDate;
        });
      }
    } catch (e) {
      print('加载最新开奖信息失败: $e');
    }
  }

  Widget _buildLatestDrawInfo() {
    if (_latestDrawNumber == null ||
        _latestDrawNumbers == null ||
        _latestDrawDate == null) {
      return const SizedBox.shrink();
    }

    final dateFormat = DateFormat('MM-dd');
    final formattedDate = dateFormat.format(_latestDrawDate!);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(
          bottom: BorderSide(
            color: Colors.grey[300]!,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '最新开奖: 第 $_latestDrawNumber 期',
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                formattedDate,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 4,
            runSpacing: 4,
            children: _latestDrawNumbers!
                .map((number) => Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.blue[100],
                      ),
                      child: Center(
                        child: Text(
                          number.toString(),
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blue[900],
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildPredictionNumber(int number, bool isHit) {
    return Container(
      width: 40,
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isHit ? Colors.green : Colors.orange,
      ),
      child: Center(
        child: Text(
          number.toString(),
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildPredictionCard(PredictionRecord prediction) {
    final dateFormat = DateFormat('MM-dd HH:mm');
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '预测时间: ${dateFormat.format(prediction.predictionTime)}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                IconButton(
                  icon: Icon(
                    prediction.isFavorite ? Icons.star : Icons.star_border,
                    color: prediction.isFavorite ? Colors.amber : Colors.grey,
                  ),
                  onPressed: () async {
                    if (prediction.id == null) return;
                    await _databaseService.toggleFavorite(
                      prediction.id!,
                      !prediction.isFavorite,
                    );
                    await _loadPredictions();
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: prediction.numbers.map((number) {
                final isHit = prediction.isNumberHit(number);
                return _buildPredictionNumber(number, isHit);
              }).toList(),
            ),
            if (prediction.isDrawn) ...[
              const SizedBox(height: 8),
              Text(
                '命中: ${prediction.hitCount} 个',
                style: TextStyle(
                  color: prediction.hitCount > 0 ? Colors.green : Colors.grey,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('预测号码'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _refreshData,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildLatestDrawInfo(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ElevatedButton(
              onPressed: _isLoading ? null : _generateSinglePrediction,
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('生成预测号码'),
            ),
          ),
          Expanded(
            child: _groupedPredictions.isEmpty
                ? const Center(
                    child: Text('暂无预测记录'),
                  )
                : ListView.builder(
                    itemCount: _groupedPredictions.length,
                    itemBuilder: (context, index) {
                      final drawNumber =
                          _groupedPredictions.keys.elementAt(index);
                      final predictions = _groupedPredictions[drawNumber]!;
                      final isExpanded =
                          _expandedDrawNumbers.contains(drawNumber);

                      return Card(
                        margin: const EdgeInsets.symmetric(
                          vertical: 4,
                          horizontal: 8,
                        ),
                        child: ExpansionTile(
                          initiallyExpanded: isExpanded,
                          onExpansionChanged: (expanded) {
                            setState(() {
                              if (expanded) {
                                _expandedDrawNumbers.add(drawNumber);
                              } else {
                                _expandedDrawNumbers.remove(drawNumber);
                              }
                            });
                          },
                          title: Text(
                            '第 $drawNumber 期预测',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          subtitle: Text(
                            '${predictions.length} 组预测号码',
                            style: const TextStyle(
                              color: Colors.grey,
                            ),
                          ),
                          children: predictions
                              .map((prediction) =>
                                  _buildPredictionCard(prediction))
                              .toList(),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
