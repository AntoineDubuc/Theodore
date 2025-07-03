#!/usr/bin/env python3
"""
Theodore v2 Test Data Management System

Comprehensive test data management system for creating, managing, and cleaning up
test data across different testing scenarios and environments.
"""

import asyncio
import json
import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import tempfile
import shutil
import csv

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


class TestDataType(Enum):
    """Types of test data"""
    COMPANY_DATA = "company_data"
    USER_DATA = "user_data"
    RESEARCH_DATA = "research_data"
    EXPORT_DATA = "export_data"
    CONFIGURATION_DATA = "configuration_data"
    MOCK_API_RESPONSES = "mock_api_responses"
    SAMPLE_FILES = "sample_files"
    PERFORMANCE_DATA = "performance_data"


class DataScope(Enum):
    """Scope of test data lifecycle"""
    SESSION = "session"  # Lives for entire test session
    TEST_SUITE = "test_suite"  # Lives for test suite execution
    INDIVIDUAL_TEST = "individual_test"  # Lives for single test
    PERSISTENT = "persistent"  # Lives across multiple sessions


@dataclass
class TestDataDefinition:
    """Test data definition and metadata"""
    name: str
    data_type: TestDataType
    scope: DataScope
    description: str
    schema: Dict[str, Any]
    generation_strategy: str
    cleanup_strategy: str
    dependencies: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestDataInstance:
    """Test data instance"""
    definition_name: str
    instance_id: str
    data: Any
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestEnvironment:
    """Test environment configuration"""
    name: str
    description: str
    configuration: Dict[str, Any]
    data_requirements: List[str]
    cleanup_policies: Dict[str, Any]
    isolation_level: str  # "isolated", "shared", "production_safe"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TestDataManager:
    """Comprehensive test data management system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_definitions: Dict[str, TestDataDefinition] = {}
        self.data_instances: Dict[str, TestDataInstance] = {}
        self.environments: Dict[str, TestEnvironment] = {}
        self.temp_directories: List[Path] = []
        self.cleanup_handlers: List[Callable] = []
        
        # Initialize default data definitions
        self._initialize_default_data_definitions()
        
        # Initialize default environments
        self._initialize_default_environments()
    
    async def initialize_test_session(self, session_id: str) -> Dict[str, Any]:
        """Initialize test session with required data"""
        
        logger.info(f"Initializing test session: {session_id}")
        
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc),
            "data_instances": {},
            "temp_resources": []
        }
        
        # Create session-scoped data
        for definition_name, definition in self.data_definitions.items():
            if definition.scope == DataScope.SESSION:
                instance = await self.create_test_data(definition_name, session_id)
                session_data["data_instances"][definition_name] = instance.instance_id
        
        logger.info(f"Test session initialized with {len(session_data['data_instances'])} data instances")
        
        return session_data
    
    async def create_test_data(self, definition_name: str, context_id: str = None) -> TestDataInstance:
        """Create test data instance based on definition"""
        
        if definition_name not in self.data_definitions:
            raise ValueError(f"Test data definition '{definition_name}' not found")
        
        definition = self.data_definitions[definition_name]
        instance_id = f"{definition_name}_{uuid.uuid4().hex[:8]}"
        
        logger.debug(f"Creating test data instance: {instance_id}")
        
        # Generate data based on strategy
        data = await self._generate_data(definition)
        
        # Calculate expiration
        expires_at = self._calculate_expiration(definition)
        
        # Create instance
        instance = TestDataInstance(
            definition_name=definition_name,
            instance_id=instance_id,
            data=data,
            metadata={
                "context_id": context_id,
                "generation_strategy": definition.generation_strategy,
                "schema_version": "1.0"
            },
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        
        # Store instance
        self.data_instances[instance_id] = instance
        
        logger.debug(f"Test data instance created: {instance_id}")
        
        return instance
    
    async def get_test_data(self, instance_id: str) -> Optional[TestDataInstance]:
        """Get test data instance by ID"""
        
        instance = self.data_instances.get(instance_id)
        
        if instance and self._is_expired(instance):
            await self.cleanup_test_data(instance_id)
            return None
        
        return instance
    
    async def create_sample_companies(self, count: int = 10) -> List[Dict[str, Any]]:
        """Create sample company data for testing"""
        
        companies = []
        
        sample_companies = [
            {"name": "TechCorp Solutions", "industry": "Software", "employees": 250, "stage": "growth"},
            {"name": "GreenEnergy Innovations", "industry": "Renewable Energy", "employees": 120, "stage": "startup"},
            {"name": "DataFlow Analytics", "industry": "Data Analytics", "employees": 75, "stage": "early"},
            {"name": "CloudSecure Systems", "industry": "Cybersecurity", "employees": 180, "stage": "growth"},
            {"name": "BioTech Research Labs", "industry": "Biotechnology", "employees": 95, "stage": "startup"},
            {"name": "FinanceAI Partners", "industry": "Financial Technology", "employees": 145, "stage": "growth"},
            {"name": "RoboticVision Corp", "industry": "Robotics", "employees": 85, "stage": "early"},
            {"name": "SmartCity Solutions", "industry": "Urban Technology", "employees": 160, "stage": "growth"},
            {"name": "HealthTech Innovations", "industry": "Healthcare Technology", "employees": 110, "stage": "startup"},
            {"name": "EdTech Learning Systems", "industry": "Educational Technology", "employees": 90, "stage": "early"}
        ]
        
        for i in range(min(count, len(sample_companies))):
            company = sample_companies[i].copy()
            company["id"] = f"test_company_{i+1}"
            company["website"] = f"https://{company['name'].lower().replace(' ', '')}.com"
            company["founded_year"] = random.randint(2015, 2023)
            company["funding_raised"] = random.randint(1, 50) * 1000000  # $1M to $50M
            company["description"] = f"{company['name']} is a leading {company['industry'].lower()} company."
            companies.append(company)
        
        logger.info(f"Created {len(companies)} sample companies for testing")
        
        return companies
    
    async def create_mock_api_responses(self) -> Dict[str, Any]:
        """Create mock API responses for testing"""
        
        mock_responses = {
            "research_success": {
                "status": "success",
                "data": {
                    "company": {
                        "name": "Test Company Inc",
                        "industry": "Technology",
                        "employees": 150,
                        "founded": 2018,
                        "description": "A leading technology company"
                    },
                    "analysis": {
                        "business_model": "B2B SaaS",
                        "market_segment": "Enterprise Software",
                        "competitive_advantages": ["Strong technical team", "Innovative product"]
                    }
                }
            },
            
            "research_not_found": {
                "status": "not_found",
                "message": "Company not found in our database",
                "suggestions": []
            },
            
            "research_error": {
                "status": "error",
                "message": "An error occurred during research",
                "error_code": "RESEARCH_FAILED"
            },
            
            "discovery_results": {
                "status": "success",
                "data": {
                    "similar_companies": [
                        {"name": "Similar Corp 1", "similarity_score": 0.85},
                        {"name": "Similar Corp 2", "similarity_score": 0.78},
                        {"name": "Similar Corp 3", "similarity_score": 0.72}
                    ],
                    "total_matches": 3
                }
            },
            
            "export_status": {
                "status": "success",
                "export_id": "exp_123456",
                "format": "csv",
                "records_count": 25,
                "file_size_bytes": 15240
            }
        }
        
        return mock_responses
    
    async def create_test_files(self, file_types: List[str] = None) -> Dict[str, Path]:
        """Create temporary test files"""
        
        if file_types is None:
            file_types = ["csv", "json", "xlsx", "pdf"]
        
        test_files = {}
        temp_dir = Path(tempfile.mkdtemp(prefix="theodore_test_"))
        self.temp_directories.append(temp_dir)
        
        for file_type in file_types:
            if file_type == "csv":
                test_files["csv"] = await self._create_test_csv(temp_dir)
            elif file_type == "json":
                test_files["json"] = await self._create_test_json(temp_dir)
            elif file_type == "xlsx":
                test_files["xlsx"] = await self._create_test_xlsx(temp_dir)
            elif file_type == "pdf":
                test_files["pdf"] = await self._create_test_pdf(temp_dir)
        
        logger.info(f"Created {len(test_files)} test files in {temp_dir}")
        
        return test_files
    
    async def create_performance_test_data(self, scenario: str) -> Dict[str, Any]:
        """Create performance test data for specific scenarios"""
        
        performance_data = {}
        
        if scenario == "load_testing":
            performance_data = {
                "concurrent_users": [5, 10, 25, 50, 100],
                "test_duration_seconds": 60,
                "operations_per_user": 10,
                "expected_response_times": {
                    "research": 3.0,
                    "discovery": 2.0,
                    "export": 5.0
                }
            }
        elif scenario == "stress_testing":
            performance_data = {
                "max_users": 500,
                "ramp_up_duration": 300,
                "failure_thresholds": {
                    "error_rate": 0.05,
                    "response_time_p95": 10.0
                }
            }
        elif scenario == "benchmark_testing":
            performance_data = {
                "baseline_metrics": {
                    "single_research_duration": 2.5,
                    "discovery_duration": 1.8,
                    "export_duration": 4.2
                },
                "regression_thresholds": {
                    "performance_degradation": 0.15,
                    "memory_increase": 0.20
                }
            }
        
        return performance_data
    
    async def cleanup_test_data(self, instance_id: str = None) -> int:
        """Cleanup test data instances"""
        
        if instance_id:
            # Cleanup specific instance
            if instance_id in self.data_instances:
                instance = self.data_instances[instance_id]
                await self._cleanup_instance(instance)
                del self.data_instances[instance_id]
                logger.debug(f"Cleaned up test data instance: {instance_id}")
                return 1
            return 0
        else:
            # Cleanup expired instances
            expired_instances = []
            for instance_id, instance in self.data_instances.items():
                if self._is_expired(instance):
                    expired_instances.append(instance_id)
            
            cleanup_count = 0
            for instance_id in expired_instances:
                instance = self.data_instances[instance_id]
                await self._cleanup_instance(instance)
                del self.data_instances[instance_id]
                cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} expired test data instances")
            return cleanup_count
    
    async def cleanup_session(self, session_id: str):
        """Cleanup all data for a test session"""
        
        session_instances = [
            instance_id for instance_id, instance in self.data_instances.items()
            if instance.metadata.get("context_id") == session_id
        ]
        
        cleanup_count = 0
        for instance_id in session_instances:
            await self.cleanup_test_data(instance_id)
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} instances for session: {session_id}")
    
    async def cleanup_all(self):
        """Cleanup all test data and temporary resources"""
        
        # Cleanup all data instances
        instance_count = len(self.data_instances)
        for instance_id in list(self.data_instances.keys()):
            await self.cleanup_test_data(instance_id)
        
        # Cleanup temporary directories
        temp_dir_count = len(self.temp_directories)
        for temp_dir in self.temp_directories:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        self.temp_directories.clear()
        
        # Execute cleanup handlers
        for handler in self.cleanup_handlers:
            try:
                await handler()
            except Exception as e:
                logger.warning(f"Cleanup handler failed: {e}")
        
        logger.info(f"Cleaned up {instance_count} data instances and {temp_dir_count} temp directories")
    
    def register_cleanup_handler(self, handler: Callable):
        """Register cleanup handler for custom resources"""
        self.cleanup_handlers.append(handler)
    
    def _initialize_default_data_definitions(self):
        """Initialize default test data definitions"""
        
        self.data_definitions = {
            "sample_companies": TestDataDefinition(
                name="sample_companies",
                data_type=TestDataType.COMPANY_DATA,
                scope=DataScope.SESSION,
                description="Sample company data for testing",
                schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "industry": {"type": "string"},
                            "employees": {"type": "integer"},
                            "stage": {"type": "string"}
                        }
                    }
                },
                generation_strategy="predefined_samples",
                cleanup_strategy="automatic",
                dependencies=[]
            ),
            
            "mock_api_responses": TestDataDefinition(
                name="mock_api_responses",
                data_type=TestDataType.MOCK_API_RESPONSES,
                scope=DataScope.TEST_SUITE,
                description="Mock API responses for testing",
                schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {"type": "object"}
                    }
                },
                generation_strategy="template_based",
                cleanup_strategy="automatic",
                dependencies=[]
            ),
            
            "test_files": TestDataDefinition(
                name="test_files",
                data_type=TestDataType.SAMPLE_FILES,
                scope=DataScope.INDIVIDUAL_TEST,
                description="Temporary test files",
                schema={"type": "object"},
                generation_strategy="file_creation",
                cleanup_strategy="file_deletion",
                dependencies=[]
            ),
            
            "performance_data": TestDataDefinition(
                name="performance_data",
                data_type=TestDataType.PERFORMANCE_DATA,
                scope=DataScope.TEST_SUITE,
                description="Performance test configuration data",
                schema={"type": "object"},
                generation_strategy="scenario_based",
                cleanup_strategy="automatic",
                dependencies=[]
            )
        }
    
    def _initialize_default_environments(self):
        """Initialize default test environments"""
        
        self.environments = {
            "unit_testing": TestEnvironment(
                name="unit_testing",
                description="Isolated unit testing environment",
                configuration={
                    "use_mocks": True,
                    "external_services": "disabled",
                    "database": "in_memory"
                },
                data_requirements=["mock_api_responses"],
                cleanup_policies={"auto_cleanup": True, "cleanup_interval": 300},
                isolation_level="isolated"
            ),
            
            "integration_testing": TestEnvironment(
                name="integration_testing",
                description="Integration testing with real services",
                configuration={
                    "use_mocks": False,
                    "external_services": "enabled",
                    "database": "test_database"
                },
                data_requirements=["sample_companies", "test_files"],
                cleanup_policies={"auto_cleanup": True, "cleanup_interval": 600},
                isolation_level="shared"
            ),
            
            "performance_testing": TestEnvironment(
                name="performance_testing",
                description="Performance and load testing environment",
                configuration={
                    "use_mocks": "selective",
                    "external_services": "throttled",
                    "database": "performance_database"
                },
                data_requirements=["performance_data", "sample_companies"],
                cleanup_policies={"auto_cleanup": False, "manual_cleanup": True},
                isolation_level="shared"
            )
        }
    
    async def _generate_data(self, definition: TestDataDefinition) -> Any:
        """Generate data based on definition strategy"""
        
        if definition.generation_strategy == "predefined_samples":
            if definition.data_type == TestDataType.COMPANY_DATA:
                return await self.create_sample_companies()
        elif definition.generation_strategy == "template_based":
            if definition.data_type == TestDataType.MOCK_API_RESPONSES:
                return await self.create_mock_api_responses()
        elif definition.generation_strategy == "file_creation":
            if definition.data_type == TestDataType.SAMPLE_FILES:
                return await self.create_test_files()
        elif definition.generation_strategy == "scenario_based":
            if definition.data_type == TestDataType.PERFORMANCE_DATA:
                return await self.create_performance_test_data("load_testing")
        
        # Default: return empty data
        return {}
    
    def _calculate_expiration(self, definition: TestDataDefinition) -> Optional[datetime]:
        """Calculate expiration time based on scope"""
        
        now = datetime.now(timezone.utc)
        
        if definition.scope == DataScope.INDIVIDUAL_TEST:
            return now + timedelta(minutes=10)
        elif definition.scope == DataScope.TEST_SUITE:
            return now + timedelta(hours=1)
        elif definition.scope == DataScope.SESSION:
            return now + timedelta(hours=8)
        else:  # PERSISTENT
            return None
    
    def _is_expired(self, instance: TestDataInstance) -> bool:
        """Check if test data instance is expired"""
        
        if instance.expires_at is None:
            return False
        
        return datetime.now(timezone.utc) > instance.expires_at
    
    async def _cleanup_instance(self, instance: TestDataInstance):
        """Cleanup individual test data instance"""
        
        definition = self.data_definitions.get(instance.definition_name)
        if not definition:
            return
        
        if definition.cleanup_strategy == "file_deletion":
            # Cleanup files if instance contains file paths
            if isinstance(instance.data, dict):
                for file_path in instance.data.values():
                    if isinstance(file_path, Path) and file_path.exists():
                        file_path.unlink()
        
        # Additional cleanup based on data type
        if definition.data_type == TestDataType.SAMPLE_FILES:
            # Handled above
            pass
        elif definition.data_type == TestDataType.COMPANY_DATA:
            # Could cleanup from test database
            pass
    
    async def _create_test_csv(self, temp_dir: Path) -> Path:
        """Create test CSV file"""
        
        csv_file = temp_dir / "test_companies.csv"
        
        companies = await self.create_sample_companies(5)
        
        with csv_file.open('w', newline='') as f:
            if companies:
                writer = csv.DictWriter(f, fieldnames=companies[0].keys())
                writer.writeheader()
                writer.writerows(companies)
        
        return csv_file
    
    async def _create_test_json(self, temp_dir: Path) -> Path:
        """Create test JSON file"""
        
        json_file = temp_dir / "test_data.json"
        
        test_data = {
            "companies": await self.create_sample_companies(3),
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "test_purpose": "integration_testing"
            }
        }
        
        with json_file.open('w') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        return json_file
    
    async def _create_test_xlsx(self, temp_dir: Path) -> Path:
        """Create test Excel file"""
        
        xlsx_file = temp_dir / "test_export.xlsx"
        
        # Create a simple Excel file simulation (would use openpyxl in real implementation)
        # For now, create a CSV with .xlsx extension
        companies = await self.create_sample_companies(3)
        
        with xlsx_file.open('w') as f:
            f.write("name,industry,employees,stage\n")
            for company in companies:
                f.write(f"{company['name']},{company['industry']},{company['employees']},{company['stage']}\n")
        
        return xlsx_file
    
    async def _create_test_pdf(self, temp_dir: Path) -> Path:
        """Create test PDF file"""
        
        pdf_file = temp_dir / "test_report.pdf"
        
        # Create a simple PDF simulation (would use reportlab in real implementation)
        with pdf_file.open('w') as f:
            f.write("%PDF-1.4\n")
            f.write("1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n")
            f.write("Test PDF content for Theodore v2 testing\n")
            f.write("%%EOF\n")
        
        return pdf_file