#!/usr/bin/env node
/**
 * HTML→PNG レンダラ（Puppeteer）。
 *
 * 使い方:
 *   node render_html.js <html_path> <png_path> [--width 1920 --height 1080 --dpi 2]
 *
 * デフォルトは 1920x1080 (16:9) で deviceScaleFactor=2（高解像度）。
 */
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer');

function parseArgs(argv) {
  const args = { width: 1920, height: 1080, dpi: 2 };
  const positional = [];
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--width') args.width = parseInt(argv[++i], 10);
    else if (a === '--height') args.height = parseInt(argv[++i], 10);
    else if (a === '--dpi') args.dpi = parseFloat(argv[++i]);
    else positional.push(a);
  }
  if (positional.length < 2) {
    console.error('usage: render_html.js <html_path> <png_path> [--width N --height N --dpi N]');
    process.exit(2);
  }
  args.html = path.resolve(positional[0]);
  args.png = path.resolve(positional[1]);
  return args;
}

(async () => {
  const args = parseArgs(process.argv);
  if (!fs.existsSync(args.html)) {
    console.error(`html not found: ${args.html}`);
    process.exit(2);
  }
  fs.mkdirSync(path.dirname(args.png), { recursive: true });

  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({
      width: args.width,
      height: args.height,
      deviceScaleFactor: args.dpi,
    });
    await page.goto('file://' + args.html, { waitUntil: 'networkidle0' });
    await page.screenshot({
      path: args.png,
      omitBackground: false,
      type: 'png',
      fullPage: false,
    });
    console.log(`OK: ${args.png}`);
  } finally {
    await browser.close();
  }
})();
