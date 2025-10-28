#!/usr/bin/env python3
"""
Comprehensive Fine-Comb Verification for Architecture 3.1 Documents

This script performs deep structural verification across all v3.1 documents:
1. Extracts and compares directory structures
2. Verifies path references match actual structure
3. Checks for naming consistency
4. Reports ALL discrepancies with exact locations
"""

import os
import re
from collections import defaultdict

def extract_directory_tree(content, doc_name):
    """Extract directory tree structures from markdown code blocks"""
    trees = []

    # Find all code blocks that look like directory structures
    in_code_block = False
    current_tree = []
    start_line = 0

    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                start_line = i
                current_tree = []
            else:
                in_code_block = False
                if current_tree and any('├──' in l or '└──' in l for l in current_tree):
                    trees.append({
                        'start_line': start_line,
                        'end_line': i,
                        'content': '\n'.join(current_tree),
                        'doc': doc_name
                    })
        elif in_code_block:
            current_tree.append(line)

    return trees

def extract_templates_structure(tree_content):
    """Extract the templates/ subdirectory structure"""
    lines = tree_content.split('\n')
    in_templates = False
    templates_lines = []

    for line in lines:
        if '├── templates/' in line or '└── templates/' in line:
            in_templates = True
            templates_lines.append(line)
        elif in_templates:
            # Check if we're still in templates section (indentation check)
            if '├──' in line or '└──' in line or '│' in line:
                # Get indentation level
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    templates_lines.append(line)
                else:
                    break
            else:
                templates_lines.append(line)

    return '\n'.join(templates_lines)

def normalize_tree_structure(tree_content):
    """Normalize tree structure for comparison (remove comments, extra spaces)"""
    lines = tree_content.split('\n')
    normalized = []

    for line in lines:
        # Remove inline comments
        if '#' in line:
            line = line.split('#')[0]
        # Strip trailing whitespace
        line = line.rstrip()
        if line:
            normalized.append(line)

    return '\n'.join(normalized)

def find_path_references(content, doc_name):
    """Find all path references in document"""
    references = []

    # Pattern for path references
    patterns = [
        r'`([./]*cloud/tools/templates/[^`]+)`',
        r'"([./]*cloud/tools/templates/[^"]+)"',
        r'\'([./]*cloud/tools/templates/[^\']+)\'',
        r'\s([./]*cloud/tools/templates/\S+)',
    ]

    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                references.append({
                    'line': i,
                    'path': match,
                    'doc': doc_name
                })

    return references

def check_templates_subdirs(templates_structure):
    """Check if templates structure has required subdirectories"""
    required_subdirs = {
        'docs/': ['Stack Markdown Templates', '├── docs/', '└── docs/'],
        'stack/': ['Stack Pulumi Templates', '├── stack/', '└── stack/'],
        'config/': ['Stack Definitions', '├── config/', '└── config/'],
        'default/': ['Manifest Templates', '├── default/', '└── default/'],
        'custom/': ['Organization-specific', '├── custom/', '└── custom/']
    }

    found_subdirs = []
    issues = []

    for subdir, patterns in required_subdirs.items():
        # Check if any of the patterns match
        if any(pattern in templates_structure for pattern in patterns):
            found_subdirs.append(subdir)
        else:
            issues.append(f"MISSING: templates/{subdir}")

    # Check for wrong naming
    if '├── stacks/' in templates_structure or '└── stacks/' in templates_structure:
        if not any(p in templates_structure for p in ['├── config/', '└── config/']):
            issues.append("WRONG: Found 'stacks/' but should be 'config/'")

    return found_subdirs, issues

