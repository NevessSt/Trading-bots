import os
import sys
import json
import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
import logging
from datetime import datetime
from threading import Lock
from dataclasses import dataclass, asdict

from .strategies.base_strategy import BaseStrategy

@dataclass
class StrategyMetadata:
    """Metadata for a trading strategy"""
    id: str
    name: str
    description: str
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    parameters: Dict[str, Any]
    file_path: str
    class_name: str
    is_active: bool = True
    tags: List[str] = None
    risk_level: str = "medium"  # low, medium, high
    min_capital: float = 100.0
    supported_timeframes: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.supported_timeframes is None:
            self.supported_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']

class DynamicStrategyManager:
    """Manager for dynamic loading and management of trading strategies"""
    
    def __init__(self, strategies_dir: str = None, config_dir: str = None):
        """
        Initialize the dynamic strategy manager
        
        Args:
            strategies_dir: Directory containing strategy files
            config_dir: Directory for strategy configurations
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default directories
        if strategies_dir is None:
            strategies_dir = os.path.join(os.path.dirname(__file__), 'strategies')
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'strategy_configs')
            
        self.strategies_dir = Path(strategies_dir)
        self.config_dir = Path(config_dir)
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Strategy registry
        self._strategies: Dict[str, StrategyMetadata] = {}
        self._strategy_classes: Dict[str, Type[BaseStrategy]] = {}
        self._strategy_instances: Dict[str, BaseStrategy] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # File modification times for hot reloading
        self._file_mtimes: Dict[str, float] = {}
        
        # Initialize
        self._discover_strategies()
        
    def _discover_strategies(self):
        """Discover all strategy files in the strategies directory"""
        try:
            for file_path in self.strategies_dir.glob('*.py'):
                if file_path.name.startswith('__') or file_path.name == 'base_strategy.py':
                    continue
                    
                self._load_strategy_from_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Error discovering strategies: {e}")
    
    def _load_strategy_from_file(self, file_path: Path) -> Optional[str]:
        """Load a strategy from a Python file
        
        Args:
            file_path: Path to the strategy file
            
        Returns:
            Strategy ID if successful, None otherwise
        """
        try:
            # Get file modification time
            mtime = file_path.stat().st_mtime
            
            # Check if file has been modified
            if str(file_path) in self._file_mtimes:
                if self._file_mtimes[str(file_path)] >= mtime:
                    return None  # No changes
            
            self._file_mtimes[str(file_path)] = mtime
            
            # Load module dynamically
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not load spec for {file_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find strategy classes in the module
            strategy_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseStrategy) and 
                    obj != BaseStrategy and 
                    obj.__module__ == module.__name__):
                    strategy_classes.append((name, obj))
            
            if not strategy_classes:
                self.logger.warning(f"No strategy classes found in {file_path}")
                return None
            
            # Process each strategy class
            for class_name, strategy_class in strategy_classes:
                strategy_id = self._register_strategy_class(strategy_class, class_name, file_path)
                if strategy_id:
                    self.logger.info(f"Loaded strategy: {strategy_id} from {file_path}")
                    
            return strategy_classes[0][0] if strategy_classes else None
            
        except Exception as e:
            self.logger.error(f"Error loading strategy from {file_path}: {e}")
            return None
    
    def _register_strategy_class(self, strategy_class: Type[BaseStrategy], 
                               class_name: str, file_path: Path) -> Optional[str]:
        """Register a strategy class
        
        Args:
            strategy_class: The strategy class
            class_name: Name of the class
            file_path: Path to the file containing the class
            
        Returns:
            Strategy ID if successful, None otherwise
        """
        try:
            # Create a temporary instance to get metadata
            temp_instance = strategy_class()
            
            # Generate strategy ID
            strategy_id = getattr(temp_instance, 'strategy_id', None)
            if not strategy_id:
                strategy_id = class_name.lower().replace('strategy', '')
            
            # Get strategy metadata
            metadata = StrategyMetadata(
                id=strategy_id,
                name=getattr(temp_instance, 'name', class_name),
                description=getattr(temp_instance, 'description', 'No description available'),
                version=getattr(temp_instance, 'version', '1.0.0'),
                author=getattr(temp_instance, 'author', 'Unknown'),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parameters=getattr(temp_instance, 'get_parameters', lambda: {})(),
                file_path=str(file_path),
                class_name=class_name,
                tags=getattr(temp_instance, 'tags', []),
                risk_level=getattr(temp_instance, 'risk_level', 'medium'),
                min_capital=getattr(temp_instance, 'min_capital', 100.0),
                supported_timeframes=getattr(temp_instance, 'supported_timeframes', 
                                           ['1m', '5m', '15m', '1h', '4h', '1d'])
            )
            
            # Store in registry
            with self._lock:
                self._strategies[strategy_id] = metadata
                self._strategy_classes[strategy_id] = strategy_class
            
            # Save metadata to file
            self._save_strategy_metadata(strategy_id, metadata)
            
            return strategy_id
            
        except Exception as e:
            self.logger.error(f"Error registering strategy class {class_name}: {e}")
            return None
    
    def _save_strategy_metadata(self, strategy_id: str, metadata: StrategyMetadata):
        """Save strategy metadata to file"""
        try:
            metadata_file = self.config_dir / f"{strategy_id}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving metadata for {strategy_id}: {e}")
    
    def get_strategy(self, strategy_id: str, parameters: Dict[str, Any] = None) -> Optional[BaseStrategy]:
        """Get a strategy instance by ID
        
        Args:
            strategy_id: Strategy identifier
            parameters: Strategy parameters
            
        Returns:
            Strategy instance or None if not found
        """
        with self._lock:
            if strategy_id not in self._strategy_classes:
                self.logger.error(f"Strategy not found: {strategy_id}")
                return None
            
            try:
                strategy_class = self._strategy_classes[strategy_id]
                instance = strategy_class()
                
                # Set parameters if provided
                if parameters:
                    if hasattr(instance, 'set_parameters'):
                        instance.set_parameters(parameters)
                    else:
                        # Set parameters as attributes
                        for key, value in parameters.items():
                            if hasattr(instance, key):
                                setattr(instance, key, value)
                
                return instance
                
            except Exception as e:
                self.logger.error(f"Error creating strategy instance {strategy_id}: {e}")
                return None
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get list of available strategies
        
        Returns:
            List of strategy information dictionaries
        """
        with self._lock:
            strategies = []
            for strategy_id, metadata in self._strategies.items():
                if metadata.is_active:
                    strategies.append({
                        'id': metadata.id,
                        'name': metadata.name,
                        'description': metadata.description,
                        'version': metadata.version,
                        'author': metadata.author,
                        'parameters': metadata.parameters,
                        'tags': metadata.tags,
                        'risk_level': metadata.risk_level,
                        'min_capital': metadata.min_capital,
                        'supported_timeframes': metadata.supported_timeframes
                    })
            return strategies
    
    def reload_strategy(self, strategy_id: str) -> bool:
        """Reload a specific strategy
        
        Args:
            strategy_id: Strategy to reload
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if strategy_id not in self._strategies:
                return False
            
            metadata = self._strategies[strategy_id]
            file_path = Path(metadata.file_path)
            
            if not file_path.exists():
                self.logger.error(f"Strategy file not found: {file_path}")
                return False
            
            # Force reload by resetting modification time
            self._file_mtimes[str(file_path)] = 0
            
            # Reload the strategy
            result = self._load_strategy_from_file(file_path)
            return result is not None
    
    def reload_all_strategies(self) -> int:
        """Reload all strategies
        
        Returns:
            Number of strategies successfully reloaded
        """
        self.logger.info("Reloading all strategies...")
        
        # Reset modification times to force reload
        self._file_mtimes.clear()
        
        # Clear current strategies
        with self._lock:
            self._strategies.clear()
            self._strategy_classes.clear()
        
        # Rediscover strategies
        self._discover_strategies()
        
        return len(self._strategies)
    
    def add_strategy_from_code(self, strategy_code: str, strategy_name: str) -> Optional[str]:
        """Add a strategy from code string
        
        Args:
            strategy_code: Python code for the strategy
            strategy_name: Name for the strategy file
            
        Returns:
            Strategy ID if successful, None otherwise
        """
        try:
            # Create strategy file
            strategy_file = self.strategies_dir / f"{strategy_name}.py"
            
            with open(strategy_file, 'w') as f:
                f.write(strategy_code)
            
            # Load the new strategy
            return self._load_strategy_from_file(strategy_file)
            
        except Exception as e:
            self.logger.error(f"Error adding strategy from code: {e}")
            return None
    
    def remove_strategy(self, strategy_id: str) -> bool:
        """Remove a strategy
        
        Args:
            strategy_id: Strategy to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if strategy_id not in self._strategies:
                    return False
                
                # Mark as inactive instead of deleting
                self._strategies[strategy_id].is_active = False
                
                # Save updated metadata
                self._save_strategy_metadata(strategy_id, self._strategies[strategy_id])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing strategy {strategy_id}: {e}")
            return False
    
    def get_strategy_metadata(self, strategy_id: str) -> Optional[StrategyMetadata]:
        """Get strategy metadata
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Strategy metadata or None if not found
        """
        with self._lock:
            return self._strategies.get(strategy_id)
    
    def update_strategy_parameters(self, strategy_id: str, parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters
        
        Args:
            strategy_id: Strategy identifier
            parameters: New parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                if strategy_id not in self._strategies:
                    return False
                
                # Update metadata
                self._strategies[strategy_id].parameters.update(parameters)
                self._strategies[strategy_id].updated_at = datetime.now()
                
                # Save updated metadata
                self._save_strategy_metadata(strategy_id, self._strategies[strategy_id])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating strategy parameters {strategy_id}: {e}")
            return False
    
    def check_for_updates(self) -> List[str]:
        """Check for strategy file updates
        
        Returns:
            List of strategy IDs that have been updated
        """
        updated_strategies = []
        
        try:
            for file_path in self.strategies_dir.glob('*.py'):
                if file_path.name.startswith('__') or file_path.name == 'base_strategy.py':
                    continue
                
                mtime = file_path.stat().st_mtime
                
                if (str(file_path) in self._file_mtimes and 
                    self._file_mtimes[str(file_path)] < mtime):
                    
                    strategy_id = self._load_strategy_from_file(file_path)
                    if strategy_id:
                        updated_strategies.append(strategy_id)
        
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
        
        return updated_strategies
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded strategies
        
        Returns:
            Dictionary with strategy statistics
        """
        with self._lock:
            total_strategies = len(self._strategies)
            active_strategies = sum(1 for s in self._strategies.values() if s.is_active)
            
            risk_levels = {}
            tags = {}
            
            for metadata in self._strategies.values():
                if metadata.is_active:
                    # Count risk levels
                    risk_levels[metadata.risk_level] = risk_levels.get(metadata.risk_level, 0) + 1
                    
                    # Count tags
                    for tag in metadata.tags:
                        tags[tag] = tags.get(tag, 0) + 1
            
            return {
                'total_strategies': total_strategies,
                'active_strategies': active_strategies,
                'inactive_strategies': total_strategies - active_strategies,
                'risk_levels': risk_levels,
                'tags': tags,
                'strategies_dir': str(self.strategies_dir),
                'config_dir': str(self.config_dir)
            }