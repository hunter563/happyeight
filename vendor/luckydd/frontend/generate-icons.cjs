const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const iconDirs = ['mipmap-mdpi', 'mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi'];
const sizes = [48, 72, 96, 144, 192];

const androidResDir = path.join(__dirname, 'android', 'app', 'src', 'main', 'res');
const svgPath = path.join(__dirname, 'public', 'icon-192.svg');

async function generateIcons() {
  const svgBuffer = fs.readFileSync(svgPath);
  
  for (let i = 0; i < iconDirs.length; i++) {
    const dir = iconDirs[i];
    const size = sizes[i];
    const dirPath = path.join(androidResDir, dir);
    
    const pngBuffer = await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toBuffer();
    
    fs.writeFileSync(path.join(dirPath, 'ic_launcher.png'), pngBuffer);
    fs.writeFileSync(path.join(dirPath, 'ic_launcher_round.png'), pngBuffer);
    fs.writeFileSync(path.join(dirPath, 'ic_launcher_foreground.png'), pngBuffer);
    
    console.log(`Created ${dir}/ic_launcher*.png (${size}x${size})`);
  }
}

generateIcons().catch(err => {
  console.error('Error generating icons:', err);
  process.exit(1);
});