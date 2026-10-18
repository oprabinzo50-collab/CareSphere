const { app, BrowserWindow, shell, session } = require('electron');

const APP_URL = 'https://caresphere.pages.dev';
const ALLOWED_ORIGINS = new Set([
  'https://caresphere.pages.dev',
  'https://caresphere-api-ewxp.onrender.com',
]);

function isAllowed(url) {
  try { return ALLOWED_ORIGINS.has(new URL(url).origin); }
  catch { return false; }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    title: 'CareSphere',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (isAllowed(url)) return { action: 'allow' };
    shell.openExternal(url);
    return { action: 'deny' };
  });

  win.loadURL(APP_URL);
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