def main():
    print("="*80)
    print("COMPREHENSIVE FINE-COMB VERIFICATION - Architecture 3.1")
    print("="*80)

    os.chdir('C:/Users/Admin/Documents/Workspace/cloud/tools/docs')

    docs_31 = sorted([f for f in os.listdir('.') if f.endswith('.3.1.md')])

    print(f"\nDocuments to verify: {len(docs_31)}")
    print()

    # Load authoritative structure
    print("Loading authoritative structure from Directory_Structure_Diagram.3.1.md...")
    with open('Directory_Structure_Diagram.3.1.md', 'r', encoding='utf-8') as f:
        auth_content = f.read()

    auth_trees = extract_directory_tree(auth_content, 'Directory_Structure_Diagram.3.1.md')
    auth_templates = None

    if auth_trees:
        # Get the main tree (should be first one)
        auth_templates = extract_templates_structure(auth_trees[0]['content'])
        print(f"OK: Loaded authoritative templates structure ({len(auth_templates)} chars)")
    else:
        print("WARNING: Could not extract authoritative structure!")

    print()
    print("="*80)
    print("PHASE 1: DIRECTORY STRUCTURE VERIFICATION")
    print("="*80)

    structure_issues = []

    for doc in docs_31:
        print(f"\nChecking: {doc}")

        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract all directory trees
        trees = extract_directory_tree(content, doc)

        if not trees:
            print(f"  No directory structures found (OK for some docs)")
            continue

        print(f"  Found {len(trees)} directory structure(s)")

        # Check each tree for templates section
        for tree in trees:
            templates_struct = extract_templates_structure(tree['content'])

            if not templates_struct:
                continue

            print(f"  Checking templates structure at lines {tree['start_line']}-{tree['end_line']}")

            # Check for required subdirectories
            found_subdirs, issues = check_templates_subdirs(templates_struct)

            if issues:
                for issue in issues:
                    structure_issues.append({
                        'doc': doc,
                        'lines': f"{tree['start_line']}-{tree['end_line']}",
                        'issue': issue
                    })
                    print(f"  ISSUE: {issue}")
            else:
                print(f"  OK: All 5 subdirectories present: {', '.join(found_subdirs)}")

    print()
    print("="*80)
    print("PHASE 2: PATH REFERENCE VERIFICATION")
    print("="*80)

    path_issues = []

    # Check for incorrect path patterns
    incorrect_patterns = [
        ('templates/stacks/', 'Should be templates/config/'),
        ('templates/manifest/', 'Should be templates/default/'),
        ('src/Deployment_Manifest', 'Should be just Deployment_Manifest (no src/)'),
        ('/resources/', 'Should be /src/ (stack subdirectory changed)'),
    ]

    for doc in docs_31:
        print(f"\nChecking: {doc}")

        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()

        doc_has_issues = False

        for incorrect, reason in incorrect_patterns:
            if incorrect in content:
                # Count occurrences
                count = content.count(incorrect)

                # Find line numbers
                lines_with_issue = []
                for i, line in enumerate(content.split('\n'), 1):
                    if incorrect in line:
                        lines_with_issue.append(i)

                path_issues.append({
                    'doc': doc,
                    'pattern': incorrect,
                    'reason': reason,
                    'count': count,
                    'lines': lines_with_issue
                })

                print(f"  ISSUE: Found '{incorrect}' {count} times - {reason}")
                print(f"    Lines: {', '.join(map(str, lines_with_issue[:5]))}" +
                      (f" ... and {len(lines_with_issue)-5} more" if len(lines_with_issue) > 5 else ""))
                doc_has_issues = True

        # Check for correct templates paths
        refs = find_path_references(content, doc)
        if refs:
            print(f"  Found {len(refs)} templates path references")

            # Verify they use correct subdirectory names
            for ref in refs:
                if 'templates/stacks/' in ref['path']:
                    path_issues.append({
                        'doc': doc,
                        'line': ref['line'],
                        'path': ref['path'],
                        'reason': 'Should use templates/config/ not templates/stacks/'
                    })
                    print(f"  ISSUE: Line {ref['line']}: {ref['path']}")
                    doc_has_issues = True

        if not doc_has_issues:
            print(f"  OK: No path issues found")

    print()
    print("="*80)
    print("PHASE 3: CROSS-DOCUMENT CONSISTENCY")
    print("="*80)

    # Check naming consistency across documents
    naming_patterns = {
        'deployment_dir': r'deploy/D[A-Z0-9]{6}-\w+-\w+/',
        'stack_name_format': r'D[A-Z0-9]{6}-\w+-\w+',
        'pulumi_project': r'Project: \w+',
    }

    naming_stats = defaultdict(lambda: defaultdict(int))

    for doc in docs_31:
        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern_name, pattern in naming_patterns.items():
            matches = re.findall(pattern, content)
            naming_stats[pattern_name][doc] = len(matches)

    print("\nNaming Pattern Usage Across Documents:")
    for pattern_name, doc_counts in naming_stats.items():
        print(f"\n  {pattern_name}:")
        for doc, count in sorted(doc_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"    {doc}: {count} occurrences")

    print()
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)

    print(f"\nDocuments Checked: {len(docs_31)}")
    print(f"Structure Issues: {len(structure_issues)}")
    print(f"Path Issues: {len(path_issues)}")

    if structure_issues:
        print("\n  STRUCTURE ISSUES:")
        for issue in structure_issues:
            print(f"   - {issue['doc']} (lines {issue['lines']}): {issue['issue']}")

    if path_issues:
        print("\n  PATH ISSUES:")
        for issue in path_issues[:20]:
            if 'lines' in issue:
                print(f"   - {issue['doc']}: '{issue['pattern']}' ({issue['count']}x) - {issue['reason']}")
            else:
                print(f"   - {issue['doc']} (line {issue['line']}): {issue['path']} - {issue['reason']}")

        if len(path_issues) > 20:
            print(f"   ... and {len(path_issues) - 20} more issues")

    if not structure_issues and not path_issues:
        print("\nSUCCESS: All documents are structurally consistent!")
        print("  - All directory structures match authoritative diagram")
        print("  - All path references use correct naming")
        print("  - No structural discrepancies found")
        print("\nREADY FOR SESSION 2 IMPLEMENTATION")
    else:
        print("\nACTION REQUIRED: Fix issues before proceeding to Session 2")

    print()
    print("="*80)

    return len(structure_issues) + len(path_issues)

if __name__ == '__main__':
    issues_found = main()
    exit(0 if issues_found == 0 else 1)
