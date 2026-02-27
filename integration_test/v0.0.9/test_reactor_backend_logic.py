import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from reactor_backend import ReactorBackend
from reactor_sim import ACTIONS, FAULTS, SCENARIOS


def test_state_shape_and_defaults():
    backend = ReactorBackend(scenario="cold_start", tick_s=0.2)
    payload, status = backend.get_state()
    assert status == 200
    assert payload["ok"] is True

    state = payload["state"]
    assert state["scenario"] == "cold_start"
    for key in (
        "time_s",
        "status",
        "controls",
        "actuators",
        "metrics",
        "alarms",
        "faults",
        "health",
        "mission",
        "alarm_state",
        "events_tail",
    ):
        assert key in state


def test_scenario_switch_and_tick_progress():
    backend = ReactorBackend(scenario="cold_start", tick_s=0.2)
    payload, status = backend.post_scenario({"name": "running"})
    assert status == 200
    assert payload["state"]["scenario"] == "running"

    t0 = payload["state"]["time_s"]
    backend.tick(1.0)
    payload, status = backend.get_state()
    assert status == 200
    assert payload["state"]["time_s"] > t0


def test_control_validation_and_update():
    backend = ReactorBackend()
    payload, status = backend.post_control({"rods": "bad"})
    assert status == 400
    assert payload["ok"] is False

    payload, status = backend.post_control({"rods": 44, "scram": True})
    assert status == 200
    controls = payload["state"]["controls"]
    assert controls["rods"] == 44.0
    assert controls["scram"] is True


def test_fault_toggle_and_clear_all():
    backend = ReactorBackend()
    payload, status = backend.post_fault({"name": "pump_degraded", "enabled": True})
    assert status == 200
    assert "pump_degraded" in payload["state"]["faults"]

    payload, status = backend.post_fault({"name": "clear_all"})
    assert status == 200
    assert payload["state"]["faults"] == []


def test_sim_pause_and_speed_effect():
    backend = ReactorBackend()
    backend.tick(0.5)
    payload, _ = backend.get_state()
    t0 = payload["state"]["time_s"]

    payload, status = backend.post_sim({"paused": True})
    assert status == 200
    backend.tick(1.0)
    payload, _ = backend.get_state()
    assert payload["state"]["time_s"] == t0

    payload, status = backend.post_sim({"paused": False, "speed": 2.0})
    assert status == 200
    backend.tick(0.5)
    payload, _ = backend.get_state()
    assert payload["state"]["time_s"] >= t0 + 1.0


def test_catalog_shape():
    backend = ReactorBackend()
    payload, status = backend.get_catalog()
    assert status == 200
    catalog = payload["catalog"]
    assert set(catalog["scenarios"].keys()) == set(SCENARIOS.keys())
    assert set(catalog["faults"].keys()) == set(FAULTS.keys())
    assert set(catalog["actions"].keys()) == set(ACTIONS.keys())
    assert "controls" in catalog
    assert "sim" in catalog


def test_events_history_and_action_flow():
    backend = ReactorBackend()
    backend.tick(1.0)

    payload, status = backend.get_events(limit=20)
    assert status == 200
    assert payload["ok"] is True
    assert len(payload["events"]) > 0

    payload, status = backend.get_history(limit=20)
    assert status == 200
    assert payload["ok"] is True
    assert len(payload["history"]) > 0

    payload, status = backend.post_action({"name": "ack_alarms"})
    assert status == 200
    assert payload["ok"] is True
    alarm_state = payload["state"]["alarm_state"]
    if alarm_state:
        assert all(item["acknowledged"] is True for item in alarm_state)

    payload, status = backend.post_action({"name": "quick_start"})
    assert status == 200
    assert payload["ok"] is True

    payload, status = backend.post_action({"name": "stabilize"})
    assert status == 200
    assert payload["ok"] is True

    payload, status = backend.post_action({"name": "does_not_exist"})
    assert status == 400
    assert payload["ok"] is False


def main() -> None:
    test_state_shape_and_defaults()
    test_scenario_switch_and_tick_progress()
    test_control_validation_and_update()
    test_fault_toggle_and_clear_all()
    test_sim_pause_and_speed_effect()
    test_catalog_shape()
    test_events_history_and_action_flow()
    print("reactor backend logic tests: PASS")


if __name__ == "__main__":
    main()
