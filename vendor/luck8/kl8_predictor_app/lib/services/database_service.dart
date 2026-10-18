import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/lottery_draw.dart';
import '../models/prediction_record.dart';

class DatabaseService {
  static final DatabaseService _instance = DatabaseService._internal();
  static Database? _database;

  factory DatabaseService() {
    return _instance;
  }

  DatabaseService._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final String path = join(await getDatabasesPath(), 'lottery_draws.db');
    print('数据库路径: $path'); // 添加日志
    return await openDatabase(
      path,
      version: 3, // 更新版本号
      onCreate: (Database db, int version) async {
        // 创建开奖记录表
        await db.execute('''
          CREATE TABLE lottery_draws(
            drawNumber TEXT PRIMARY KEY,
            drawDate TEXT NOT NULL,
            numbers TEXT NOT NULL
          )
        ''');

        // 创建预测记录表
        await db.execute('''
          CREATE TABLE prediction_records(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drawNumber TEXT NOT NULL,
            predictionTime TEXT NOT NULL,
            numbers TEXT NOT NULL,
            isDrawn INTEGER DEFAULT 0,
            drawnNumbers TEXT,
            isFavorite INTEGER DEFAULT 0
          )
        ''');
      },
      onUpgrade: (Database db, int oldVersion, int newVersion) async {
        if (oldVersion < 2) {
          // 添加预测记录表
          await db.execute('''
            CREATE TABLE prediction_records(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              drawNumber TEXT NOT NULL,
              predictionTime TEXT NOT NULL,
              numbers TEXT NOT NULL,
              isDrawn INTEGER DEFAULT 0,
              drawnNumbers TEXT
            )
          ''');
        }
        if (oldVersion < 3) {
          // 添加收藏字段
          await db.execute(
              'ALTER TABLE prediction_records ADD COLUMN isFavorite INTEGER DEFAULT 0');
        }
      },
    );
  }

  // 开奖记录相关方法
  Future<void> insertDraw(LotteryDraw draw) async {
    final db = await database;
    final map = draw.toMap();
    print('插入数据: $map'); // 添加日志
    await db.insert(
      'lottery_draws',
      map,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertMultipleDraws(List<LotteryDraw> draws) async {
    final db = await database;
    final batch = db.batch();
    for (var draw in draws) {
      final map = draw.toMap();
      print('批量插入数据: $map'); // 添加日志
      batch.insert(
        'lottery_draws',
        map,
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<LotteryDraw>> getAllDraws() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'lottery_draws',
      orderBy: 'drawDate DESC',
    );
    print('从数据库读取到 ${maps.length} 条记录'); // 添加日志

    if (maps.isEmpty) return [];

    return List.generate(maps.length, (i) {
      try {
        return LotteryDraw.fromMap(maps[i]);
      } catch (e) {
        print('解析记录失败: ${maps[i]}, 错误: $e'); // 添加日志
        rethrow;
      }
    });
  }

  Future<LotteryDraw?> getLatestDraw() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'lottery_draws',
      orderBy: 'drawDate DESC',
      limit: 1,
    );
    if (maps.isEmpty) return null;
    try {
      print('最新记录: ${maps.first}'); // 添加日志
      return LotteryDraw.fromMap(maps.first);
    } catch (e) {
      print('解析最新记录失败: ${maps.first}, 错误: $e'); // 添加日志
      rethrow;
    }
  }

  // 预测记录相关方法
  Future<int> insertPrediction(PredictionRecord prediction) async {
    final db = await database;
    print('插入预测记录: ${prediction.toMap()}');
    return await db.insert('prediction_records', prediction.toMap());
  }

  Future<void> updatePrediction(PredictionRecord prediction) async {
    final db = await database;
    print('更新预测记录: ${prediction.toMap()}');
    await db.update(
      'prediction_records',
      prediction.toMap(),
      where: 'id = ?',
      whereArgs: [prediction.id],
    );
  }

  Future<List<PredictionRecord>> getPredictionsByDrawNumber(
      String drawNumber) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'prediction_records',
      where: 'drawNumber = ?',
      whereArgs: [drawNumber],
      orderBy: 'predictionTime DESC',
    );
    return maps.map((map) => PredictionRecord.fromMap(map)).toList();
  }

  Future<List<PredictionRecord>> getAllPredictions() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'prediction_records',
      orderBy: 'drawNumber DESC, predictionTime DESC',
    );
    return maps.map((map) => PredictionRecord.fromMap(map)).toList();
  }

  // 更新已开奖的预测记录
  Future<void> updateDrawnPredictions(
      String drawNumber, List<int> drawnNumbers) async {
    final db = await database;
    await db.update(
      'prediction_records',
      {
        'isDrawn': 1,
        'drawnNumbers': drawnNumbers.join(','),
      },
      where: 'drawNumber = ?',
      whereArgs: [drawNumber],
    );
  }

  Future<void> clearAllDraws() async {
    final db = await database;
    await db.delete('lottery_draws');
    print('开奖记录已清空');
  }

  Future<void> clearAllPredictions() async {
    final db = await database;
    await db.delete('prediction_records');
    print('预测记录已清空');
  }

  // 更新预测记录的收藏状态
  Future<void> toggleFavorite(int id, bool isFavorite) async {
    final db = await database;
    await db.update(
      'prediction_records',
      {'isFavorite': isFavorite ? 1 : 0},
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
