"""The role model for event-service, shared by the integration and contract tests.

See langrenn-sprint/event-service-gui#215. All GET operations are open, and so
is the contestant search. Every write operation is listed here with the roles
that may call it.
"""

ADMIN = "admin"
EVENT_ADMIN = "event-admin"
RESULT_ADMIN = "result-admin"
CONTESTANT_ADMIN = "contestant-admin"

ROLES = [ADMIN, EVENT_ADMIN, RESULT_ADMIN, CONTESTANT_ADMIN]
# Roles that no longer exist, and must not give access:
REMOVED_ROLES = ["user-admin", "race-result", "race-office"]

# Event setup, before raceday:
EVENT_SETUP = {ADMIN, EVENT_ADMIN}
# Late entries on raceday: contestant-admin may add and change, not delete:
LATE_ENTRIES = {ADMIN, EVENT_ADMIN, CONTESTANT_ADMIN}
# Publishing results on raceday; event-admin keeps its raceday rights:
RESULTS = {ADMIN, EVENT_ADMIN, RESULT_ADMIN}

WRITE_ACCESS: dict[tuple[str, str], set[str]] = {
    ("POST", "/events"): EVENT_SETUP,
    ("PUT", "/events/{event_id}"): EVENT_SETUP,
    ("DELETE", "/events/{event_id}"): EVENT_SETUP,
    ("POST", "/events/{event_id}/generate-raceclasses"): EVENT_SETUP,
    ("POST", "/events/{event_id}/raceclasses"): EVENT_SETUP,
    ("DELETE", "/events/{event_id}/raceclasses"): EVENT_SETUP,
    ("PUT", "/events/{event_id}/raceclasses/{raceclass_id}"): EVENT_SETUP,
    ("DELETE", "/events/{event_id}/raceclasses/{raceclass_id}"): EVENT_SETUP,
    ("POST", "/events/{event_id}/contestants"): LATE_ENTRIES,
    ("PUT", "/events/{event_id}/contestants/{contestant_id}"): LATE_ENTRIES,
    ("DELETE", "/events/{event_id}/contestants/{contestant_id}"): EVENT_SETUP,
    ("DELETE", "/events/{event_id}/contestants"): EVENT_SETUP,
    ("POST", "/events/{event_id}/contestants/file"): EVENT_SETUP,
    ("POST", "/events/{event_id}/contestants/assign-bibs"): EVENT_SETUP,
    ("POST", "/events/{event_id}/results"): RESULTS,
    ("DELETE", "/events/{event_id}/results/{raceclass_name}"): RESULTS,
}


def access_cases(roles: list[str]) -> list[tuple[str, str, str, bool]]:
    """Return (method, path, role, allowed) for every write operation and role."""
    return [
        (method, path, role, role in allowed)
        for (method, path), allowed in WRITE_ACCESS.items()
        for role in roles
    ]
