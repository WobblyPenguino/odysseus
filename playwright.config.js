const chromiumPath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || '/usr/lib/chromium/chromium';

module.exports = {
  testDir: '.',
  timeout: 45000,
  use: {
    browserName: 'chromium',
    headless: true,
    launchOptions: {
      executablePath: chromiumPath,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security', '--allow-insecure-localhost', '--allow-running-insecure-content', '--disable-features=HttpsFirstBalancedModeAutoEnable,BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessSendPreflights,HttpsUpgrades'],
    },
  },
};
