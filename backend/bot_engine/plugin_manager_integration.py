import os
import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from .strategy_plugin_system import StrategyPluginSystem, StrategyPlugin, IndicatorPlugin
from .strategy_factory import StrategyFactory
from .dynamic_strategy_manager import DynamicStrategyManager

class EnhancedStrategyFactory(StrategyFactory):
    """Enhanced strategy factory with plugin system integration"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize plugin system
        plugin_dirs = [
            os.path.join(os.path.dirname(__file__), 'plugins', 'strategies'),
            os.path.join(os.path.dirname(__file__), 'plugins', 'indicators'),
            os.path.join(os.path.dirname(__file__), 'strategies', 'custom')
        ]
        
        self.plugin_system = StrategyPluginSystem(plugin_dirs)
        self.logger.info(f"Initialized plugin system with {len(self.plugin_system.list_plugins())} plugins")
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get all available strategies including plugins"""
        # Get legacy strategies
        strategies = super().get_available_strategies()
        
        # Add plugin strategies
        plugin_strategies = self.plugin_system.list_plugins('strategy')
        
        for plugin_info in plugin_strategies:
            try:
                plugin = self.plugin_system.get_strategy_plugin(plugin_info.name)
                if plugin:
                    metadata = plugin.get_metadata()
                    
                    strategies[plugin_info.name] = {
                        'name': metadata.get('name', plugin_info.name),
                        'description': metadata.get('description', plugin_info.description),
                        'parameters': metadata.get('parameters', {}),
                        'version': metadata.get('version', plugin_info.version),
                        'author': metadata.get('author', plugin_info.author),
                        'type': 'plugin',
                        'category': metadata.get('category', 'custom'),
                        'tags': metadata.get('tags', []),
                        'plugin_id': plugin_info.name
                    }
            except Exception as e:
                self.logger.error(f"Error loading plugin strategy {plugin_info.name}: {e}")
        
        return strategies
    
    def create_strategy(self, strategy_name: str, **kwargs):
        """Create strategy instance (legacy or plugin)"""
        # Check if it's a plugin strategy
        plugin_strategies = {p.name: p for p in self.plugin_system.list_plugins('strategy')}
        
        if strategy_name in plugin_strategies:
            try:
                return self.plugin_system.create_strategy_instance(strategy_name, **kwargs)
            except Exception as e:
                self.logger.error(f"Failed to create plugin strategy {strategy_name}: {e}")
                raise
        
        # Fall back to legacy strategy creation
        return super().create_strategy(strategy_name, **kwargs)
    
    def install_strategy_plugin(self, plugin_file: str) -> Optional[str]:
        """Install a new strategy plugin"""
        return self.plugin_system.install_plugin_from_file(plugin_file)
    
    def uninstall_strategy_plugin(self, plugin_id: str) -> bool:
        """Uninstall a strategy plugin"""
        return self.plugin_system.uninstall_plugin(plugin_id)
    
    def reload_strategy_plugin(self, plugin_id: str) -> bool:
        """Reload a strategy plugin"""
        return self.plugin_system.reload_plugin(plugin_id)
    
    def get_plugin_system_status(self) -> Dict[str, Any]:
        """Get plugin system status"""
        return self.plugin_system.get_system_status()

