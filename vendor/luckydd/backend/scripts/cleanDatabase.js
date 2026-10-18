const fs = require('fs');
const path = require('path');

const DATABASE_PATH = path.join(__dirname, '../data/database.json');

const cleanDatabase = () => {
  const db = JSON.parse(fs.readFileSync(DATABASE_PATH, 'utf-8'));
  
  const lotteryTypes = ['double_color_ball', 'super_lotto', 'lottery_3d', 'happy_8', 'arrangement_3', 'arrangement_5', 'seven_star', 'seven_color'];
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  lotteryTypes.forEach(type => {
    if (!db[type]) return;
    
    let data = db[type];
    
    data = data.filter(item => {
      if (!item.date) return false;
      const itemDate = new Date(item.date);
      return !isNaN(itemDate.getTime()) && itemDate <= today;
    });
    
    data = data.sort((a, b) => {
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
    
    const seen = new Set();
    data = data.filter(item => {
      const key = `${item.id}-${item.date}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    
    db[type] = data;
    console.log(`${type}: 清理后 ${data.length} 条记录`);
  });
  
  fs.writeFileSync(DATABASE_PATH, JSON.stringify(db, null, 2), 'utf-8');
  console.log('数据库清理完成！');
};

cleanDatabase();