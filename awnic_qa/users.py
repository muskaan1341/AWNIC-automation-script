"""
The test accounts: email, name, role and department.

Emails for the accounts named in the settings file (adminEmail, agentEmail, ...) come from
that file; this module adds the role and department for each one from _KNOWN_ACCOUNTS.
Role names were worked out from the user / user_roles data, not read from a roles table
(see ROLES_UNVERIFIED).
"""

from dataclasses import dataclass

from awnic_qa.config import Config, ConfigError

# True until the `roles` table is exported and the role names below are confirmed.
ROLES_UNVERIFIED = True

# The eight role keys, as the application names them.
ADMIN = "admin"
HEAD_OF_DEPARTMENT = "head_of_department"
MANAGER = "manager"
COMPLAINT_HANDLER = "complaint_handler"
CC_SUPERVISOR = "cc_supervisor"
CC_INITIATOR = "cc_initiator"
COMPLIANCE_OFFICER = "compliance_officer"
DEPT_POC = "dept_poc"

# Roles nobody holds on this environment. A test needing one should skip, not fail.
ROLE_HAS_NO_HOLDER = frozenset({COMPLIANCE_OFFICER})


@dataclass(frozen=True)
class Account:
    """One test account."""

    email: str
    name: str
    role: str | None
    department: str | None
    # False = never signed in. Signing in as them changes their Admin Portal status
    # from "Pending Invitation" to "Active" for good, so avoid those accounts.
    has_signed_in: bool = True

    @property
    def holds_a_role(self):
        return self.role is not None


# Name, role and department for every email a settings file may name.
_KNOWN_ACCOUNTS = {
    "admin@awnic.ae": ("Platform Admin", ADMIN, None),
    "agent@awnic.ae": ("Aisha Rahman", CC_INITIATOR, None),
    "a_hassouna@awnic.com": ("Ahmed Nabil Saad Hassouna", CC_INITIATOR, None),
    "supervisor@awnic.ae": ("Omar Farooq", CC_SUPERVISOR, None),
    "supervisor-gen@awnic.com": ("Supervisor-General Inquiry", CC_SUPERVISOR, None),
    "complaints.officer@awnic.ae": ("Leila Nasser", COMPLAINT_HANDLER, None),
    "v_mertia@awnic.com": ("Vikrant Mertia", HEAD_OF_DEPARTMENT, "Broker & Motor Underwriting"),
    "c_chiong@awnic.com": ("Cindy Chiong", MANAGER, "Business Support"),
    "a_shalaby@awnic.com": ("Ahmed Mohamed Shalaby", DEPT_POC, "Medical Operations"),
}


def _configured_account(setting_key):
    """The account whose email is in this setting, with its role and department."""
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

# Accounts with NO role (on UAT these do not exist at all).
UNGRANTED_HOD = Account("hod@awnic.ae", "Hana Al Dhaheri", None, None)
UNGRANTED_COMPLAINTS_MANAGER = Account("complaints.manager@awnic.ae", "Marwan Haddad", None, None)
UNGRANTED_COMPLIANCE = Account("compliance@awnic.ae", "Yusuf Kareem", None, None)

# Real staff accounts, emails from the settings file (hodEmail / managerEmail / deptPocEmail).
HOD_BROKER_MOTOR = _configured_account("hodEmail")
MANAGER_BUSINESS_SUPPORT = _configured_account("managerEmail")
DEPT_POC_MEDICAL_OPS = _configured_account("deptPocEmail")

# General Accident dept_poc. Has NEVER signed in - do not use it in a live test.
GA_DEPT_POC = Account(
    "r_ulhaq@awnic.com", "Rizwan Ul Haq Meher Muhammad Zafar", DEPT_POC,
    "General Accident", has_signed_in=False,
)

# Accounts that have already signed in, so using them changes nothing.
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

# Two dept_poc accounts in DIFFERENT departments, for the department-isolation test
# (dept_poc is the only role limited to its own department's tickets).
ISOLATION_PAIR = (DEPT_POC_MEDICAL_OPS, DEPT_POC_FINANCE)


ALL = (
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


def with_role(role):
    """Every account holding this role (may be an empty list)."""
    result = []
    for account in ALL:
        if account.role == role:
            result.append(account)
    return result


def in_department(department):
    """Every account in this department."""
    result = []
    for account in ALL:
        if account.department == department:
            result.append(account)
    return result


def by_email(email):
    for account in ALL:
        if account.email == email:
            return account
    raise KeyError(f"No test account for {email!r}. Add it here rather than inlining it.")
