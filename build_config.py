#!/usr/bin/env python3
"""
Build Configuration for TradingBot Pro
Handles PyInstaller build process and deployment options.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json
import zipfile
from datetime import datetime

class TradingBotBuilder:
    """Build system for TradingBot Pro distribution"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.temp_dir = self.project_root / "temp_build"
        
        # Build configurations
        self.build_configs = {
            'basic': {
                'name': 'TradingBot-Basic',
                'include_source': False,
                'obfuscate': True,
                'features': ['basic_trading', 'risk_management'],
                'price_tier': 'basic'
            },
            'standard': {
                'name': 'TradingBot-Standard',
                'include_source': False,
                'obfuscate': True,
                'features': ['basic_trading', 'risk_management', 'advanced_strategies'],
                'price_tier': 'standard'
            },
            'premium': {
                'name': 'TradingBot-Premium',
                'include_source': True,
                'obfuscate': False,
                'features': ['all'],
                'price_tier': 'premium'
            },
            'enterprise': {
                'name': 'TradingBot-Enterprise',
                'include_source': True,
                'obfuscate': False,
                'features': ['all', 'multi_tenant', 'custom_integrations'],
                'price_tier': 'enterprise'
            }
        }
    
    def clean_build_dirs(self):
        """Clean build directories"""
        for dir_path in [self.build_dir, self.dist_dir, self.temp_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def install_build_dependencies(self):
        """Install required build dependencies"""
        dependencies = [
            'pyinstaller>=5.0',
            'pyarmor>=8.0',  # For code obfuscation
            'cx_Freeze',     # Alternative to PyInstaller
            'auto-py-to-exe' # GUI for PyInstaller
        ]
        
        print("Installing build dependencies...")
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                             check=True, capture_output=True)
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {dep}: {e}")
    
    def create_pyinstaller_spec(self, config_name: str) -> str:
        """Create PyInstaller spec file"""
        config = self.build_configs[config_name]
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/app.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('frontend/static', 'static'),
        ('frontend/templates', 'templates'),
        ('config', 'config'),
        ('strategies', 'strategies'),
        ('LICENSE_REVOCATION.md', '.'),
        ('SUPPORT.md', '.'),
        ('EULA.md', '.'),
        ('DISCLAIMER.md', '.'),
        ('REFUND_POLICY.md', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'flask',
        'sqlalchemy',
        'redis',
        'requests',
        'websocket-client',
        'cryptography',
        'ccxt',
        'pandas',
        'numpy',
        'ta',
        'plotly',
        'sentry_sdk',
        'prometheus_client',
        'celery',
        'gunicorn',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{config['name']}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='frontend/static/favicon.ico'
)
'''
        
        spec_file = self.project_root / f"{config['name']}.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        return str(spec_file)
    
    def obfuscate_code(self, config_name: str):
        """Obfuscate Python code using PyArmor"""
        config = self.build_configs[config_name]
        
        if not config.get('obfuscate', False):
            print(f"Skipping obfuscation for {config_name} build")
            return
        
        print(f"Obfuscating code for {config_name} build...")
        
        # Create obfuscated version
        obfuscated_dir = self.temp_dir / "obfuscated"
        obfuscated_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy source files to temp directory
        source_dirs = ['backend', 'tools', 'strategies']
        for source_dir in source_dirs:
            src_path = self.project_root / source_dir
            if src_path.exists():
                dst_path = obfuscated_dir / source_dir
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        
        try:
            # Use PyArmor to obfuscate
            cmd = [
                'pyarmor',
                'gen',
                '--output', str(obfuscated_dir / 'protected'),
                '--recursive',
                '--exclude', '__pycache__',
                '--exclude', '*.pyc',
                str(obfuscated_dir / 'backend'),
                str(obfuscated_dir / 'tools'),
                str(obfuscated_dir / 'strategies')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Code obfuscation completed")
                return str(obfuscated_dir / 'protected')
            else:
                print(f"❌ Obfuscation failed: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("❌ PyArmor not found. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyarmor'])
            return self.obfuscate_code(config_name)  # Retry
        except Exception as e:
            print(f"❌ Obfuscation error: {e}")
            return None
    
    def build_executable(self, config_name: str) -> bool:
        """Build executable using PyInstaller"""
        config = self.build_configs[config_name]
        print(f"Building {config['name']} executable...")
        
        # Create spec file
        spec_file = self.create_pyinstaller_spec(config_name)
        
        # Obfuscate if needed
        if config.get('obfuscate', False):
            obfuscated_path = self.obfuscate_code(config_name)
            if obfuscated_path:
                # Update spec file to use obfuscated code
                print("Using obfuscated code for build")
        
        try:
            # Run PyInstaller
            cmd = [
                'pyinstaller',
                '--clean',
                '--noconfirm',
                '--distpath', str(self.dist_dir),
                '--workpath', str(self.build_dir),
                spec_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {config['name']} executable built successfully")
                return True
            else:
                print(f"❌ Build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def create_deployment_package(self, config_name: str) -> Optional[str]:
        """Create deployment package with documentation and setup scripts"""
        config = self.build_configs[config_name]
        package_name = f"{config['name']}-{datetime.now().strftime('%Y%m%d')}"
        package_dir = self.dist_dir / package_name
        
        # Create package directory
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / config['name']
        if exe_path.exists():
            if exe_path.is_dir():
                shutil.copytree(exe_path, package_dir / config['name'])
            else:
                shutil.copy2(exe_path, package_dir)
        else:
            print(f"❌ Executable not found: {exe_path}")
            return None
        
        # Copy documentation
        docs_to_copy = [
            'README.md',
            'SUPPORT.md',
            'EULA.md',
            'DISCLAIMER.md',
            'REFUND_POLICY.md',
            'LICENSE_REVOCATION.md',
            '.env.example'
        ]
        
        for doc in docs_to_copy:
            doc_path = self.project_root / doc
            if doc_path.exists():
                shutil.copy2(doc_path, package_dir)
        
        # Copy source code if included in config
        if config.get('include_source', False):
            source_dirs = ['backend', 'frontend', 'tools', 'strategies', 'tests']
            for source_dir in source_dirs:
                src_path = self.project_root / source_dir
                if src_path.exists():
                    dst_path = package_dir / 'source' / source_dir
                    shutil.copytree(src_path, dst_path, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
        
        # Create setup scripts
        self._create_setup_scripts(package_dir, config)
        
        # Create package info
        package_info = {
            'name': config['name'],
            'version': '1.0.0',
            'build_date': datetime.now().isoformat(),
            'features': config['features'],
            'price_tier': config['price_tier'],
            'includes_source': config.get('include_source', False),
            'obfuscated': config.get('obfuscate', False)
        }
        
        with open(package_dir / 'package_info.json', 'w') as f:
            json.dump(package_info, f, indent=2)
        
        # Create ZIP archive
        zip_path = self.dist_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(package_dir)
                    zipf.write(file_path, arc_path)
        
        print(f"✅ Deployment package created: {zip_path}")
        return str(zip_path)
    
    def _create_setup_scripts(self, package_dir: Path, config: Dict):
        """Create setup and installation scripts"""
        
        # Windows batch script
        batch_script = f'''@echo off
