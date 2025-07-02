#!/usr/bin/env python3
"""
Theodore v2 Tickets Comprehensive Validation Analysis
=====================================================
Analyzes all 27 tickets for:
1. Architecture consistency (hexagonal patterns)
2. Interface coherence across system  
3. Dependency integrity and graph
4. Implementation feasibility
5. Documentation quality
6. Missing components
"""

import re
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import glob

@dataclass
class TicketInfo:
    """Information extracted from a ticket"""
    number: int
    title: str
    overview: str
    estimated_time: str
    dependencies: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    phase: int = 0
    has_implementation: bool = False
    has_tests: bool = False
    has_udemy_content: bool = False
    architecture_layer: str = ""
    interfaces_defined: List[str] = field(default_factory=list)
    adapters_implemented: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """Results of validation analysis"""
    total_tickets: int = 0
    architecture_issues: List[str] = field(default_factory=list)
    dependency_issues: List[str] = field(default_factory=list)
    interface_issues: List[str] = field(default_factory=list)
    implementation_issues: List[str] = field(default_factory=list)
    documentation_issues: List[str] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)
    readiness_score: float = 0.0
    
    # Detailed analysis
    tickets_by_phase: Dict[int, List[int]] = field(default_factory=dict)
    dependency_graph: Dict[int, List[int]] = field(default_factory=dict)
    interface_coverage: Dict[str, List[int]] = field(default_factory=dict)
    file_coverage: Dict[str, List[int]] = field(default_factory=dict)

