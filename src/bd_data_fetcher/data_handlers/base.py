"""Base data handler for BD Data Fetcher."""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

from ..api.client import APIClient

logger = structlog.get_logger(__name__)


class DataHandlerConfig(BaseModel):
    """Configuration for data handlers."""
    
    output_dir: str = Field(default="data", description="Output directory for data files")
    file_format: str = Field(default="json", description="Output file format (json, csv)")
    include_timestamp: bool = Field(default=True, description="Include timestamp in filename")
    compress_output: bool = Field(default=False, description="Compress output files")


class BaseDataHandler(ABC):
    """Base class for all data handlers."""
    
    def __init__(self, api_client: APIClient, config: Optional[DataHandlerConfig] = None):
        """Initialize the data handler.
        
        Args:
            api_client: API client instance
            config: Handler configuration
        """
        self.api_client = api_client
        self.config = config or DataHandlerConfig()
        
        # Ensure output directory exists
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Data handler initialized", output_dir=str(self.output_dir))
    
    @abstractmethod
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from the API.
        
        Args:
            **kwargs: Additional parameters for data fetching
            
        Returns:
            Fetched data
        """
        pass
    
    @abstractmethod
    def process_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw data into structured format.
        
        Args:
            data: Raw data from API
            
        Returns:
            Processed data list
        """
        pass
    
    def save_data(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Save processed data to file.
        
        Args:
            data: Processed data to save
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.include_timestamp else ""
            handler_name = self.__class__.__name__.lower().replace("handler", "")
            filename = f"{handler_name}_data_{timestamp}.{self.config.file_format}"
        
        file_path = self.output_dir / filename
        
        try:
            if self.config.file_format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            elif self.config.file_format == "csv":
                import csv
                if data and isinstance(data[0], dict):
                    fieldnames = data[0].keys()
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
            else:
                raise ValueError(f"Unsupported file format: {self.config.file_format}")
            
            logger.info("Data saved successfully", file_path=str(file_path), record_count=len(data))
            return str(file_path)
            
        except Exception as e:
            logger.error("Failed to save data", file_path=str(file_path), error=str(e))
            raise
    
    def fetch_and_save(self, **kwargs) -> str:
        """Fetch data, process it, and save to file.
        
        Args:
            **kwargs: Parameters for data fetching
            
        Returns:
            Path to saved file
        """
        logger.info("Starting data fetch and save operation")
        
        # Fetch data
        raw_data = self.fetch_data(**kwargs)
        logger.info("Data fetched successfully", data_size=len(str(raw_data)))
        
        # Process data
        processed_data = self.process_data(raw_data)
        logger.info("Data processed successfully", record_count=len(processed_data))
        
        # Save data
        file_path = self.save_data(processed_data)
        
        logger.info("Data fetch and save operation completed", file_path=file_path)
        return file_path
    
    def get_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the data.
        
        Args:
            data: Processed data
            
        Returns:
            Data summary
        """
        if not data:
            return {"record_count": 0, "fields": []}
        
        summary = {
            "record_count": len(data),
            "fields": list(data[0].keys()) if data else [],
            "sample_record": data[0] if data else None,
        }
        
        # Add field statistics if data is numeric
        if data:
            for field in summary["fields"]:
                values = [item.get(field) for item in data if item.get(field) is not None]
                if values and all(isinstance(v, (int, float)) for v in values):
                    summary[f"{field}_stats"] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                    }
        
        return summary 