import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('快乐8预测'),
      ),
      body: const Center(
        child: Text('欢迎使用快乐8预测'),
      ),
    );
  }
}
