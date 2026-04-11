from app.core.cv.pipelines.multi_reid import run_detection_multi_reid, stop_events


def run_detection_dual_reid(
    source0: str = "0",
    source1: str = "1",
    conf: float = 0.5,
    task_id: str = "default",
):
    print("\n=== run_detection_dual_reid wrapper start ===")
    print("task_id =", task_id)
    print("source0 =", source0)
    print("source1 =", source1)
    print("conf =", conf)

    run_detection_multi_reid(
        sources=[source0, source1],
        conf=conf,
        task_id=task_id,
    )