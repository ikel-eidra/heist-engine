#!/usr/bin/env python3
"""
Issue Classifier
================

Classifies detected issues by severity and determines if human approval is needed.
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Issue severity levels"""
    MINOR = "minor"
    MEDIUM = "medium"
    CRITICAL = "critical"


class ApprovalLevel(Enum):
    """Approval requirements"""
    AUTO_FIX = "auto_fix"  # Can fix automatically
    REQUEST_APPROVAL = "request_approval"  # Ask human first
    MANUAL_ONLY = "manual_only"  # Human must fix manually


@dataclass
class ClassifiedIssue:
    """A classified issue with recommended action"""
    issue_type: str
    severity: Severity
    approval_required: ApprovalLevel
    confidence: float  # 0.0 to 1.0
    description: str
    proposed_fix: str
    raw_issue: Dict


class IssueClassifier:
    """Classifies issues and determines appropriate responses"""
    
    def __init__(self):
        # Define classification rules
        self.auto_fix_patterns = {
            "invalid_config": {
                "keywords": ["invalid", "config", "username", "channel"],
                "severity": Severity.MINOR,
                "approval": ApprovalLevel.AUTO_FIX
            },
            "outdated_dependency": {
                "keywords": ["deprecated", "outdated", "old version"],
                "severity": Severity.MINOR,
                "approval": ApprovalLevel.AUTO_FIX
            },
            "missing_import": {
                "keywords": ["modulenotfound", "importerror"],
                "severity": Severity.MEDIUM,
                "approval": ApprovalLevel.AUTO_FIX
            }
        }
        
        self.approval_required_patterns = {
            "logic_error": {
                "keywords": ["logic", "algorithm", "calculation"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.REQUEST_APPROVAL
            },
            "security_issue": {
                "keywords": ["security", "vulnerability", "exploit"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.REQUEST_APPROVAL
            },
            "database_change": {
                "keywords": ["database", "schema", "migration"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.REQUEST_APPROVAL
            },
            "trading_strategy": {
                "keywords": ["strategy", "risk", "position", "trade"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.REQUEST_APPROVAL
            }
        }
        
        self.manual_only_patterns = {
            "api_credentials": {
                "keywords": ["api key", "token", "credentials", "password"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.MANUAL_ONLY
            },
            "wallet_access": {
                "keywords": ["wallet", "private key", "funds"],
                "severity": Severity.CRITICAL,
                "approval": ApprovalLevel.MANUAL_ONLY
            }
        }
    
    def classify(self, issue: Dict) -> ClassifiedIssue:
        """
        Classify an issue and determine appropriate action
        
        Args:
            issue: Issue dict from monitor
            
        Returns:
            Classified issue with recommended action
        """
        issue_text = f"{issue['type']} {issue['log_line']}".lower()
        
        # Check manual-only patterns first (highest priority)
        for pattern_name, pattern in self.manual_only_patterns.items():
            if self._matches_pattern(issue_text, pattern['keywords']):
                return ClassifiedIssue(
                    issue_type=pattern_name,
                    severity=pattern['severity'],
                    approval_required=pattern['approval'],
                    confidence=0.95,
                    description=f"Manual intervention required: {pattern_name}",
                    proposed_fix="Human must handle this manually",
                    raw_issue=issue
                )
        
        # Check approval-required patterns
        for pattern_name, pattern in self.approval_required_patterns.items():
            if self._matches_pattern(issue_text, pattern['keywords']):
                return ClassifiedIssue(
                    issue_type=pattern_name,
                    severity=pattern['severity'],
                    approval_required=pattern['approval'],
                    confidence=0.85,
                    description=f"Approval needed for: {pattern_name}",
                    proposed_fix="Will generate fix and request approval",
                    raw_issue=issue
                )
        
        # Check auto-fix patterns
        for pattern_name, pattern in self.auto_fix_patterns.items():
            if self._matches_pattern(issue_text, pattern['keywords']):
                return ClassifiedIssue(
                    issue_type=pattern_name,
                    severity=pattern['severity'],
                    approval_required=pattern['approval'],
                    confidence=0.92,
                    description=f"Can auto-fix: {pattern_name}",
                    proposed_fix="Will generate and apply fix automatically",
                    raw_issue=issue
                )
        
        # Unknown issue - default to request approval
        return ClassifiedIssue(
            issue_type="unknown",
            severity=Severity.MEDIUM,
            approval_required=ApprovalLevel.REQUEST_APPROVAL,
            confidence=0.5,
            description="Unknown issue type",
            proposed_fix="Will analyze and propose fix",
            raw_issue=issue
        )
    
    def _matches_pattern(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any keyword in the pattern"""
        return any(keyword.lower() in text for keyword in keywords)
    
    def filter_by_confidence(self, classified_issues: List[ClassifiedIssue], min_confidence: float = 0.7) -> List[ClassifiedIssue]:
        """Filter issues by minimum confidence threshold"""
        return [issue for issue in classified_issues if issue.confidence >= min_confidence]
    
    def get_auto_fixable_issues(self, classified_issues: List[ClassifiedIssue]) -> List[ClassifiedIssue]:
        """Get issues that can be auto-fixed"""
        return [
            issue for issue in classified_issues 
            if issue.approval_required == ApprovalLevel.AUTO_FIX 
            and issue.confidence >= 0.9
        ]
    
    def get_approval_required_issues(self, classified_issues: List[ClassifiedIssue]) -> List[ClassifiedIssue]:
        """Get issues that require approval"""
        return [
            issue for issue in classified_issues 
            if issue.approval_required == ApprovalLevel.REQUEST_APPROVAL
        ]


if __name__ == "__main__":
    # Test the classifier
    classifier = IssueClassifier()
    
    test_issues = [
        {
            "type": "telegram_error",
            "log_line": "UsernameInvalidError: Nobody is using this username",
            "severity": "medium"
        },
        {
            "type": "security_issue",
            "log_line": "Potential SQL injection vulnerability detected",
            "severity": "critical"
        },
        {
            "type": "import_error",
            "log_line": "ModuleNotFoundError: No module named 'requests'",
            "severity": "medium"
        }
    ]
    
    print("🔍 Testing Issue Classifier\n")
    for issue in test_issues:
        classified = classifier.classify(issue)
        print(f"Issue: {classified.issue_type}")
        print(f"Severity: {classified.severity.value}")
        print(f"Approval: {classified.approval_required.value}")
        print(f"Confidence: {classified.confidence:.0%}")
        print(f"Fix: {classified.proposed_fix}\n")