class IndicatorManager:
    """Manager for technical indicators using plugin system"""
    
    def __init__(self, plugin_system: StrategyPluginSystem = None):
        self.logger = logging.getLogger(__name__)
        
        if plugin_system is None:
            plugin_dirs = [
                os.path.join(os.path.dirname(__file__), 'plugins', 'indicators')
            ]
            self.plugin_system = StrategyPluginSystem(plugin_dirs)
        else:
            self.plugin_system = plugin_system
        
        self.logger.info(f"Initialized indicator manager with {len(self.get_available_indicators())} indicators")
    
    def get_available_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Get all available indicators"""
        indicators = {}
        plugin_indicators = self.plugin_system.list_plugins('indicator')
        
        for plugin_info in plugin_indicators:
            try:
                plugin = self.plugin_system.get_indicator_plugin(plugin_info.name)
                if plugin:
                    metadata = plugin.get_metadata()
                    
                    indicators[plugin_info.name] = {
                        'name': metadata.get('name', plugin_info.name),
                        'description': metadata.get('description', plugin_info.description),
                        'parameters': metadata.get('parameters', {}),
                        'outputs': metadata.get('outputs', {}),
                        'version': metadata.get('version', plugin_info.version),
                        'author': metadata.get('author', plugin_info.author),
                        'category': metadata.get('category', 'technical'),
                        'tags': metadata.get('tags', []),
                        'plugin_id': plugin_info.name
                    }
            except Exception as e:
                self.logger.error(f"Error loading indicator plugin {plugin_info.name}: {e}")
        
        return indicators
    
    def calculate_indicator(self, indicator_name: str, data, **kwargs):
        """Calculate an indicator"""
        try:
            return self.plugin_system.calculate_indicator(indicator_name, data, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to calculate indicator {indicator_name}: {e}")
            raise
    
    def install_indicator_plugin(self, plugin_file: str) -> Optional[str]:
        """Install a new indicator plugin"""
        return self.plugin_system.install_plugin_from_file(plugin_file)
    
    def uninstall_indicator_plugin(self, plugin_id: str) -> bool:
        """Uninstall an indicator plugin"""
        return self.plugin_system.uninstall_plugin(plugin_id)
    
    def create_indicator_chain(self, indicators: List[Dict[str, Any]], data):
        """Create a chain of indicators that feed into each other"""
        result_data = data.copy()
        
        for indicator_config in indicators:
            indicator_name = indicator_config['name']
            parameters = indicator_config.get('parameters', {})
            output_prefix = indicator_config.get('output_prefix', indicator_name)
            
            try:
                indicator_result = self.calculate_indicator(indicator_name, result_data, **parameters)
                
                # Add indicator results to data
                if isinstance(indicator_result, dict):
                    for key, series in indicator_result.items():
                        result_data[f"{output_prefix}_{key}"] = series
                else:
                    result_data[f"{output_prefix}_value"] = indicator_result
                
            except Exception as e:
                self.logger.error(f"Failed to calculate indicator {indicator_name} in chain: {e}")
                raise
        
        return result_data

class PluginManagerIntegration:
    """Main integration class for plugin system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.strategy_factory = EnhancedStrategyFactory()
        self.indicator_manager = IndicatorManager(self.strategy_factory.plugin_system)
        
        self.logger.info("Plugin manager integration initialized")
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview"""
        return {
            'strategies': {
                'total': len(self.strategy_factory.get_available_strategies()),
                'plugins': len(self.strategy_factory.plugin_system.list_plugins('strategy')),
                'legacy': len(self.strategy_factory.get_available_strategies()) - len(self.strategy_factory.plugin_system.list_plugins('strategy'))
            },
            'indicators': {
                'total': len(self.indicator_manager.get_available_indicators()),
                'plugins': len(self.indicator_manager.plugin_system.list_plugins('indicator'))
            },
            'plugin_system': self.strategy_factory.plugin_system.get_system_status()
        }
    
    def create_custom_strategy_template(self, strategy_name: str, strategy_type: str = 'trend_following') -> str:
        """Create a custom strategy template"""
        return self.strategy_factory.plugin_system.create_plugin_template('strategy', strategy_name)
    
    def create_custom_indicator_template(self, indicator_name: str) -> str:
        """Create a custom indicator template"""
        return self.indicator_manager.plugin_system.create_plugin_template('indicator', indicator_name)
    
    def validate_plugin_compatibility(self, plugin_file: str) -> Dict[str, Any]:
        """Validate plugin compatibility before installation"""
        try:
            # This would involve loading the plugin temporarily and checking compatibility
            # For now, return basic validation
            return {
                'compatible': True,
                'warnings': [],
                'requirements_met': True,
                'version_compatible': True
            }
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e),
                'warnings': [],
                'requirements_met': False,
                'version_compatible': False
            }
    
    def export_plugin_configuration(self, output_file: str):
        """Export current plugin configuration"""
        self.strategy_factory.plugin_system.export_plugin_list(output_file)
    
    def get_plugin_marketplace_info(self) -> Dict[str, Any]:
        """Get information for plugin marketplace"""
        strategies = self.strategy_factory.get_available_strategies()
        indicators = self.indicator_manager.get_available_indicators()
        
        marketplace_info = {
            'strategies': [],
            'indicators': [],
            'categories': set(),
            'authors': set(),
            'total_plugins': 0
        }
        
        # Process strategies
        for strategy_id, strategy_info in strategies.items():
            if strategy_info.get('type') == 'plugin':
                marketplace_info['strategies'].append({
                    'id': strategy_id,
                    'name': strategy_info['name'],
                    'description': strategy_info['description'],
                    'category': strategy_info.get('category', 'custom'),
                    'author': strategy_info.get('author', 'Unknown'),
                    'version': strategy_info.get('version', '1.0.0'),
                    'tags': strategy_info.get('tags', []),
                    'parameters': len(strategy_info.get('parameters', {}))
                })
                marketplace_info['categories'].add(strategy_info.get('category', 'custom'))
                marketplace_info['authors'].add(strategy_info.get('author', 'Unknown'))
        
        # Process indicators
        for indicator_id, indicator_info in indicators.items():
            marketplace_info['indicators'].append({
                'id': indicator_id,
                'name': indicator_info['name'],
                'description': indicator_info['description'],
                'category': indicator_info.get('category', 'technical'),
                'author': indicator_info.get('author', 'Unknown'),
                'version': indicator_info.get('version', '1.0.0'),
                'tags': indicator_info.get('tags', []),
                'outputs': len(indicator_info.get('outputs', {}))
            })
            marketplace_info['categories'].add(indicator_info.get('category', 'technical'))
            marketplace_info['authors'].add(indicator_info.get('author', 'Unknown'))
        
        marketplace_info['categories'] = list(marketplace_info['categories'])
        marketplace_info['authors'] = list(marketplace_info['authors'])
        marketplace_info['total_plugins'] = len(marketplace_info['strategies']) + len(marketplace_info['indicators'])
        
        return marketplace_info

# Global instance for easy access
_plugin_manager = None

def get_plugin_manager() -> PluginManagerIntegration:
    """Get global plugin manager instance"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManagerIntegration()
    return _plugin_manager

