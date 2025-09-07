"""Data Utilities Module

This module provides comprehensive data processing and validation utilities:
- OHLC data validation and cleaning
- Time series resampling and alignment
- Data normalization and transformation
- Missing data handling
- Outlier detection and removal
- Data quality metrics

All functions are optimized for financial time series data.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
from dataclasses import dataclass
import logging

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class DataQualityReport:
    """Data quality assessment report"""
    total_records: int
    missing_values: Dict[str, int]
    duplicate_records: int
    outliers_detected: Dict[str, int]
    data_gaps: List[Tuple[datetime, datetime]]
    quality_score: float
    recommendations: List[str]

class DataValidator:
    """Comprehensive data validation for financial time series"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_rules = {
            'ohlc': self._validate_ohlc_rules,
            'volume': self._validate_volume_rules,
            'price': self._validate_price_rules,
            'returns': self._validate_returns_rules
        }
    
    def validate(self, data: Union[pd.DataFrame, pd.Series], 
                data_type: str = 'ohlc') -> Tuple[bool, List[str]]:
        """Validate data based on type
        
        Args:
            data: Data to validate
            data_type: Type of data ('ohlc', 'volume', 'price', 'returns')
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Basic checks
        if data is None or len(data) == 0:
            errors.append("Data is empty or None")
            return False, errors
        
        # Type-specific validation
        if data_type in self.validation_rules:
            type_errors = self.validation_rules[data_type](data)
            errors.extend(type_errors)
        else:
            errors.append(f"Unknown data type: {data_type}")
        
        # General data quality checks
        general_errors = self._validate_general_quality(data)
        errors.extend(general_errors)
        
        is_valid = len(errors) == 0 or not self.strict_mode
        
        if errors:
            logger.warning(f"Data validation issues: {errors}")
        
        return is_valid, errors
    
    def _validate_ohlc_rules(self, data: pd.DataFrame) -> List[str]:
        """Validate OHLC data rules"""
        errors = []
        
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return errors
        
        # OHLC relationship validation
        for idx, row in data.iterrows():
            if pd.isna(row[required_columns]).any():
                continue
            
            o, h, l, c = row['open'], row['high'], row['low'], row['close']
            
            # High should be >= max(open, close)
            if h < max(o, c):
                errors.append(f"High < max(open, close) at index {idx}")
            
            # Low should be <= min(open, close)
            if l > min(o, c):
                errors.append(f"Low > min(open, close) at index {idx}")
            
            # All values should be positive
            if any(val <= 0 for val in [o, h, l, c]):
                errors.append(f"Non-positive price values at index {idx}")
        
        return errors
    
    def _validate_volume_rules(self, data: Union[pd.DataFrame, pd.Series]) -> List[str]:
        """Validate volume data rules"""
        errors = []
        
        if isinstance(data, pd.DataFrame):
            if 'volume' not in data.columns:
                errors.append("Volume column not found")
                return errors
            volume_data = data['volume']
        else:
            volume_data = data
        
        # Volume should be non-negative
        negative_volume = volume_data < 0
        if negative_volume.any():
            errors.append(f"Negative volume values found: {negative_volume.sum()} instances")
        
        # Check for unrealistic volume spikes
        if len(volume_data) > 1:
            volume_changes = volume_data.pct_change().abs()
            extreme_changes = volume_changes > 10  # 1000% change
            if extreme_changes.any():
                errors.append(f"Extreme volume changes detected: {extreme_changes.sum()} instances")
        
        return errors
    
    def _validate_price_rules(self, data: Union[pd.DataFrame, pd.Series]) -> List[str]:
        """Validate price data rules"""
        errors = []
        
        if isinstance(data, pd.DataFrame):
            price_columns = [col for col in data.columns if col in ['open', 'high', 'low', 'close', 'price']]
            if not price_columns:
                errors.append("No price columns found")
                return errors
            price_data = data[price_columns[0]]
        else:
            price_data = data
        
        # Prices should be positive
        non_positive = price_data <= 0
        if non_positive.any():
            errors.append(f"Non-positive price values: {non_positive.sum()} instances")
        
        # Check for unrealistic price movements
        if len(price_data) > 1:
            price_changes = price_data.pct_change().abs()
            extreme_changes = price_changes > 0.5  # 50% change
            if extreme_changes.any():
                errors.append(f"Extreme price changes detected: {extreme_changes.sum()} instances")
        
        return errors
    
    def _validate_returns_rules(self, data: Union[pd.DataFrame, pd.Series]) -> List[str]:
        """Validate returns data rules"""
        errors = []
        
        if isinstance(data, pd.DataFrame):
            returns_columns = [col for col in data.columns if 'return' in col.lower()]
            if not returns_columns:
                errors.append("No returns columns found")
                return errors
            returns_data = data[returns_columns[0]]
        else:
            returns_data = data
        
        # Check for extreme returns
        extreme_returns = returns_data.abs() > 1.0  # 100% return
        if extreme_returns.any():
            errors.append(f"Extreme returns detected: {extreme_returns.sum()} instances")
        
        return errors
    
    def _validate_general_quality(self, data: Union[pd.DataFrame, pd.Series]) -> List[str]:
        """General data quality validation"""
        errors = []
        
        # Check for excessive missing values
        if isinstance(data, pd.DataFrame):
            missing_pct = data.isnull().sum() / len(data)
            high_missing = missing_pct > 0.1  # More than 10% missing
            if high_missing.any():
                high_missing_cols = missing_pct[high_missing].index.tolist()
                errors.append(f"High missing value percentage in columns: {high_missing_cols}")
        else:
            missing_pct = data.isnull().sum() / len(data)
            if missing_pct > 0.1:
                errors.append(f"High missing value percentage: {missing_pct:.2%}")
        
        # Check for duplicate indices (if datetime index)
        if hasattr(data.index, 'duplicated'):
            duplicates = data.index.duplicated()
            if duplicates.any():
                errors.append(f"Duplicate index values: {duplicates.sum()} instances")
        
        return errors

class PriceDataCleaner:
    """Advanced price data cleaning and preprocessing"""
    
    def __init__(self, outlier_method: str = 'iqr', fill_method: str = 'forward'):
        self.outlier_method = outlier_method
        self.fill_method = fill_method
        self.cleaning_log = []
    
    def clean_data(self, data: pd.DataFrame, 
                   remove_outliers: bool = True,
                   fill_missing: bool = True,
                   validate_ohlc: bool = True) -> pd.DataFrame:
        """Comprehensive data cleaning pipeline
        
        Args:
            data: Raw OHLC data
            remove_outliers: Whether to remove outlier detection
            fill_missing: Whether to fill missing values
            validate_ohlc: Whether to validate OHLC relationships
            
        Returns:
            Cleaned DataFrame
        """
        cleaned_data = data.copy()
        self.cleaning_log = []
        
        # Remove duplicates
        initial_len = len(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()
        if len(cleaned_data) < initial_len:
            removed = initial_len - len(cleaned_data)
            self.cleaning_log.append(f"Removed {removed} duplicate records")
        
        # Sort by index (assuming datetime index)
        if not cleaned_data.index.is_monotonic_increasing:
            cleaned_data = cleaned_data.sort_index()
            self.cleaning_log.append("Sorted data by index")
        
        # Remove outliers
        if remove_outliers:
            cleaned_data = self._remove_outliers(cleaned_data)
        
        # Fill missing values
        if fill_missing:
            cleaned_data = self._fill_missing_values(cleaned_data)
        
        # Validate and fix OHLC relationships
        if validate_ohlc and self._has_ohlc_columns(cleaned_data):
            cleaned_data = self._fix_ohlc_relationships(cleaned_data)
        
        # Final validation
        validator = DataValidator()
        is_valid, errors = validator.validate(cleaned_data, 'ohlc')
        if not is_valid:
            logger.warning(f"Data still has validation issues after cleaning: {errors}")
        
        return cleaned_data
    
    def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers using specified method"""
        cleaned_data = data.copy()
        
        numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if self.outlier_method == 'iqr':
                outliers = self._detect_outliers_iqr(cleaned_data[column])
            elif self.outlier_method == 'zscore':
                outliers = self._detect_outliers_zscore(cleaned_data[column])
            else:
                continue
            
            if outliers.any():
                # Replace outliers with NaN (will be filled later)
                cleaned_data.loc[outliers, column] = np.nan
                self.cleaning_log.append(f"Removed {outliers.sum()} outliers from {column}")
        
        return cleaned_data
    
    def _detect_outliers_iqr(self, series: pd.Series, factor: float = 1.5) -> pd.Series:
        """Detect outliers using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        
        return (series < lower_bound) | (series > upper_bound)
    
    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> pd.Series:
        """Detect outliers using Z-score method"""
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold
    
    def _fill_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values using specified method"""
        cleaned_data = data.copy()
        
        if self.fill_method == 'forward':
            cleaned_data = cleaned_data.fillna(method='ffill')
        elif self.fill_method == 'backward':
            cleaned_data = cleaned_data.fillna(method='bfill')
        elif self.fill_method == 'interpolate':
            cleaned_data = cleaned_data.interpolate(method='linear')
        elif self.fill_method == 'mean':
            cleaned_data = cleaned_data.fillna(cleaned_data.mean())
        
        # Fill any remaining NaN with forward fill
        cleaned_data = cleaned_data.fillna(method='ffill')
        
        missing_filled = data.isnull().sum().sum() - cleaned_data.isnull().sum().sum()
        if missing_filled > 0:
            self.cleaning_log.append(f"Filled {missing_filled} missing values")
        
        return cleaned_data
    
    def _has_ohlc_columns(self, data: pd.DataFrame) -> bool:
        """Check if data has OHLC columns"""
        required_columns = ['open', 'high', 'low', 'close']
        return all(col in data.columns for col in required_columns)
    
    def _fix_ohlc_relationships(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fix invalid OHLC relationships"""
        cleaned_data = data.copy()
        fixes_applied = 0
        
        for idx, row in cleaned_data.iterrows():
            if pd.isna(row[['open', 'high', 'low', 'close']]).any():
                continue
            
            o, h, l, c = row['open'], row['high'], row['low'], row['close']
            
            # Fix high value
            correct_high = max(o, h, l, c)
            if h != correct_high:
                cleaned_data.loc[idx, 'high'] = correct_high
                fixes_applied += 1
            
            # Fix low value
            correct_low = min(o, h, l, c)
            if l != correct_low:
                cleaned_data.loc[idx, 'low'] = correct_low
                fixes_applied += 1
        
        if fixes_applied > 0:
            self.cleaning_log.append(f"Fixed {fixes_applied} OHLC relationship violations")
        
        return cleaned_data
    
    def get_cleaning_report(self) -> List[str]:
        """Get report of cleaning operations performed"""
        return self.cleaning_log.copy()

class TimeSeriesResampler:
    """Advanced time series resampling and alignment"""
    
    def __init__(self):
        self.resampling_methods = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'price': 'last'
        }
    
    def resample_data(self, data: pd.DataFrame, 
                     target_frequency: str,
                     method: str = 'standard') -> pd.DataFrame:
        """Resample time series data to target frequency
        
        Args:
            data: Input time series data
            target_frequency: Target frequency ('1H', '1D', etc.)
            method: Resampling method ('standard', 'vwap', 'custom')
            
        Returns:
            Resampled DataFrame
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex for resampling")
        
        if method == 'standard':
            return self._standard_resample(data, target_frequency)
        elif method == 'vwap':
            return self._vwap_resample(data, target_frequency)
        else:
            raise ValueError(f"Unknown resampling method: {method}")
    
    def _standard_resample(self, data: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """Standard OHLC resampling"""
        resampled_data = {}
        
        for column in data.columns:
            if column in self.resampling_methods:
                method = self.resampling_methods[column]
                resampled_data[column] = data[column].resample(frequency).agg(method)
            else:
                # Default to last value for unknown columns
                resampled_data[column] = data[column].resample(frequency).last()
        
        result = pd.DataFrame(resampled_data)
        
        # Remove periods with no data
        result = result.dropna(how='all')
        
        return result
    
    def _vwap_resample(self, data: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """Volume-weighted average price resampling"""
        if 'volume' not in data.columns:
            logger.warning("Volume column not found, falling back to standard resampling")
            return self._standard_resample(data, frequency)
        
        # Calculate VWAP for each period
        def calculate_vwap(group):
            if len(group) == 0 or group['volume'].sum() == 0:
                return group.iloc[-1] if len(group) > 0 else None
            
            # Typical price
            if all(col in group.columns for col in ['high', 'low', 'close']):
                typical_price = (group['high'] + group['low'] + group['close']) / 3
            else:
                typical_price = group['close']
            
            # VWAP calculation
            vwap = (typical_price * group['volume']).sum() / group['volume'].sum()
            
            result = {
                'open': group['open'].iloc[0],
                'high': group['high'].max(),
                'low': group['low'].min(),
                'close': group['close'].iloc[-1],
                'volume': group['volume'].sum(),
                'vwap': vwap
            }
            
            return pd.Series(result)
        
        resampled = data.resample(frequency).apply(calculate_vwap)
        return resampled.dropna()
    
    def align_data(self, *dataframes: pd.DataFrame, 
                   method: str = 'inner') -> List[pd.DataFrame]:
        """Align multiple DataFrames to common time index
        
        Args:
            dataframes: DataFrames to align
            method: Alignment method ('inner', 'outer', 'left', 'right')
            
        Returns:
            List of aligned DataFrames
        """
        if len(dataframes) < 2:
            return list(dataframes)
        
        # Find common time range
        if method == 'inner':
            start_time = max(df.index.min() for df in dataframes)
            end_time = min(df.index.max() for df in dataframes)
        elif method == 'outer':
            start_time = min(df.index.min() for df in dataframes)
            end_time = max(df.index.max() for df in dataframes)
        else:
            # Use first DataFrame as reference
            start_time = dataframes[0].index.min()
            end_time = dataframes[0].index.max()
        
        # Create common index
        common_freq = pd.infer_freq(dataframes[0].index)
        if common_freq is None:
            # Fallback to most common frequency
            common_freq = '1H'  # Default hourly
        
        common_index = pd.date_range(start=start_time, end=end_time, freq=common_freq)
        
        # Align all DataFrames
        aligned_dfs = []
        for df in dataframes:
            aligned_df = df.reindex(common_index, method='ffill')
            aligned_dfs.append(aligned_df)
        
        return aligned_dfs

class DataProcessor:
    """Main data processing orchestrator"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.cleaner = PriceDataCleaner()
        self.resampler = TimeSeriesResampler()
    
    def process_data(self, data: pd.DataFrame,
                    clean: bool = True,
                    validate: bool = True,
                    resample_to: Optional[str] = None) -> Tuple[pd.DataFrame, DataQualityReport]:
        """Complete data processing pipeline
        
        Args:
            data: Raw input data
            clean: Whether to clean the data
            validate: Whether to validate the data
            resample_to: Target frequency for resampling
            
        Returns:
            Tuple of (processed_data, quality_report)
        """
        processed_data = data.copy()
        
        # Initial validation
        if validate:
            is_valid, errors = self.validator.validate(processed_data, 'ohlc')
            if not is_valid:
                logger.warning(f"Initial validation failed: {errors}")
        
        # Data cleaning
        if clean:
            processed_data = self.cleaner.clean_data(processed_data)
        
        # Resampling
        if resample_to:
            processed_data = self.resampler.resample_data(processed_data, resample_to)
        
        # Generate quality report
        quality_report = self._generate_quality_report(data, processed_data)
        
        return processed_data, quality_report
    
    def _generate_quality_report(self, original_data: pd.DataFrame, 
                               processed_data: pd.DataFrame) -> DataQualityReport:
        """Generate comprehensive data quality report"""
        # Calculate metrics
        total_records = len(processed_data)
        missing_values = processed_data.isnull().sum().to_dict()
        duplicate_records = processed_data.duplicated().sum()
        
        # Detect outliers (simplified)
        outliers_detected = {}
        numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            z_scores = np.abs((processed_data[col] - processed_data[col].mean()) / processed_data[col].std())
            outliers_detected[col] = (z_scores > 3).sum()
        
        # Detect data gaps (simplified)
        data_gaps = []
        if isinstance(processed_data.index, pd.DatetimeIndex):
            time_diffs = processed_data.index.to_series().diff()
            median_diff = time_diffs.median()
            large_gaps = time_diffs > median_diff * 3
            
            for idx in processed_data.index[large_gaps]:
                prev_idx = processed_data.index[processed_data.index < idx][-1]
                data_gaps.append((prev_idx, idx))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            total_records, missing_values, duplicate_records, outliers_detected
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_values, duplicate_records, outliers_detected, data_gaps
        )
        
        return DataQualityReport(
            total_records=total_records,
            missing_values=missing_values,
            duplicate_records=duplicate_records,
            outliers_detected=outliers_detected,
            data_gaps=data_gaps,
            quality_score=quality_score,
            recommendations=recommendations
        )
    
    def _calculate_quality_score(self, total_records: int, missing_values: Dict[str, int],
                               duplicate_records: int, outliers_detected: Dict[str, int]) -> float:
        """Calculate overall data quality score (0-100)"""
        if total_records == 0:
            return 0.0
        
        # Penalize missing values
        missing_penalty = sum(missing_values.values()) / (total_records * len(missing_values)) * 30
        
        # Penalize duplicates
        duplicate_penalty = (duplicate_records / total_records) * 20
        
        # Penalize outliers
        outlier_penalty = sum(outliers_detected.values()) / (total_records * len(outliers_detected)) * 25
        
        # Base score
        quality_score = 100 - missing_penalty - duplicate_penalty - outlier_penalty
        
        return max(0, min(100, quality_score))
    
    def _generate_recommendations(self, missing_values: Dict[str, int],
                                duplicate_records: int, outliers_detected: Dict[str, int],
                                data_gaps: List[Tuple]) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        # Missing values recommendations
        high_missing = {k: v for k, v in missing_values.items() if v > 0}
        if high_missing:
            recommendations.append(f"Consider filling missing values in: {list(high_missing.keys())}")
        
        # Duplicate recommendations
        if duplicate_records > 0:
            recommendations.append(f"Remove {duplicate_records} duplicate records")
        
        # Outlier recommendations
        high_outliers = {k: v for k, v in outliers_detected.items() if v > 0}
        if high_outliers:
            recommendations.append(f"Review outliers in: {list(high_outliers.keys())}")
        
        # Data gap recommendations
        if data_gaps:
            recommendations.append(f"Address {len(data_gaps)} data gaps in time series")
        
        return recommendations

# Utility functions for quick access
def validate_ohlc_data(data: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Quick OHLC data validation"""
    validator = DataValidator()
    return validator.validate(data, 'ohlc')

def clean_price_data(data: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Quick price data cleaning"""
    cleaner = PriceDataCleaner(**kwargs)
    return cleaner.clean_data(data)

def resample_data(data: pd.DataFrame, frequency: str, **kwargs) -> pd.DataFrame:
    """Quick data resampling"""
    resampler = TimeSeriesResampler()
    return resampler.resample_data(data, frequency, **kwargs)

def calculate_returns(prices: pd.Series, method: str = 'simple') -> pd.Series:
    """Calculate price returns
    
    Args:
        prices: Price series
        method: 'simple' or 'log'
        
    Returns:
        Returns series
    """
    if method == 'simple':
        return prices.pct_change()
    elif method == 'log':
        return np.log(prices / prices.shift(1))
    else:
        raise ValueError(f"Unknown method: {method}")

def normalize_data(data: Union[pd.DataFrame, pd.Series], 
                  method: str = 'minmax') -> Union[pd.DataFrame, pd.Series]:
    """Normalize data using specified method
    
    Args:
        data: Data to normalize
        method: 'minmax', 'zscore', or 'robust'
        
    Returns:
        Normalized data
    """
    if method == 'minmax':
        return (data - data.min()) / (data.max() - data.min())
    elif method == 'zscore':
        return (data - data.mean()) / data.std()
    elif method == 'robust':
        median = data.median()
        mad = (data - median).abs().median()
        return (data - median) / mad
    else:
        raise ValueError(f"Unknown normalization method: {method}")