import 'package:intl/intl.dart';

class PredictionRecord {
  final int? id;
  final String drawNumber;
  final DateTime predictionTime;
  final List<int> numbers;
  final bool isDrawn;
  final List<int>? drawnNumbers;
  final bool isFavorite;

  PredictionRecord({
    this.id,
    required this.drawNumber,
    required this.predictionTime,
    required this.numbers,
    this.isDrawn = false,
    this.drawnNumbers,
    this.isFavorite = false,
  });

  // 计算命中数量
  int get hitCount {
    if (!isDrawn || drawnNumbers == null) return 0;
    return numbers.where((number) => drawnNumbers!.contains(number)).length;
  }

  // 检查某个号码是否命中
  bool isNumberHit(int number) {
    return isDrawn && drawnNumbers != null && drawnNumbers!.contains(number);
  }

  // 从Map创建实例（用于数据库读取）
  factory PredictionRecord.fromMap(Map<String, dynamic> map) {
    return PredictionRecord(
      id: map['id'] as int?,
      drawNumber: map['drawNumber'] as String,
      predictionTime: DateTime.parse(map['predictionTime'] as String),
      numbers: (map['numbers'] as String)
          .split(',')
          .map((e) => int.parse(e.trim()))
          .toList(),
      isDrawn: (map['isDrawn'] as int) == 1,
      drawnNumbers: map['drawnNumbers'] == null
          ? null
          : (map['drawnNumbers'] as String)
              .split(',')
              .map((e) => int.parse(e.trim()))
              .toList(),
      isFavorite: (map['isFavorite'] as int?) == 1,
    );
  }

  // 转换为Map（用于数据库存储）
  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'drawNumber': drawNumber,
      'predictionTime': predictionTime.toIso8601String(),
      'numbers': numbers.join(','),
      'isDrawn': isDrawn ? 1 : 0,
      'drawnNumbers': drawnNumbers?.join(','),
      'isFavorite': isFavorite ? 1 : 0,
    };
  }

  // 创建更新后的记录
  PredictionRecord copyWith({
    int? id,
    String? drawNumber,
    DateTime? predictionTime,
    List<int>? numbers,
    bool? isDrawn,
    List<int>? drawnNumbers,
    bool? isFavorite,
  }) {
    return PredictionRecord(
      id: id ?? this.id,
      drawNumber: drawNumber ?? this.drawNumber,
      predictionTime: predictionTime ?? this.predictionTime,
      numbers: numbers ?? this.numbers,
      isDrawn: isDrawn ?? this.isDrawn,
      drawnNumbers: drawnNumbers ?? this.drawnNumbers,
      isFavorite: isFavorite ?? this.isFavorite,
    );
  }

  @override
  String toString() {
    return 'PredictionRecord(id: $id, drawNumber: $drawNumber, predictionTime: ${DateFormat('yyyy-MM-dd HH:mm:ss').format(predictionTime)}, numbers: $numbers, isDrawn: $isDrawn, drawnNumbers: $drawnNumbers, isFavorite: $isFavorite)';
  }
}
