"""
Employee Exclusion Validator
Handles validation of employee records against exclusion list with intelligent name matching
"""

import json
import logging
import re
from typing import Dict, List, Any, Tuple, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ExclusionMatch:
    """Represents a match between a record and an excluded employee"""
    record_id: str
    employee_name: str
    excluded_name: str
    match_score: float
    match_type: str  # 'exact', 'partial', 'fuzzy'
    record_index: int
    
    # Add compatibility properties for run_user_controlled_automation.py
    @property
    def matched_exclusion(self) -> str:
        """Alias for excluded_name for compatibility"""
        return self.excluded_name
    
    @property
    def original_record(self) -> Dict[str, Any]:
        """Placeholder for original record reference"""
        return {"employee_name": self.employee_name, "record_index": self.record_index}

@dataclass 
class ValidationResult:
    """Result of exclusion validation"""
    has_exclusions: bool
    excluded_matches: List[ExclusionMatch]
    clean_records: List[Dict[str, Any]]
    clean_indices: List[int]
    excluded_records: List[Dict[str, Any]]
    excluded_indices: List[int]
    total_records: int
    summary: str
    
    # Add compatibility properties for run_user_controlled_automation.py
    @property
    def excluded_count(self) -> int:
        return len(self.excluded_matches)
    
    @property
    def clean_count(self) -> int:
        return len(self.clean_records)
    
    @property
    def exclusion_matches(self) -> List['ExclusionMatch']:
        """Alias for excluded_matches for compatibility"""
        return self.excluded_matches

