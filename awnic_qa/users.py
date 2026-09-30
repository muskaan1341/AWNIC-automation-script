"""
WHO THE TEST ACCOUNTS ARE - one place, built from the database, not from guesswork.

WHY THIS EXISTS
config.properties answers "which email do I sign in with for the supervisor test", and that
is all it can answer. It cannot say what DEPARTMENT that person is in, whether they hold a
role at all, or which two people differ only by department - and those are exactly the facts
a scoping test needs. Spreading them through the test files is how a suite ends up asserting
something that was true once.

WHERE THIS CAME FROM
A join of three exports taken on 2026-09-09: the `user` table, the `user_roles` table, and
`app/teams/seed_data.py`'s ROLE_PERMISSIONS.

HOW THE ROLE NAMES WERE RESOLVED - read this before trusting the `role` field
The `roles` table itself was NOT exported, so `user_roles` gave role IDs and no names. The
IDs below were resolved by anchoring on accounts whose role is known independently, and
every anchor agrees:

  831d6836…  admin               admin@awnic.ae, created by seed_demo.py as "admin"
  14f8382f…  cc_supervisor       supervisor@awnic.ae, seeded as "cc_supervisor"
  38cf5473…  cc_initiator        agent@awnic.ae, seeded as "cc_initiator". Corroborated by
                                 COUNT: 18 users hold it, and the "CC Ticket Initiator"
                                 round-robin pool has exactly 18 members.
  c3cfa37a…  dept_poc            held by General Accident's Level-1 escalation contacts
  83ee404c…  manager             held by General Accident's Level-2 (first escalation)
  265dffb6…  head_of_department  held by General Accident's Level-3 (final escalation)

The last three fall straight out of app/non_motor_sla/seed_data.py: the people listed at
each escalation LEVEL for a department hold the role that level belongs to. The deployed
config's own three mappings agree independently (v_mertia=hod, c_chiong=manager,
a_shalaby=dept_poc), which is a third witness.

Export the `roles` table if you want this pinned rather than inferred - see ROLES_UNVERIFIED.

ONE SOURCE OF TRUTH FOR EMAIL ADDRESSES (2026-09-17)
Every account that the settings files name (adminEmail, agentEmail, supervisorEmail,
hodEmail, managerEmail, deptPocEmail) takes its EMAIL from the loaded settings file - the
same value tests 01-15 read through BaseTest.get(). This module only adds the facts a
settings file cannot hold (role, department), looked up BY that email in _KNOWN_ACCOUNTS.
Before this, test_17 and test_18 signed in as a hard-coded agent@awnic.ae while every other
class used the file's agentEmail (a_hassouna@awnic.com under --env=deployed), so one run
exercised two different agents. If a settings file names an email that is not in
_KNOWN_ACCOUNTS, collection stops with a message saying so - add the real role and
department there; never guess them.

ONE ROLE HAS NO HOLDER AT ALL on UAT: compliance_officer (re-checked 2026-09-30 by a
read-only SELECT on user_roles - zero holders). complaint_handler is now held by
complaints.officer@awnic.ae and cc_supervisor by supervisor-gen@awnic.com (the old
supervisor@awnic.ae placeholder no longer exists there). See ROLE_HAS_NO_HOLDER.
"""

from __future__ import annotations

from dataclasses import dataclass

from awnic_qa.config import Config, ConfigError

#: Set True until somebody exports the `roles` table and confirms the six IDs above. The
#: role NAMES here are inferred (from three agreeing witnesses); the emails, departments
#: and "does this person hold any role at all" facts are read directly and are not in doubt.
ROLES_UNVERIFIED = True

# The eight role keys, exactly as app/teams/seed_data.py names them. Gate on these, never
# on a display label - "Head of Department" is what the screen shows, `head_of_department`
# is what the system decides with.
ADMIN = "admin"
HEAD_OF_DEPARTMENT = "head_of_department"
MANAGER = "manager"
COMPLAINT_HANDLER = "complaint_handler"
CC_SUPERVISOR = "cc_supervisor"
CC_INITIATOR = "cc_initiator"
COMPLIANCE_OFFICER = "compliance_officer"
DEPT_POC = "dept_poc"

#: Nobody on this environment holds these, so a test that needs one has nothing to sign in
#: as. Skip with a sentence saying so - do not fail, and do not quietly use a different role.
ROLE_HAS_NO_HOLDER = frozenset({COMPLIANCE_OFFICER})