# Convenience functions
def create_strategy(strategy_name: str, **kwargs):
    """Create a strategy instance"""
    return get_plugin_manager().strategy_factory.create_strategy(strategy_name, **kwargs)

def calculate_indicator(indicator_name: str, data, **kwargs):
    """Calculate an indicator"""
    return get_plugin_manager().indicator_manager.calculate_indicator(indicator_name, data, **kwargs)

def get_available_strategies() -> Dict[str, Dict[str, Any]]:
    """Get all available strategies"""
    return get_plugin_manager().strategy_factory.get_available_strategies()

def get_available_indicators() -> Dict[str, Dict[str, Any]]:
    """Get all available indicators"""
    return get_plugin_manager().indicator_manager.get_available_indicators()

def install_plugin(plugin_file: str) -> Optional[str]:
    """Install a plugin (auto-detect type)"""
    manager = get_plugin_manager()
    
    # Try as strategy first
    plugin_id = manager.strategy_factory.install_strategy_plugin(plugin_file)
    if plugin_id:
        return plugin_id
    
    # Try as indicator
    return manager.indicator_manager.install_indicator_plugin(plugin_file)

if __name__ == "__main__":
    # Example usage
    manager = get_plugin_manager()
    
    print("System Overview:")
    overview = manager.get_system_overview()
    for key, value in overview.items():
        print(f"  {key}: {value}")
    
    print("\nAvailable Strategies:")
    strategies = get_available_strategies()
    for name, info in strategies.items():
        print(f"  {name}: {info['description']}")
    
    print("\nAvailable Indicators:")
    indicators = get_available_indicators()
    for name, info in indicators.items():
        print(f"  {name}: {info['description']}")