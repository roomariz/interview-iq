from concurrent.futures import ThreadPoolExecutor
from threading import Event, get_ident

from interview_app_backend.services import question_generation_job as job


def test_worker_cancellation_does_not_read_streamlit_state():
    main_thread = get_ident()

    class MainThreadState(dict):
        def get(self, *args):
            assert get_ident() == main_thread, "worker accessed Streamlit state"
            return super().get(*args)

    event = Event()
    state = MainThreadState(role="Backend Engineer", difficulty="Medium", **{job.QUESTION_GENERATION_CANCEL_EVENT: event})
    payload = job._build_payload(state)
    with ThreadPoolExecutor(max_workers=1) as worker:
        assert worker.submit(payload["should_abort"]).result(timeout=2) is False
        event.set()
        assert worker.submit(payload["should_abort"]).result(timeout=2) is True


def test_worker_payload_copies_mutable_context():
    state = {"role": "Backend Engineer", "gap_analysis": {"skills": ["Python"]}}
    payload = job._build_payload(state)
    state["gap_analysis"]["skills"].append("React")
    assert payload["gap_analysis"] == {"skills": ["Python"]}