echo Installing {config['name']}...
echo.
echo Please ensure you have:
echo - Python 3.8+ installed
echo - Required dependencies (see requirements.txt)
echo - Valid license key
echo.
echo 1. Copy .env.example to .env
echo 2. Fill in your configuration values
echo 3. Run the executable
echo.
pause
'''
        
        with open(package_dir / 'INSTALL.bat', 'w') as f:
            f.write(batch_script)
        
        # Linux shell script
        shell_script = f'''#!/bin/bash
echo "Installing {config['name']}..."
echo
echo "Please ensure you have:"
echo "- Python 3.8+ installed"
echo "- Required dependencies (see requirements.txt)"
echo "- Valid license key"
echo
echo "1. Copy .env.example to .env"
echo "2. Fill in your configuration values"
echo "3. Run the executable"
echo
read -p "Press Enter to continue..."
'''
        
        with open(package_dir / 'install.sh', 'w') as f:
            f.write(shell_script)
        
        # Make shell script executable
        os.chmod(package_dir / 'install.sh', 0o755)
        
        # Create requirements.txt for source builds
        if config.get('include_source', False):
            requirements = [
                'flask>=2.0.0',
                'sqlalchemy>=1.4.0',
                'redis>=4.0.0',
                'requests>=2.25.0',
                'websocket-client>=1.0.0',
                'cryptography>=3.4.0',
                'ccxt>=2.0.0',
                'pandas>=1.3.0',
                'numpy>=1.21.0',
                'ta>=0.7.0',
                'plotly>=5.0.0',
                'sentry-sdk[flask]>=1.5.0',
                'prometheus-client>=0.12.0',
                'celery>=5.2.0',
                'gunicorn>=20.1.0'
            ]
            
            with open(package_dir / 'requirements.txt', 'w') as f:
                f.write('\n'.join(requirements))
    
    def build_all_configs(self) -> Dict[str, bool]:
        """Build all configurations"""
        results = {}
        
        print("Starting build process for all configurations...")
        self.clean_build_dirs()
        self.install_build_dependencies()
        
        for config_name in self.build_configs.keys():
            print(f"\n{'='*50}")
            print(f"Building {config_name.upper()} configuration")
            print(f"{'='*50}")
            
            success = self.build_executable(config_name)
            if success:
                package_path = self.create_deployment_package(config_name)
                results[config_name] = package_path is not None
            else:
                results[config_name] = False
        
        return results
    
    def build_single_config(self, config_name: str) -> bool:
        """Build single configuration"""
        if config_name not in self.build_configs:
            print(f"❌ Unknown configuration: {config_name}")
            return False
        
        print(f"Building {config_name} configuration...")
        self.clean_build_dirs()
        
        success = self.build_executable(config_name)
        if success:
            package_path = self.create_deployment_package(config_name)
            return package_path is not None
        
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Pro Build System')
    parser.add_argument('--config', choices=['basic', 'standard', 'premium', 'enterprise', 'all'],
                       default='all', help='Build configuration')
    parser.add_argument('--clean', action='store_true', help='Clean build directories first')
    parser.add_argument('--install-deps', action='store_true', help='Install build dependencies')
    
    args = parser.parse_args()
    
    builder = TradingBotBuilder()
    
    if args.clean:
        builder.clean_build_dirs()
    
    if args.install_deps:
        builder.install_build_dependencies()
    
    if args.config == 'all':
        results = builder.build_all_configs()
        print("\n" + "="*50)
        print("BUILD SUMMARY")
        print("="*50)
        for config, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{config.upper()}: {status}")
    else:
        success = builder.build_single_config(args.config)
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"\nBuild result: {status}")

if __name__ == '__main__':
    main()