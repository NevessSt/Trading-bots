import os
import sys
import json
import importlib
import inspect
from typing import Dict, List, Optional, Any, Type, Callable
from pathlib import Path
import logging
from datetime import datetime
from threading import Lock
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Plugin interface definitions
class StrategyPlugin(ABC):
    """Base class for strategy plugins"""
    
    @abstractmethod
    def get_strategy_class(self) -> Type:
        """Return the strategy class"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Return list of required dependencies"""
        return []
    
    def validate_environment(self) -> bool:
        """Validate that the environment supports this plugin"""
        return True
    
    def on_load(self):
        """Called when plugin is loaded"""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        pass

class IndicatorPlugin(ABC):
    """Base class for indicator plugins"""
    
    @abstractmethod
    def calculate(self, data: Any, **kwargs) -> Any:
        """Calculate the indicator"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return indicator metadata"""
        pass
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return indicator parameters"""
        return {}
    
    def validate_data(self, data: Any) -> bool:
        """Validate input data"""
        return True

@dataclass
class PluginInfo:
    """Information about a loaded plugin"""
    name: str
    version: str
    author: str
    description: str
    plugin_type: str  # 'strategy' or 'indicator'
    file_path: str
    class_name: str
    loaded_at: datetime
    is_active: bool = True
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

class StrategyPluginSystem:
    """Plugin system for managing strategy and indicator plugins"""
    
    def __init__(self, plugin_dirs: List[str] = None, config_file: str = None):
        """
        Initialize the plugin system
        
        Args:
            plugin_dirs: List of directories to search for plugins
            config_file: Configuration file for plugin settings
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default plugin directories
        if plugin_dirs is None:
            base_dir = os.path.dirname(__file__)
            plugin_dirs = [
                os.path.join(base_dir, 'plugins', 'strategies'),
                os.path.join(base_dir, 'plugins', 'indicators'),
                os.path.join(base_dir, 'strategies', 'custom')
            ]
        
        self.plugin_dirs = [Path(d) for d in plugin_dirs]
        
        # Ensure plugin directories exist
        for plugin_dir in self.plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), 'plugin_config.json')
        self.config = self._load_config()
        
        # Plugin registry
        self._strategy_plugins: Dict[str, StrategyPlugin] = {}
        self._indicator_plugins: Dict[str, IndicatorPlugin] = {}
        self._plugin_info: Dict[str, PluginInfo] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # File watchers for hot reloading
        self._file_watchers: Dict[str, float] = {}
        
        # Initialize plugin system
        self._discover_plugins()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration"""
        default_config = {
            'auto_reload': True,
            'validate_plugins': True,
            'allowed_plugin_types': ['strategy', 'indicator'],
            'security_checks': True,
            'max_plugins': 100,
            'plugin_timeout': 30
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save plugin configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _discover_plugins(self):
        """Discover all plugins in plugin directories"""
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            for file_path in plugin_dir.rglob('*.py'):
                if file_path.name.startswith('__'):
                    continue
                
                try:
                    self._load_plugin_from_file(file_path)
                except Exception as e:
                    self.logger.error(f"Failed to load plugin {file_path}: {e}")
    
    def _load_plugin_from_file(self, file_path: Path) -> Optional[str]:
        """Load a plugin from a Python file"""
        try:
            # Create module spec
            module_name = f"plugin_{file_path.stem}_{hash(str(file_path)) % 10000}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not create spec for {file_path}")
                return None
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, StrategyPlugin) and obj != StrategyPlugin) or \
                   (issubclass(obj, IndicatorPlugin) and obj != IndicatorPlugin):
                    plugin_classes.append((name, obj))
            
            if not plugin_classes:
                self.logger.warning(f"No plugin classes found in {file_path}")
                return None
            
            # Load each plugin class
            loaded_plugins = []
            for class_name, plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    plugin_id = self._register_plugin(plugin_instance, file_path, class_name)
                    if plugin_id:
                        loaded_plugins.append(plugin_id)
                except Exception as e:
                    self.logger.error(f"Failed to instantiate plugin {class_name}: {e}")
            
            return loaded_plugins[0] if loaded_plugins else None
            
        except Exception as e:
            self.logger.error(f"Error loading plugin from {file_path}: {e}")
            return None
    
    def _register_plugin(self, plugin_instance, file_path: Path, class_name: str) -> Optional[str]:
        """Register a plugin instance"""
        try:
            metadata = plugin_instance.get_metadata()
            plugin_id = metadata.get('id', f"{file_path.stem}_{class_name}")
            
            # Validate plugin
            if self.config.get('validate_plugins', True):
                if not self._validate_plugin(plugin_instance, metadata):
                    self.logger.error(f"Plugin validation failed: {plugin_id}")
                    return None
            
            # Check if plugin already exists
            if plugin_id in self._plugin_info:
                self.logger.warning(f"Plugin {plugin_id} already exists, replacing...")
                self.unload_plugin(plugin_id)
            
            # Create plugin info
            plugin_info = PluginInfo(
                name=metadata.get('name', plugin_id),
                version=metadata.get('version', '1.0.0'),
                author=metadata.get('author', 'Unknown'),
                description=metadata.get('description', ''),
                plugin_type=metadata.get('type', 'strategy'),
                file_path=str(file_path),
                class_name=class_name,
                loaded_at=datetime.now(),
                dependencies=plugin_instance.get_dependencies() if hasattr(plugin_instance, 'get_dependencies') else [],
                metadata=metadata
            )
            
            # Register plugin based on type
            with self._lock:
                if isinstance(plugin_instance, StrategyPlugin):
                    self._strategy_plugins[plugin_id] = plugin_instance
                elif isinstance(plugin_instance, IndicatorPlugin):
                    self._indicator_plugins[plugin_id] = plugin_instance
                else:
                    self.logger.error(f"Unknown plugin type for {plugin_id}")
                    return None
                
                self._plugin_info[plugin_id] = plugin_info
            
            # Call plugin's on_load method
            if hasattr(plugin_instance, 'on_load'):
                plugin_instance.on_load()
            
            self.logger.info(f"Loaded plugin: {plugin_id} ({plugin_info.plugin_type})")
            return plugin_id
            
        except Exception as e:
            self.logger.error(f"Failed to register plugin: {e}")
            return None
    
    def _validate_plugin(self, plugin_instance, metadata: Dict[str, Any]) -> bool:
        """Validate a plugin instance"""
        try:
            # Check required metadata fields
            required_fields = ['id', 'name', 'version', 'type']
            for field in required_fields:
                if field not in metadata:
                    self.logger.error(f"Missing required metadata field: {field}")
                    return False
            
            # Check plugin type
            plugin_type = metadata.get('type')
            if plugin_type not in self.config.get('allowed_plugin_types', []):
                self.logger.error(f"Plugin type not allowed: {plugin_type}")
                return False
            
            # Validate environment if plugin supports it
            if hasattr(plugin_instance, 'validate_environment'):
                if not plugin_instance.validate_environment():
                    self.logger.error("Plugin environment validation failed")
                    return False
            
            # Check dependencies
            if hasattr(plugin_instance, 'get_dependencies'):
                dependencies = plugin_instance.get_dependencies()
                for dep in dependencies:
                    if not self._check_dependency(dep):
                        self.logger.error(f"Missing dependency: {dep}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Plugin validation error: {e}")
            return False
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is available"""
        try:
            if '.' in dependency:
                # Module import
                importlib.import_module(dependency)
            else:
                # Package import
                __import__(dependency)
            return True
        except ImportError:
            return False
    
    def load_plugin(self, file_path: str) -> Optional[str]:
        """Load a plugin from a file path"""
        return self._load_plugin_from_file(Path(file_path))
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        try:
            with self._lock:
                # Get plugin info
                if plugin_id not in self._plugin_info:
                    self.logger.warning(f"Plugin not found: {plugin_id}")
                    return False
                
                plugin_info = self._plugin_info[plugin_id]
                
                # Get plugin instance
                plugin_instance = None
                if plugin_id in self._strategy_plugins:
                    plugin_instance = self._strategy_plugins.pop(plugin_id)
                elif plugin_id in self._indicator_plugins:
                    plugin_instance = self._indicator_plugins.pop(plugin_id)
                
                # Call plugin's on_unload method
                if plugin_instance and hasattr(plugin_instance, 'on_unload'):
                    plugin_instance.on_unload()
                
                # Remove from registry
                del self._plugin_info[plugin_id]
            
            self.logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin"""
        if plugin_id not in self._plugin_info:
            return False
        
        plugin_info = self._plugin_info[plugin_id]
        file_path = plugin_info.file_path
        
        # Unload current plugin
        if not self.unload_plugin(plugin_id):
            return False
        
        # Reload from file
        new_plugin_id = self.load_plugin(file_path)
        return new_plugin_id is not None
    
    def get_strategy_plugin(self, plugin_id: str) -> Optional[StrategyPlugin]:
        """Get a strategy plugin by ID"""
        return self._strategy_plugins.get(plugin_id)
    
    def get_indicator_plugin(self, plugin_id: str) -> Optional[IndicatorPlugin]:
        """Get an indicator plugin by ID"""
        return self._indicator_plugins.get(plugin_id)
    
    def list_plugins(self, plugin_type: str = None) -> List[PluginInfo]:
        """List all loaded plugins"""
        plugins = list(self._plugin_info.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        
        return plugins
    
    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin"""
        return self._plugin_info.get(plugin_id)
    
    def create_strategy_instance(self, plugin_id: str, **kwargs):
        """Create a strategy instance from a plugin"""
        plugin = self.get_strategy_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Strategy plugin not found: {plugin_id}")
        
        strategy_class = plugin.get_strategy_class()
        return strategy_class(**kwargs)
    
    def calculate_indicator(self, plugin_id: str, data, **kwargs):
        """Calculate an indicator using a plugin"""
        plugin = self.get_indicator_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Indicator plugin not found: {plugin_id}")
        
        if not plugin.validate_data(data):
            raise ValueError(f"Invalid data for indicator {plugin_id}")
        
        return plugin.calculate(data, **kwargs)
    
    def install_plugin_from_file(self, source_file: str, target_dir: str = None) -> Optional[str]:
        """Install a plugin from a file"""
        try:
            source_path = Path(source_file)
            if not source_path.exists():
                raise FileNotFoundError(f"Plugin file not found: {source_file}")
            
            # Determine target directory
            if target_dir is None:
                target_dir = self.plugin_dirs[0]  # Use first plugin directory
            else:
                target_dir = Path(target_dir)
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            target_path = target_dir / source_path.name
            import shutil
            shutil.copy2(source_path, target_path)
            
            # Load plugin
            plugin_id = self.load_plugin(str(target_path))
            
            if plugin_id:
                self.logger.info(f"Installed plugin: {plugin_id}")
            
            return plugin_id
            
        except Exception as e:
            self.logger.error(f"Failed to install plugin: {e}")
            return None
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin (unload and delete file)"""
        try:
            if plugin_id not in self._plugin_info:
                return False
            
            plugin_info = self._plugin_info[plugin_id]
            file_path = Path(plugin_info.file_path)
            
            # Unload plugin
            if not self.unload_plugin(plugin_id):
                return False
            
            # Delete file
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Deleted plugin file: {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get plugin system status"""
        return {
            'total_plugins': len(self._plugin_info),
            'strategy_plugins': len(self._strategy_plugins),
            'indicator_plugins': len(self._indicator_plugins),
            'plugin_directories': [str(d) for d in self.plugin_dirs],
            'config': self.config,
            'active_plugins': [p.name for p in self._plugin_info.values() if p.is_active]
        }
    
    def export_plugin_list(self, file_path: str):
        """Export plugin list to JSON file"""
        try:
            plugin_data = {
                'exported_at': datetime.now().isoformat(),
                'plugins': [asdict(info) for info in self._plugin_info.values()]
            }
            
            with open(file_path, 'w') as f:
                json.dump(plugin_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported plugin list to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export plugin list: {e}")
    
    def create_plugin_template(self, plugin_type: str, plugin_name: str, output_dir: str = None) -> str:
        """Create a plugin template file"""
        if output_dir is None:
            output_dir = self.plugin_dirs[0]
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate template based on type
        if plugin_type == 'strategy':
            template = self._generate_strategy_plugin_template(plugin_name)
        elif plugin_type == 'indicator':
            template = self._generate_indicator_plugin_template(plugin_name)
        else:
            raise ValueError(f"Unknown plugin type: {plugin_type}")
        
        # Write template file
        file_name = f"{plugin_name.lower().replace(' ', '_')}_plugin.py"
        file_path = output_dir / file_name
        
        with open(file_path, 'w') as f:
            f.write(template)
        
        self.logger.info(f"Created plugin template: {file_path}")
        return str(file_path)
    
    def _generate_strategy_plugin_template(self, plugin_name: str) -> str:
        """Generate strategy plugin template"""
        class_name = ''.join(word.capitalize() for word in plugin_name.split())
        
        return f'''from typing import Dict, Any, Type
from datetime import datetime
from ..strategy_plugin_system import StrategyPlugin
from ..strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class {class_name}Strategy(BaseStrategy):
    """Custom {plugin_name} strategy"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.name = '{plugin_name}'
        self.description = 'Custom {plugin_name} trading strategy'
        
        # Initialize parameters
        self.param1 = kwargs.get('param1', 10)
        self.param2 = kwargs.get('param2', 0.02)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        result_df = df.copy()
        
        # TODO: Implement your signal logic here
        result_df['signal'] = 0
        result_df['signal_strength'] = 0.5
        
        return result_df
    
    def get_parameters(self) -> Dict[str, Any]:
        return {{
            'param1': self.param1,
            'param2': self.param2
        }}
    
    def set_parameters(self, parameters: Dict[str, Any]):
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)

class {class_name}Plugin(StrategyPlugin):
    """Plugin wrapper for {plugin_name} strategy"""
    
    def get_strategy_class(self) -> Type:
        return {class_name}Strategy
    
    def get_metadata(self) -> Dict[str, Any]:
        return {{
            'id': '{plugin_name.lower().replace(" ", "_")}',
            'name': '{plugin_name}',
            'version': '1.0.0',
            'author': 'Your Name',
            'description': 'Custom {plugin_name} trading strategy',
            'type': 'strategy',
            'created_at': datetime.now().isoformat(),
            'parameters': {{
                'param1': {{
                    'type': 'int',
                    'default': 10,
                    'min': 1,
                    'max': 100,
                    'description': 'Parameter 1 description'
                }},
                'param2': {{
                    'type': 'float',
                    'default': 0.02,
                    'min': 0.01,
                    'max': 0.1,
                    'description': 'Parameter 2 description'
                }}
            }}
        }}
    
    def get_dependencies(self) -> list:
        return ['pandas', 'numpy']
    
    def validate_environment(self) -> bool:
        try:
            import pandas
            import numpy
            return True
        except ImportError:
            return False
'''
    
    def _generate_indicator_plugin_template(self, plugin_name: str) -> str:
        """Generate indicator plugin template"""
        class_name = ''.join(word.capitalize() for word in plugin_name.split())
        
        return f'''from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from ..strategy_plugin_system import IndicatorPlugin

class {class_name}Indicator(IndicatorPlugin):
    """Custom {plugin_name} indicator"""
    
    def __init__(self, period: int = 14, **kwargs):
        self.period = period
        # Add more parameters as needed
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """Calculate the indicator"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for {plugin_name} indicator")
        
        # TODO: Implement your indicator calculation here
        # Example: Simple moving average
        return data['close'].rolling(window=self.period).mean()
    
    def get_metadata(self) -> Dict[str, Any]:
        return {{
            'id': '{plugin_name.lower().replace(" ", "_")}',
            'name': '{plugin_name}',
            'version': '1.0.0',
            'author': 'Your Name',
            'description': 'Custom {plugin_name} indicator',
            'type': 'indicator',
            'created_at': datetime.now().isoformat(),
            'parameters': {{
                'period': {{
                    'type': 'int',
                    'default': 14,
                    'min': 1,
                    'max': 100,
                    'description': 'Calculation period'
                }}
            }}
        }}
    
    def get_parameters(self) -> Dict[str, Any]:
        return {{
            'period': self.period
        }}
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_columns = ['close']
        return all(col in data.columns for col in required_columns) and len(data) >= self.period
'''

# Example usage and testing
if __name__ == "__main__":
    # Initialize plugin system
    plugin_system = StrategyPluginSystem()
    
    # Create example templates
    strategy_template = plugin_system.create_plugin_template('strategy', 'My Custom Strategy')
    indicator_template = plugin_system.create_plugin_template('indicator', 'My Custom Indicator')
    
    print(f"Created strategy template: {strategy_template}")
    print(f"Created indicator template: {indicator_template}")
    
    # Show system status
    status = plugin_system.get_system_status()
    print(f"Plugin system status: {status}")