from pathlib import Path

from scripts.check_scrubbed import find_forbidden_matches, scan

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_placeholders_are_allowed_but_private_values_are_rejected() -> None:
    private_ip = ".".join(("10", "23", "45", "67"))
    machine_path = "C:" + "\\" + "Us" + "ers" + "\\actual-name\\project"
    assert find_forbidden_matches(r"C:\Users\<user>\project") == []
    assert find_forbidden_matches("/Users/REPLACE_ME/project") == []
    assert find_forbidden_matches("https://" + private_ip + "/service")
    assert find_forbidden_matches(machine_path)
####


def test_repository_passes_generic_scrub_scan() -> None:
    assert scan(REPOSITORY_ROOT) == []
####
