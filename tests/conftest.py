"""Shared configuration for the camt-exceptions test suite."""

import os

from hypothesis import HealthCheck, settings

# The property tests are deterministic (``derandomize``) so a failure
# reproduces on the next run and in CI. No per-example deadline: the
# first call on a message type compiles its XSD, which is a cold-start
# cost, not a property of the code under test. Under mutmut they use a
# slimmer profile: each mutant re-runs the whole selection, so twenty
# examples per property keeps the mutation run within its CI budget
# while still exercising the invariant.
settings.register_profile("default", derandomize=True, deadline=None)
settings.register_profile(
    "mutation",
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.differing_executors],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))
