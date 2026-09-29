"""
THE DATA MART TEST CUSTOMERS - the four numbers, and what each one is actually good for.

WHY NO NAMES, EMIRATES IDs OR CHASSIS NUMBERS ARE IN THIS FILE
Two reasons, and the second one is the one that matters:

  1. YOU CANNOT ASSERT ON THEM ANYWAY. apps/api deliberately strips customerName,
     emiratesId, mobileNo, chassisNo and nationality out of every Data Mart response before
     anything downstream sees it (docs/datamart-lookup-response-shape.md - the drop list is a
     hard requirement, not a preference). The ticket shows the name the CUSTOMER STATED at
     intake, never AWNIC's record of it. A test asserting "the ticket shows the Data Mart
     customer name" would be asserting something the system is designed not to do.

  2. QA/ IS NOT GITIGNORED. .gitignore excludes QA/*.pdf|xlsx|csv|docx and nothing else, so
     this file is committed. Emirates IDs in git history cannot practically be removed.

The fields kept below - mobile, policy, claim, department - are reference identifiers, and
they are precisely the ones that survive minimisation and can therefore be checked on screen.
If a scenario ever genuinely needs a full record, put it in customers.local.py and add that
name to .gitignore; do not widen this file.

WHERE THIS CAME FROM
Live Data Mart responses for three numbers (provided 2026-09-09) plus the fourth from
docs/datamart-uat-test-details.md. All four are AWNIC UAT numbers; lookups are READ ONLY and
cannot alter a real customer's record.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataMartCustomer:
    """One Data Mart search key and the records it returns."""

    #: The mobile number - the search key itself, and the only key confirmed to match.
    mobile: str
    policies: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()
    departments: tuple[str, ...] = ()
    #: How many records the lookup returns in total.
    record_count: int = 0
    #: True when the number maps to MANY different people. See MULTI_CUSTOMER_NUMBER.
    is_multi_customer: bool = False
    notes: str = ""

    @property
    def policy(self) -> str:
        """The single policy, for the one-record customers. Raises rather than silently
        picking the first of several - a test that mixes one customer's policy with
        another's claim is worse than a test that fails."""
        if len(self.policies) != 1:
            raise ValueError(
                f"{self.mobile} has {len(self.policies)} policies, so 'the' policy is "
                "ambiguous. Pick one from .policies explicitly."
            )
        return self.policies[0]

    @property
    def claim(self) -> str:
        if len(self.claims) != 1:
            raise ValueError(
                f"{self.mobile} has {len(self.claims)} claims, so 'the' claim is ambiguous. "
                "Pick one from .claims explicitly."
            )
        return self.claims[0]


# ======================================================================
# The four numbers
# ======================================================================

#: NOT A CUSTOMER - a shared test number. 20 records spanning about 18 DIFFERENT people and
#: companies, individuals and corporates, across Motor and General Accident. There is no
#: single customer/policy/claim triple to build a scenario on, so this is deliberately given
#: no policies or claims: use it to exercise a MULTI-MATCH lookup, never an identity check.
#: It also contains one exactly duplicated record (same policy and claim twice), which makes
#: it a natural fixture for duplicate handling but a bad one for counting.
MULTI_CUSTOMER_NUMBER = DataMartCustomer(
    mobile="0560000000",
    departments=("Motor", "General Accident"),
    record_count=20,
    is_multi_customer=True,
    notes="~18 distinct customers on one number; contains one exact duplicate record.",
)

#: A clean single-record Motor customer. Policy is EXPIRED (2023-06-29) - fine for lookup and
#: reference assertions, wrong for anything that needs a live policy.
SINGLE_MOTOR_CUSTOMER = DataMartCustomer(
    mobile="0564544403",
    policies=("40/9018/90/2022/7608",),
    claims=("40/9018/90/2022/6929",),
    departments=("Motor",),
    record_count=1,
    notes="One record. Policy expired 2023-06-29. Claim status REGISTERED.",
)

#: A second clean single-record Motor customer - use this one whenever a test needs TWO
#: unrelated customers (duplicate detection, customer-history isolation). Policy also expired.
SECOND_SINGLE_MOTOR_CUSTOMER = DataMartCustomer(
    mobile="0561609000",
    policies=("81/9018/90/2021/4055",),
    claims=("81/9018/90/2022/630",),
    departments=("Motor",),
    record_count=1,
    notes="One record. Policy expired 2022-10-26. Claim status REGISTERED.",
)

