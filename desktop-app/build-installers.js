#!/usr/bin/env node

/**
 * Build Script for Trading Bot Desktop Installers
 * Creates one-click installers for Windows, macOS, and Linux
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logStep(step, message) {
    log(`\n[${step}] ${message}`, 'cyan');
}

function logSuccess(message) {
    log(`✓ ${message}`, 'green');
}

function logError(message) {
    log(`✗ ${message}`, 'red');
}

function logWarning(message) {
    log(`⚠ ${message}`, 'yellow');
}

function execCommand(command, options = {}) {
    try {
        const result = execSync(command, { 
            stdio: 'inherit', 
            encoding: 'utf8',
            ...options 
        });
        return result;
    } catch (error) {
        logError(`Command failed: ${command}`);
        logError(error.message);
        process.exit(1);
    }
}

function checkPrerequisites() {
    logStep('1', 'Checking prerequisites...');
    
    // Check if node_modules exists
    if (!fs.existsSync('node_modules')) {
        logError('node_modules not found. Please run "npm install" first.');
        process.exit(1);
    }
    
    // Check if electron-builder is installed
    try {
        execCommand('npx electron-builder --version', { stdio: 'pipe' });
        logSuccess('electron-builder is available');
    } catch (error) {
        logError('electron-builder not found. Please run "npm install" first.');
        process.exit(1);
    }
    
    // Check if required files exist
    const requiredFiles = [
        'main.js',
        'preload.js',
        'index.html',
        'package.json'
    ];
    
    for (const file of requiredFiles) {
        if (!fs.existsSync(file)) {
            logError(`Required file missing: ${file}`);
            process.exit(1);
        }
    }
    
    logSuccess('All prerequisites met');
}

function createDistDirectory() {
    logStep('2', 'Preparing build directory...');
    
    if (fs.existsSync('dist')) {
        log('Cleaning existing dist directory...');
        fs.rmSync('dist', { recursive: true, force: true });
    }
    
    fs.mkdirSync('dist', { recursive: true });
    logSuccess('Build directory prepared');
}

function buildForPlatform(platform, arch = null) {
    const platformName = {
        'win': 'Windows',
        'mac': 'macOS',
        'linux': 'Linux'
    }[platform] || platform;
    
    logStep('BUILD', `Building for ${platformName}${arch ? ` (${arch})` : ''}...`);
    
    let command = `npx electron-builder --${platform}`;
    if (arch) {
        command += ` --${arch}`;
    }
    
    try {
        execCommand(command);
        logSuccess(`${platformName} build completed`);
        return true;
    } catch (error) {
        logError(`${platformName} build failed`);
        return false;
    }
}

function buildAll() {
    logStep('3', 'Building installers for all platforms...');
    
    const builds = [];
    const currentPlatform = os.platform();
    
    // Always build for current platform first
    if (currentPlatform === 'win32') {
        builds.push({ platform: 'win', name: 'Windows' });
    } else if (currentPlatform === 'darwin') {
        builds.push({ platform: 'mac', name: 'macOS' });
    } else {
        builds.push({ platform: 'linux', name: 'Linux' });
    }
    
    // Add other platforms
    if (currentPlatform !== 'win32') {
        builds.push({ platform: 'win', name: 'Windows' });
    }
    if (currentPlatform !== 'darwin') {
        builds.push({ platform: 'mac', name: 'macOS' });
    }
    if (currentPlatform !== 'linux') {
        builds.push({ platform: 'linux', name: 'Linux' });
    }
    
    const results = [];
    
    for (const build of builds) {
        const success = buildForPlatform(build.platform);
        results.push({ ...build, success });
    }
    
    return results;
}

function generateBuildReport(results) {
    logStep('4', 'Generating build report...');
    
    const report = {
        timestamp: new Date().toISOString(),
        platform: os.platform(),
        arch: os.arch(),
        nodeVersion: process.version,
        builds: results,
        artifacts: []
    };
    
    // Scan dist directory for artifacts
    if (fs.existsSync('dist')) {
        const files = fs.readdirSync('dist');
        for (const file of files) {
            const filePath = path.join('dist', file);
            const stats = fs.statSync(filePath);
            if (stats.isFile()) {
                report.artifacts.push({
                    name: file,
                    size: stats.size,
                    sizeFormatted: formatBytes(stats.size),
                    created: stats.birthtime.toISOString()
                });
            }
        }
    }
    
    // Write report to file
    const reportPath = path.join('dist', 'build-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    // Display summary
    log('\n' + '='.repeat(60), 'bright');
    log('BUILD SUMMARY', 'bright');
    log('='.repeat(60), 'bright');
    
    for (const result of results) {
        const status = result.success ? '✓' : '✗';
        const color = result.success ? 'green' : 'red';
        log(`${status} ${result.name}`, color);
    }
    
    if (report.artifacts.length > 0) {
        log('\nGenerated Artifacts:', 'bright');
        for (const artifact of report.artifacts) {
            log(`  • ${artifact.name} (${artifact.sizeFormatted})`);
        }
    }
    
    log(`\nBuild report saved to: ${reportPath}`, 'cyan');
    log('='.repeat(60), 'bright');
    
    logSuccess('Build process completed');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showUsage() {
    log('Usage: node build-installers.js [options]', 'bright');
    log('\nOptions:');
    log('  --win          Build for Windows only');
    log('  --mac          Build for macOS only');
    log('  --linux        Build for Linux only');
    log('  --all          Build for all platforms (default)');
    log('  --help         Show this help message');
    log('\nExamples:');
    log('  node build-installers.js --win');
    log('  node build-installers.js --all');
    log('  npm run build-installers');
}

function main() {
    const args = process.argv.slice(2);
    
    if (args.includes('--help')) {
        showUsage();
        return;
    }
    
    log('Trading Bot Desktop - Installer Builder', 'bright');
    log('======================================\n', 'bright');
    
    checkPrerequisites();
    createDistDirectory();
    
    let results = [];
    
    if (args.includes('--win')) {
        results.push({ platform: 'win', name: 'Windows', success: buildForPlatform('win') });
    } else if (args.includes('--mac')) {
        results.push({ platform: 'mac', name: 'macOS', success: buildForPlatform('mac') });
    } else if (args.includes('--linux')) {
        results.push({ platform: 'linux', name: 'Linux', success: buildForPlatform('linux') });
    } else {
        // Build for all platforms
        results = buildAll();
    }
    
    generateBuildReport(results);
}

if (require.main === module) {
    main();
}

module.exports = {
    buildForPlatform,
    checkPrerequisites,
    createDistDirectory,
    generateBuildReport
};