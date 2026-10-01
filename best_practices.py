"""Best practices validation based on Extreme Networks official KB articles.

Incorporates recommendations from:
- Fabric Engine Best Practice - Autosense Ports
- Fabric Engine Best Practice - Switch Selection and Features
- Fabric Engine Best Practice - Layer 2 VSN
- Fabric Engine Best Practice - Chassis Settings
- Fabric Engine Best Practice - DvR
- Fabric Engine Best Practice - Onboarding and Provisioning
- Fabric Engine Best Practice - vIST Cluster
- Fabric Engine Best Practice - Multi-Area SPBm
- Fabric Engine Best Practice - IS-IS/OSPF Route Policies
- Fabric Engine Best Practice - Architecture and Topology
- Fabric Engine Best Practice - Loop Prevention
- Fabric Engine Best Practice - Fabric Management
- Fabric Engine Best Practice - QoS
- Fabric Engine Best Practice - IP Multicast
"""
from dataclasses import dataclass
from typing import List
from enum import Enum
from parser import ShowTechAnalysis, Severity


class BestPracticeSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class BestPracticeFinding:
    category: str
    title: str
    description: str
    severity: BestPracticeSeverity
    recommendation: str


def validate_best_practices(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Validate against official Extreme Fabric Engine best practices."""
    findings = []

    # Lowercase once to avoid repeated expensive operations on large strings
    raw_text_lower = raw_text.lower()

    # Security & Management Best Practices
    findings.extend(_check_security_and_management(analysis, raw_text_lower))

    # Configuration Best Practices
    findings.extend(_check_configuration(analysis, raw_text_lower))

    # High Availability Best Practices
    findings.extend(_check_ha_and_redundancy(analysis, raw_text_lower))

    # Feature-Specific Best Practices
    findings.extend(_check_features(analysis, raw_text_lower))

    # Performance & Scaling Best Practices
    findings.extend(_check_performance(analysis, raw_text_lower))

    return findings


def _check_security_and_management(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Check security and management best practices from Extreme KB."""
    findings = []

    # From Chassis Settings Best Practice
    if "SSHD" not in analysis.system_info.enabled_features:
        findings.append(BestPracticeFinding(
            category="Security",
            title="SSH Not Enabled",
            description="SSHv2 is not enabled. SSHv2 secure mode takes precedence and disables other management protocols.",
            severity=BestPracticeSeverity.HIGH,
            recommendation="Enable SSHv2 using boot config flags. When SSHv2 is enabled, it automatically disables telnet/FTP on switch reset."
        ))

    # From Onboarding Best Practice - License check
    if "Trial Expired" in analysis.system_info.license:
        findings.append(BestPracticeFinding(
            category="Security",
            title="Trial License Expired - Features at Risk",
            description=f"License status: {analysis.system_info.license}. After 60-day factory default license expires, new features cannot be configured.",
            severity=BestPracticeSeverity.CRITICAL,
            recommendation="Obtain a valid license bound to this switch's Base MAC address. Generate through Extreme Networks Support Portal. Existing configs continue running but new features cannot load post-reboot."
        ))

    # From Fabric Management Best Practice
    if "SYSLOG" not in analysis.system_info.enabled_features:
        findings.append(BestPracticeFinding(
            category="Management",
            title="Syslog Not Configured",
            description="Syslog is not enabled. Fabric nodes should send logs to a central management system.",
            severity=BestPracticeSeverity.MEDIUM,
            recommendation="Configure syslog for centralized logging and monitoring. This is critical for fabric troubleshooting and operational visibility."
        ))

    # From Chassis Settings - SNMP check
    if "block-snmp" in raw_text or "boot config flag block-snmp" in raw_text:
        findings.append(BestPracticeFinding(
            category="Management",
            title="SNMP Blocked",
            description="SNMP is explicitly blocked via boot config flag. SNMP must be re-enabled if monitoring is needed.",
            severity=BestPracticeSeverity.MEDIUM,
            recommendation="If SNMP monitoring is required, execute: 'no boot config flag block-snmp' and save config."
        ))

    return findings


def _check_configuration(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Check general configuration best practices."""
    findings = []

    # From Architecture Best Practice - ZTP recommendation
    if "ztp" not in raw_text and "zero touch" not in raw_text:
        findings.append(BestPracticeFinding(
            category="Configuration",
            title="Zero Touch Provisioning Not Configured",
            description="ZTP+ (Zero Touch Provisioning) simplifies edge switch onboarding and is a core Fabric Engine benefit.",
            severity=BestPracticeSeverity.LOW,
            recommendation="For new deployments, use ZTP+ to automate edge switch configuration. Create ztp.py script on USB stick for automatic onboarding."
        ))

    # From Layer 2 VSN Best Practice
    if analysis.vlans > 200:
        findings.append(BestPracticeFinding(
            category="Configuration",
            title="High VLAN Count Impacting Scalability",
            description=f"Device has {analysis.vlans} VLANs configured. While SPB supports many VLANs, best practice limits traditional deployments to avoid complexity.",
            severity=BestPracticeSeverity.MEDIUM,
            recommendation="Best practice guidance: use ~100-200 VLANs in busy environments. Consolidate and review VLAN architecture to reduce management complexity."
        ))

    # From Chassis Settings - password security
    if "hsecure" not in raw_text:
        findings.append(BestPracticeFinding(
            category="Security",
            title="Strong Password Requirements Not Enforced",
            description="Password strength enforcement (hsecure flag) is not enabled.",
            severity=BestPracticeSeverity.MEDIUM,
            recommendation="Enable hsecure flag: 'boot config flag hsecure' requires passwords with 10+ chars, 2 uppercase, 2 lowercase, 2 numbers, 2 special characters."
        ))

    return findings


def _check_ha_and_redundancy(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Check high availability and redundancy best practices."""
    findings = []

    # From vIST Cluster Best Practice
    if "vIST" in raw_text and "SMLT" not in analysis.system_info.enabled_features:
        findings.append(BestPracticeFinding(
            category="Redundancy",
            title="vIST Cluster Without SMLT",
            description="vIST cluster detected but SMLT (Stackable Multi-Link Trunking) not enabled. SMLT provides sub-second failover.",
            severity=BestPracticeSeverity.HIGH,
            recommendation="Enable SMLT for vIST clusters: 1) Enable SPBM first, 2) Configure vIST link, 3) Enable MLT ports in SMLT mode, 4) Configure CVLANs. Use LACP for dynamic aggregation."
        ))

    # From vIST Cluster Best Practice - Gateway redundancy
    if "VRRP" not in analysis.system_info.enabled_features and "vIST" in raw_text:
        findings.append(BestPracticeFinding(
            category="Redundancy",
            title="Gateway Redundancy Not Configured",
            description="No VRRP or RSMLT configured for gateway redundancy on vIST cluster.",
            severity=BestPracticeSeverity.HIGH,
            recommendation="Use RSMLT for routing protocols or VRRP V3 for bridged access. Use unique VRID per VLAN (not VRID 1). RSMLT is preferred for true sub-second failover."
        ))

    # From Multi-Area SPBm Best Practice
    if "boundary" in raw_text or "multi.*area" in raw_text:
        findings.append(BestPracticeFinding(
            category="Redundancy",
            title="Multi-Area Deployment - Boundary Node Redundancy Check",
            description="Multi-area topology detected. Boundary node redundancy is critical for failover protection.",
            severity=BestPracticeSeverity.HIGH,
            recommendation="Deploy minimum 2 boundary nodes per area for failover. Ensure B-VIDs match across areas. Do not chain more than 5 areas. Make SD-WAN its own area."
        ))

    return findings


def _check_features(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Check feature-specific best practices."""
    findings = []

    # From Multicast Best Practice
    if "multicast" in raw_text:
        if "IGMP" not in raw_text:
            findings.append(BestPracticeFinding(
                category="Features",
                title="Multicast Configured Without IGMP Snooping",
                description="Multicast is in use but IGMP snooping may not be enabled on all required VLANs.",
                severity=BestPracticeSeverity.HIGH,
                recommendation="Enable IGMP snooping on all VLANs with multicast receivers. Consider IPMC-Lite (v8.8+) for Layer 3 multicast without licensing."
            ))

    # From IS-IS/OSPF Route Policies Best Practice
    if "ospf" in raw_text and "isis" in raw_text:
        findings.append(BestPracticeFinding(
            category="Features",
            title="Mixed IS-IS and OSPF Routing",
            description="Both IS-IS and OSPF are configured. Route redistribution requires careful filtering to prevent loops.",
            severity=BestPracticeSeverity.HIGH,
            recommendation="Use route maps with prefix lists. Run OSPF on L2VSN between tie-points for redundancy. Redistribute OSPF as ISIS external. Use accept policies to block external routes from being preferred."
        ))

    # From QoS Best Practice
    findings.append(BestPracticeFinding(
        category="Features",
        title="QoS Configuration Review Needed",
        description="QoS decisions must be explicit in SPB environments. Default trust behavior applies (802.1p and DSCP).",
        severity=BestPracticeSeverity.MEDIUM,
        recommendation="Decide: Layer 2 (802.1p) or Layer 3 (DSCP) QoS? Configure QoS-level (0-6) for untrusted ports. Auto-sense enables 802.1p override by default."
    ))

    return findings


def _check_performance(analysis: ShowTechAnalysis, raw_text: str) -> List[BestPracticeFinding]:
    """Check performance and scaling best practices."""
    findings = []

    # Check for high down port count
    if analysis.down_ports > 10:
        down_ratio = analysis.down_ports / len(analysis.interfaces) if analysis.interfaces else 0
        findings.append(BestPracticeFinding(
            category="Performance",
            title=f"High Number of Down Ports ({analysis.down_ports}/{len(analysis.interfaces)})",
            description=f"{analysis.down_ports} out of {len(analysis.interfaces)} ports are down ({down_ratio*100:.1f}%). This impacts fabric resilience.",
            severity=BestPracticeSeverity.HIGH if down_ratio > 0.3 else BestPracticeSeverity.MEDIUM,
            recommendation="Investigate root cause: cable issues, transceiver failures, or configuration errors. Verify physical connections and port status on connected equipment."
        ))

    # From Architecture Best Practice - port design
    if analysis.down_ports == 0:
        findings.append(BestPracticeFinding(
            category="Performance",
            title="Port Design Follows Best Practice",
            description="All ports are operational. Verify port counts match network design requirements (bandwidth, redundancy).",
            severity=BestPracticeSeverity.INFO,
            recommendation="Periodically verify port capacity aligns with traffic requirements. Use CLI Key Health Indicators to monitor available resources."
        ))

    # From Loop Prevention Best Practice
    if "slpp" not in raw_text:
        findings.append(BestPracticeFinding(
            category="Performance",
            title="SLPP Loop Detection Not Visible",
            description="Switched Loop Prevention Protocol (SLPP) guards against topology loops in fabric.",
            severity=BestPracticeSeverity.LOW,
            recommendation="Enable SLPP Guard on UNI edge ports. Use threshold 50/500 on vIST cluster peers. Configure SLPP timeout for automatic recovery (10-65535 sec) vs manual (0)."
        ))

    return findings