@dataclass(frozen=True)
class Account:
    """One test account, as the database has it."""

    email: str
    name: str
    role: str | None
    department: str | None
    #: False when the person has never signed in - the Admin Portal shows them as "Pending
    #: Invitation". SIGNING IN AS THEM FLIPS THAT TO "Active" PERMANENTLY, because status is
    #: derived from last_login_at (app/api/app/users/schemas.py derive_status), not stored.
    #: Prefer an already-active account, and never use a pending one in a test that asserts
    #: the Admin Portal's Pending count.
    has_signed_in: bool = True

    @property
    def holds_a_role(self) -> bool:
        return self.role is not None


# ======================================================================
# The seeded @awnic.ae accounts (scripts/seed_demo.py)
# ======================================================================
# On a LOCAL seed these all exist. On UAT (read-only SELECT, 2026-09-30): supervisor@,
# hod@, complaints.manager@ and compliance@awnic.ae do NOT exist at all; admin@awnic.ae holds
# admin; complaints.officer@awnic.ae holds complaint_handler. The UAT settings file therefore
# names supervisor-gen@awnic.com for cc_supervisor, and real staff for HOD / manager.

#: Role and department for every email a settings file may name, keyed by email. The EMAIL
#: itself always comes from the settings file (see _configured_account); this table only
#: says who that person is. a_hassouna@awnic.com: cc_initiator per config.deployed.properties,
#: display name as shown in the deployed site's top bar; no department recorded.
_KNOWN_ACCOUNTS: dict[str, tuple[str, str | None, str | None]] = {
    "admin@awnic.ae": ("Platform Admin", ADMIN, None),
    "agent@awnic.ae": ("Aisha Rahman", CC_INITIATOR, None),
    "a_hassouna@awnic.com": ("Ahmed Nabil Saad Hassouna", CC_INITIATOR, None),
    "supervisor@awnic.ae": ("Omar Farooq", CC_SUPERVISOR, None),
    # UAT's only cc_supervisor holder - read-only SELECT on user/user_roles, 2026-09-30.
    "supervisor-gen@awnic.com": ("Supervisor-General Inquiry", CC_SUPERVISOR, None),
    # Holds complaint_handler on UAT since 2026-09-30 (same read-only check); no department.
    "complaints.officer@awnic.ae": ("Leila Nasser", COMPLAINT_HANDLER, None),
    "v_mertia@awnic.com": ("Vikrant Mertia", HEAD_OF_DEPARTMENT, "Broker & Motor Underwriting"),
    "c_chiong@awnic.com": ("Cindy Chiong", MANAGER, "Business Support"),
    "a_shalaby@awnic.com": ("Ahmed Mohamed Shalaby", DEPT_POC, "Medical Operations"),
}


def _configured_account(setting_key: str) -> Account:
    """The account a settings key names, with its role and department attached."""
    if not Config.file_name:
        raise ConfigError(
            "awnic_qa.users needs the settings file loaded first (conftest.py does this in "
            "pytest_configure). Import it from a test, not at tool start-up."
        )
    email = Config.get(setting_key)
    if email not in _KNOWN_ACCOUNTS:
        raise ConfigError(
            f"{Config.file_name} sets {setting_key} = {email}, but awnic_qa/users.py has no "
            "role/department recorded for that address. Add it to _KNOWN_ACCOUNTS with the "
            "values confirmed for this environment - do not guess them."
        )
    name, role, department = _KNOWN_ACCOUNTS[email]
    return Account(email, name, role, department)


PLATFORM_ADMIN = _configured_account("adminEmail")
CC_AGENT = _configured_account("agentEmail")
CC_SUPERVISOR_ACCOUNT = _configured_account("supervisorEmail")
COMPLAINT_HANDLER_ACCOUNT = _configured_account("complaintHandlerEmail")

# Seeded placeholders meant to hold NO role. On UAT (2026-09-30) none of these three exists
# at all, so there is still no role-less account to prove fail-closed with. The fourth,
# complaints.officer@awnic.ae, was dropped from this list: it now holds complaint_handler.
UNGRANTED_HOD = Account("hod@awnic.ae", "Hana Al Dhaheri", None, None)
UNGRANTED_COMPLAINTS_MANAGER = Account("complaints.manager@awnic.ae", "Marwan Haddad", None, None)
UNGRANTED_COMPLIANCE = Account("compliance@awnic.ae", "Yusuf Kareem", None, None)