class TicketValidator:
    """Validates Theodore v2 tickets for completeness and consistency"""
    
    def __init__(self, tickets_dir: str = "."):
        self.tickets_dir = tickets_dir
        self.tickets: Dict[int, TicketInfo] = {}
        self.validation_result = ValidationResult()
        
    def parse_ticket(self, ticket_file: str) -> TicketInfo:
        """Parse a single ticket file"""
        with open(ticket_file, 'r') as f:
            content = f.read()
        
        # Extract ticket number from filename
        ticket_num = int(re.search(r'TICKET-(\d+)', ticket_file).group(1))
        
        # Parse basic info
        title_match = re.search(r'# TICKET-\d+:\s*(.+)', content)
        title = title_match.group(1) if title_match else "Unknown"
        
        overview_match = re.search(r'## Overview\s*\n(.+?)(?=\n##|\nEstimated|\n---|\Z)', content, re.DOTALL)
        overview = overview_match.group(1).strip() if overview_match else ""
        
        time_match = re.search(r'## Estimated Time:\s*(.+)', content)
        estimated_time = time_match.group(1) if time_match else "Unknown"
        
        # Parse dependencies
        deps_match = re.search(r'## Dependencies\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
        dependencies = []
        if deps_match:
            deps_text = deps_match.group(1)
            ticket_refs = re.findall(r'TICKET-(\d+)', deps_text)
            dependencies = [int(t) for t in ticket_refs]
        
        # Parse files to create
        files_match = re.search(r'## Files to Create\s*\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
        files_to_create = []
        if files_match:
            files_text = files_match.group(1)
            # Extract file paths (lines starting with - and containing .py)
            file_lines = re.findall(r'-\s*`([^`]+\.py)`', files_text)
            files_to_create = file_lines
        
        # Parse acceptance criteria
        criteria_match = re.search(r'## Acceptance Criteria\s*\n(.+?)(?=\n##|\nEstimated|\n---|\Z)', content, re.DOTALL)
        acceptance_criteria = []
        if criteria_match:
            criteria_text = criteria_match.group(1)
            criteria_lines = re.findall(r'-\s*\[\s*\]\s*(.+)', criteria_text)
            acceptance_criteria = criteria_lines
        
        # Check for implementation section
        has_implementation = '## Implementation' in content or '```python' in content
        
        # Check for test files
        has_tests = any('test_' in f for f in files_to_create)
        
        # Check for Udemy content
        has_udemy_content = 'Udemy Tutorial Script' in content
        
        # Determine architecture layer
        architecture_layer = self._determine_architecture_layer(title, files_to_create)
        
        # Extract interfaces defined
        interfaces_defined = self._extract_interfaces(content, files_to_create)
        
        # Extract adapters implemented
        adapters_implemented = self._extract_adapters(content, files_to_create)
        
        # Determine phase
        phase = self._determine_phase(ticket_num)
        
        return TicketInfo(
            number=ticket_num,
            title=title,
            overview=overview,
            estimated_time=estimated_time,
            dependencies=dependencies,
            files_to_create=files_to_create,
            acceptance_criteria=acceptance_criteria,
            phase=phase,
            has_implementation=has_implementation,
            has_tests=has_tests,
            has_udemy_content=has_udemy_content,
            architecture_layer=architecture_layer,
            interfaces_defined=interfaces_defined,
            adapters_implemented=adapters_implemented
        )
    
    def _determine_architecture_layer(self, title: str, files: List[str]) -> str:
        """Determine which architecture layer a ticket belongs to"""
        title_lower = title.lower()
        
        if any('cli' in f for f in files) or 'cli' in title_lower:
            return "Application/CLI"
        elif any('use_case' in f for f in files) or 'use case' in title_lower:
            return "Domain/Use Cases"
        elif any('entities' in f for f in files) or 'domain model' in title_lower:
            return "Domain/Entities"
        elif any('ports' in f for f in files) or 'port' in title_lower:
            return "Domain/Ports"
        elif any('adapters' in f for f in files) or 'adapter' in title_lower:
            return "Infrastructure/Adapters"
        elif 'api' in title_lower or 'server' in title_lower:
            return "Application/API"
        elif 'config' in title_lower or 'injection' in title_lower:
            return "Infrastructure/Config"
        else:
            return "Unknown"
    
    def _extract_interfaces(self, content: str, files: List[str]) -> List[str]:
        """Extract interface/port names from ticket"""
        interfaces = []
        
        # Look for port files
        port_files = [f for f in files if '/ports/' in f]
        for pf in port_files:
            interface_name = os.path.basename(pf).replace('.py', '')
            interfaces.append(interface_name)
        
        # Look for protocol/ABC definitions in content
        protocol_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Protocol[^)]*\)', content)
        abc_matches = re.findall(r'class\s+(\w+)\s*\([^)]*ABC[^)]*\)', content)
        
        interfaces.extend(protocol_matches + abc_matches)
        
        return list(set(interfaces))
    
    def _extract_adapters(self, content: str, files: List[str]) -> List[str]:
        """Extract adapter names from ticket"""
        adapters = []
        
        # Look for adapter files
        adapter_files = [f for f in files if '/adapters/' in f]
        for af in adapter_files:
            adapter_name = os.path.basename(af).replace('.py', '')
            adapters.append(adapter_name)
        
        return adapters
    
    def _determine_phase(self, ticket_num: int) -> int:
        """Determine which development phase a ticket belongs to"""
        if ticket_num <= 9:
            return 1  # Foundation
        elif ticket_num <= 11:
            return 2  # Core Use Cases
        elif ticket_num <= 18:
            return 3  # Infrastructure Adapters
        elif ticket_num <= 22:
            return 4  # Integration
        else:
            return 5  # Advanced Features
    
    def load_all_tickets(self):
        """Load and parse all ticket files"""
        ticket_files = glob.glob(os.path.join(self.tickets_dir, "TICKET-*.md"))
        
        for ticket_file in ticket_files:
            try:
                ticket = self.parse_ticket(ticket_file)
                self.tickets[ticket.number] = ticket
            except Exception as e:
                print(f"Error parsing {ticket_file}: {e}")
        
        self.validation_result.total_tickets = len(self.tickets)
    
    def validate_architecture_consistency(self):
        """Validate hexagonal architecture patterns"""
        issues = []
        
        # Check for proper layering
        domain_tickets = [t for t in self.tickets.values() if 'Domain' in t.architecture_layer]
        infrastructure_tickets = [t for t in self.tickets.values() if 'Infrastructure' in t.architecture_layer]
        application_tickets = [t for t in self.tickets.values() if 'Application' in t.architecture_layer]
        
        if len(domain_tickets) < 5:
            issues.append("Insufficient domain layer tickets (expected at least 5 for entities, use cases, ports)")
        
        if len(infrastructure_tickets) < 8:
            issues.append("Insufficient infrastructure layer tickets (expected at least 8 for adapters)")
        
        if len(application_tickets) < 3:
            issues.append("Insufficient application layer tickets (expected at least 3 for CLI, API, commands)")
        
        # Check for dependency direction (application -> domain -> infrastructure forbidden)
        for ticket in self.tickets.values():
            if ticket.architecture_layer.startswith('Domain'):
                # Domain should not depend on infrastructure
                for dep_num in ticket.dependencies:
                    if dep_num in self.tickets:
                        dep_ticket = self.tickets[dep_num]
                        if dep_ticket.architecture_layer.startswith('Infrastructure'):
                            issues.append(f"TICKET-{ticket.number} (Domain) depends on TICKET-{dep_num} (Infrastructure) - violates dependency inversion")
        
        # Check for port definitions before adapters
        port_tickets = [t.number for t in self.tickets.values() if 'port' in t.title.lower()]
        adapter_tickets = [t for t in self.tickets.values() if 'adapter' in t.title.lower()]
        
        for adapter_ticket in adapter_tickets:
            # Each adapter should depend on a corresponding port
            has_port_dependency = any(dep in port_tickets for dep in adapter_ticket.dependencies)
            if not has_port_dependency:
                issues.append(f"TICKET-{adapter_ticket.number} (Adapter) should depend on a port definition")
        
        self.validation_result.architecture_issues = issues
    
    def validate_interface_coherence(self):
        """Validate interface definitions and implementations"""
        issues = []
        
        # Collect all interfaces defined
        all_interfaces = {}
        for ticket in self.tickets.values():
            for interface in ticket.interfaces_defined:
                if interface in all_interfaces:
                    issues.append(f"Interface '{interface}' defined in multiple tickets: {all_interfaces[interface]} and {ticket.number}")
                all_interfaces[interface] = ticket.number
        
        # Check that key interfaces are defined
        expected_interfaces = [
            'web_scraper', 'ai_provider', 'vector_storage', 'progress_tracker',
            'mcp_search_tool', 'domain_discovery'
        ]
        
        for expected in expected_interfaces:
            if not any(expected in interface.lower() for interface in all_interfaces.keys()):
                issues.append(f"Expected interface '{expected}' not found in any ticket")
        
        # Check adapter-port pairing
        adapters_by_type = defaultdict(list)
        for ticket in self.tickets.values():
            for adapter in ticket.adapters_implemented:
                adapter_type = adapter.split('_')[0]  # e.g., 'crawl4ai' from 'crawl4ai_adapter'
                adapters_by_type[adapter_type].append(ticket.number)
        
        self.validation_result.interface_issues = issues
        self.validation_result.interface_coverage = dict(all_interfaces)
    
    def validate_dependency_integrity(self):
        """Validate dependency graph for cycles and missing dependencies"""
        issues = []
        
        # Build dependency graph
        graph = {}
        for ticket in self.tickets.values():
            graph[ticket.number] = ticket.dependencies
        
        # Check for missing dependencies
        for ticket_num, deps in graph.items():
            for dep in deps:
                if dep not in self.tickets:
                    issues.append(f"TICKET-{ticket_num} depends on non-existent TICKET-{dep}")
        
        # Check for circular dependencies
        def has_cycle(node, visited, rec_stack):
            visited[node] = True
            rec_stack[node] = True
            
            for neighbor in graph.get(node, []):
                if neighbor in self.tickets:  # Only check existing tickets
                    if not visited.get(neighbor, False):
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif rec_stack.get(neighbor, False):
                        return True
            
            rec_stack[node] = False
            return False
        
        visited = {}
        rec_stack = {}
        
        for ticket_num in self.tickets.keys():
            if not visited.get(ticket_num, False):
                if has_cycle(ticket_num, visited, rec_stack):
                    issues.append(f"Circular dependency detected involving TICKET-{ticket_num}")
        
        # Check phase ordering
        for ticket in self.tickets.values():
            for dep in ticket.dependencies:
                if dep in self.tickets:
                    dep_ticket = self.tickets[dep]
                    if ticket.phase < dep_ticket.phase:
                        issues.append(f"TICKET-{ticket.number} (Phase {ticket.phase}) depends on TICKET-{dep} (Phase {dep_ticket.phase}) - violates phase ordering")
        
        self.validation_result.dependency_issues = issues
        self.validation_result.dependency_graph = graph
    
    def validate_implementation_feasibility(self):
        """Validate that tickets have sufficient implementation detail"""
        issues = []
        
        for ticket in self.tickets.values():
            # Check for implementation content
            if not ticket.has_implementation and ticket.phase <= 4:
                issues.append(f"TICKET-{ticket.number} lacks implementation details (critical for phases 1-4)")
            
            # Check for test coverage
            if not ticket.has_tests:
                issues.append(f"TICKET-{ticket.number} lacks test files")
            
            # Check acceptance criteria completeness
            if len(ticket.acceptance_criteria) < 3:
                issues.append(f"TICKET-{ticket.number} has insufficient acceptance criteria (< 3)")
            
            # Check estimated time is reasonable
            if ticket.estimated_time == "Unknown":
                issues.append(f"TICKET-{ticket.number} missing time estimate")
            
            # Check file creation list
            if len(ticket.files_to_create) == 0:
                issues.append(f"TICKET-{ticket.number} doesn't specify files to create")
        
        self.validation_result.implementation_issues = issues
    
    def validate_documentation_quality(self):
        """Validate documentation completeness"""
        issues = []
        
        for ticket in self.tickets.values():
            # Check overview quality
            if len(ticket.overview) < 50:
                issues.append(f"TICKET-{ticket.number} has insufficient overview (< 50 chars)")
            
            # Check for Udemy tutorial content in foundation tickets
            if ticket.phase <= 2 and not ticket.has_udemy_content:
                issues.append(f"TICKET-{ticket.number} (Phase {ticket.phase}) missing Udemy tutorial content")
            
            # Check title descriptiveness
            generic_titles = ['implement', 'create', 'add', 'setup']
            if any(generic in ticket.title.lower() for generic in generic_titles):
                if len(ticket.title) < 20:
                    issues.append(f"TICKET-{ticket.number} has generic/short title")
        
        self.validation_result.documentation_issues = issues
    
    def check_missing_components(self):
        """Check for missing critical components"""
        missing = []
        
        # Check for essential files across all tickets
        all_files = []
        for ticket in self.tickets.values():
            all_files.extend(ticket.files_to_create)
        
        # Critical paths that should exist
        critical_paths = [
            'core/domain/entities',
            'core/use_cases',
            'core/ports',
            'infrastructure/adapters',
            'cli/commands',
            'tests/unit',
            'tests/integration'
        ]
        
        for path in critical_paths:
            if not any(path in f for f in all_files):
                missing.append(f"No files created in critical path: {path}")
        
        # Essential components
        essential_components = [
            ('Company entity', 'company.py'),
            ('Research use case', 'research_company.py'),
            ('Web scraper port', 'web_scraper.py'),
            ('DI container', 'container.py'),
            ('CLI main', 'cli/main.py')
        ]
        
        for component_name, file_pattern in essential_components:
            if not any(file_pattern in f for f in all_files):
                missing.append(f"Missing essential component: {component_name}")
        
        self.validation_result.missing_components = missing
    
    def calculate_readiness_score(self):
        """Calculate overall readiness score"""
        total_issues = (
            len(self.validation_result.architecture_issues) +
            len(self.validation_result.dependency_issues) +
            len(self.validation_result.interface_issues) +
            len(self.validation_result.implementation_issues) +
            len(self.validation_result.documentation_issues) +
            len(self.validation_result.missing_components)
        )
        
        # Score calculation (lower is better)
        # Start with 100, subtract points for issues
        score = 100.0
        score -= len(self.validation_result.architecture_issues) * 5  # Architecture issues are critical
        score -= len(self.validation_result.dependency_issues) * 4    # Dependency issues block implementation
        score -= len(self.validation_result.interface_issues) * 3     # Interface issues cause integration problems
        score -= len(self.validation_result.implementation_issues) * 2  # Implementation issues slow development
        score -= len(self.validation_result.documentation_issues) * 1   # Documentation issues affect maintainability
        score -= len(self.validation_result.missing_components) * 3     # Missing components block progress
        
        self.validation_result.readiness_score = max(0.0, score)
    
    def generate_phase_analysis(self):
        """Generate phase-based analysis"""
        phases = defaultdict(list)
        for ticket in self.tickets.values():
            phases[ticket.phase].append(ticket.number)
        
        self.validation_result.tickets_by_phase = dict(phases)
    
    def run_full_validation(self):
        """Run complete validation analysis"""
        print("Loading all tickets...")
        self.load_all_tickets()
        
        print("Validating architecture consistency...")
        self.validate_architecture_consistency()
        
        print("Validating interface coherence...")
        self.validate_interface_coherence()
        
        print("Validating dependency integrity...")
        self.validate_dependency_integrity()
        
        print("Validating implementation feasibility...")
        self.validate_implementation_feasibility()
        
        print("Validating documentation quality...")
        self.validate_documentation_quality()
        
        print("Checking for missing components...")
        self.check_missing_components()
        
        print("Calculating readiness score...")
        self.calculate_readiness_score()
        
        print("Generating phase analysis...")
        self.generate_phase_analysis()
        
        return self.validation_result
    
    def print_validation_report(self):
        """Print comprehensive validation report"""
        result = self.validation_result
        
        print("=" * 80)
        print("THEODORE V2 TICKETS COMPREHENSIVE VALIDATION REPORT")
        print("=" * 80)
        
        print(f"\n📊 SUMMARY")
        print(f"Total Tickets: {result.total_tickets}")
        print(f"Readiness Score: {result.readiness_score:.1f}/100")
        
        # Readiness assessment
        if result.readiness_score >= 90:
            readiness = "🟢 EXCELLENT - Ready for implementation"
        elif result.readiness_score >= 75:
            readiness = "🟡 GOOD - Minor issues to address"
        elif result.readiness_score >= 60:
            readiness = "🟠 NEEDS WORK - Significant issues"
        else:
            readiness = "🔴 CRITICAL - Major architectural problems"
        
        print(f"Overall Assessment: {readiness}")
        
        # Phase breakdown
        print(f"\n📋 PHASE BREAKDOWN")
        for phase, tickets in sorted(result.tickets_by_phase.items()):
            phase_names = {
                1: "Foundation", 2: "Core Use Cases", 3: "Infrastructure Adapters",
                4: "Integration", 5: "Advanced Features"
            }
            print(f"Phase {phase} ({phase_names.get(phase, 'Unknown')}): {len(tickets)} tickets")
            print(f"  Tickets: {', '.join(f'TICKET-{t}' for t in sorted(tickets))}")
        
        # Issue categories
        issue_categories = [
            ("🏗️  ARCHITECTURE ISSUES", result.architecture_issues),
            ("🔗 DEPENDENCY ISSUES", result.dependency_issues),
            ("🔌 INTERFACE ISSUES", result.interface_issues),
            ("⚙️  IMPLEMENTATION ISSUES", result.implementation_issues),
            ("📚 DOCUMENTATION ISSUES", result.documentation_issues),
            ("❌ MISSING COMPONENTS", result.missing_components)
        ]
        
        for category_name, issues in issue_categories:
            print(f"\n{category_name} ({len(issues)} issues)")
            if issues:
                for i, issue in enumerate(issues[:10], 1):  # Show first 10
                    print(f"  {i}. {issue}")
                if len(issues) > 10:
                    print(f"  ... and {len(issues) - 10} more issues")
            else:
                print("  ✅ No issues found")
        
        # Interface coverage
        print(f"\n🔌 INTERFACE COVERAGE")
        if result.interface_coverage:
            for interface, ticket_num in result.interface_coverage.items():
                print(f"  {interface}: TICKET-{ticket_num}")
        else:
            print("  No interfaces detected")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        critical_issues = len(result.architecture_issues) + len(result.dependency_issues)
        if critical_issues > 0:
            print(f"  1. 🚨 CRITICAL: Address {critical_issues} architecture/dependency issues first")
        
        if len(result.missing_components) > 0:
            print(f"  2. 📦 Add {len(result.missing_components)} missing essential components")
        
        if len(result.interface_issues) > 0:
            print(f"  3. 🔌 Fix {len(result.interface_issues)} interface definition problems")
        
        if len(result.implementation_issues) > 5:
            print(f"  4. ⚙️  Enhance implementation details in {len(result.implementation_issues)} tickets")
        
        if result.readiness_score < 80:
            print(f"  5. 📈 Focus on high-impact fixes to improve readiness score")
        
        print(f"\n🎯 NEXT STEPS")
        if result.readiness_score >= 90:
            print("  - Tickets are ready for implementation")
            print("  - Begin with Phase 1 (Foundation) tickets")
            print("  - Follow dependency order strictly")
        elif result.readiness_score >= 75:
            print("  - Address critical architecture issues first")
            print("  - Review and fix dependency violations")
            print("  - Then proceed with implementation")
        else:
            print("  - Significant rework needed before implementation")
            print("  - Focus on architectural consistency")
            print("  - Redesign problematic dependencies")
            print("  - Add missing essential components")
        
        print("=" * 80)

if __name__ == "__main__":
    validator = TicketValidator()
    result = validator.run_full_validation()
    validator.print_validation_report()