class EmployeeExclusionValidator:
    """
    Validates employee records against exclusion list with intelligent matching
    """
    
    def __init__(self, config_path: str = "config/employee_exclusion_list.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.exclusion_config = self._load_exclusion_config()
        self.excluded_employees = self._prepare_exclusion_list()
        
    def _load_exclusion_config(self) -> Dict[str, Any]:
        """Load exclusion configuration from JSON file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Exclusion config not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"✅ Loaded exclusion config: {len(config.get('excluded_employees', []))} employees")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load exclusion config: {e}")
            # Return default config if loading fails
            return {
                "exclusion_settings": {
                    "enabled": True,
                    "case_sensitive": False,
                    "partial_match": True,
                    "trim_whitespace": True,
                    "allow_user_override": True,
                    "require_confirmation": True
                },
                "excluded_employees": [],
                "validation": {
                    "minimum_match_threshold": 0.85,
                    "fuzzy_matching": False,
                    "log_exclusions": True
                }
            }
    
    def _prepare_exclusion_list(self) -> Set[str]:
        """Prepare normalized exclusion list for matching"""
        excluded = set()
        raw_excluded = self.exclusion_config.get('excluded_employees', [])
        settings = self.exclusion_config.get('exclusion_settings', {})
        
        for name in raw_excluded:
            if settings.get('trim_whitespace', True):
                name = name.strip()
            
            if not settings.get('case_sensitive', False):
                name = name.lower()
            
            # Apply normalization rules
            name = self._normalize_name(name)
            excluded.add(name)
        
        self.logger.info(f"📋 Prepared {len(excluded)} normalized exclusion names")
        return excluded
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name according to configuration rules"""
        if not name:
            return ""
        
        # Remove extra spaces
        if self.exclusion_config.get('normalization_rules', {}).get('remove_extra_spaces', True):
            name = re.sub(r'\s+', ' ', name).strip()
        
        # Apply abbreviation rules
        abbreviations = self.exclusion_config.get('normalization_rules', {}).get('handle_abbreviations', [])
        for abbrev in abbreviations:
            pattern = abbrev.get('pattern', '')
            replacement = abbrev.get('replacement', '')
            if pattern and replacement:
                name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        
        return name
    
    def validate_employee_records(self, records: List[Dict[str, Any]]) -> 'ValidationResult':
        """
        Validate employee records against exclusion list
        
        Args:
            records: List of employee records to validate
            
        Returns:
            ValidationResult with exclusion analysis
        """
        # Convert to format expected by validate_records
        selected_indices = list(range(len(records)))
        return self.validate_records(records, selected_indices)
    
    def validate_records(self, records: List[Dict[str, Any]], selected_indices: List[int]) -> ValidationResult:
        """
        Validate selected records against exclusion list
        
        Args:
            records: List of all available records
            selected_indices: List of indices of selected records
            
        Returns:
            ValidationResult with exclusion analysis
        """
        if not self.exclusion_config.get('exclusion_settings', {}).get('enabled', True):
            self.logger.info("🔓 Exclusion validation is disabled")
            return ValidationResult(
                has_exclusions=False,
                excluded_matches=[],
                clean_records=[records[i] for i in selected_indices],
                clean_indices=selected_indices,
                excluded_records=[],
                excluded_indices=[],
                total_records=len(selected_indices),
                summary="Exclusion validation disabled - all records allowed"
            )
        
        excluded_matches = []
        clean_indices = []
        excluded_indices = []
        
        self.logger.info(f"🔍 Validating {len(selected_indices)} selected records against exclusion list")
        
        for i, record_index in enumerate(selected_indices):
            if record_index >= len(records):
                self.logger.warning(f"⚠️ Invalid record index: {record_index}")
                continue
                
            record = records[record_index]
            employee_name = record.get('employee_name', '')
            
            if not employee_name:
                self.logger.warning(f"⚠️ Record {record_index} has no employee_name")
                clean_indices.append(record_index)
                continue
            
            # Check for exclusion match
            match = self._find_exclusion_match(employee_name, record, record_index)
            
            if match:
                excluded_matches.append(match)
                excluded_indices.append(record_index)
                self.logger.warning(f"🚫 EXCLUDED: {employee_name} (matched: {match.excluded_name})")
            else:
                clean_indices.append(record_index)
                self.logger.debug(f"✅ ALLOWED: {employee_name}")
        
        # Generate summary
        summary = self._generate_summary(excluded_matches, len(selected_indices))
        
        result = ValidationResult(
            has_exclusions=len(excluded_matches) > 0,
            excluded_matches=excluded_matches,
            clean_records=[records[i] for i in clean_indices],
            clean_indices=clean_indices,
            excluded_records=[records[i] for i in excluded_indices],
            excluded_indices=excluded_indices,
            total_records=len(selected_indices),
            summary=summary
        )
        
        if result.has_exclusions and self.exclusion_config.get('validation', {}).get('log_exclusions', True):
            self.logger.info(f"🚫 Exclusion Summary: {summary}")
        
        return result
    
    def _find_exclusion_match(self, employee_name: str, record: Dict[str, Any], record_index: int) -> Optional[ExclusionMatch]:
        """Find if employee name matches any excluded name"""
        if not employee_name:
            return None
        
        settings = self.exclusion_config.get('exclusion_settings', {})
        
        # Normalize input name
        normalized_name = employee_name.strip()
        if not settings.get('case_sensitive', False):
            normalized_name = normalized_name.lower()
        normalized_name = self._normalize_name(normalized_name)
        
        # Check for exact match
        if normalized_name in self.excluded_employees:
            return ExclusionMatch(
                record_id=record.get('id', str(record_index)),
                employee_name=employee_name,
                excluded_name=normalized_name,
                match_score=1.0,
                match_type='exact',
                record_index=record_index
            )
        
        # Check for partial match if enabled
        if settings.get('partial_match', True):
            for excluded_name in self.excluded_employees:
                if normalized_name in excluded_name or excluded_name in normalized_name:
                    return ExclusionMatch(
                        record_id=record.get('id', str(record_index)),
                        employee_name=employee_name,
                        excluded_name=excluded_name,
                        match_score=0.9,
                        match_type='partial',
                        record_index=record_index
                    )
        
        # Check for fuzzy match if enabled
        validation_config = self.exclusion_config.get('validation', {})
        if validation_config.get('fuzzy_matching', False):
            threshold = validation_config.get('minimum_match_threshold', 0.85)
            
            for excluded_name in self.excluded_employees:
                similarity = SequenceMatcher(None, normalized_name, excluded_name).ratio()
                if similarity >= threshold:
                    return ExclusionMatch(
                        record_id=record.get('id', str(record_index)),
                        employee_name=employee_name,
                        excluded_name=excluded_name,
                        match_score=similarity,
                        match_type='fuzzy',
                        record_index=record_index
                    )
        
        return None
    
    def _generate_summary(self, excluded_matches: List[ExclusionMatch], total_selected: int) -> str:
        """Generate human-readable summary of exclusion results"""
        if not excluded_matches:
            return f"All {total_selected} selected records are allowed for processing"
        
        excluded_count = len(excluded_matches)
        clean_count = total_selected - excluded_count
        
        summary_parts = [
            f"Found {excluded_count} excluded employee(s) in selection:",
        ]
        
        # Group by excluded name
        excluded_names = set(match.excluded_name for match in excluded_matches)
        for name in sorted(excluded_names):
            matching_records = [m for m in excluded_matches if m.excluded_name == name]
            if len(matching_records) == 1:
                summary_parts.append(f"  • {name}")
            else:
                summary_parts.append(f"  • {name} ({len(matching_records)} records)")
        
        summary_parts.append(f"Remaining {clean_count} records are allowed for processing")
        
        return "\n".join(summary_parts)
    
    def get_confirmation_dialog_data(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Generate data for confirmation dialog"""
        if not validation_result.has_exclusions:
            return {
                "show_dialog": False,
                "title": "No Exclusions Found",
                "message": "All selected records are allowed for processing.",
                "excluded_employees": [],
                "clean_count": len(validation_result.clean_records),
                "excluded_count": 0,
                "total_count": validation_result.total_records
            }
        
        # Group excluded employees
        excluded_employees = {}
        for match in validation_result.excluded_matches:
            name = match.excluded_name
            if name not in excluded_employees:
                excluded_employees[name] = {
                    "name": name,
                    "records": [],
                    "match_type": match.match_type,
                    "match_score": match.match_score
                }
            excluded_employees[name]["records"].append({
                "employee_name": match.employee_name,
                "record_id": match.record_id,
                "record_index": match.record_index
            })
        
        return {
            "show_dialog": True,
            "title": "Excluded Employees Detected",
            "message": f"Found {len(validation_result.excluded_matches)} excluded employee(s) in your selection.",
            "excluded_employees": list(excluded_employees.values()),
            "clean_count": len(validation_result.clean_records),
            "excluded_count": len(validation_result.excluded_matches),
            "total_count": validation_result.total_records,
            "summary": validation_result.summary
        }
    
    def is_enabled(self) -> bool:
        """Check if exclusion validation is enabled"""
        return self.exclusion_config.get('exclusion_settings', {}).get('enabled', True)
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get current exclusion configuration"""
        return self.exclusion_config
    
    def get_excluded_employees_list(self) -> List[str]:
        """Get list of excluded employee names"""
        return self.exclusion_config.get('excluded_employees', [])
    
    def reload_config(self) -> bool:
        """Reload exclusion configuration from file"""
        try:
            self.exclusion_config = self._load_exclusion_config()
            self.excluded_employees = self._prepare_exclusion_list()
            self.logger.info("🔄 Exclusion configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to reload exclusion configuration: {e}")
            return False 