# ======================================================================
# Real AWNIC staff accounts, by role
# ======================================================================

# Emails from the settings file (hodEmail / managerEmail / deptPocEmail); the variable names
# describe the account the files name today.
HOD_BROKER_MOTOR = _configured_account("hodEmail")
MANAGER_BUSINESS_SUPPORT = _configured_account("managerEmail")
DEPT_POC_MEDICAL_OPS = _configured_account("deptPocEmail")

# ----------------------------------------------------------------------
# General Accident - a whole department at every escalation level.
# ----------------------------------------------------------------------
# The only department where all three levels are covered by accounts that have signed in,
# which makes it the one department a full escalation-chain test can actually use.

# NOT USABLE FOR A LIVE TEST, and here so nobody reaches for it again. Every one of General
# Accident's Level-1 contacts (r_ulhaq, s_sistoza, a_babu, a_shah, general.accident@) has
# NEVER SIGNED IN, so signing in as any of them would permanently flip their Admin Portal
# status from "Pending Invitation" to "Active" on a shared environment.
GA_DEPT_POC = Account(
    "r_ulhaq@awnic.com", "Rizwan Ul Haq Meher Muhammad Zafar", DEPT_POC,
    "General Accident", has_signed_in=False,
)

# ----------------------------------------------------------------------
# Already-active dept_poc holders, in other departments
# ----------------------------------------------------------------------
# Both have signed in already, so using them changes nothing anybody can see.

DEPT_POC_FINANCE = Account(
    "m_mohanan@awnic.com", "Mahesh Thannikkattukalayil Mohanan", DEPT_POC, "Finance & Accounts"
)
DEPT_POC_BROKER_MOTOR = Account(
    "s_bayoumy@awnic.com", "Shimaa Abdelfatah Ahmed Bayoumy", DEPT_POC,
    "Broker & Motor Underwriting"
)
GA_MANAGER = Account(
    "p_manalo@awnic.com", "Primo Ramiro Manalo", MANAGER, "General Accident"
)
GA_HOD = Account(
    "k_sirish@awnic.com", "Sirish Kumar Seshagiri Rao", HEAD_OF_DEPARTMENT, "General Accident"
)

# ----------------------------------------------------------------------
# A SECOND department, for the only isolation test the product actually scopes.
# ----------------------------------------------------------------------
# dept_poc is the ONE role restricted to its own department's rows
# (VIEW_TICKETS_OWN_DEPARTMENT in app/tickets/policy.py). Every other role is org-wide or
# own-assigned, so "department A cannot see department B" is only testable dept_poc against
# dept_poc. These two are that pair.

#: Both are dept_poc, in DIFFERENT departments, and both have already signed in - so the
#: test costs nothing and nobody's Admin Portal status changes.
ISOLATION_PAIR = (DEPT_POC_MEDICAL_OPS, DEPT_POC_FINANCE)


# ======================================================================
# Lookups
# ======================================================================

ALL: tuple[Account, ...] = (
    PLATFORM_ADMIN,
    CC_AGENT,
    CC_SUPERVISOR_ACCOUNT,
    UNGRANTED_HOD,
    UNGRANTED_COMPLAINTS_MANAGER,
    COMPLAINT_HANDLER_ACCOUNT,
    UNGRANTED_COMPLIANCE,
    HOD_BROKER_MOTOR,
    MANAGER_BUSINESS_SUPPORT,
    DEPT_POC_MEDICAL_OPS,
    GA_DEPT_POC,
    GA_MANAGER,
    GA_HOD,
    DEPT_POC_FINANCE,
    DEPT_POC_BROKER_MOTOR,
)


def with_role(role: str) -> list[Account]:
    """Every account holding this role. Empty for a role nobody holds - check that, do not
    index blindly into the result."""
    return [account for account in ALL if account.role == role]


def in_department(department: str) -> list[Account]:
    """Every account whose User.department is this - the field dept_poc scoping compares."""
    return [account for account in ALL if account.department == department]


def by_email(email: str) -> Account:
    for account in ALL:
        if account.email == email:
            return account
    raise KeyError(f"No test account for {email!r}. Add it here rather than inlining it.")
