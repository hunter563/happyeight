import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.luckydd.app',
  appName: 'LuckyDD',
  webDir: 'dist',
  server: {
    androidScheme: 'http'
  }
};

export default config;