#: The richest of the four, and the only one with all THREE record categories (claims,
#: policies and quotes). Broker-routed history is mixed - 2 of 5 claim/policy records carry a
#: channel - so parse_datamart_response returns is_broker_routed: true. The worked example in
#: docs/datamart-lookup-response-shape.md uses this number.
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

ALL: tuple[DataMartCustomer, ...] = (
    MULTI_CUSTOMER_NUMBER,
    SINGLE_MOTOR_CUSTOMER,
    SECOND_SINGLE_MOTOR_CUSTOMER,
    BROKER_ROUTED_CUSTOMER,
)

#: The ones safe for "this customer, this policy, this claim" scenarios - i.e. everything
#: except the shared multi-customer number.
USABLE_AS_ONE_CUSTOMER: tuple[DataMartCustomer, ...] = tuple(
    customer for customer in ALL if not customer.is_multi_customer
)


def by_mobile(mobile: str) -> DataMartCustomer:
    for customer in ALL:
        if customer.mobile == mobile:
            return customer
    raise KeyError(f"No Data Mart test customer for {mobile!r}.")


# ======================================================================
# What a ticket about these customers actually SAYS
# ======================================================================
# WHY THIS IS HERE AND NOT INVENTED PER TEST
# Tickets used to be created with "Automation test enquiry" and
# "automation.customer@example.ae". That works, and it tests almost nothing: it never carries
# a policy or claim number, so the customer-lookup path, the policy/claim display and the
# duplicate-detection rules are all exercised with empty values.
#
# The text below is written to read like something a Customer Care agent would really type
# after a phone call, and it is ANCHORED TO A REAL DATA MART CUSTOMER so the policy and claim
# on the ticket are that customer's genuine ones.
#
# THE ONE DELIBERATE GIVEAWAY: every subject ends with a short marker (see QA_MARKER). These
# tickets are created on a SHARED environment, and a complaint that reads as completely
# genuine is one somebody will action, chase, or report on. Realistic content plus a findable
# marker is the honest balance - and it keeps clean-up to a single search.


#: Appended to every subject an automated run creates. Searchable, and unmistakable to a human
#: reading the queue. Keep it short - it also has to stay readable in the list's Subject column.
QA_MARKER = "[QA-AUTO]"


@dataclass(frozen=True)
class TicketScenario:
    """One realistic reason a customer would get in touch, and who it is about."""

    customer: DataMartCustomer
    subject: str
    description: str
    #: Why a walk-in customer came to the branch instead of phoning. Only used when the
    #: Source is Walk-in, where the form makes it mandatory.
    walk_in_reason: str

    def subject_line(self, unique_suffix: str = "") -> str:
        """The subject as typed, carrying the QA marker and an optional run id."""
        tail = f" {unique_suffix}" if unique_suffix else ""
        return f"{self.subject} {QA_MARKER}{tail}"


#: A motor claim follow-up - the commonest real call the CC Centre takes, and the reason the
#: claim number matters. Uses the single-record customer so the claim is unambiguous.
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

#: A policy-renewal question, against the second single-record customer - so two tests that
#: both need "a customer" are not silently talking about the same one.
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

#: The richest customer (policies, claims AND quotes, broker-routed) - for anything that needs
#: a customer with real history behind them rather than a single record.
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

#: The default for any test that just needs "a realistic ticket".
DEFAULT_SCENARIO = MOTOR_CLAIM_FOLLOW_UP

SCENARIOS: tuple[TicketScenario, ...] = (
    MOTOR_CLAIM_FOLLOW_UP,
    POLICY_RENEWAL_QUERY,
    BROKER_CUSTOMER_COMPLAINT,
)


#: The call-back address put on tickets these tests create. Deliberately an obvious QA
#: address: the Data Mart records carry NO email field, so there is no real customer address
#: to use, and inventing one would put a plausible-looking stranger's address on a live
#: ticket. The mobile beside it IS real - that one has a genuine Data Mart record behind it.
QA_CONTACT_EMAIL = "qa.automation@awnic.ae"
