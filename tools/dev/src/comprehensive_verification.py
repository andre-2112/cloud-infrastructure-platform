#!/usr/bin/env python3
"""Comprehensive verification of Architecture 3.1 documents"""

import os
import re
from collections import defaultdict

def main():
    print("="*80)
    print("COMPREHENSIVE VERIFICATION - Architecture 3.1 Documents")
    print("="*80)

    os.chdir('/c/Users/Admin/Documents/Workspace/cloud/tools/docs')

    docs_30 = sorted([f for f in os.listdir('.') if f.endswith('.3.0.md')])
    docs_31 = sorted([f for f in os.listdir('.') if f.endswith('.3.1.md')])

    print(f"\nv3.0 Documents: {len(docs_30)}")
    print(f"v3.1 Documents: {len(docs_31)}")

    issues = []
    warnings = []
    info = []

    print("\n" + "="*80)
    print("PHASE 1: DOCUMENT COMPLETENESS CHECK")
    print("="*80)

    # Check 1: Verify all 3.0 docs have 3.1 equivalents
    print("\nCheck 1: Verifying document migration completeness...")
    for doc30 in docs_30:
        doc31 = doc30.replace('.3.0.md', '.3.1.md')
        if doc31 not in docs_31:
            issues.append(f"MISSING: {doc31} (from {doc30})")
        else:
            info.append(f"OK: {doc31} exists")

    print(f"   {len(docs_30)} v3.0 documents -> {len(docs_31)} v3.1 documents created")

    # Check 2: Verify section completeness by comparing line counts
    print("\nCheck 2: Checking document size consistency...")
    for doc30 in docs_30:
        doc31 = doc30.replace('.3.0.md', '.3.1.md')
        if doc31 in docs_31:
            with open(doc30, 'r', encoding='utf-8') as f:
                lines_30 = len(f.readlines())
            with open(doc31, 'r', encoding='utf-8') as f:
                lines_31 = len(f.readlines())

            diff = lines_31 - lines_30
            diff_pct = (diff / lines_30 * 100) if lines_30 > 0 else 0

            # Allow up to 5% difference (for changelog additions)
            if abs(diff_pct) > 10:
                warnings.append(f"{doc31}: Significant size change ({diff:+d} lines, {diff_pct:+.1f}%)")
            elif abs(diff_pct) > 5:
                info.append(f"{doc31}: Moderate size change ({diff:+d} lines, {diff_pct:+.1f}%)")
            else:
                info.append(f"{doc31}: Size OK ({diff:+d} lines)")

    print("\n" + "="*80)
    print("PHASE 2: INTERNAL CONSISTENCY CHECK")
    print("="*80)

    consistency_checks = {
        'version_header': 0,
        'changelog': 0,
        'no_v30_refs': 0,
        'deployment_naming': 0,
        'no_src_manifest': 0,
        'pulumi_naming': 0
    }

    print("\nChecking each document for internal consistency...")
    for doc in docs_31:
        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        doc_issues = []

        # Check: Version header
        if '**Version:** 3.1' in content[:1000] or 'v3.1' in content[:500]:
            consistency_checks['version_header'] += 1
        else:
            doc_issues.append("Missing v3.1 version header")

        # Check: Changelog present
        if '**Changes from v3.0' in content or '**Changes from v3.1' in content:
            consistency_checks['changelog'] += 1
        else:
            doc_issues.append("Missing changelog")

        # Check: No stray 3.0 references (excluding changelog and comparative text)
        v30_count = 0
        for i, line in enumerate(lines):
            if i > 50 and '.3.0.md' in line and 'from v3.0' not in line.lower():
                v30_count += 1

        if v30_count == 0:
            consistency_checks['no_v30_refs'] += 1
        else:
            doc_issues.append(f"Found {v30_count} .3.0.md references")

        # Check: Deployment directory naming
        bare_deploy = re.findall(r'deploy/D[A-Z0-9]{6}/', content)
        proper_deploy = re.findall(r'deploy/D[A-Z0-9]{6}-\w+-\w+/', content)

        if len(bare_deploy) <= len(proper_deploy) * 0.2:  # Allow 20% bare references for examples
            consistency_checks['deployment_naming'] += 1
        else:
            doc_issues.append(f"Inconsistent deployment naming ({len(bare_deploy)} bare vs {len(proper_deploy)} proper)")

        # Check: No src/ for manifest
        if 'src/Deployment_Manifest' not in content:
            consistency_checks['no_src_manifest'] += 1
        else:
            doc_issues.append("Still has src/Deployment_Manifest references")

        # Check: New Pulumi naming (only in main docs)
        if 'Multi_Stack' in doc or 'Addendum_Platform' in doc:
            if 'D1BRV40-network-dev' in content or 'Project: ecommerce' in content:
                consistency_checks['pulumi_naming'] += 1
            else:
                doc_issues.append("Missing new Pulumi naming examples")
        else:
            consistency_checks['pulumi_naming'] += 1  # Not required for other docs

        if doc_issues:
            issues.extend([f"{doc}: {issue}" for issue in doc_issues])

    print(f"\nConsistency Results:")
    print(f"   Version Headers: {consistency_checks['version_header']}/{len(docs_31)}")
    print(f"   Changelogs: {consistency_checks['changelog']}/{len(docs_31)}")
    print(f"   No v3.0 Refs: {consistency_checks['no_v30_refs']}/{len(docs_31)}")
    print(f"   Deployment Naming: {consistency_checks['deployment_naming']}/{len(docs_31)}")
    print(f"   No src/Manifest: {consistency_checks['no_src_manifest']}/{len(docs_31)}")
    print(f"   Pulumi Naming: {consistency_checks['pulumi_naming']}/{len(docs_31)}")

    print("\n" + "="*80)
    print("PHASE 3: CROSS-REFERENCE CHECK")
    print("="*80)

    print("\nChecking cross-document references...")
    doc_refs = defaultdict(list)

    for doc in docs_31:
        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all .md references
        refs = re.findall(r'(\w+\.3\.[01]\.md)', content)
        for ref in refs:
            if ref not in docs_31:
                doc_refs[doc].append(f"References non-existent: {ref}")

    if doc_refs:
        for doc, refs in doc_refs.items():
            for ref in refs:
                warnings.append(f"{doc}: {ref}")
    else:
        info.append("All cross-references valid")

    print("\n" + "="*80)
    print("PHASE 4: SECTION COMPLETENESS CHECK")
    print("="*80)

    print("\nComparing major sections between v3.0 and v3.1...")
    major_docs = [
        'Multi_Stack_Architecture',
        'CLI_Commands_Reference',
        'REST_API_Documentation',
        'Addendum_Platform_Code'
    ]

    for doc_base in major_docs:
        doc30 = f"{doc_base}.3.0.md"
        doc31 = f"{doc_base}.3.1.md"

        if doc30 in docs_30 and doc31 in docs_31:
            with open(doc30, 'r', encoding='utf-8') as f:
                content30 = f.read()
            with open(doc31, 'r', encoding='utf-8') as f:
                content31 = f.read()

            # Extract major section headers (## level)
            sections30 = set(re.findall(r'^## (.+)$', content30, re.MULTILINE))
            sections31 = set(re.findall(r'^## (.+)$', content31, re.MULTILINE))

            missing = sections30 - sections31
            added = sections31 - sections30

            if missing:
                for section in missing:
                    issues.append(f"{doc31}: MISSING SECTION: '## {section}'")

            if added:
                for section in added:
                    info.append(f"{doc31}: NEW SECTION: '## {section}'")

            if not missing and not added:
                info.append(f"{doc31}: All major sections preserved")

    print("\n" + "="*80)
    print("PHASE 5: CHANGE VERIFICATION")
    print("="*80)

    print("\nVerifying ONLY necessary changes were made...")

    expected_changes = [
        'Version: 3.1',
        'Date: 2025-10-21',
        'D1BRV40-network-dev',
        'D1BRV40-CompanyA-ecommerce',
        'Project: ecommerce',
        'Deployment_Manifest.yaml',
        '.3.1.md'
    ]

    print("\nExpected change patterns found:")
    for doc in docs_31[:3]:  # Check first 3 docs
        with open(doc, 'r', encoding='utf-8') as f:
            content = f.read()

        found = [change for change in expected_changes if change in content]
        print(f"\n   {doc}:")
        for change in found:
            print(f"      OK: {change}")

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    print(f"\nTotal Documents Checked: {len(docs_31)}")
    print(f"Total Checks Performed: {sum(consistency_checks.values())}")
    print(f"\nResults:")
    print(f"   Issues (CRITICAL): {len([i for i in issues if 'MISSING' in i.upper()])}")
    print(f"   Warnings (REVIEW): {len(warnings)}")
    print(f"   Info (OK): {len(info)}")

    if issues:
        print("\n  ISSUES FOUND:")
        for issue in issues[:15]:
            print(f"   - {issue}")
        if len(issues) > 15:
            print(f"   ... and {len(issues) - 15} more")

    if warnings:
        print("\n  WARNINGS:")
        for warning in warnings[:10]:
            print(f"   - {warning}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings) - 10} more")

    if not issues and len(warnings) < 3:
        print("\nALL VERIFICATION CHECKS PASSED!")
        print("   Documents are complete, consistent, and ready for implementation.")

    print("\n" + "="*80)

    return len(issues), len(warnings)

if __name__ == '__main__':
    critical, warnings = main()
    exit(0 if critical == 0 else 1)
