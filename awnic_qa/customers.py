"""
The Data Mart test customers (AWNIC UAT numbers) and realistic ticket text about them.

Only reference numbers are kept here (mobile, policy, claim) - no names or Emirates IDs.
This file is committed to git, and the app hides those details on screen anyway.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DataMartCustomer:
    """One Data Mart mobile number and the records it returns."""

    mobile: str
    policies: tuple = ()
    claims: tuple = ()
    departments: tuple = ()
    record_count: int = 0
    # True when the number belongs to many different people.
    is_multi_customer: bool = False
    notes: str = ""

    @property
    def policy(self):
        """The one policy. Raises if there is not exactly one."""
        if len(self.policies) != 1:
            raise ValueError(
                f"{self.mobile} has {len(self.policies)} policies, so 'the' policy is "
                "ambiguous. Pick one from .policies explicitly."
            )
        return self.policies[0]

    @property
    def claim(self):
        """The one claim. Raises if there is not exactly one."""
        if len(self.claims) != 1:
            raise ValueError(
                f"{self.mobile} has {len(self.claims)} claims, so 'the' claim is ambiguous. "
                "Pick one from .claims explicitly."
            )
        return self.claims[0]


# A shared number with ~18 different customers. Use for multi-match lookups only.
MULTI_CUSTOMER_NUMBER = DataMartCustomer(
    mobile="0560000000",
    departments=("Motor", "General Accident"),
    record_count=20,
    is_multi_customer=True,
    notes="~18 distinct customers on one number; contains one exact duplicate record.",
)

# One Motor customer, one record. Policy expired.
SINGLE_MOTOR_CUSTOMER = DataMartCustomer(
    mobile="0564544403",
    policies=("40/9018/90/2022/7608",),
    claims=("40/9018/90/2022/6929",),
    departments=("Motor",),
    record_count=1,
    notes="One record. Policy expired 2023-06-29. Claim status REGISTERED.",
)

# A second one-record Motor customer, for tests that need two different customers.
SECOND_SINGLE_MOTOR_CUSTOMER = DataMartCustomer(
    mobile="0561609000",
    policies=("81/9018/90/2021/4055",),
    claims=("81/9018/90/2022/630",),
    departments=("Motor",),
    record_count=1,
    notes="One record. Policy expired 2022-10-26. Claim status REGISTERED.",
)

# Policies, claims and quotes; some records came through a broker.
BROKER_ROUTED_CUSTOMER = DataMartCustomer(
    mobile="0564687765",
    policies=(
        "20/9018/90/2026/20082",
        "20/9018/90/2026/20441",
        "20/2023/20/2026/99",
    ),
    claims=(
        "40/9018/90/2026/11",
        "20/9018/90/2021/5665",
    ),
    departments=("Motor",),
    record_count=8,
    notes="3 policies, 2 claims, 3 quotes. Mixed broker/direct -> is_broker_routed true.",
)

ALL = (
    MULTI_CUSTOMER_NUMBER,
    SINGLE_MOTOR_CUSTOMER,
    SECOND_SINGLE_MOTOR_CUSTOMER,
    BROKER_ROUTED_CUSTOMER,
)

# Every customer except the shared multi-customer number.
USABLE_AS_ONE_CUSTOMER = tuple(customer for customer in ALL if not customer.is_multi_customer)


def by_mobile(mobile):
    for customer in ALL:
        if customer.mobile == mobile:
            return customer
    raise KeyError(f"No Data Mart test customer for {mobile!r}.")


# ----------------------------------------------------------------------
# Ticket text
# ----------------------------------------------------------------------

# Added to every subject a test creates, so QA tickets are easy to find on the shared site.
QA_MARKER = "[QA-AUTO]"


@dataclass(frozen=True)
class TicketScenario:
    """A realistic reason a customer gets in touch, and which customer it is."""

    customer: DataMartCustomer
    subject: str
    description: str
    # Only used when Source is Walk-in (the form requires it then).
    walk_in_reason: str

    def subject_line(self, unique_suffix=""):
        """The subject with the QA marker and an optional run id on the end."""
        tail = f" {unique_suffix}" if unique_suffix else ""
        return f"{self.subject} {QA_MARKER}{tail}"


MOTOR_CLAIM_FOLLOW_UP = TicketScenario(
    customer=SINGLE_MOTOR_CUSTOMER,
    subject="Follow-up on motor claim settlement status",
    description=(
        "Customer called to ask where their motor claim has reached. The vehicle was "
        "assessed at the approved garage last week and they have not had an update since. "
        "They would like to know the expected settlement date and whether any further "
        "documents are needed from their side."
    ),
    walk_in_reason=(
        "Customer came to the branch in person because they had not received a call back "
        "about the claim assessment and wanted an update the same day."
    ),
)

POLICY_RENEWAL_QUERY = TicketScenario(
    customer=SECOND_SINGLE_MOTOR_CUSTOMER,
    subject="Query on motor policy renewal terms",
    description=(
        "Customer asked what their renewal premium will be and whether the no-claims "
        "discount still applies, as the policy is approaching expiry. They also asked "
        "whether the current cover can be extended without a fresh inspection."
    ),
    walk_in_reason=(
        "Customer visited the branch to discuss renewal options face to face and to bring "
        "the vehicle registration documents with them."
    ),
)

BROKER_CUSTOMER_COMPLAINT = TicketScenario(
    customer=BROKER_ROUTED_CUSTOMER,
    subject="Complaint about delay in broker-routed claim handling",
    description=(
        "Customer is unhappy with how long their claim has taken to progress and says they "
        "have had to chase the broker twice without a clear answer. They want the case "
        "reviewed and a firm timeline confirmed in writing."
    ),
    walk_in_reason=(
        "Customer came to the branch to escalate in person after two unanswered follow-ups "
        "through the broker."
    ),
)

# The default for any test that just needs "a realistic ticket".
DEFAULT_SCENARIO = MOTOR_CLAIM_FOLLOW_UP

SCENARIOS = (
    MOTOR_CLAIM_FOLLOW_UP,
    POLICY_RENEWAL_QUERY,
    BROKER_CUSTOMER_COMPLAINT,
)

# Contact email put on test tickets - an obvious QA address (Data Mart has no customer email).
QA_CONTACT_EMAIL = "qa.automation@awnic.ae"
